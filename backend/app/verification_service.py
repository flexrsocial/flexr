"""Gemeinsame Logik der Alters- und Identitätsprüfung.

Hier liegt alles, was Nutzer-Router, Admin-Router und der Aufräumlauf teilen:
die Statusableitung, die Freischaltung des Kontos und das nachweisliche Löschen
der temporären Aufnahmen.

Grundsatz: Der Status eines Kontos ergibt sich immer aus dem Server-Zustand.
Es gibt keinen Weg, ``approved``, ``age_verified`` oder ``activated_at`` über
ein Client-Feld zu setzen - diese Werte werden ausschließlich in diesem Modul
und nur aus dem Admin-Router heraus vergeben.
"""

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import storage
from .config import settings
from .models import (
    DOCUMENT_TYPES_WITH_BACK,
    VERIFICATION_OPEN_STATES,
    User,
    VerificationDocumentType,
    VerificationRequest,
    VerificationReviewReason,
    VerificationStatus,
)

logger = logging.getLogger("flexr.verification")

# Sachliche Rückmeldung an den Nutzer je Prüfgrund. Fester Katalog statt
# Freitext - so entstehen keine sensiblen Notizen zum Ausweis, und interne
# Prüfheuristiken werden nicht offengelegt.
REASON_TEXTS = {
    VerificationReviewReason.document_unreadable.value:
        "Die Aufnahme des Ausweises war nicht gut genug lesbar.",
    VerificationReviewReason.details_not_visible.value:
        "Auf der Aufnahme waren nicht alle für die Prüfung nötigen Angaben sichtbar.",
    VerificationReviewReason.person_mismatch.value:
        "Wir konnten die Verifizierung deinem Profil nicht zuordnen.",
    VerificationReviewReason.dob_mismatch.value:
        "Das Geburtsdatum auf dem Ausweis stimmt nicht mit deiner Angabe bei der "
        "Registrierung überein.",
    VerificationReviewReason.underage.value:
        "Nach dem vorgelegten Ausweis bist du noch nicht 18 Jahre alt.",
    VerificationReviewReason.document_unsuitable.value:
        "Das vorgelegte Dokument ist für die Alters- und Identitätsprüfung nicht geeignet.",
    VerificationReviewReason.selfie_unusable.value:
        "Die Verifizierungs-Selfies waren nicht verwertbar.",
    VerificationReviewReason.other.value:
        "Wir konnten deine Verifizierung nicht abschließen.",
}

# Verwaiste Uploads (Registrierung abgebrochen, nie eingereicht) werden nach
# dieser Frist entfernt. Kurz gehalten - es sind Ausweisaufnahmen.
ORPHAN_RETENTION_DAYS = 14


def document_type_options() -> list[dict]:
    """Auswahlliste für den Client inkl. Angabe, ob eine Rückseite nötig ist."""
    labels = {
        VerificationDocumentType.id_card: "Personalausweis",
        VerificationDocumentType.passport: "Reisepass",
        VerificationDocumentType.drivers_license: "Führerschein",
    }
    return [
        {
            "value": doc_type.value,
            "label": labels[doc_type],
            "needs_back": doc_type in DOCUMENT_TYPES_WITH_BACK,
        }
        for doc_type in VerificationDocumentType
    ]


def needs_back_side(document_type: str) -> bool:
    try:
        return VerificationDocumentType(document_type) in DOCUMENT_TYPES_WITH_BACK
    except ValueError:
        return False


def latest_request(db: Session, user_id: str) -> VerificationRequest | None:
    return (
        db.query(VerificationRequest)
        .filter(VerificationRequest.user_id == user_id)
        .order_by(VerificationRequest.created_at.desc())
        .first()
    )


def open_request(db: Session, user_id: str) -> VerificationRequest | None:
    """Laufender Vorgang - also einer, bei dem noch etwas offen ist."""
    return (
        db.query(VerificationRequest)
        .filter(
            VerificationRequest.user_id == user_id,
            VerificationRequest.status.in_(VERIFICATION_OPEN_STATES),
        )
        .order_by(VerificationRequest.created_at.desc())
        .first()
    )


