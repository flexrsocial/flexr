"""Taegliche transaktionale E-Mails, fuer die Stripe kein Ereignis erzeugt."""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from . import mailer, notifications
from .database import SessionLocal
from .email_notifications import send_once
from .models import User

# Ab wie vielen wartenden Profilen im Suchradius benachrichtigt wird.
QUEUE_THRESHOLD = 3

# Nach wie vielen Tagen ohne Vordergrund-Nutzung die Erinnerung fällig wird.
INACTIVITY_DAYS = 7


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

    result: dict[str, int] = {"trial_ending_sent": 0, "trial_ended_sent": 0, "failed": 0}

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
    """Wartende Profile und Inaktivität - E-Mail und App-Benachrichtigung.

    Beide Anlässe sind an einen Tagesschlüssel gebunden, nicht an den Zustand
    allein: "3 Profile warten" bleibt tagelang wahr, ohne den Schlüssel ginge
    die Nachricht bei jedem Joblauf erneut raus.
    """
    # Ein Wiener Kalendertag als Sperrschlüssel - derselbe Bezugsrahmen wie bei
    # den Abo-Mails oben, damit ein Nutzer nicht wegen der UTC-Grenze zweimal
    # am selben lokalen Tag angeschrieben wird.
    day_key = current.replace(tzinfo=timezone.utc).astimezone(mailer.VIENNA).date().isoformat()
    result = {"queue_notified": 0, "inactivity_notified": 0}

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
        # Inaktivitätsmail zuerst prüfen: sie schließt die Deck-Nachricht aus,
        # sonst bekäme ein Rückkehrer beide Nachrichten am selben Tag.
        reference = user.last_active_at or user.created_at
        if reference is not None and reference <= inactive_before:
            days = max(INACTIVITY_DAYS, (current - reference).days)
            notifications.notify_inactivity(db, user, days, day_key)
            result["inactivity_notified"] += 1
            continue

        if not (
            notifications.wants_email(user, notifications.NotificationTopic.queue_waiting)
            or notifications.wants_push(user, notifications.NotificationTopic.queue_waiting)
        ):
            # Beide Kanäle aus - dann auch nicht das (teure) Deck berechnen.
            continue
        # Nur die Schwelle interessiert, nicht das volle Deck: das spart bei
        # gut gefüllten Umkreisen den Großteil der Gym-Stapel.
        waiting = _waiting_count(db, user)
        if waiting >= QUEUE_THRESHOLD:
            notifications.notify_queue_waiting(db, user, waiting, day_key)
            result["queue_notified"] += 1

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
