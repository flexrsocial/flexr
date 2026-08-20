"""Idempotenter Versand transaktionaler E-Mails."""

from collections.abc import Callable
from datetime import datetime
from hashlib import sha256

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import EmailNotification


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
    # Keine Nutzer-, Stripe- oder Rechnungs-ID als Klartext in der
    # Versandhistorie speichern. Fuer die Idempotenz reicht der Hash.
    stored_key = sha256(notification_key.encode("utf-8")).hexdigest()
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
        record.sent_at = datetime.utcnow()
        db.commit()
        return True

    db.delete(record)
    db.commit()
    return False
