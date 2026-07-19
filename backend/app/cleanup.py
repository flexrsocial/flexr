"""Endgültige Löschung von Konten nach der 30-Tage-Karenzzeit.

Die Selbstlöschung (DELETE /api/profiles/me) deaktiviert das Konto nur
(deleted_at gesetzt). Dieses Modul löscht abgelaufene Konten endgültig -
inklusive der Fotos und Verifizierungs-Selfies aus dem Objekt-Storage.
Aufgerufen wird es opportunistisch beim Login (billige Abfrage, in der
Regel null Treffer) - so braucht es keinen eigenen Cron-Job.
"""

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .config import settings
from .models import Photo, User, VerificationRequest
from .storage import get_s3_client

logger = logging.getLogger("flexr.cleanup")

GRACE_PERIOD_DAYS = 30


def _object_key_from_url(url: str) -> str | None:
    base = settings.s3_public_base_url.rstrip("/")
    if base and url.startswith(base + "/"):
        return url[len(base) + 1:]
    return None


def _delete_objects(keys: list[str]) -> None:
    if not keys or not settings.s3_bucket_name:
        return
    try:
        client = get_s3_client()
        for key in keys:
            client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
    except Exception:
        # Best effort: DB-Löschung darf nicht an Storage-Fehlern scheitern
        logger.exception("Objekt-Storage-Aufräumen fehlgeschlagen")


def purge_deleted_users(db: Session) -> int:
    """Löscht Konten, deren Karenzzeit abgelaufen ist, endgültig. Gibt die
    Anzahl gelöschter Konten zurück."""
    cutoff = datetime.utcnow() - timedelta(days=GRACE_PERIOD_DAYS)
    expired = db.query(User).filter(User.deleted_at.isnot(None), User.deleted_at < cutoff).all()
    if not expired:
        return 0

    for user in expired:
        keys: list[str] = []
        for photo in db.query(Photo).filter(Photo.user_id == user.id).all():
            for url in (photo.url, photo.thumb_url):
                key = _object_key_from_url(url) if url else None
                if key:
                    keys.append(key)
        for req in db.query(VerificationRequest).filter(VerificationRequest.user_id == user.id).all():
            if req.selfies:
                try:
                    keys.extend(s["object_key"] for s in json.loads(req.selfies))
                except (ValueError, KeyError, TypeError):
                    pass
        _delete_objects(keys)
        db.delete(user)  # Kaskaden räumen Fotos, Matches, Nachrichten etc. ab
        logger.info("Konto %s nach Ablauf der Karenzzeit endgültig gelöscht", user.id)

    db.commit()
    return len(expired)
