"""Zustellung der Aktivitäts-Benachrichtigungen über beide Kanäle.

Drei Anlässe, zwei Kanäle: neues Match, wartende Profile im Suchradius und
Inaktivität - jeweils als E-Mail und als App-Benachrichtigung. Beide Kanäle
laufen bewusst durch dieselbe Funktion, damit ein Anlass nicht auf einem Kanal
anders entschieden wird als auf dem anderen.

Warum der Push-Teil hier und nicht im Client entschieden wird: FLEXR hat kein
FCM/APNs, die Apps holen ihre Benachrichtigungen per Hintergrundabgleich ab
(siehe models.PushNotification). Läge die Regel im Client, müssten Android und
iOS die Schalterlogik doppelt nachbauen und ein abgeschalteter Kanal wäre erst
nach dem nächsten App-Update wirksam.
"""

from datetime import datetime
from hashlib import sha256

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import mailer
from .email_notifications import send_once
from .models import NotificationTopic, PushNotification, User

# Welcher Schalter gilt für welchen Anlass. Ein Anlass ohne Eintrag würde
# ungefragt zugestellt - deshalb steht die Zuordnung an einer Stelle und wird
# unten konsequent nachgeschlagen.
_EMAIL_FLAG = {
    NotificationTopic.new_match: "notify_match_email",
    NotificationTopic.queue_waiting: "notify_queue_email",
    NotificationTopic.inactivity: "notify_inactive_email",
}
_PUSH_FLAG = {
    NotificationTopic.new_match: "notify_match_push",
    NotificationTopic.queue_waiting: "notify_queue_push",
    NotificationTopic.inactivity: "notify_inactive_push",
}


def wants_email(user: User, topic: NotificationTopic) -> bool:
    return bool(getattr(user, _EMAIL_FLAG[topic]))


def wants_push(user: User, topic: NotificationTopic) -> bool:
    return bool(getattr(user, _PUSH_FLAG[topic]))


def is_reachable(user: User) -> bool:
    """Konten, die grundsätzlich keine Werbe- oder Aktivitätspost bekommen.

    Gelöschte und gesperrte Konten sowie solche mit unbestätigter Adresse sind
    ausgenommen - dieselbe Bedingung, die auch die Abo-Mails in email_jobs.py
    anlegen.
    """
    return (
        user.deleted_at is None
        and not user.is_banned
        and user.email_verified_at is not None
    )


def queue_push(
    db: Session,
    user: User,
    topic: NotificationTopic,
    title: str,
    body: str,
    dedupe_key: str,
    target: str | None = None,
) -> bool:
    """Legt eine App-Benachrichtigung ins Zustellfach.

    Gibt True zurück, wenn dadurch etwas Neues entstanden ist. Ein bereits
    vorhandener dedupe_key ist kein Fehler, sondern der Normalfall bei
    wiederholten Jobläufen - dann passiert schlicht nichts.
    """
    if not is_reachable(user) or not wants_push(user, topic):
        return False

    # Wie bei den E-Mails nur den Hash speichern: der Klarschlüssel enthält die
    # Nutzer-ID und hätte in einer Zustellhistorie nichts verloren.
    stored_key = sha256(dedupe_key.encode("utf-8")).hexdigest()
    if db.query(PushNotification).filter(PushNotification.dedupe_key == stored_key).first():
        return False

    db.add(PushNotification(
        user_id=user.id,
        topic=topic,
        title=title,
        body=body,
        target=target,
        dedupe_key=stored_key,
    ))
    try:
        db.commit()
    except IntegrityError:
        # Paralleler Lauf war schneller - derselbe Anlass, nichts zu tun.
        db.rollback()
        return False
    return True


def send_email_once(
    db: Session,
    user: User,
    topic: NotificationTopic,
    dedupe_key: str,
    sender,
) -> bool:
    """E-Mail-Hälfte eines Anlasses - Schalter und Idempotenz in einem Schritt."""
    if not is_reachable(user) or not wants_email(user, topic):
        return False
    return send_once(db, dedupe_key, topic.value, sender)


# --- Die drei Anlässe ------------------------------------------------------

def notify_new_match(db: Session, user: User, match_name: str, match_id: str) -> None:
    """Beide Seiten eines frischen Matches benachrichtigen.

    Der Schlüssel hängt an der Match-ID, nicht am Zeitpunkt: ein zweiter Swipe
    auf dasselbe Profil erzeugt kein zweites Match und darf auch keine zweite
    Nachricht auslösen.
    """
    key = f"match:{match_id}:{user.id}"
    queue_push(
        db, user, NotificationTopic.new_match,
        title="Neues Match",
        body=f"{match_name} hat dich auch geliked.",
        dedupe_key=key,
        target="matches",
    )
    send_email_once(
        db, user, NotificationTopic.new_match, key,
        lambda: mailer.send_new_match(user.email, user.name, match_name),
    )


def notify_queue_waiting(db: Session, user: User, count: int, period_key: str) -> None:
    """Wartende Profile im Suchradius.

    period_key hält die Nachricht auf höchstens eine pro Zeitraum - ohne ihn
    würde jeder Joblauf erneut zustellen, solange das Deck gefüllt bleibt.
    """
    key = f"queue:{user.id}:{period_key}"
    queue_push(
        db, user, NotificationTopic.queue_waiting,
        title=f"{count} neue Profile",
        body="In deinem Umkreis warten neue Profile auf dich.",
        dedupe_key=key,
        target="swipe",
    )
    send_email_once(
        db, user, NotificationTopic.queue_waiting, key,
        lambda: mailer.send_queue_waiting(user.email, user.name, count),
    )


def notify_inactivity(db: Session, user: User, days: int, period_key: str) -> None:
    key = f"inactive:{user.id}:{period_key}"
    queue_push(
        db, user, NotificationTopic.inactivity,
        title="Lange nicht gesehen",
        body=f"Du warst {days} Tage nicht mehr in FLEXR.",
        dedupe_key=key,
        target="swipe",
    )
    send_email_once(
        db, user, NotificationTopic.inactivity, key,
        lambda: mailer.send_inactivity_reminder(user.email, user.name, days),
    )


def pending_for(db: Session, user_id: str, limit: int = 20) -> list[PushNotification]:
    return (
        db.query(PushNotification)
        .filter(
            PushNotification.user_id == user_id,
            PushNotification.delivered_at.is_(None),
        )
        .order_by(PushNotification.created_at)
        .limit(limit)
        .all()
    )


def mark_delivered(db: Session, user_id: str, ids: list[str]) -> int:
    if not ids:
        return 0
    now = datetime.utcnow()
    changed = (
        db.query(PushNotification)
        .filter(
            PushNotification.user_id == user_id,
            PushNotification.id.in_(ids),
            PushNotification.delivered_at.is_(None),
        )
        .update({PushNotification.delivered_at: now}, synchronize_session=False)
    )
    db.commit()
    return changed
