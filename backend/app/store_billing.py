"""Kaeufe in den Apps: Belege pruefen, Berechtigung schreiben.

FLEXR Premium gibt es auf drei Wegen - im Browser ueber Stripe, in der
iOS-App ueber StoreKit, in der Android-App ueber Play Billing. Die Vorteile
sind in allen dreien dieselben; verschieden ist nur, wer das Geld nimmt und
wer kuendigt.

**Kein Client bestimmt hier irgendetwas.** Was aus einer App kommt, ist ein
Beleg, kein Ergebnis: Apple liefert eine signierte Transaktion, Google einen
Kauf-Token. Der eine wird kryptografisch gegen Apples Wurzelzertifikat
geprueft, der andere durch Rueckfrage bei Google. Ein Client, der behauptet,
er habe bezahlt, erzeugt hier nichts.

Zwei Wege fuehren zu einer Berechtigung, und beide muenden in
``apply_subscription()``:

* **Der Kauf selbst.** Die App reicht ihren Beleg ein, sobald der Kauf
  abgeschlossen ist (und erneut bei jedem Start, siehe die Clients) - nur so
  erfaehrt der Server ueberhaupt, zu welchem *FLEXR-Konto* der Kauf gehoert.
  Apple und Google kennen unser Konto nicht.
* **Die Benachrichtigungen der Stores.** Verlaengerung, Kuendigung,
  Rueckerstattung, Sperre. Sie tragen kein FLEXR-Konto, sondern nur die
  Kennung des Abos - zugeordnet wird ueber die Zeile, die der Kauf angelegt
  hat.

Weil beide Stores ihre Benachrichtigungen **nicht garantiert zustellen**,
haengt die Berechtigung nicht an einem "aktiv"-Schalter, sondern an einem
Ablaufzeitpunkt (``users.store_premium_until``). Bleibt eine Nachricht aus,
erlischt Premium von selbst, statt auf ewig offen zu stehen.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from sqlalchemy.orm import Session

from .config import settings
from .models import StoreProvider, StoreSubscription, User

logger = logging.getLogger(__name__)

APPLE_ROOT_CA = Path(__file__).parent / "data" / "AppleRootCA-G3.cer"

# Wie lange eine Berechtigung ueber das gemeldete Ablaufdatum hinaus gilt.
#
# Apple und Google buchen kurz vor Ablauf ab und melden die Verlaengerung
# danach. Faellt eine Benachrichtigung aus oder kommt sie verspaetet, stuende
# ein zahlender Kunde sonst fuer Stunden ohne Premium da - fuer etwas, das er
# bezahlt hat. Andersherum kostet die Kulanz bei einer echten Kuendigung genau
# diese Zeitspanne zu viel, was die deutlich kleinere Unfreundlichkeit ist.
GRACE = timedelta(hours=16)


class StoreVerificationError(Exception):
    """Der Beleg ist nicht gueltig, nicht fuer uns oder nicht zu pruefen."""


# ---------------------------------------------------------------------------
# Apple: signierte Transaktionen (StoreKit 2) und Server-Benachrichtigungen V2
# ---------------------------------------------------------------------------
#
# Beides sind JWS im selben Format: Der Header traegt unter "x5c" die
# vollstaendige Zertifikatskette (Blatt, Zwischenstelle, Wurzel), signiert
# wird mit ES256. Geprueft wird deshalb in dieser Reihenfolge:
#
#   1. Die Kette endet bei genau dem Wurzelzertifikat, das hier im
#      Repository liegt - nicht bei irgendeinem, dem das System vertraut.
#   2. Jedes Glied ist vom naechsten signiert.
#   3. Die Signatur des JWS stammt vom Blattzertifikat.
#
# Ohne Schritt 1 koennte jeder mit irgendeinem gueltigen Zertifikat Belege
# ausstellen; ohne Schritt 3 waere die Kette nur Dekoration.


def _b64url(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _apple_root() -> x509.Certificate:
    return x509.load_der_x509_certificate(APPLE_ROOT_CA.read_bytes())


def _verify_cert_signed_by(child: x509.Certificate, parent: x509.Certificate) -> None:
    key = parent.public_key()
    if isinstance(key, ec.EllipticCurvePublicKey):
        key.verify(
            child.signature,
            child.tbs_certificate_bytes,
            ec.ECDSA(child.signature_hash_algorithm),
        )
    elif isinstance(key, rsa.RSAPublicKey):
        key.verify(
            child.signature,
            child.tbs_certificate_bytes,
            padding.PKCS1v15(),
            child.signature_hash_algorithm,
        )
    else:  # pragma: no cover - Apple verwendet ausschliesslich EC und RSA
        raise StoreVerificationError("Unbekannter Schluesseltyp in der Zertifikatskette.")


def verify_apple_jws(token: str) -> dict[str, Any]:
    """Prueft ein Apple-JWS und gibt seine Nutzlast zurueck.

    Wirft ``StoreVerificationError``, wenn irgendetwas daran nicht stimmt -
    nie ``True``/``False``: Ein uebersehener Rueckgabewert soll hier keinen
    ungeprueften Beleg durchlassen.
    """
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        header = json.loads(_b64url(header_b64))
    except Exception as fehler:  # noqa: BLE001 - jede Formstoerung ist dasselbe
        raise StoreVerificationError("Beleg ist kein gueltiges JWS.") from fehler

    if header.get("alg") != "ES256":
        raise StoreVerificationError(f"Unerwartetes Signaturverfahren: {header.get('alg')}")

    chain_b64 = header.get("x5c") or []
    if len(chain_b64) < 2:
        raise StoreVerificationError("Beleg ohne Zertifikatskette.")

    try:
        chain = [x509.load_der_x509_certificate(base64.b64decode(c)) for c in chain_b64]
    except Exception as fehler:  # noqa: BLE001
        raise StoreVerificationError("Zertifikatskette nicht lesbar.") from fehler

    # 1. Die Wurzel muss unsere sein.
    if chain[-1].fingerprint(hashes.SHA256()) != _apple_root().fingerprint(hashes.SHA256()):
        raise StoreVerificationError("Beleg stammt nicht aus Apples Zertifikatskette.")

    # 2. Jedes Glied vom naechsten signiert, und keines abgelaufen.
    #
    # Die zeitzonenbehafteten Varianten, weil die alten Namen seit
    # cryptography 42 eine Deprecation-Warnung werfen - hier laufen sie in
    # jeder Anfrage, das waere lautes Rauschen im Log.
    jetzt = datetime.now(timezone.utc)
    for cert in chain:
        if not (cert.not_valid_before_utc <= jetzt <= cert.not_valid_after_utc):
            raise StoreVerificationError("Zertifikat der Kette ist nicht gueltig.")
    try:
        for kind, eltern in zip(chain, chain[1:]):
            _verify_cert_signed_by(kind, eltern)
    except InvalidSignature as fehler:
        raise StoreVerificationError("Zertifikatskette ist gebrochen.") from fehler

    # 3. Die Signatur des Belegs stammt vom Blattzertifikat.
    leaf_key = chain[0].public_key()
    if not isinstance(leaf_key, ec.EllipticCurvePublicKey):
        raise StoreVerificationError("Blattzertifikat traegt keinen EC-Schluessel.")
    roh = _b64url(signature_b64)
    if len(roh) != 64:
        raise StoreVerificationError("Signatur hat die falsche Laenge.")
    # ES256 signiert als r||s, X.509 erwartet DER.
    der = encode_dss_signature(
        int.from_bytes(roh[:32], "big"), int.from_bytes(roh[32:], "big")
    )
    try:
        leaf_key.verify(
            der, f"{header_b64}.{payload_b64}".encode(), ec.ECDSA(hashes.SHA256())
        )
    except InvalidSignature as fehler:
        raise StoreVerificationError("Signatur des Belegs stimmt nicht.") from fehler

    try:
        return json.loads(_b64url(payload_b64))
    except Exception as fehler:  # noqa: BLE001
        raise StoreVerificationError("Nutzlast des Belegs nicht lesbar.") from fehler


def _ms_to_datetime(wert: Any) -> datetime | None:
    """Apple und Google zaehlen in Millisekunden seit 1970, als Zahl oder Text."""
    if wert in (None, ""):
        return None
    try:
        return datetime.utcfromtimestamp(int(wert) / 1000)
    except (TypeError, ValueError):
        return None


def apple_transaction_from_jws(token: str) -> dict[str, Any]:
    """Geprueften Kauf aus einer signierten StoreKit-Transaktion lesen."""
    payload = verify_apple_jws(token)

    if payload.get("bundleId") != settings.apple_bundle_id:
        raise StoreVerificationError("Beleg gehoert zu einer anderen App.")

    produkt = payload.get("productId")
    if settings.apple_subscription_product_id and produkt != settings.apple_subscription_product_id:
        raise StoreVerificationError("Beleg gehoert zu einem anderen Produkt.")

    umgebung = payload.get("environment") or "Production"
    ablauf = _ms_to_datetime(payload.get("expiresDate"))
    widerrufen = _ms_to_datetime(payload.get("revocationDate"))

    return {
        "provider": StoreProvider.apple,
        "external_id": str(
            payload.get("originalTransactionId") or payload.get("transactionId") or ""
        ),
        "product_id": produkt or "",
        # Eine Rueckerstattung hebt den Kauf rueckwirkend auf - dann zaehlt
        # nicht das Ablaufdatum, sondern der Zeitpunkt des Widerrufs.
        "expires_at": None if widerrufen else ablauf,
        "status": "revoked" if widerrufen else "active",
        "auto_renewing": True,
        "environment": umgebung,
    }


# ---------------------------------------------------------------------------
# Google Play: Kauf-Token bei Google nachfragen
# ---------------------------------------------------------------------------
#
# Anders als bei Apple traegt ein Play-Kauf keine pruefbare Signatur - der
# Token ist nur ein Verweis. Die Wahrheit steht bei Google, also wird dort
# gefragt. Das Dienstkonto dafuer richtet man einmalig ein (siehe HANDOFF).

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_API = "https://androidpublisher.googleapis.com/androidpublisher/v3"
_GOOGLE_SCOPE = "https://www.googleapis.com/auth/androidpublisher"

# Zugriffstoken leben eine Stunde; hier gecacht, damit nicht jeder Kauf und
# jede Benachrichtigung eine zusaetzliche Anmeldung ausloest.
_google_token: dict[str, Any] = {"wert": None, "gueltig_bis": 0.0}


def google_configured() -> bool:
    return bool(settings.google_service_account_file and settings.google_package_name)


def _google_access_token() -> str:
    if _google_token["wert"] and _google_token["gueltig_bis"] > time.time() + 60:
        return _google_token["wert"]

    try:
        konto = json.loads(Path(settings.google_service_account_file).read_text())
    except Exception as fehler:  # noqa: BLE001
        raise StoreVerificationError("Google-Dienstkonto nicht lesbar.") from fehler

    jetzt = int(time.time())
    kopf = {"alg": "RS256", "typ": "JWT"}
    rumpf = {
        "iss": konto["client_email"],
        "scope": _GOOGLE_SCOPE,
        "aud": _GOOGLE_TOKEN_URL,
        "iat": jetzt,
        "exp": jetzt + 3600,
    }

    def _teil(daten: dict) -> bytes:
        roh = json.dumps(daten, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(roh).rstrip(b"=")

    zu_signieren = _teil(kopf) + b"." + _teil(rumpf)
    schluessel = serialization.load_pem_private_key(
        konto["private_key"].encode(), password=None
    )
    signatur = schluessel.sign(zu_signieren, padding.PKCS1v15(), hashes.SHA256())
    assertion = zu_signieren + b"." + base64.urlsafe_b64encode(signatur).rstrip(b"=")

    antwort = requests.post(
        _GOOGLE_TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion.decode(),
        },
        timeout=15,
    )
    if antwort.status_code != 200:
        raise StoreVerificationError(
            f"Google-Anmeldung fehlgeschlagen ({antwort.status_code})."
        )
    daten = antwort.json()
    _google_token["wert"] = daten["access_token"]
    _google_token["gueltig_bis"] = time.time() + int(daten.get("expires_in", 3600))
    return _google_token["wert"]


# Googles Zustaende, bei denen das Abo bezahlt ist. "IN_GRACE_PERIOD" gehoert
# dazu: Google wiederholt die Abbuchung ueber einige Tage, genau wie Stripe es
# mit "past_due" tut - wer in dieser Zeit ausgesperrt wird, steht ohne eigenes
# Zutun vor einer verschlossenen App.
_GOOGLE_AKTIV = {
    "SUBSCRIPTION_STATE_ACTIVE",
    "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
    "SUBSCRIPTION_STATE_CANCELED",  # gekuendigt, laeuft aber bis expiryTime
}


def google_subscription_from_token(purchase_token: str) -> dict[str, Any]:
    """Einen Play-Kauf bei Google nachschlagen."""
    if not google_configured():
        raise StoreVerificationError("Play-Kaeufe sind auf diesem Server nicht eingerichtet.")

    antwort = requests.get(
        f"{_GOOGLE_API}/applications/{settings.google_package_name}"
        f"/purchases/subscriptionsv2/tokens/{purchase_token}",
        headers={"Authorization": f"Bearer {_google_access_token()}"},
        timeout=15,
    )
    if antwort.status_code == 404:
        raise StoreVerificationError("Google kennt diesen Kauf nicht.")
    if antwort.status_code != 200:
        raise StoreVerificationError(f"Google antwortet mit {antwort.status_code}.")

    daten = antwort.json()
    zustand = daten.get("subscriptionState", "")
    posten = (daten.get("lineItems") or [{}])[0]
    produkt = posten.get("productId", "")

    if settings.google_subscription_product_id and produkt != settings.google_subscription_product_id:
        raise StoreVerificationError("Kauf gehoert zu einem anderen Produkt.")

    ablauf = None
    if posten.get("expiryTime"):
        # RFC-3339 mit Z und Nanosekunden - auf Mikrosekunden kuerzen, damit
        # fromisoformat es auch unter Python 3.10 nimmt.
        text = posten["expiryTime"].replace("Z", "+00:00")
        if "." in text:
            kopf, rest = text.split(".", 1)
            bruch, _, zone = rest.partition("+")
            text = f"{kopf}.{bruch[:6]}+{zone}" if zone else f"{kopf}.{bruch[:6]}"
        try:
            ablauf = datetime.fromisoformat(text).replace(tzinfo=None)
        except ValueError:
            ablauf = None

    return {
        "provider": StoreProvider.google,
        "external_id": daten.get("latestOrderId") or purchase_token,
        "product_id": produkt,
        "expires_at": ablauf if zustand in _GOOGLE_AKTIV else None,
        "status": zustand.replace("SUBSCRIPTION_STATE_", "").lower() or "unknown",
        "auto_renewing": bool(posten.get("autoRenewingPlan", {}).get("autoRenewEnabled")),
        # Testkaeufe tragen ein eigenes Feld. Sie duerfen in der Produktion
        # kein Premium erzeugen - genau wie Apples Sandbox.
        "environment": "Sandbox" if daten.get("testPurchase") is not None else "Production",
        # Fuer die Bestaetigung weiter unten.
        "_purchase_token": purchase_token,
        "_acknowledged": daten.get("acknowledgementState")
        == "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
    }


def google_acknowledge(product_id: str, purchase_token: str) -> None:
    """Kauf gegenueber Google bestaetigen.

    Ohne diese Bestaetigung storniert Google den Kauf nach drei Tagen
    selbsttaetig und erstattet das Geld - der Kunde haette bezahlt und stuende
    dann ohne Premium da. Serverseitig und nicht im Client, weil erst hier
    feststeht, dass die Berechtigung auch wirklich gutgeschrieben wurde.
    """
    antwort = requests.post(
        f"{_GOOGLE_API}/applications/{settings.google_package_name}"
        f"/purchases/subscriptions/{product_id}/tokens/{purchase_token}:acknowledge",
        headers={"Authorization": f"Bearer {_google_access_token()}"},
        json={},
        timeout=15,
    )
    if antwort.status_code not in (200, 204):
        logger.warning(
            "Play-Kauf konnte nicht bestaetigt werden (%s): %s",
            antwort.status_code,
            antwort.text[:200],
        )


# ---------------------------------------------------------------------------
# Berechtigung schreiben
# ---------------------------------------------------------------------------


def apply_subscription(
    db: Session, user: User | None, beleg: dict[str, Any]
) -> StoreSubscription | None:
    """Traegt einen geprueften Kauf ein und setzt die Berechtigung.

    ``user`` ist gesetzt, wenn der Kauf gerade aus einer App eingereicht wurde;
    bei einer Benachrichtigung des Stores ist er ``None`` und wird ueber die
    vorhandene Zeile gefunden. Kommt eine Benachrichtigung zu einem Kauf, den
    wir nie gesehen haben, gibt es nichts zuzuordnen - dann ``None``.
    """
    if beleg["environment"] != "Production" and not settings.store_sandbox_allowed:
        raise StoreVerificationError(
            "Testkaeufe werden auf diesem Server nicht angenommen."
        )
    if not beleg["external_id"]:
        raise StoreVerificationError("Beleg ohne Kennung.")

    zeile = (
        db.query(StoreSubscription)
        .filter(
            StoreSubscription.provider == beleg["provider"],
            StoreSubscription.external_id == beleg["external_id"],
        )
        .first()
    )

    if zeile is None:
        if user is None:
            logger.info(
                "Benachrichtigung zu unbekanntem Kauf (%s/%s) - nichts zuzuordnen.",
                beleg["provider"].value,
                beleg["external_id"][:12],
            )
            return None
        zeile = StoreSubscription(
            user_id=user.id,
            provider=beleg["provider"],
            external_id=beleg["external_id"],
        )
        db.add(zeile)
    elif user is not None and zeile.user_id != user.id:
        # Derselbe Kauf, ein anderes FLEXR-Konto. Das passiert im Alltag, wenn
        # jemand sein Konto neu anlegt und denselben Apple-/Google-Zugang
        # benutzt. Der Kauf **wandert** dann - er wird nicht kopiert, sonst
        # haetten zwei Konten Premium fuer einmal Geld. Das alte Konto verliert
        # die Berechtigung im selben Zug.
        vorher = db.query(User).filter(User.id == zeile.user_id).first()
        if vorher is not None:
            vorher.store_premium_until = None
        logger.info(
            "Store-Abo %s/%s wechselt das Konto: %s -> %s",
            beleg["provider"].value,
            beleg["external_id"][:12],
            zeile.user_id,
            user.id,
        )
        zeile.user_id = user.id

    zeile.product_id = beleg["product_id"]
    zeile.status = beleg["status"]
    zeile.expires_at = beleg["expires_at"]
    zeile.auto_renewing = beleg["auto_renewing"]
    zeile.environment = beleg["environment"]

    konto = user or db.query(User).filter(User.id == zeile.user_id).first()
    if konto is not None:
        konto.store_premium_until = (
            beleg["expires_at"] + GRACE if beleg["expires_at"] else None
        )
    db.commit()
    return zeile
