"""Web Push fuer die Web-App - vor allem fuer das iPhone.

Warum es das gibt: Die iOS-App steht (noch) nicht im App Store. iPhone-Nutzer
bekommen FLEXR stattdessen als Web-App auf den Home-Bildschirm, und seit
iOS 16.4 kann eine so installierte Web-App echte Benachrichtigungen
empfangen - ueber den offenen Web-Push-Standard, ohne Apple-Entwicklerkonto
und ohne APNs-Schluessel. Derselbe Weg funktioniert in Chrome, Edge und
Firefox auf dem Desktop und unter Android.

Zwei Standards, beide hier ohne Fremdpaket umgesetzt (``cryptography`` ist
ohnehin da):

* **VAPID** (RFC 8292): Der Server weist sich beim Push-Dienst mit einem
  ES256-signierten JWT aus. Der oeffentliche Schluessel steckt im Abo, das der
  Browser anlegt - nur wer den passenden privaten Schluessel hat, darf an
  dieses Abo schicken.
* **Verschluesselung** (RFC 8291, ``aes128gcm``): Der Push-Dienst (Apple,
  Google, Mozilla) sieht nur Chiffretext. Entschluesseln kann allein der
  Browser, der das Abo angelegt hat.

**Ohne Schluessel passiert hier nichts** - wie bei FCM und APNs (siehe
``push.py``). ``configured()`` ist dann False, die Web-App bietet den
Schalter gar nicht erst an, und ``send()`` gibt 0 zurueck.

Schluessel erzeugen: ``python -m app.webpush`` gibt eine Zeile fuer die .env
aus (``WEBPUSH_VAPID_PRIVATE_KEY=...``). Der oeffentliche Teil wird daraus
abgeleitet und muss nirgends eingetragen werden.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import struct
import time
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from sqlalchemy.orm import Session

from .config import settings
from .models import PushToken

logger = logging.getLogger(__name__)

#: Datensatzgroesse im aes128gcm-Kopf. Eine Benachrichtigung passt immer in
#: einen einzigen Datensatz - der Wert muss nur groesser als die Nutzlast sein.
_RECORD_SIZE = 4096

#: So lange darf der Push-Dienst eine Nachricht fuer ein ausgeschaltetes
#: Geraet vorhalten. Ein Tag reicht: Was aelter ist, sieht der Nutzer beim
#: naechsten Oeffnen ohnehin in der App.
_TTL_SECONDS = 24 * 60 * 60


#: Nur an diese Push-Dienste wird geschickt. Der Endpunkt kommt vom Browser -
#: ohne diese Liste koennte jedes Konto den Server dazu bringen, POST-Anfragen
#: an beliebige Adressen zu schicken, auch an interne (SSRF).
_ERLAUBTE_DIENSTE = (
    "web.push.apple.com",            # Safari / iOS
    "fcm.googleapis.com",            # Chrome, Edge (Chromium), Android
    "updates.push.services.mozilla.com",  # Firefox
    ".notify.windows.com",           # aeltere Edge-Fassungen (WNS)
)


def endpoint_allowed(endpoint: str) -> bool:
    teile = urlparse(endpoint)
    if teile.scheme != "https" or not teile.hostname or teile.port not in (None, 443):
        return False
    host = teile.hostname.lower()
    return any(
        host.endswith(dienst) if dienst.startswith(".") else host == dienst
        for dienst in _ERLAUBTE_DIENSTE
    )


def _b64url(daten: bytes) -> str:
    return base64.urlsafe_b64encode(daten).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    text = text.strip()
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _private_key() -> ec.EllipticCurvePrivateKey | None:
    roh = settings.webpush_vapid_private_key.strip()
    if not roh:
        return None
    try:
        wert = int.from_bytes(_b64url_decode(roh), "big")
        return ec.derive_private_key(wert, ec.SECP256R1())
    except Exception:  # noqa: BLE001 - kaputter Eintrag in der .env
        logger.exception("WEBPUSH_VAPID_PRIVATE_KEY ist nicht lesbar")
        return None


def _public_bytes(key: ec.EllipticCurvePublicKey) -> bytes:
    return key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )


def configured() -> bool:
    return _private_key() is not None


def public_key() -> str | None:
    """Oeffentlicher VAPID-Schluessel (base64url, 65 Byte unkomprimiert).

    Genau diese Form verlangt ``PushManager.subscribe({applicationServerKey})``
    im Browser.
    """
    key = _private_key()
    return _b64url(_public_bytes(key.public_key())) if key else None


def generate_private_key() -> str:
    """Neuen VAPID-Schluessel erzeugen - Ausgabe fuer die .env."""
    key = ec.generate_private_key(ec.SECP256R1())
    return _b64url(key.private_numbers().private_value.to_bytes(32, "big"))


# ---------------------------------------------------------------------------
# VAPID (RFC 8292)
# ---------------------------------------------------------------------------

def vapid_authorization(endpoint: str, key: ec.EllipticCurvePrivateKey, jetzt: int | None = None) -> str:
    """``Authorization``-Kopf fuer einen Push an ``endpoint``.

    ``aud`` ist der Ursprung des Push-Dienstes (etwa https://web.push.apple.com),
    nicht der Endpunkt selbst - so verlangt es der Standard.
    """
    teile = urlparse(endpoint)
    jetzt = int(time.time()) if jetzt is None else jetzt
    kopf = _b64url(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    inhalt = _b64url(json.dumps({
        "aud": f"{teile.scheme}://{teile.netloc}",
        # Hoechstens 24 Stunden erlaubt; 12 lassen Luft fuer schiefe Uhren.
        "exp": jetzt + 12 * 60 * 60,
        "sub": settings.webpush_subject,
    }, separators=(",", ":")).encode())
    zu_signieren = f"{kopf}.{inhalt}".encode("ascii")
    der = key.sign(zu_signieren, ec.ECDSA(hashes.SHA256()))
    # JWS will r||s, cryptography liefert DER - wie beim APNs-Token in push.py.
    r, s = decode_dss_signature(der)
    signatur = _b64url(r.to_bytes(32, "big") + s.to_bytes(32, "big"))
    return f"vapid t={kopf}.{inhalt}.{signatur}, k={_b64url(_public_bytes(key.public_key()))}"


# ---------------------------------------------------------------------------
# Verschluesselung (RFC 8291, Content-Encoding aes128gcm nach RFC 8188)
# ---------------------------------------------------------------------------

def _hkdf(salt: bytes, ikm: bytes, info: bytes, laenge: int) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=laenge, salt=salt, info=info).derive(ikm)


def encrypt(
    nutzlast: bytes,
    p256dh: str,
    auth: str,
    *,
    _server_key: ec.EllipticCurvePrivateKey | None = None,
    _salt: bytes | None = None,
) -> bytes:
    """Nutzlast fuer genau ein Abo verschluesseln.

    ``_server_key`` und ``_salt`` nur fuer Tests (Pruefvektor aus RFC 8291,
    Anhang A) - im Betrieb sind beide bei jeder Nachricht frisch und zufaellig.
    """
    ua_public = _b64url_decode(p256dh)
    auth_secret = _b64url_decode(auth)
    ua_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_public)

    server_key = _server_key or ec.generate_private_key(ec.SECP256R1())
    as_public = _public_bytes(server_key.public_key())
    salt = _salt or os.urandom(16)

    ecdh = server_key.exchange(ec.ECDH(), ua_key)
    ikm = _hkdf(auth_secret, ecdh, b"WebPush: info\x00" + ua_public + as_public, 32)
    cek = _hkdf(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = _hkdf(salt, ikm, b"Content-Encoding: nonce\x00", 12)

    # 0x02 markiert den letzten (und hier einzigen) Datensatz.
    chiffre = AESGCM(cek).encrypt(nonce, nutzlast + b"\x02", None)
    kopf = salt + struct.pack("!IB", _RECORD_SIZE, len(as_public)) + as_public
    return kopf + chiffre


# ---------------------------------------------------------------------------
# Zustellung
# ---------------------------------------------------------------------------

def send(db: Session, eintraege: list[PushToken], title: str, body: str, target: str | None) -> int:
    """An alle Web-Abos in ``eintraege`` zustellen; Rueckgabe: wie viele angenommen wurden.

    Wirft nie - Push ist eine Zugabe (siehe ``push.send``).
    """
    key = _private_key()
    if key is None:
        return 0

    nutzlast = json.dumps(
        {"title": title, "body": body, "target": target or ""}, ensure_ascii=False
    ).encode("utf-8")

    zugestellt = 0
    for eintrag in eintraege:
        if not (eintrag.web_p256dh and eintrag.web_auth) or not endpoint_allowed(eintrag.token):
            continue
        try:
            daten = encrypt(nutzlast, eintrag.web_p256dh, eintrag.web_auth)
            antwort = requests.post(
                eintrag.token,
                data=daten,
                headers={
                    "Authorization": vapid_authorization(eintrag.token, key),
                    "Content-Encoding": "aes128gcm",
                    "Content-Type": "application/octet-stream",
                    "TTL": str(_TTL_SECONDS),
                    # Chat und Match sollen das Geraet sofort erreichen, nicht
                    # erst im naechsten Energiesparfenster.
                    "Urgency": "high",
                },
                timeout=10,
                # Keine Weiterleitungen: Das Ziel ist oben auf die bekannten
                # Push-Dienste beschraenkt, eine Umleitung wuerde das aushebeln.
                allow_redirects=False,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Web-Push nicht erreichbar (user=%s)", eintrag.user_id)
            continue

        if antwort.status_code in (200, 201, 202):
            zugestellt += 1
        elif antwort.status_code in (403, 404, 410):
            # 404/410: Abo abgelaufen oder im Browser widerrufen. 403: Das Abo
            # gehoert zu einem anderen VAPID-Schluessel (etwa nach einem
            # Schluesselwechsel) - in allen Faellen dauerhaft wertlos.
            logger.info("Web-Push verwirft Abo (%s): %s", antwort.status_code, antwort.text[:160])
            db.delete(eintrag)
        else:
            logger.warning("Web-Push antwortet mit %s: %s", antwort.status_code, antwort.text[:160])
    return zugestellt


if __name__ == "__main__":  # pragma: no cover - Hilfsaufruf fuer die Einrichtung
    print(f"WEBPUSH_VAPID_PRIVATE_KEY={generate_private_key()}")
