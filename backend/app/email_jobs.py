"""Taegliche transaktionale E-Mails, fuer die Stripe kein Ereignis erzeugt."""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from . import mailer, notifications
from .config import settings
from .database import SessionLocal
from .email_notifications import send_once
from .models import Swipe, User

# Ab wie vielen wartenden Profilen im Suchradius benachrichtigt wird.
QUEUE_THRESHOLD = 3

# Nach wie vielen Tagen ohne Vordergrund-Nutzung die Erinnerung fällig wird.
INACTIVITY_DAYS = 7

# Wochentag (Montag = 0), an dem die "offene Likes"-Mail läuft - einmal
# wöchentlich statt bei jedem täglichen Joblauf.
PENDING_LIKES_WEEKDAY = 0


def _utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _vienna_day_window(day: date) -> tuple[datetime, datetime]:
    start_local = datetime.combine(day, time.min, tzinfo=mailer.VIENNA)
    end_local = start_local + timedelta(days=1)
    return _utc_naive(start_local), _utc_naive(end_local)


def run_due_email_jobs(db: Session, now: datetime | None = None) -> dict[str, int]:
    """Versendet Faelliges und gibt nur aggregierte Zaehler zurueck."""
    current = now or datetime.now(timezone.utc).replace(tzinfo=None)
    local_day = current.replace(tzinfo=timezone.utc).astimezone(mailer.VIENNA).date()
    ending_start, ending_end = _vienna_day_window(local_day + timedelta(days=3))

    result: dict[str, int] = {"trial_ending_sent": 0, "trial_ended_sent": 0, "failed": 0}

    # Solange die Abogebuehr ausgesetzt ist, endet mit dem Probemonat gar
    # nichts: der Zugang bleibt (User.is_active_member()). "Dein Probemonat
    # laeuft ab" waere dann schlicht falsch - beide Mails entfallen, bis
    # BILLING_ENABLED wieder true ist. Die uebrigen Benachrichtigungen
    # (wartende Profile, Inaktivitaet) laufen unveraendert weiter.
    if not settings.billing_enabled:
        result.update(run_activity_notifications(db, current))
        return result

    base = db.query(User).filter(
        User.deleted_at.is_(None),
        User.is_banned.is_(False),
        User.email_verified_at.isnot(None),
        User.is_subscribed.is_(False),
        User.stripe_subscription_id.is_(None),
    )

    ending_users = base.filter(
        User.trial_ends_at >= ending_start,
        User.trial_ends_at < ending_end,
    ).all()
    ended_users = base.filter(
        User.trial_ends_at <= current,
        User.trial_ends_at > current - timedelta(days=2),
    ).all()

    for user in ending_users:
        key = f"trial:ending:{user.id}:{user.trial_ends_at.isoformat()}"
        sent = send_once(
            db,
            key,
            "free_trial_ending",
            lambda user=user: mailer.send_free_trial_ending(
                user.email, user.name, user.trial_ends_at
            ),
        )
        result["trial_ending_sent" if sent else "failed"] += 1

    for user in ended_users:
        key = f"trial:ended:{user.id}:{user.trial_ends_at.isoformat()}"
        sent = send_once(
            db,
            key,
            "free_trial_ended",
            lambda user=user: mailer.send_free_trial_ended(user.email, user.name),
        )
        result["trial_ended_sent" if sent else "failed"] += 1

    result.update(run_activity_notifications(db, current))
    return result


