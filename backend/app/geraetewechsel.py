"""Am Handy weitermachen: Einmal-Link per QR-Code (seit 14.10.2026).

Wer sich in der Web-App am Rechner registriert, hat dort meist keine Kamera -
das Live-Selfie der Pruefung geht aber nur mit Kamera. Der Pruefbildschirm
zeigt deshalb einen QR-Code; das Handy oeffnet damit die Web-App und ist
sofort angemeldet, ohne Passwort.

Weil der Link ein Konto oeffnet, gilt dasselbe wie beim Passwort-Reset
(password_reset.py): Zufallstoken, nur als SHA-256-Hash gespeichert, kurze
Laufzeit, einmal einloesbar. Zusaetzlich nur fuer Konten, die noch nicht
freigeschaltet sind - ein abfotografierter Code oeffnet also nie ein Konto
mit Matches und Chats. Der Token steht im Link hinter "#": Diesen Teil
schickt der Browser nicht an den Server, er landet in keinem Zugriffslog.
"""

import base64
import secrets
from datetime import timedelta
from io import BytesIO

import qrcode
import qrcode.image.svg
from sqlalchemy.orm import Session

from .config import settings
from .email_verification import hash_token
from .models import DeviceHandoff, User
from .timeutil import utcnow

TOKEN_TTL_MINUTES = 10


class HandoffError(Exception):
    """Der Code taugt nicht (mehr) - mit einer Begruendung fuer den Nutzer."""


def build_link(token: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/app/#weiter={token}"


def qr_data_uri(link: str) -> str:
    """QR-Code als SVG-Data-URI (schwarz auf weiss, mit Ruhezone)."""
    bild = qrcode.make(link, image_factory=qrcode.image.svg.SvgPathFillImage, box_size=10)
    puffer = BytesIO()
    bild.save(puffer)
    return "data:image/svg+xml;base64," + base64.b64encode(puffer.getvalue()).decode("ascii")


def issue(db: Session, user: User) -> tuple[str, object]:
    """Neuen Einmal-Link ausstellen; aeltere dieses Kontos verfallen sofort."""
    jetzt = utcnow()
    db.query(DeviceHandoff).filter(DeviceHandoff.user_id == user.id).delete()
    # Abgelaufene anderer Konten gleich mit wegraeumen - sonst blieben sie bis
    # zur naechsten Ausstellung desselben Kontos liegen.
    db.query(DeviceHandoff).filter(DeviceHandoff.expires_at < jetzt).delete()
    token = secrets.token_urlsafe(32)
    ablauf = jetzt + timedelta(minutes=TOKEN_TTL_MINUTES)
    db.add(DeviceHandoff(user_id=user.id, token_hash=hash_token(token), expires_at=ablauf))
    db.commit()
    return token, ablauf


def redeem(db: Session, token: str) -> User:
    eintrag = (
        db.query(DeviceHandoff)
        .filter(DeviceHandoff.token_hash == hash_token(token))
        .first()
    )
    if eintrag is None or utcnow() > eintrag.expires_at:
        if eintrag is not None:
            db.delete(eintrag)
            db.commit()
        raise HandoffError(
            "Dieser Code ist abgelaufen oder wurde schon benutzt. "
            "Erzeuge am Computer einen neuen."
        )
    user = db.query(User).filter(User.id == eintrag.user_id).first()
    db.delete(eintrag)
    db.commit()
    if (
        user is None
        or user.deleted_at is not None
        or user.is_banned
        or user.is_account_activated
    ):
        # Freigeschaltet: Der Code war nur fuer die Pruefung gedacht - ab hier
        # gilt der normale Login.
        raise HandoffError("Mit diesem Code ist keine Anmeldung mehr möglich. Bitte melde dich an.")
    return user
