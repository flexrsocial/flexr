"""Aufräumarbeiten im Objekt-Storage.

Zwei Aufgaben:

* Endgültige Löschung von Konten nach der 30-Tage-Karenzzeit. Die Selbstlöschung
  (DELETE /api/profiles/me) deaktiviert das Konto nur (deleted_at gesetzt).
* Temporäre Aufnahmen der Alters- und Identitätsprüfung, die niemand mehr
  braucht: abgebrochene Registrierungen und Vorgänge, bei denen das Löschen
  nach der Entscheidung fehlgeschlagen ist.

Aufgerufen wird beides opportunistisch beim Login (billige Abfragen, in der
Regel null Treffer) UND täglich per Timer (``python -m app.cleanup``,
deploy/flexr-cleanup.timer). Der Timer ist nötig, weil die Fristen sonst nur
eingehalten werden, solange sich irgendwer einloggt - am 02.10.2026 lag ein
Verifizierungs-Selfie schon über der 14-Tage-Frist. Es werden nur
Objektschlüssel geloggt, nie Bildinhalte.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .config import settings
from .models import (
    Message, Photo, PushNotification, Report, User, VerificationRequest, VerificationStatus,
)
from .retention import ACCOUNT_GRACE_PERIOD_DAYS as GRACE_PERIOD_DAYS
from .retention import (
    FLAGGED_MESSAGE_UNMATCHED_DAYS, PUSH_NOTIFICATION_RETENTION_DAYS, REPORT_EVIDENCE_RETENTION_DAYS,
)
from .storage import _buckets_for, get_s3_client, list_object_keys
from .verification_service import (
    ORPHAN_RETENTION_DAYS,
    object_keys_for,
    orphan_keys_for,
    purge_uploads,
)
from .timeutil import utcnow

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
        for key in keys:
            # Pruefaufnahmen liegen ggf. im privaten Bucket (und als
            # Altbestand noch im Foto-Bucket) - siehe storage._buckets_for.
            for bucket in _buckets_for(key):
                get_s3_client(bucket).delete_object(Bucket=bucket, Key=key)
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
    # Und alles, was sonst unter dem Ordner des Kontos liegt: hochgeladen, aber
    # nie als Foto gespeichert (abgebrochene Registrierung, abgewiesene Datei).
    # Bis zum 14.10.2026 blieb das öffentlich abrufbar liegen - in der
    # Produktion zehn Bilder von fünf längst gelöschten Konten.
    keys.extend(list_object_keys(f"users/{user.id}/"))
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
    cutoff = utcnow() - timedelta(days=ORPHAN_RETENTION_DAYS)
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


def stripe_abo_auslaufen_lassen(user: User) -> bool:
    """Ein laufendes Stripe-Abo eines geloeschten Kontos zum Periodenende
    beenden. ``True``, wenn nichts (mehr) abgebucht wird.

    Store-Abos (Google Play, App Store) kann der Server nicht kuendigen - das
    sagt der Loeschdialog der Clients dazu.
    """
    if not (user.is_subscribed and user.stripe_subscription_id):
        return True
    from .stripe_client import cancel_subscription_at_period_end

    try:
        cancel_subscription_at_period_end(user.stripe_subscription_id)
        return True
    except Exception:  # noqa: BLE001 - jede Stoerung wird gemeldet, keine kippt die Loeschung
        logger.exception("Stripe-Abo von Konto %s nicht beendet", user.id)
        return False


def purge_deleted_users(db: Session) -> int:
    """Löscht Konten, deren Karenzzeit abgelaufen ist, endgültig. Gibt die
    Anzahl gelöschter Konten zurück."""
    cutoff = utcnow() - timedelta(days=GRACE_PERIOD_DAYS)
    expired = db.query(User).filter(User.deleted_at.isnot(None), User.deleted_at < cutoff).all()
    if not expired:
        return 0

    for user in expired:
        # Zweiter Versuch, falls es bei der Loeschung selbst nicht geklappt
        # hat - danach gibt es kein Konto mehr, dem das Abo zuzuordnen waere.
        stripe_abo_auslaufen_lassen(user)
        delete_storage_objects(storage_keys_for_user(db, user))
        db.delete(user)  # Kaskaden räumen Fotos, Matches, Nachrichten etc. ab
        logger.info("Konto %s nach Ablauf der Karenzzeit endgültig gelöscht", user.id)

    db.commit()
    return len(expired)


def purge_old_report_evidence(db: Session) -> int:
    """Chat-Auszuege entschiedener Meldungen nach Ablauf der Frist leeren.

    Die Meldung selbst bleibt (Nachweis der Entscheidung, Art. 16/17 DSA), nur
    die Nachrichten daraus nicht laenger als fuer eine Beschwerde gegen die
    Entscheidung noetig (Art. 20 DSA: sechs Monate).
    """
    cutoff = utcnow() - timedelta(days=REPORT_EVIDENCE_RETENTION_DAYS)
    n = (
        db.query(Report)
        .filter(
            Report.evidence.isnot(None),
            Report.dismissed_at.isnot(None),
            Report.dismissed_at < cutoff,
        )
        .update({Report.evidence: None}, synchronize_session=False)
    )
    if n:
        db.commit()
    return n


# Ab wann ein hochgeladenes, aber nie gespeichertes Profilfoto als verwaist
# gilt. Ein Upload dauert Sekunden; die Woche ist reiner Sicherheitsabstand.
ORPHAN_PHOTO_DAYS = 7

# Notbremse: Mehr auf einmal löscht der Lauf nie. In der Produktion waren es am
# 14.10.2026 zehn. Schlägt sie an, stimmt eher die Zuordnung nicht (etwa eine
# geänderte öffentliche Basis-URL) als dass so viel verwaist wäre.
ORPHAN_PHOTO_MAX_PER_RUN = 50


def _key_aus_foto_url(url: str) -> str | None:
    """Objektschlüssel aus einer gespeicherten Foto-URL, unabhängig davon,
    unter welcher Basis-URL sie gespeichert wurde."""
    stelle = url.find("users/")
    return url[stelle:] if stelle >= 0 else None


def purge_orphan_photo_objects(db: Session, now: datetime | None = None) -> int:
    """Profilbilder im Storage, zu denen kein Foto (mehr) gehört.

    Sofort, wenn das Konto nicht mehr existiert; nach ORPHAN_PHOTO_DAYS bei
    bestehenden Konten (Upload ohne anschließendes Speichern). Prüfaufnahmen
    unter ``/verify/`` räumt purge_stale_verification_uploads() ab.
    """
    if not settings.s3_bucket_name:
        return 0
    referenziert: set[str] = set()
    for url, thumb in db.query(Photo.url, Photo.thumb_url):
        for wert in filter(None, (url, thumb)):
            key = _key_aus_foto_url(wert)
            if key is None:
                logger.error("Foto-URL ohne Objektschlüssel, Aufräumen übersprungen: %s", wert)
                return 0
            referenziert.add(key)
    konten = {uid for (uid,) in db.query(User.id)}
    grenze = (now or utcnow()).replace(tzinfo=timezone.utc) - timedelta(days=ORPHAN_PHOTO_DAYS)

    verwaist: list[str] = []
    try:
        seiten = get_s3_client().get_paginator("list_objects_v2").paginate(
            Bucket=settings.s3_bucket_name, Prefix="users/"
        )
        for seite in seiten:
            for objekt in seite.get("Contents", []):
                key = objekt["Key"]
                if "/verify/" in key or key in referenziert:
                    continue
                besitzer = key.split("/")[1]
                if besitzer not in konten or objekt["LastModified"] < grenze:
                    verwaist.append(key)
    except Exception:
        logger.exception("Profilbilder konnten nicht aufgelistet werden")
        return 0

    if len(verwaist) > ORPHAN_PHOTO_MAX_PER_RUN:
        logger.error(
            "%d verwaiste Profilbilder - mehr als %d, nichts gelöscht. Bitte prüfen.",
            len(verwaist), ORPHAN_PHOTO_MAX_PER_RUN,
        )
        return 0
    if verwaist:
        delete_storage_objects(verwaist)
        logger.info("Verwaiste Profilbilder gelöscht: %d", len(verwaist))
    return len(verwaist)


def purge_old_push_notifications(db: Session) -> int:
    """App-Benachrichtigungen nach Ablauf der Frist löschen.

    Ausgeliefert wird nur eine Woche lang (notifications.PENDING_MAX_AGE).
    Wer nur die Web-App nutzt, holt nie etwas ab - in der Produktion lagen am
    14.10.2026 365 von 377 Einträgen unabgeholt, mit Namen aus Match-Meldungen.
    """
    cutoff = utcnow() - timedelta(days=PUSH_NOTIFICATION_RETENTION_DAYS)
    n = (
        db.query(PushNotification)
        .filter(PushNotification.created_at < cutoff)
        .delete(synchronize_session=False)
    )
    if n:
        db.commit()
    return n


def purge_unmatched_flagged_messages(db: Session) -> int:
    """Markierte Nachrichten aus aufgelösten Matches nach Ablauf der Frist.

    Sie bleiben beim Auflösen nur für die Moderation stehen
    (routers/matches.unmatch). Mit der Prüfung verschwinden sie sofort
    (admin.clear_flagged_message); was bis FLAGGED_MESSAGE_UNMATCHED_DAYS nach
    dem Senden niemand geprüft hat, geht hier.
    """
    cutoff = utcnow() - timedelta(days=FLAGGED_MESSAGE_UNMATCHED_DAYS)
    n = (
        db.query(Message)
        .filter(Message.match_id.is_(None), Message.created_at < cutoff)
        .delete(synchronize_session=False)
    )
    if n:
        db.commit()
    return n


def run_all(db: Session) -> dict[str, int]:
    """Alle Fristen auf einmal - für den täglichen Timer."""
    return {
        "deleted_users": purge_deleted_users(db),
        "verification_requests": purge_stale_verification_uploads(db),
        "report_evidence": purge_old_report_evidence(db),
        "push_notifications": purge_old_push_notifications(db),
        "orphan_photos": purge_orphan_photo_objects(db),
        "unmatched_flagged_messages": purge_unmatched_flagged_messages(db),
    }


def main() -> None:
    from .database import SessionLocal

    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        result = run_all(db)
    finally:
        db.close()
    print(result)
    # Fehlgeschlagene Storage-Löschungen bleiben als cleanup_pending stehen und
    # werden beim nächsten Lauf wiederholt; als Fehler melden, damit es auffällt.
    db = SessionLocal()
    try:
        pending = db.query(VerificationRequest).filter(VerificationRequest.cleanup_pending.is_(True)).count()
    finally:
        db.close()
    if pending:
        print(f"{pending} Verifizierungsvorgänge mit fehlgeschlagener Storage-Löschung")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
