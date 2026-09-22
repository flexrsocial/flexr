"""Echte Push-Zustellung ueber Firebase Cloud Messaging.

Warum es das ueberhaupt gibt: FLEXR hat seine Benachrichtigungen bis zum
17.09.2026 von den Apps **abholen** lassen - WorkManager auf Android,
BGTaskScheduler auf iOS. Das funktioniert fuer alles, was ein paar Stunden Zeit
hat (neues Match, Erinnerungen), und es funktioniert fuer eine Chatnachricht
nicht:

* WorkManager laesst als kuerzestes Intervall 15 Minuten zu.
* Im Doze-Modus wird auch dieser Lauf in die naechste Wartungsphase geschoben -
  auf einem schlafenden Telefon ein bis zwei Stunden.
* Nach einem erzwungenen Beenden (Akku-Optimierung mancher Hersteller) laeuft
  gar nichts mehr, bis die App von Hand gestartet wird. Dann kommt die
  Benachrichtigung im selben Moment wie der App-Start - genau so gemeldet.

Mit FCM schickt der Server, und das Geraet wacht dafuer auch aus dem Doze auf.

**Ohne Zugangsdaten passiert hier nichts.** ``send()`` gibt dann still 0
zurueck; der Hintergrundabgleich der Apps bleibt als Fallback bestehen und
liefert weiter, nur eben langsam. Der Server soll nicht mit einem Fehler
antworten, bloss weil Push nicht eingerichtet ist - eine Nachricht zu senden
muss auch dann gelingen.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from pathlib import Path

import httpx
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from sqlalchemy.orm import Session

from .config import settings
from .models import PushToken, User
from .timeutil import utcnow

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"

# Zugriffstoken leben eine Stunde. Gecacht, damit nicht jede Chatnachricht eine
# zusaetzliche Anmeldung bei Google ausloest.
_zugriff: dict[str, object] = {"wert": None, "gueltig_bis": 0.0}


def configured() -> bool:
    return bool(settings.fcm_service_account_file and settings.fcm_project_id)


def _access_token() -> str:
    if _zugriff["wert"] and float(_zugriff["gueltig_bis"]) > time.time() + 60:
        return str(_zugriff["wert"])

    konto = json.loads(Path(settings.fcm_service_account_file).read_text())
    jetzt = int(time.time())

    def _teil(daten: dict) -> bytes:
        return base64.urlsafe_b64encode(
            json.dumps(daten, separators=(",", ":")).encode()
        ).rstrip(b"=")

    zu_signieren = _teil({"alg": "RS256", "typ": "JWT"}) + b"." + _teil({
        "iss": konto["client_email"],
        "scope": _SCOPE,
        "aud": _TOKEN_URL,
        "iat": jetzt,
        "exp": jetzt + 3600,
    })
    schluessel = serialization.load_pem_private_key(
        konto["private_key"].encode(), password=None
    )
    signatur = schluessel.sign(zu_signieren, padding.PKCS1v15(), hashes.SHA256())
    assertion = zu_signieren + b"." + base64.urlsafe_b64encode(signatur).rstrip(b"=")

    antwort = requests.post(
        _TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion.decode(),
        },
        timeout=15,
    )
    antwort.raise_for_status()
    daten = antwort.json()
    _zugriff["wert"] = daten["access_token"]
    _zugriff["gueltig_bis"] = time.time() + int(daten.get("expires_in", 3600))
    return str(_zugriff["wert"])


# ---------------------------------------------------------------------------
# Apple: direkt an APNs, ohne Firebase
# ---------------------------------------------------------------------------
#
# Warum nicht auch ueber FCM: Dafuer muesste die iOS-App das Firebase-SDK
# einbinden. Ein Swift-Package laesst sich nicht so nebenbei ins Xcode-Projekt
# haengen wie eine Gradle-Zeile, und die App braucht fuer den direkten Weg kein
# einziges fremdes Paket - nur die Push-Berechtigung. Dazu kommt, dass so
# nichts an Google geht, was nicht muss.
#
# APNs spricht ausschliesslich HTTP/2, deshalb httpx statt requests.

_APNS_PROD = "https://api.push.apple.com"
_APNS_SANDBOX = "https://api.sandbox.push.apple.com"

# Apples Token ist eine Stunde gueltig und darf hoechstens alle 20 Minuten neu
# erzeugt werden. 50 Minuten liegen bequem zwischen beiden Grenzen.
_apns_jwt: dict[str, object] = {"wert": None, "erzeugt": 0.0}


def apns_configured() -> bool:
    return bool(settings.apns_key_file and settings.apns_key_id and settings.apns_team_id)


def _apns_jwt_token() -> str:
    if _apns_jwt["wert"] and time.time() - float(_apns_jwt["erzeugt"]) < 50 * 60:
        return str(_apns_jwt["wert"])

    schluessel = serialization.load_pem_private_key(
        Path(settings.apns_key_file).read_bytes(), password=None
    )

    def _teil(daten: dict) -> bytes:
        return base64.urlsafe_b64encode(
            json.dumps(daten, separators=(",", ":")).encode()
        ).rstrip(b"=")

    zu_signieren = _teil({"alg": "ES256", "kid": settings.apns_key_id}) + b"." + _teil(
        {"iss": settings.apns_team_id, "iat": int(time.time())}
    )
    der = schluessel.sign(zu_signieren, ec.ECDSA(hashes.SHA256()))
    # ES256 will r||s, cryptography liefert DER.
    r, s = decode_dss_signature(der)
    roh = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    jwt = zu_signieren + b"." + base64.urlsafe_b64encode(roh).rstrip(b"=")

    _apns_jwt["wert"] = jwt.decode()
    _apns_jwt["erzeugt"] = time.time()
    return str(_apns_jwt["wert"])


def _apns_send_one(
    client: httpx.Client, basis: str, jwt: str, eintrag: PushToken, nutzlast: dict
) -> httpx.Response:
    return client.post(
        f"{basis}/3/device/{eintrag.token}",
        headers={
            "authorization": f"bearer {jwt}",
            "apns-topic": settings.apns_topic,
            "apns-push-type": "alert",
            # 10 = sofort zustellen und das Geraet dafuer aufwecken. Genau das
            # ist der Punkt der ganzen Uebung.
            "apns-priority": "10",
        },
        json=nutzlast,
    )


def _send_apns(db: Session, eintraege: list[PushToken], title: str, body: str, target: str | None) -> int:
    if not apns_configured():
        return 0
    try:
        jwt = _apns_jwt_token()
    except Exception:  # noqa: BLE001 - Schluesseldatei fehlt oder ist unlesbar
        logger.exception("APNs-Schluessel nicht verwendbar")
        return 0

    nutzlast = {
        "aps": {
            "alert": {"title": title, "body": body},
            "sound": "default",
        },
        # Flach neben "aps": Die App liest den Schluessel im
        # Benachrichtigungs-Handler (siehe FlexrApp.swift) und weiss dadurch,
        # wohin der Tipp fuehrt, ohne den Text zu deuten.
        "target": target or "",
    }

    zuerst = _APNS_SANDBOX if settings.apns_sandbox else _APNS_PROD
    dann = _APNS_PROD if settings.apns_sandbox else _APNS_SANDBOX

    zugestellt = 0
    with httpx.Client(http2=True, timeout=10) as client:
        for eintrag in eintraege:
            try:
                antwort = _apns_send_one(client, zuerst, jwt, eintrag, nutzlast)
                # "BadDeviceToken" heisst fast immer: Der Token gehoert zur
                # jeweils anderen Umgebung. Ein Entwicklungs-Build bekommt
                # Sandbox-Tokens, TestFlight und App Store Produktions-Tokens -
                # und beide koennen gleichzeitig im Umlauf sein. Statt das zu
                # konfigurieren, wird schlicht die andere Seite probiert.
                if antwort.status_code == 400 and "BadDeviceToken" in antwort.text:
                    antwort = _apns_send_one(client, dann, jwt, eintrag, nutzlast)
            except Exception:  # noqa: BLE001
                logger.warning("APNs nicht erreichbar (user=%s)", eintrag.user_id)
                continue

            if antwort.status_code == 200:
                zugestellt += 1
            elif antwort.status_code in (400, 403, 410):
                # 410 = Unregistered: Die App ist von diesem Geraet
                # verschwunden. Der Token ist dauerhaft wertlos.
                logger.info("APNs verwirft Token (%s): %s", antwort.status_code, antwort.text[:160])
                db.delete(eintrag)
            else:
                logger.warning("APNs antwortet mit %s: %s", antwort.status_code, antwort.text[:160])
    return zugestellt


def register(db: Session, user: User, platform: str, token: str) -> PushToken:
    """Einen Geraetetoken hinterlegen.

    Derselbe Token kann nach einem Kontowechsel auf demselben Geraet erneut
    gemeldet werden - dann **wandert** er, statt doppelt zu existieren. Sonst
    bekaeme der Vorbesitzer die Benachrichtigungen des neuen Nutzers auf sein
    Geraet.
    """
    from datetime import datetime

    eintrag = db.query(PushToken).filter(PushToken.token == token).first()
    if eintrag is None:
        eintrag = PushToken(user_id=user.id, platform=platform, token=token)
        db.add(eintrag)
    else:
        if eintrag.user_id != user.id:
            logger.info("Push-Token wechselt das Konto: %s -> %s", eintrag.user_id, user.id)
        eintrag.user_id = user.id
        eintrag.platform = platform
        eintrag.last_seen = utcnow()
    db.commit()
    return eintrag


def unregister(db: Session, token: str) -> None:
    """Token entfernen - beim Abmelden und beim Abschalten der Benachrichtigungen.

    Der Token **ist** der Schalter: Ohne ihn hat der Server niemanden, dem er
    zustellen koennte.
    """
    db.query(PushToken).filter(PushToken.token == token).delete()
    db.commit()


def _send_fcm(db: Session, eintraege: list[PushToken], title: str, body: str, target: str | None) -> int:
    if not configured():
        return 0
    try:
        kopf = {"Authorization": f"Bearer {_access_token()}"}
    except Exception:  # noqa: BLE001 - Zugangsdaten falsch, Google weg, egal
        logger.exception("FCM-Anmeldung fehlgeschlagen")
        return 0

    url = f"https://fcm.googleapis.com/v1/projects/{settings.fcm_project_id}/messages:send"
    zugestellt = 0
    for eintrag in eintraege:
        nachricht = {
            "message": {
                "token": eintrag.token,
                "notification": {"title": title, "body": body},
                # Die Nutzlast traegt das Ziel mit, damit der Tap in der App am
                # richtigen Bildschirm landet, ohne den Text zu deuten.
                "data": {"target": target or ""},
                "android": {
                    # Hoechste Prioritaet: Nur damit weckt FCM ein Geraet aus
                    # dem Doze. Ohne sie waere der ganze Umbau wirkungslos -
                    # die Nachricht laege bis zum naechsten Wartungsfenster.
                    "priority": "high",
                    "notification": {"channel_id": "flexr_messages"},
                },
            }
        }
        try:
            antwort = requests.post(url, headers=kopf, json=nachricht, timeout=10)
        except Exception:  # noqa: BLE001
            logger.warning("FCM nicht erreichbar (user=%s)", eintrag.user_id)
            continue

        if antwort.status_code == 200:
            zugestellt += 1
            continue

        # 404/UNREGISTERED heisst: Die App ist von diesem Geraet verschwunden.
        # Der Token ist damit dauerhaft wertlos - stehen zu lassen hiesse, ihn
        # bei jeder kuenftigen Nachricht erneut zu versuchen.
        if antwort.status_code in (400, 403, 404):
            logger.info(
                "Push-Token verworfen (%s): %s",
                antwort.status_code,
                antwort.text[:160],
            )
            db.delete(eintrag)
        else:
            logger.warning("FCM antwortet mit %s: %s", antwort.status_code, antwort.text[:160])
    return zugestellt


def send(
    db: Session,
    user: User,
    title: str,
    body: str,
    target: str | None = None,
) -> int:
    """An alle Geraete dieses Nutzers zustellen. Gibt zurueck, wie viele erreicht wurden.

    Zwei Wege, je nach Plattform: Android ueber FCM, iOS direkt an APNs (der
    Grund steht bei ``_send_apns``). Fuer den Aufrufer ist das eine Frage -
    er weiss nicht, auf welchem Geraet jemand gerade liest, und soll es auch
    nicht wissen muessen.

    Wirft bewusst **nie**: Push ist eine Zugabe. Eine Chatnachricht muss auch
    dann ankommen, wenn Apple oder Google gerade nicht erreichbar sind oder
    Push gar nicht eingerichtet wurde.
    """
    eintraege = db.query(PushToken).filter(PushToken.user_id == user.id).all()
    if not eintraege:
        return 0

    android = [e for e in eintraege if e.platform == "android"]
    ios = [e for e in eintraege if e.platform == "ios"]

    zugestellt = 0
    if android:
        zugestellt += _send_fcm(db, android, title, body, target)
    if ios:
        zugestellt += _send_apns(db, ios, title, body, target)

    db.commit()
    return zugestellt


def send_async(user_id: str, title: str, body: str, target: str | None = None) -> None:
    """Wie ``send()``, aber mit einer eigenen, kurzlebigen DB-Session - fuer
    den Aufruf aus ``BackgroundTasks`` heraus.

    FastAPI schliesst Dependencies mit ``yield`` (also die Request-Session)
    **vor** den BackgroundTasks (siehe der Kommentar dazu in
    ``routers/auth.py``) - ``send()`` bekaeme von dort aus schon eine
    geschlossene Session uebergeben. Deshalb hier bewusst ``database`` als
    Modul importiert und ``database.SessionLocal`` erst beim Aufruf
    nachgeschlagen (nicht ``from .database import SessionLocal`` oben im
    Modul): Tests ersetzen die Session-Fabrik fuer genau diesen Weg, ein
    Import zum Ladezeitpunkt der Datei wuerde die alte Fabrik einfrieren.

    Wirft wie ``send()`` bewusst nie - hier gibt es zusaetzlich keinen
    Aufrufer mehr, der einen Fehler ohnehin nur wegloggen wuerde.
    """
    from . import database

    db = database.SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return
        send(db, user, title, body, target)
    except Exception:  # noqa: BLE001 - siehe Docstring
        logger.exception("Push-Zustellung im Hintergrund fehlgeschlagen (user=%s)", user_id)
    finally:
        db.close()
