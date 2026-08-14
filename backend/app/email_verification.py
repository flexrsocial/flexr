"""E-Mail-Bestätigung per Aktivierungslink.

Der Token im Link ist ein Passwort auf Zeit: Wer ihn hat, bestätigt die
Adresse. Er wird deshalb wie der SMS-Code behandelt - zufällig erzeugt, nur als
SHA-256-Hash gespeichert, mit Ablaufzeit, und pro Konto gibt es höchstens einen
offenen Vorgang.

Warum die Bestätigung vor der Alters- und Identitätsprüfung steht: Ein Mensch
soll keine Ausweisaufnahme begutachten, solange nicht feststeht, dass die
Adresse dem Nutzer gehört. Und weil es kein "Passwort vergessen" gibt, ist eine
vertippte Adresse sonst ein unrettbares Konto - der Tippfehler soll auffallen,
solange der Nutzer noch weiß, was er eingegeben hat.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .config import settings
from .mailer import send_verification_email
from .models import EmailVerification, User

logger = logging.getLogger("flexr.mail")

TOKEN_TTL_HOURS = 24


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def build_link(token: str) -> str:
    """Der Link zeigt auf das Web-Frontend, nicht auf die API.

    Die Seite dort löst den Token gegen POST /api/auth/email/confirm ein. Ein
    reiner GET-Endpunkt wäre bequemer, würde aber von Linkscannern in
    Mailservern mit ausgelöst - die Bestätigung fände dann statt, ohne dass der
    Nutzer je geklickt hat. Auf Android fängt derselbe Link die App ab
    (Digital Asset Links, siehe frontend/.well-known/assetlinks.json).
    """
    return f"{settings.frontend_url.rstrip('/')}/mail-bestaetigen?token={token}"


def issue(db: Session, user: User) -> str:
    """Erzeugt einen neuen Token und verwirft alle älteren dieses Kontos.

    Der Aufrufer bekommt den Klartext-Token zurück - er existiert nur in dieser
    einen Antwort und danach nirgends mehr.
    """
    db.query(EmailVerification).filter(EmailVerification.user_id == user.id).delete()

    token = secrets.token_urlsafe(32)
    db.add(
        EmailVerification(
            user_id=user.id,
            email=user.email,
            token_hash=hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS),
        )
    )
    db.commit()
    return token


class ConfirmationError(Exception):
    """Der Token taugt nicht - mit einer Begründung für den Nutzer."""


def confirm(db: Session, token: str) -> User:
    """Löst einen Token ein und gibt das bestätigte Konto zurück."""
    entry = (
        db.query(EmailVerification)
        .filter(EmailVerification.token_hash == hash_token(token))
        .first()
    )
    if entry is None:
        raise ConfirmationError(
            "Dieser Bestätigungslink ist ungültig oder wurde bereits benutzt. "
            "Fordere in der App einen neuen an."
        )

    if datetime.utcnow() > entry.expires_at:
        db.delete(entry)
        db.commit()
        raise ConfirmationError(
            f"Dieser Bestätigungslink ist abgelaufen (er gilt {TOKEN_TTL_HOURS} Stunden). "
            "Fordere in der App einen neuen an."
        )

    user = db.query(User).filter(User.id == entry.user_id).first()
    if user is None or user.deleted_at is not None:
        db.delete(entry)
        db.commit()
        raise ConfirmationError("Zu diesem Link gibt es kein Konto mehr.")

    # Die Adresse kann sich seit dem Versand geändert haben - dann bestätigt
    # der alte Link die falsche und ist wertlos.
    if entry.email != user.email:
        db.delete(entry)
        db.commit()
        raise ConfirmationError(
            "Dieser Link gehört zu einer anderen E-Mail-Adresse. Fordere einen neuen an."
        )

    if user.email_verified_at is None:
        user.email_verified_at = datetime.utcnow()
    db.query(EmailVerification).filter(EmailVerification.user_id == user.id).delete()
    db.commit()
    db.refresh(user)
    logger.info("E-Mail-Adresse bestätigt (Konto %s)", user.id)
    return user