def run_activity_notifications(db: Session, current: datetime) -> dict[str, int]:
    """Wartende Profile, Inaktivität und offene Likes - E-Mail und App.

    Wartende Profile und Inaktivität sind an einen Tagesschlüssel gebunden,
    nicht an den Zustand allein: "3 Profile warten" bleibt tagelang wahr, ohne
    den Schlüssel ginge die Nachricht bei jedem Joblauf erneut raus. Offene
    Likes hängen entsprechend an einem Wochenschlüssel, siehe
    PENDING_LIKES_WEEKDAY unten.
    """
    local_date = current.replace(tzinfo=timezone.utc).astimezone(mailer.VIENNA).date()
    # Ein Wiener Kalendertag als Sperrschlüssel - derselbe Bezugsrahmen wie bei
    # den Abo-Mails oben, damit ein Nutzer nicht wegen der UTC-Grenze zweimal
    # am selben lokalen Tag angeschrieben wird.
    day_key = local_date.isoformat()
    iso_year, iso_week, _ = local_date.isocalendar()
    week_key = f"{iso_year}-W{iso_week:02d}"
    result = {"queue_notified": 0, "inactivity_notified": 0, "pending_likes_notified": 0}

    candidates = (
        db.query(User)
        .filter(
            User.deleted_at.is_(None),
            User.is_banned.is_(False),
            User.email_verified_at.isnot(None),
        )
        .all()
    )

    inactive_before = current - timedelta(days=INACTIVITY_DAYS)

    for user in candidates:
        # Wer gerade ohnehin in der App ist, braucht keine Erinnerung. Die
        # Inaktivitätsmail zuerst prüfen: sie schließt Deck- und Like-Nachricht
        # aus, sonst bekäme ein Rückkehrer mehrere Nachrichten am selben Tag.
        reference = user.last_active_at or user.created_at
        if reference is not None and reference <= inactive_before:
            days = max(INACTIVITY_DAYS, (current - reference).days)
            notifications.notify_inactivity(db, user, days, day_key)
            result["inactivity_notified"] += 1
            continue

        if (
            notifications.wants_email(user, notifications.NotificationTopic.queue_waiting)
            or notifications.wants_push(user, notifications.NotificationTopic.queue_waiting)
        ):
            # Nur die Schwelle interessiert, nicht das volle Deck: das spart bei
            # gut gefüllten Umkreisen den Großteil der Gym-Stapel.
            waiting = _waiting_count(db, user)
            if waiting >= QUEUE_THRESHOLD:
                notifications.notify_queue_waiting(db, user, waiting, day_key)
                result["queue_notified"] += 1

        # Nur einmal pro Woche prüfen, nicht bei jedem täglichen Joblauf -
        # der Wochenschlüssel wäre zwar ohnehin idempotent, aber ohne die
        # Tagesbedingung würde trotzdem jeden Tag umsonst gezählt.
        if local_date.weekday() == PENDING_LIKES_WEEKDAY and (
            notifications.wants_email(user, notifications.NotificationTopic.pending_likes)
            or notifications.wants_push(user, notifications.NotificationTopic.pending_likes)
        ):
            pending = _pending_likes_count(db, user)
            if pending >= 1:
                notifications.notify_pending_likes(db, user, pending, week_key)
                result["pending_likes_notified"] += 1

    return result


def _waiting_count(db: Session, user: User) -> int:
    """Wie viele Profile im Deck dieses Nutzers liegen (gedeckelt).

    Nutzt bewusst dieselbe Funktion wie der Swipe-Endpunkt, damit gemeldete und
    tatsächlich sichtbare Profile nicht auseinanderlaufen.
    """
    from .routers.swipes import deck_profiles

    if not user.is_active_member():
        # Ohne aktive Mitgliedschaft liefert /deck ohnehin nichts - dann über
        # wartende Profile zu schreiben, wäre eine Einladung in eine Bezahlwand.
        return 0
    return len(deck_profiles(db, user, limit=QUEUE_THRESHOLD))


def _pending_likes_count(db: Session, user: User) -> int:
    """Wie viele Mitglieder diesen Nutzer geliked haben, ohne dass er/sie schon
    reagiert hat (weder zurückgeliked noch gepasst).

    Ein Like, das bereits zu einem Match geführt hat, taucht hier nicht auf:
    dann hat der Nutzer selbst schon "like" geswiped, und genau das schließt
    die Zeile über den Anti-Join unten aus. Ein bereits gepasstes Profil
    ebenfalls nicht - das ist eine bereits getroffene Entscheidung, keine
    offene.
    """
    swiped_ids = db.query(Swipe.to_user_id).filter(Swipe.from_user_id == user.id)
    return (
        db.query(Swipe)
        .join(User, User.id == Swipe.from_user_id)
        .filter(
            Swipe.to_user_id == user.id,
            Swipe.action == "like",
            ~Swipe.from_user_id.in_(swiped_ids),
            User.deleted_at.is_(None),
            User.is_banned.is_(False),
        )
        .count()
    )


def main() -> None:
    db = SessionLocal()
    try:
        result = run_due_email_jobs(db)
    finally:
        db.close()
    print(result)
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
