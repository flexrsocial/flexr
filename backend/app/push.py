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

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from sqlalchemy.orm import Session

from .config import settings
from .models import PushToken, User

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
        eintrag.last_seen = datetime.utcnow()
    db.commit()
    return eintrag


def unregister(db: Session, token: str) -> None:
    """Token entfernen - beim Abmelden und beim Abschalten der Benachrichtigungen.

    Der Token **ist** der Schalter: Ohne ihn hat der Server niemanden, dem er
    zustellen koennte.
    """
    db.query(PushToken).filter(PushToken.token == token).delete()
    db.commit()


def send(
    db: Session,
    user: User,
    title: str,
    body: str,
    target: str | None = None,
) -> int:
    """An alle Geraete dieses Nutzers zustellen. Gibt zurueck, wie viele erreicht wurden.

    Wirft bewusst **nie**: Push ist eine Zugabe. Eine Chatnachricht muss auch
    dann ankommen, wenn Google gerade nicht erreichbar ist oder Push gar nicht
    eingerichtet wurde.
    """
    if not configured():
        return 0

    eintraege = db.query(PushToken).filter(PushToken.user_id == user.id).all()
    if not eintraege:
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
                "apns": {
                    "headers": {"apns-priority": "10"},
                    "payload": {"aps": {"sound": "default"}},
                },
            }
        }
        try:
            antwort = requests.post(url, headers=kopf, json=nachricht, timeout=10)
        except Exception:  # noqa: BLE001
            logger.warning("FCM nicht erreichbar (user=%s)", user.id)
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

    db.commit()
    return zugestellt
