"""Idempotenter Versand transaktionaler E-Mails."""

from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import EmailNotification


def _stored_key(notification_key: str) -> str:
    # Keine Nutzer-, Stripe- oder Rechnungs-ID als Klartext in der
    # Versandhistorie speichern. Fuer die Idempotenz reicht der Hash.
    return sha256(notification_key.encode("utf-8")).hexdigest()


def sent_at(db: Session, notification_key: str) -> datetime | None:
    """Wann die Nachricht verschickt wurde - None, wenn (noch) nicht."""
    return (
        db.query(EmailNotification.sent_at)
        .filter(EmailNotification.notification_key == _stored_key(notification_key))
        .scalar()
    )


def send_once(
    db: Session,
    notification_key: str,
    kind: str,
    sender: Callable[[], bool],
) -> bool:
    """Versendet eine fachliche Nachricht hoechstens einmal.

    Die Reservierung wird vor dem SMTP-Aufruf gespeichert. Schlaegt der
    Versand fehl, wird sie wieder entfernt, damit ein spaeterer Webhook oder
    Job erneut versuchen kann.
    """
    stored_key = _stored_key(notification_key)
    record = (
        db.query(EmailNotification)
        .filter(EmailNotification.notification_key == stored_key)
        .first()
    )
    if record and record.sent_at:
        return True

    if record is None:
        record = EmailNotification(notification_key=stored_key, kind=kind)
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            # Ein paralleler Aufruf hat dieselbe Nachricht bereits reserviert.
            return True

    sent = sender()
    if sent:
        record.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        return True

    db.delete(record)
    db.commit()
    return False
