"""Passwort vergessen: Zuruecksetzen per Link.

Gleiches Muster wie email_verification: Zufallstoken, nur als SHA-256-Hash
gespeichert, mit Ablaufzeit, hoechstens ein offener Vorgang pro Konto. Die
Laufzeit ist kuerzer als beim Bestaetigungslink, weil dieser Link ein Konto
uebernehmen kann.
"""

import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .config import settings
from .email_verification import hash_token
from .models import PasswordReset, User
from .security import hash_password
from .timeutil import utcnow

logger = logging.getLogger("flexr.mail")

TOKEN_TTL_MINUTES = 60

# Hoechstens eine Mail je Konto in diesem Abstand. Die IP-Grenze der Route
# (5/Stunde) hilft nicht, wenn die Anfragen von wechselnden Adressen kommen:
# Am 22.09.2026 schickten Googles Pre-Launch-Testgeraete binnen 21 Minuten
# drei Reset-Mails an dieselbe Adresse. Genauso koennte jemand ein fremdes
# Postfach zumuellen.
RESEND_COOLDOWN_MINUTES = 10


def recently_issued(db: Session, user: User) -> bool:
    grenze = utcnow() - timedelta(minutes=RESEND_COOLDOWN_MINUTES)
    return (
        db.query(PasswordReset.id)
        .filter(PasswordReset.user_id == user.id, PasswordReset.created_at > grenze)
        .first()
        is not None
    )


def build_link(token: str) -> str:
    """Link auf die Web-App. Die Seite fragt das neue Passwort ab und loest
    den Token per POST ein - ein GET-Endpunkt wuerde von Linkscannern in
    Mailservern ausgeloest (siehe email_verification.build_link)."""
    return f"{settings.frontend_url.rstrip('/')}/app/?reset={token}"


def issue(db: Session, user: User) -> str:
    db.query(PasswordReset).filter(PasswordReset.user_id == user.id).delete()
    token = secrets.token_urlsafe(32)
    db.add(
        PasswordReset(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES),
        )
    )
    db.commit()
    return token


class ResetError(Exception):
    """Der Token taugt nicht - mit einer Begruendung fuer den Nutzer."""


def set_new_password(db: Session, user: User, new_password: str) -> None:
    """Passwort setzen und alle bis jetzt ausgestellten Sitzungen beenden."""
    user.password_hash = hash_password(new_password)
    # Mikrosekundengenau, siehe security.token_predates_password_change: Der
    # gleich danach ausgestellte neue Token liegt sicher dahinter.
    user.password_changed_at = utcnow()
    # Wer das Passwort neu gesetzt hat, darf sofort wieder hinein.
    user.failed_login_attempts = 0
    user.login_locked_until = None
    db.query(PasswordReset).filter(PasswordReset.user_id == user.id).delete()


def redeem(db: Session, token: str, new_password: str) -> User:
    entry = (
        db.query(PasswordReset)
        .filter(PasswordReset.token_hash == hash_token(token))
        .first()
    )
    if entry is None:
        raise ResetError(
            "Dieser Link ist ungültig oder wurde bereits benutzt. "
            "Fordere über „Passwort vergessen?“ einen neuen an."
        )
    if utcnow() > entry.expires_at:
        db.delete(entry)
        db.commit()
        raise ResetError(
            f"Dieser Link ist abgelaufen (er gilt {TOKEN_TTL_MINUTES} Minuten). "
            "Fordere über „Passwort vergessen?“ einen neuen an."
        )
    user = db.query(User).filter(User.id == entry.user_id).first()
    if user is None or user.deleted_at is not None or user.is_banned:
        db.delete(entry)
        db.commit()
        raise ResetError("Zu diesem Link gibt es kein nutzbares Konto mehr.")

    set_new_password(db, user, new_password)
    # Wer den Link aus seinem Postfach einloest, hat die Adresse damit
    # bestaetigt - dasselbe, was der Bestaetigungslink nachweist.
    if user.email_verified_at is None:
        user.email_verified_at = utcnow()
    db.commit()
    db.refresh(user)
    logger.info("Passwort per Link zurueckgesetzt (Konto %s)", user.id)
    return user