def decision_is_binding(user: User, req: VerificationRequest) -> bool:
    """Blockiert diese abgeschlossene Prüfung einen neuen Anlauf?

    Ja, solange sie zur zuletzt verlangten Prüfung gehört - eine Ablehnung soll
    sich nicht einfach durch einen neuen Versuch aushebeln lassen.

    Nein, wenn die Prüfung danach erneut angefordert wurde: Bei einem
    Bestandskonto, das ein Admin nachträglich in die Prüfung holt, liegt die
    frühere Entscheidung vor dieser Anforderung und darf den neuen Durchlauf
    nicht verhindern.
    """
    demanded_at = user.verification_required_at
    if demanded_at is None:
        return True
    if req.decided_at is None:
        return True
    return req.decided_at >= demanded_at


def next_step_for(req: VerificationRequest | None) -> str:
    """Was der Nutzer als Nächstes tun muss."""
    if req is None:
        return "selfie"
    if req.status == VerificationStatus.in_progress:
        return "selfie"
    if req.status in (VerificationStatus.id_required, VerificationStatus.reupload_required):
        # Ohne gültige Selfies beginnt der Vorgang wieder bei Schritt 1 - etwa
        # wenn der Prüfer sie verworfen hat oder der Aufräumlauf sie entfernt hat.
        return "document" if req.selfies else "selfie"
    if req.status == VerificationStatus.submitted:
        return "wait"
    return "none"


def account_visible_condition():
    """SQLAlchemy-Bedingung: Konto ist freigeschaltet.

    Bestandskonten (verification_required False) bleiben unverändert sichtbar,
    neue Konten erst nach bestandener Prüfung.
    """
    return or_(User.verification_required.is_(False), User.activated_at.isnot(None))


def activate_account(user: User) -> None:
    """Schaltet das Konto nach bestandener Prüfung frei.

    Der Probemonat startet hier neu. Sonst würde eine lange manuelle Prüfung
    von der Gratiszeit abgehen - der Nutzer konnte in dieser Zeit nichts nutzen.
    Bereits freigeschaltete Konten werden nicht erneut angefasst, damit die
    Gratiszeit nicht mehrfach verlängert werden kann.
    """
    if user.activated_at is not None:
        return
    now = datetime.utcnow()
    user.activated_at = now
    user.trial_ends_at = now + timedelta(days=settings.stripe_trial_days)


def object_keys_for(req: VerificationRequest) -> list[str]:
    """Alle Storage-Schlüssel eines Vorgangs (Selfies + Ausweisaufnahmen)."""
    return selfie_keys(req) + document_keys(req)


def selfie_keys(req: VerificationRequest) -> list[str]:
    return _keys_from_json(req.selfies)


def document_keys(req: VerificationRequest) -> list[str]:
    return _keys_from_json(req.documents)


def _keys_from_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        return [entry["object_key"] for entry in json.loads(raw)]
    except (ValueError, KeyError, TypeError):
        # Kaputter Datensatz darf den Aufräumlauf nicht anhalten
        logger.warning("Unlesbarer Verweis auf Verifizierungs-Aufnahmen übersprungen")
        return []


def purge_uploads(req: VerificationRequest, *, selfies: bool = True, documents: bool = True) -> bool:
    """Löscht die temporären Aufnahmen eines Vorgangs und prüft das Ergebnis.

    Gibt True zurück, wenn nachweislich nichts mehr im Storage liegt. Andernfalls
    bleiben die Verweise stehen (die Schlüssel sind Zufalls-IDs ohne
    Personenbezug), ``cleanup_pending`` wird gesetzt und app/cleanup.py
    wiederholt den Versuch. Es werden nie Bildinhalte protokolliert.
    """
    keys: list[str] = []
    if selfies:
        keys += selfie_keys(req)
    if documents:
        keys += document_keys(req)

    remaining = storage.delete_objects_verified(keys)

    if selfies and not any(key in remaining for key in selfie_keys(req)):
        req.selfies = None
    if documents and not any(key in remaining for key in document_keys(req)):
        req.documents = None

    req.cleanup_pending = bool(remaining)
    if remaining:
        logger.error(
            "Verifizierungs-Aufnahmen konnten nicht gelöscht werden (Vorgang %s, %d Objekte)",
            req.id,
            len(remaining),
        )
    return not remaining


def reason_text(reason_code: str | None) -> str | None:
    if not reason_code:
        return None
    return REASON_TEXTS.get(reason_code, REASON_TEXTS[VerificationReviewReason.other.value])
