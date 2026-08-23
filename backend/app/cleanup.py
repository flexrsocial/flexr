"""Aufräumarbeiten im Objekt-Storage.

Zwei Aufgaben:

* Endgültige Löschung von Konten nach der 30-Tage-Karenzzeit. Die Selbstlöschung
  (DELETE /api/profiles/me) deaktiviert das Konto nur (deleted_at gesetzt).
* Temporäre Aufnahmen der Alters- und Identitätsprüfung, die niemand mehr
  braucht: abgebrochene Registrierungen und Vorgänge, bei denen das Löschen
  nach der Entscheidung fehlgeschlagen ist.

Aufgerufen wird beides opportunistisch beim Login (billige Abfragen, in der
Regel null Treffer) - so braucht es keinen eigenen Cron-Job. Es werden nur
Objektschlüssel geloggt, nie Bildinhalte.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .config import settings
from .models import Photo, User, VerificationRequest, VerificationStatus
from .retention import ACCOUNT_GRACE_PERIOD_DAYS as GRACE_PERIOD_DAYS
from .storage import get_s3_client
from .verification_service import (
    ORPHAN_RETENTION_DAYS,
    object_keys_for,
    orphan_keys_for,
    purge_uploads,
)

logger = logging.getLogger("flexr.cleanup")


def _object_key_from_url(url: str) -> str | None:
    base = settings.s3_public_base_url.rstrip("/")
    if base and url.startswith(base + "/"):
        return url[len(base) + 1:]
    return None


def delete_storage_objects(keys: list[str]) -> None:
    if not keys or not settings.s3_bucket_name:
        return
    try:
        client = get_s3_client()
        for key in keys:
            client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
    except Exception:
        # Best effort: DB-Löschung darf nicht an Storage-Fehlern scheitern
        logger.exception("Objekt-Storage-Aufräumen fehlgeschlagen")


def storage_keys_for_photo(photo: Photo) -> list[str]:
    """Objektschlüssel eines Fotos: Original und - falls vorhanden - Thumbnail.

    Wird beim Löschen eines einzelnen Fotos gebraucht (durch den Nutzer oder
    die Moderation): ohne diesen Schritt bleibt die Bilddatei unter ihrer
    öffentlichen URL abrufbar, obwohl das Foto aus dem Profil verschwunden ist.
    """
    keys: list[str] = []
    for url in (photo.url, photo.thumb_url):
        key = _object_key_from_url(url) if url else None
        if key:
            keys.append(key)
    return keys


def storage_keys_for_user(db: Session, user: User) -> list[str]:
    """Alle Storage-Objekte eines Nutzers: Profilfotos, Thumbnails,
    Verifizierungs-Selfies und noch vorhandene Ausweisaufnahmen.

    Eine Stelle für alle Löschwege (Selbstlöschung, Karenzablauf,
    Admin-Löschung), damit im Storage nichts verwaist zurückbleibt.
    """
    keys: list[str] = []
    for photo in db.query(Photo).filter(Photo.user_id == user.id).all():
        keys.extend(storage_keys_for_photo(photo))
    for req in db.query(VerificationRequest).filter(VerificationRequest.user_id == user.id).all():
        keys.extend(object_keys_for(req))
        # Auch angefangene Uploads, die nie eingereicht wurden (siehe
        # verification_service.orphan_keys_for) - beim endgültigen Löschen darf
        # nichts übrig bleiben.
        keys.extend(orphan_keys_for(req))
    return _unique(keys)


def _unique(keys: list[str]) -> list[str]:
    """Reihenfolge erhalten, Doppelte entfernen."""
    seen: set[str] = set()
    return [k for k in keys if not (k in seen or seen.add(k))]


def purge_verification_uploads_for_user(db: Session, user: User) -> None:
    """Löscht Selfies und Ausweisaufnahmen eines Nutzers sofort.

    Wird bei der Selbstlöschung aufgerufen: Ausweisaufnahmen sollen nicht
    30 Tage Karenzzeit überdauern, nur weil das Konto noch nicht endgültig
    gelöscht ist.
    """
    requests = (
        db.query(VerificationRequest).filter(VerificationRequest.user_id == user.id).all()
    )
    for req in requests:
        purge_uploads(req)
    if requests:
        db.commit()


def purge_stale_verification_uploads(db: Session) -> int:
    """Aufnahmen ohne Zweck entfernen.

    Zwei Fälle:

    * ``cleanup_pending``: Die Löschung nach einer Entscheidung ist
      fehlgeschlagen - hier wird sie wiederholt.
    * Abgebrochene Vorgänge: Selfies oder Ausweisaufnahmen liegen seit mehr als
      ORPHAN_RETENTION_DAYS in einem offenen Schritt, ohne dass jemals
      eingereicht wurde (Registrierung abgebrochen). Diese Vorgänge werden nach
      dem Löschen der Aufnahmen ganz entfernt - der Nutzer beginnt dann von vorn.

    Bereits eingereichte Vorgänge (``submitted``) bleiben unangetastet: sie
    warten auf die Prüfung.

    Gibt die Zahl der aufgeräumten Vorgänge zurück.
    """
    cutoff = datetime.utcnow() - timedelta(days=ORPHAN_RETENTION_DAYS)
    stale_states = (
        VerificationStatus.in_progress,
        VerificationStatus.id_required,
        VerificationStatus.reupload_required,
    )
    candidates = (
        db.query(VerificationRequest)
        .filter(
            or_(
                VerificationRequest.cleanup_pending.is_(True),
                (VerificationRequest.status.in_(stale_states))
                & (VerificationRequest.created_at < cutoff),
            )
        )
        .limit(100)
        .all()
    )
    if not candidates:
        return 0

    for req in candidates:
        purged = purge_uploads(req)
        # Abgebrochener Vorgang: Nach erfolgreichem Löschen bleibt kein
        # halbfertiger Zustand zurück. Bei fehlgeschlagener Löschung bleibt der
        # Datensatz als Merkposten stehen (cleanup_pending) und wird erneut
        # versucht.
        if purged and req.status in stale_states:
            db.delete(req)
    db.commit()
    logger.info("Verifizierungs-Aufnahmen aufgeräumt: %d Vorgänge", len(candidates))
    return len(candidates)


def purge_deleted_users(db: Session) -> int:
    """Löscht Konten, deren Karenzzeit abgelaufen ist, endgültig. Gibt die
    Anzahl gelöschter Konten zurück."""
    cutoff = datetime.utcnow() - timedelta(days=GRACE_PERIOD_DAYS)
    expired = db.query(User).filter(User.deleted_at.isnot(None), User.deleted_at < cutoff).all()
    if not expired:
        return 0

    for user in expired:
        delete_storage_objects(storage_keys_for_user(db, user))
        db.delete(user)  # Kaskaden räumen Fotos, Matches, Nachrichten etc. ab
        logger.info("Konto %s nach Ablauf der Karenzzeit endgültig gelöscht", user.id)

    db.commit()
    return len(expired)
