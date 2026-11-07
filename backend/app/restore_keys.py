"""Restore Credentials der Android-App: Anmeldung nach dem Geraetewechsel.

Google Play verlangt ab April 2027, dass eingeloggte Nutzer nach einem
Geraetewechsel (Geraet-zu-Geraet-Uebertragung oder Cloud-Backup) ohne erneute
Anmeldung eingeloggt sind ("Zero-Tap-Wiederherstellung von Anmeldedaten").
Der Weg dorthin ist der Restore Key des Android Credential Managers
(``CreateRestoreCredentialRequest`` / ``GetRestoreCredentialOption``):

1. Nach dem Anmelden holt die App hier Erstellungsoptionen
   (``registration_options``), legt damit still einen WebAuthn-Schluessel an
   und schickt dessen Registrierungsantwort zurueck (``register``). Gespeichert
   wird nur der oeffentliche Schluessel.
2. Auf dem neuen Geraet holt die App beim ersten Start - noch ohne Konto -
   eine Challenge (``authentication_options``), laesst sie vom mitgewanderten
   Schluessel signieren und tauscht die Antwort gegen ein Zugriffstoken
   (``authenticate``). Danach gelten dieselben Regeln wie beim Passwort-Login.
3. Abmelden, Kontoloeschung und Passwortwechsel verwerfen den Schluessel.

Die Pruefung ist bewusst hier ausprogrammiert statt ueber eine
WebAuthn-Bibliothek: Gebraucht wird nur ein kleiner, fester Ausschnitt
(Attestation "none", ES256/RS256/EdDSA, ein bekannter Ursprung), und die
Kryptografie selbst macht ``cryptography`` - das ohnehin installiert ist
(python-jose[cryptography]). Eine neue Abhaengigkeit haette auf dem Server
ein ``pip install`` beim Deploy bedeutet.

Abweichungen von einem Passkey-Server, beide von Google so vorgegeben:

* Kein ``uv``-Zwang: Restore Keys werden still eingeloest, Android setzt das
  User-Verified-Flag dabei auf falsch.
* Kein Abgleich des Signaturzaehlers: Ein Restore Key wird absichtlich auf ein
  anderes Geraet kopiert. Der Zaehler wird nur mitgeschrieben.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import struct
from datetime import timedelta
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .config import settings
from .models import RestoreChallenge, RestoreCredential, User
from .retention import RESTORE_KEY_MAX_AGE_DAYS
from .timeutil import utcnow

#: Gueltigkeit einer Challenge. Die App fragt sie unmittelbar vor dem Aufruf
#: des Credential Managers ab; mehr als ein paar Sekunden braucht es nie.
CHALLENGE_TTL = timedelta(minutes=5)

#: Hoechstens so viele Restore Keys je Konto (Handy, Tablet, Wechsel).
#: Ein Geraet hat ohnehin nur einen - siehe register().
MAX_KEYS_PER_USER = 5

PURPOSE_REGISTER = "register"
PURPOSE_LOGIN = "login"

# COSE-Algorithmen, die wir anbieten und annehmen.
ALG_ES256 = -7
ALG_EDDSA = -8
ALG_RS256 = -257
SUPPORTED_ALGS = (ALG_ES256, ALG_EDDSA, ALG_RS256)

# Flags in den Authenticator-Daten (WebAuthn § 6.1).
FLAG_UP = 0x01
FLAG_UV = 0x04
FLAG_AT = 0x40
FLAG_ED = 0x80


class RestoreKeyError(Exception):
    """Antwort taugt nicht. Der Text ist fuers Log, nicht fuer den Nutzer."""


# ---------------------------------------------------------------------------
# Kodierung
# ---------------------------------------------------------------------------


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    if not isinstance(value, str):
        raise RestoreKeyError("base64url erwartet")
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, TypeError) as err:
        raise RestoreKeyError("kein gueltiges base64url") from err


def _cbor_decode(data: bytes, pos: int = 0, depth: int = 0) -> tuple[Any, int]:
    """Minimaler CBOR-Leser (RFC 8949) fuer Attestation-Objekt und COSE-Key.

    Kann genau das, was dort vorkommt: ganze Zahlen, Byte- und Textketten,
    Arrays, Maps und die einfachen Werte false/true/null - jeweils mit
    bestimmter Laenge. Alles andere ist hier ein Fehler.
    """
    if depth > 8:
        raise RestoreKeyError("CBOR zu tief verschachtelt")
    if pos >= len(data):
        raise RestoreKeyError("CBOR endet vorzeitig")
    first = data[pos]
    pos += 1
    major, info = first >> 5, first & 0x1F

    if major == 7:
        simple = {20: False, 21: True, 22: None}
        if info in simple:
            return simple[info], pos
        raise RestoreKeyError("CBOR-Wert nicht unterstuetzt")

    if info < 24:
        arg = info
    elif info in (24, 25, 26, 27):
        size = 1 << (info - 24)
        if pos + size > len(data):
            raise RestoreKeyError("CBOR endet vorzeitig")
        arg = int.from_bytes(data[pos:pos + size], "big")
        pos += size
    else:
        raise RestoreKeyError("CBOR mit unbestimmter Laenge nicht unterstuetzt")

    if major == 0:
        return arg, pos
    if major == 1:
        return -1 - arg, pos
    if major in (2, 3):
        if pos + arg > len(data):
            raise RestoreKeyError("CBOR endet vorzeitig")
        chunk = data[pos:pos + arg]
        pos += arg
        if major == 2:
            return chunk, pos
        try:
            return chunk.decode("utf-8"), pos
        except UnicodeDecodeError as err:
            raise RestoreKeyError("CBOR-Text kein UTF-8") from err
    if major == 4:
        if arg > 64:
            raise RestoreKeyError("CBOR-Array zu lang")
        items = []
        for _ in range(arg):
            item, pos = _cbor_decode(data, pos, depth + 1)
            items.append(item)
        return items, pos
    if major == 5:
        if arg > 64:
            raise RestoreKeyError("CBOR-Map zu lang")
        result: dict = {}
        for _ in range(arg):
            key, pos = _cbor_decode(data, pos, depth + 1)
            if isinstance(key, (list, dict)):
                raise RestoreKeyError("CBOR-Schluessel ungueltig")
            value, pos = _cbor_decode(data, pos, depth + 1)
            result[key] = value
        return result, pos
    raise RestoreKeyError("CBOR-Typ nicht unterstuetzt")


def cbor_decode(data: bytes) -> Any:
    value, end = _cbor_decode(data)
    if end != len(data):
        raise RestoreKeyError("CBOR mit Restdaten")
    return value


# ---------------------------------------------------------------------------
# Schluessel und Signatur
# ---------------------------------------------------------------------------


def _cose_alg(cose: dict) -> int:
    alg = cose.get(3)
    if alg not in SUPPORTED_ALGS:
        raise RestoreKeyError(f"Algorithmus {alg!r} nicht unterstuetzt")
    return alg


def _public_key_from_cose(cose: dict):
    alg = _cose_alg(cose)
    kty = cose.get(1)
    try:
        if alg == ALG_ES256:
            x, y = cose.get(-2), cose.get(-3)
            if kty != 2 or cose.get(-1) != 1 or not isinstance(x, bytes) or not isinstance(y, bytes) \
                    or len(x) != 32 or len(y) != 32:
                raise RestoreKeyError("ES256-Schluessel ungueltig")
            return ec.EllipticCurvePublicNumbers(
                int.from_bytes(x, "big"), int.from_bytes(y, "big"), ec.SECP256R1()
            ).public_key()
        if alg == ALG_EDDSA:
            x = cose.get(-2)
            if kty != 1 or cose.get(-1) != 6 or not isinstance(x, bytes):
                raise RestoreKeyError("EdDSA-Schluessel ungueltig")
            return ed25519.Ed25519PublicKey.from_public_bytes(x)
        n, e = cose.get(-1), cose.get(-2)
        if kty != 3 or not isinstance(n, bytes) or not isinstance(e, bytes) or len(n) < 256:
            raise RestoreKeyError("RS256-Schluessel ungueltig")
        return rsa.RSAPublicNumbers(int.from_bytes(e, "big"), int.from_bytes(n, "big")).public_key()
    except ValueError as err:  # Punkt nicht auf der Kurve u. ae.
        raise RestoreKeyError("Schluessel ungueltig") from err


def _verify_signature(cose: dict, signature: bytes, signed: bytes) -> None:
    alg = _cose_alg(cose)
    key = _public_key_from_cose(cose)
    try:
        if alg == ALG_ES256:
            key.verify(signature, signed, ec.ECDSA(hashes.SHA256()))
        elif alg == ALG_EDDSA:
            key.verify(signature, signed)
        else:
            key.verify(signature, signed, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature as err:
        raise RestoreKeyError("Signatur ungueltig") from err


# ---------------------------------------------------------------------------
# Herkunft
# ---------------------------------------------------------------------------


def allowed_origins() -> set[str]:
    """Ursprung, den Android in clientDataJSON eintraegt:
    ``android:apk-key-hash:`` + base64url(SHA-256 des Signaturzertifikats)."""
    origins = set()
    for fp in settings.restore_key_cert_fingerprints.split(","):
        hex_digits = fp.strip().replace(":", "")
        if not hex_digits:
            continue
        origins.add("android:apk-key-hash:" + b64url_encode(bytes.fromhex(hex_digits)))
    return origins


def _rp_id_hash() -> bytes:
    return hashlib.sha256(settings.webauthn_rp_id.encode("ascii")).digest()


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------


def _new_challenge(db: Session, purpose: str, user: User | None) -> str:
    challenge = b64url_encode(secrets.token_bytes(32))
    db.add(
        RestoreChallenge(
            challenge=challenge,
            purpose=purpose,
            user_id=user.id if user else None,
            expires_at=utcnow() + CHALLENGE_TTL,
        )
    )
    db.commit()
    return challenge


def _parse_client_data(raw: bytes, expected_type: str) -> dict:
    try:
        client_data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise RestoreKeyError("clientDataJSON unlesbar") from err
    if not isinstance(client_data, dict):
        raise RestoreKeyError("clientDataJSON kein Objekt")
    if client_data.get("type") != expected_type:
        raise RestoreKeyError("falscher clientData-Typ")
    origin = str(client_data.get("origin", "")).rstrip("=")
    if origin not in allowed_origins():
        raise RestoreKeyError(f"Ursprung {origin!r} nicht zugelassen")
    package = client_data.get("androidPackageName")
    if package is not None and package != settings.google_package_name:
        raise RestoreKeyError("fremdes App-Paket")
    return client_data


def _consume_challenge(
    db: Session, client_data: dict, purpose: str, user: User | None
) -> None:
    """Challenge aus clientDataJSON pruefen und sofort verbrauchen."""
    challenge = client_data.get("challenge")
    if not isinstance(challenge, str) or not challenge:
        raise RestoreKeyError("Challenge fehlt")
    entry = (
        db.query(RestoreChallenge)
        .filter(RestoreChallenge.challenge == challenge.rstrip("="))
        .first()
    )
    if entry is None:
        raise RestoreKeyError("Challenge unbekannt oder schon benutzt")
    # Einmalig - auch wenn der Rest der Pruefung gleich scheitert.
    db.delete(entry)
    db.commit()
    if entry.purpose != purpose:
        raise RestoreKeyError("Challenge fuer einen anderen Zweck")
    if utcnow() > entry.expires_at:
        raise RestoreKeyError("Challenge abgelaufen")
    if purpose == PURPOSE_REGISTER and (user is None or entry.user_id != user.id):
        raise RestoreKeyError("Challenge gehoert zu einem anderen Konto")


def _parse_auth_data(auth_data: bytes) -> tuple[int, int, int]:
    """(flags, sign_count, Laenge des festen Kopfes)."""
    if len(auth_data) < 37:
        raise RestoreKeyError("authenticatorData zu kurz")
    if not secrets.compare_digest(auth_data[:32], _rp_id_hash()):
        raise RestoreKeyError("rpIdHash passt nicht")
    flags = auth_data[32]
    (sign_count,) = struct.unpack(">I", auth_data[33:37])
    return flags, sign_count, 37


def _load_response(response_json: str) -> dict:
    try:
        data = json.loads(response_json)
    except (TypeError, json.JSONDecodeError) as err:
        raise RestoreKeyError("Antwort ist kein JSON") from err
    if not isinstance(data, dict) or not isinstance(data.get("response"), dict):
        raise RestoreKeyError("Antwort ohne response")
    if data.get("type", "public-key") != "public-key":
        raise RestoreKeyError("falscher Credential-Typ")
    return data


# ---------------------------------------------------------------------------
# Anlegen
# ---------------------------------------------------------------------------


def registration_options(db: Session, user: User) -> dict:
    """``PublicKeyCredentialCreationOptionsJSON`` fuer CreateRestoreCredentialRequest.

    Als user.name steht bewusst die Konto-ID statt E-Mail oder Name: Der
    Schluessel landet im Google-Backup des Nutzers, und niemand bekommt ihn je
    angezeigt - dafuer braucht es keine Klardaten.
    """
    return {
        "challenge": _new_challenge(db, PURPOSE_REGISTER, user),
        "rp": {"name": "FLEXR", "id": settings.webauthn_rp_id},
        "user": {
            "id": b64url_encode(user.id.encode("utf-8")),
            "name": user.id,
            "displayName": "FLEXR",
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": ALG_ES256},
            {"type": "public-key", "alg": ALG_RS256},
        ],
        "timeout": 60000,
        "attestation": "none",
        "excludeCredentials": [],
        "authenticatorSelection": {
            "requireResidentKey": True,
            "residentKey": "required",
            "userVerification": "required",
        },
    }


def register(
    db: Session, user: User, response_json: str, device_id: str | None
) -> RestoreCredential:
    data = _load_response(response_json)
    response = data["response"]

    client_data = _parse_client_data(
        b64url_decode(response.get("clientDataJSON")), "webauthn.create"
    )
    _consume_challenge(db, client_data, PURPOSE_REGISTER, user)

    attestation = cbor_decode(b64url_decode(response.get("attestationObject")))
    if not isinstance(attestation, dict) or not isinstance(attestation.get("authData"), bytes):
        raise RestoreKeyError("attestationObject ohne authData")
    # Die Attestation selbst pruefen wir nicht (angefordert ist "none"): Es
    # geht um die Bindung an ein Konto, nicht um das Modell des Geraets.
    auth_data = attestation["authData"]
    flags, sign_count, pos = _parse_auth_data(auth_data)
    if not flags & FLAG_AT:
        raise RestoreKeyError("keine Credential-Daten")
    if len(auth_data) < pos + 18:
        raise RestoreKeyError("Credential-Daten zu kurz")
    pos += 16  # AAGUID
    (cred_len,) = struct.unpack(">H", auth_data[pos:pos + 2])
    pos += 2
    if cred_len < 16 or cred_len > 1023 or len(auth_data) < pos + cred_len:
        raise RestoreKeyError("Credential-ID ungueltig")
    credential_id = auth_data[pos:pos + cred_len]
    pos += cred_len
    cose, end = _cbor_decode(auth_data, pos)
    if not isinstance(cose, dict):
        raise RestoreKeyError("COSE-Key ungueltig")
    if end != len(auth_data) and not flags & FLAG_ED:
        raise RestoreKeyError("authenticatorData mit Restdaten")
    _public_key_from_cose(cose)  # wirft, wenn der Schluessel nichts taugt

    raw_id = data.get("rawId") or data.get("id")
    if raw_id is not None and b64url_decode(raw_id) != credential_id:
        raise RestoreKeyError("id passt nicht zu den Credential-Daten")

    credential_b64 = b64url_encode(credential_id)
    taken = (
        db.query(RestoreCredential)
        .filter(RestoreCredential.credential_id == credential_b64)
        .first()
    )
    if taken is not None and taken.user_id != user.id:
        raise RestoreKeyError("Credential-ID gehoert einem anderen Konto")

    # Ein Geraet haelt je App genau einen Restore Key - ein neuer ersetzt den
    # alten dort, also auch hier.
    replaced = [RestoreCredential.credential_id == credential_b64]
    if device_id:
        replaced.append(RestoreCredential.device_id == device_id)
    db.query(RestoreCredential).filter(
        RestoreCredential.user_id == user.id, or_(*replaced)
    ).delete(synchronize_session=False)
    db.flush()

    entry = RestoreCredential(
        user_id=user.id,
        credential_id=credential_b64,
        public_key=b64url_encode(auth_data[pos:end]),
        sign_count=sign_count,
        device_id=device_id,
    )
    db.add(entry)
    db.flush()

    # Obergrenze je Konto: die aeltesten fallen weg.
    keys = (
        db.query(RestoreCredential)
        .filter(RestoreCredential.user_id == user.id)
        .order_by(RestoreCredential.created_at.desc(), RestoreCredential.id)
        .all()
    )
    for old in keys[MAX_KEYS_PER_USER:]:
        if old.id != entry.id:
            db.delete(old)
    db.commit()
    return entry


# ---------------------------------------------------------------------------
# Einloesen
# ---------------------------------------------------------------------------


def authentication_options(db: Session) -> dict:
    """``PublicKeyCredentialRequestOptionsJSON`` fuer GetRestoreCredentialOption.

    Ohne allowCredentials: Das neue Geraet weiss noch nicht, wer es ist - das
    sagt erst die Antwort (userHandle und Credential-ID).
    """
    return {
        "challenge": _new_challenge(db, PURPOSE_LOGIN, None),
        "rpId": settings.webauthn_rp_id,
        "allowCredentials": [],
        "timeout": 60000,
        "userVerification": "discouraged",
    }


def authenticate(db: Session, response_json: str) -> tuple[User, RestoreCredential]:
    """Signierte Challenge pruefen. Die Kontoregeln (geloescht, gesperrt,
    Passwortwechsel) prueft der Aufrufer - siehe routers/auth.py."""
    data = _load_response(response_json)
    response = data["response"]

    client_data_raw = b64url_decode(response.get("clientDataJSON"))
    client_data = _parse_client_data(client_data_raw, "webauthn.get")
    _consume_challenge(db, client_data, PURPOSE_LOGIN, None)

    raw_id = data.get("rawId") or data.get("id")
    if not isinstance(raw_id, str):
        raise RestoreKeyError("Credential-ID fehlt")
    credential_b64 = b64url_encode(b64url_decode(raw_id))
    entry = (
        db.query(RestoreCredential)
        .filter(RestoreCredential.credential_id == credential_b64)
        .first()
    )
    if entry is None:
        raise RestoreKeyError("Restore Key unbekannt")

    user_handle = response.get("userHandle")
    if user_handle and b64url_decode(user_handle) != entry.user_id.encode("utf-8"):
        raise RestoreKeyError("userHandle passt nicht zum Schluessel")

    auth_data = b64url_decode(response.get("authenticatorData"))
    _flags, sign_count, _ = _parse_auth_data(auth_data)
    signed = auth_data + hashlib.sha256(client_data_raw).digest()
    cose = cbor_decode(b64url_decode(entry.public_key))
    _verify_signature(cose, b64url_decode(response.get("signature")), signed)

    user = db.query(User).filter(User.id == entry.user_id).first()
    if user is None:
        raise RestoreKeyError("Konto nicht mehr vorhanden")

    entry.sign_count = max(entry.sign_count or 0, sign_count)
    entry.last_used_at = utcnow()
    db.commit()
    return user, entry


# ---------------------------------------------------------------------------
# Verwerfen
# ---------------------------------------------------------------------------


def delete_for_device(
    db: Session, user: User, device_id: str | None, credential_id: str | None
) -> int:
    """Beim Abmelden: den Schluessel dieses Geraets verwerfen.

    Erkannt an der Credential-ID, die die App sich gemerkt hat, oder an der
    Geraete-ID. Andere Geraete desselben Kontos behalten ihren.
    """
    if not device_id and not credential_id:
        return 0
    query = db.query(RestoreCredential).filter(RestoreCredential.user_id == user.id)
    conditions = []
    if device_id:
        conditions.append(RestoreCredential.device_id == device_id)
    if credential_id:
        conditions.append(RestoreCredential.credential_id == credential_id.rstrip("="))
    n = query.filter(or_(*conditions)).delete(synchronize_session=False)
    db.commit()
    return n


def delete_all_for_user(db: Session, user: User, commit: bool = True) -> int:
    """Kontoloeschung und Passwortwechsel: alle Schluessel des Kontos."""
    n = (
        db.query(RestoreCredential)
        .filter(RestoreCredential.user_id == user.id)
        .delete(synchronize_session=False)
    )
    db.query(RestoreChallenge).filter(RestoreChallenge.user_id == user.id).delete(
        synchronize_session=False
    )
    if commit:
        db.commit()
    return n


def purge_expired(db: Session) -> int:
    """Stuendlicher Lauf: abgelaufene Challenges und Schluessel, die aelter
    sind als RESTORE_KEY_MAX_AGE_DAYS. Die App erneuert ihren Schluessel
    regelmaessig; was so alt ist, gehoert zu einer deinstallierten App oder
    einem Geraet, das nie mehr geoeffnet wurde."""
    now = utcnow()
    db.query(RestoreChallenge).filter(RestoreChallenge.expires_at < now).delete(
        synchronize_session=False
    )
    n = (
        db.query(RestoreCredential)
        .filter(RestoreCredential.created_at < now - timedelta(days=RESTORE_KEY_MAX_AGE_DAYS))
        .delete(synchronize_session=False)
    )
    db.commit()
    return n
