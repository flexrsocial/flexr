"""Einwilligungen erteilen, nachweisen und widerrufen.

Art. 7 Abs. 1 DSGVO verlangt den Nachweis, *wozu* eingewilligt wurde - dafür
reicht ein Zeitstempel nicht, es braucht die Fassung des Textes. Art. 7 Abs. 3
verlangt, dass der Widerruf nicht schwerer ist als die Erteilung: Angehakt wird
mit einem Klick im Formular, also muss er auch mit einem Klick im Konto-Bereich
gehen - nicht per Mail an den Support.

Was hier bewusst NICHT passiert: Es wird keine IP-Adresse gespeichert. Für den
Nachweis genügt Konto, Art, Fassung und Zeitpunkt.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from . import legal
from .models import Consent, ConsentType, User

# Welche Fassung für welche Einwilligungsart gilt. Ändert sich ein Text
# inhaltlich, wird in app/legal.py die Fassung erhöht - alte Einwilligungen
# bleiben mit ihrer alten Fassung stehen und sind damit als "zu einem anderen
# Text erteilt" erkennbar.
VERSION_FOR = {
    ConsentType.sensitive_data: legal.PRIVACY_VERSION,
    ConsentType.verification_media: legal.PRIVACY_VERSION,
    ConsentType.immediate_start: legal.WITHDRAWAL_VERSION,
    ConsentType.terms: legal.TERMS_VERSION,
}


def grant(
    db: Session,
    user: User,
    consent_type: ConsentType,
    *,
    at: datetime | None = None,
    commit: bool = True,
) -> Consent:
    """Erteilt eine Einwilligung in der aktuell geltenden Fassung.

    Eine bereits aktive Einwilligung derselben Art und Fassung wird nicht
    verdoppelt - sonst entstünde bei jedem Speichern ein neuer Nachweis.
    """
    timestamp = at or datetime.utcnow()
    version = VERSION_FOR[consent_type]

    existing = active(db, user.id, consent_type)
    if existing is not None and existing.version == version:
        return existing

    entry = Consent(
        user_id=user.id,
        consent_type=consent_type.value,
        version=version,
        granted_at=timestamp,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry


def revoke(db: Session, user_id: str, consent_type: ConsentType) -> bool:
    """Widerruft eine Einwilligung mit Wirkung für die Zukunft.

    Der Nachweis bleibt stehen, nur mit Widerrufszeitpunkt - sonst ließe sich
    später nicht mehr zeigen, dass überhaupt einmal eingewilligt wurde.
    Liefert, ob es etwas zu widerrufen gab.
    """
    entry = active(db, user_id, consent_type)
    if entry is None:
        return False
    entry.revoked_at = datetime.utcnow()
    db.commit()
    return True


def active(db: Session, user_id: str, consent_type: ConsentType) -> Consent | None:
    """Die derzeit wirksame Einwilligung dieser Art, falls es eine gibt."""
    return (
        db.query(Consent)
        .filter(
            Consent.user_id == user_id,
            Consent.consent_type == consent_type.value,
            Consent.revoked_at.is_(None),
        )
        .order_by(Consent.granted_at.desc())
        .first()
    )


def history(db: Session, user_id: str) -> list[Consent]:
    """Alle Einwilligungen eines Kontos, neueste zuerst - Grundlage für die
    Auskunft nach Art. 15 DSGVO und für die Anzeige im Konto-Bereich."""
    return (
        db.query(Consent)
        .filter(Consent.user_id == user_id)
        .order_by(Consent.granted_at.desc())
        .all()
    )
