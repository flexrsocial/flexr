"""Web Push: Verschluesselung, VAPID, Abo-Verwaltung und Zustellung.

Web Push ist der Benachrichtigungsweg der Web-App - vor allem fuer iPhones,
solange es keine App-Store-App gibt (installiert auf dem Home-Bildschirm,
ab iOS 16.4). Verschluesselung und Signatur sind ohne Fremdpaket gebaut
(app/webpush.py); der Pruefvektor aus RFC 8291 haelt fest, dass sie Byte fuer
Byte dem Standard entsprechen - sonst verwirft der Browser jede Nachricht
still, und niemand merkt es.
"""

import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from app import notifications, push, webpush
from app.config import settings
from app.models import NotificationTopic, PushToken, User
from tests.conftest import TestingSessionLocal, register_user


def _b64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _key_from_b64(text: str) -> ec.EllipticCurvePrivateKey:
    return ec.derive_private_key(int.from_bytes(_b64(text), "big"), ec.SECP256R1())


# Schluessel eines erfundenen Browsers fuer die API-Tests.
_UA_KEY = ec.generate_private_key(ec.SECP256R1())
_UA_PUBLIC = base64.urlsafe_b64encode(
    _UA_KEY.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
).rstrip(b"=").decode()
_AUTH = base64.urlsafe_b64encode(b"0123456789abcdef").rstrip(b"=").decode()
_APPLE = "https://web.push.apple.com/QGuQyavXutnMbnHQgMBYnMQ-testabo"


@pytest.fixture
def vapid(monkeypatch):
    monkeypatch.setattr(settings, "webpush_vapid_private_key", webpush.generate_private_key())


# ---------------------------------------------------------------------------
# Standardtreue
# ---------------------------------------------------------------------------

def test_verschluesselung_entspricht_dem_pruefvektor_aus_rfc_8291():
    """RFC 8291, Anhang A - Eingaben und erwartete Nachricht wortgleich."""
    ergebnis = webpush.encrypt(
        b"When I grow up, I want to be a watermelon",
        "BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4",
        "BTBZMqHH6r4Tts7J_aSIgg",
        _server_key=_key_from_b64("yfWPiYE-n46HLnH0KqZOF1fJJU3MYrct3AELtAQ-oRw"),
        _salt=_b64("DGv6ra1nlYgDCS1FRnbzlw"),
    )
    erwartet = _b64(
        "DGv6ra1nlYgDCS1FRnbzlwAAEABBBP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A_yl95bQpu6cVPTpK4Mqgkf1CXztLVBSt2Ks3oZwbuwXPXLWyouBWLVWGNWQexSgSxsj_Qulcy4a-fN"
    )
    assert ergebnis == erwartet


def test_vapid_token_ist_mit_dem_oeffentlichen_schluessel_pruefbar(vapid):
    key = webpush._private_key()
    kopf = webpush.vapid_authorization(_APPLE, key, jetzt=1_800_000_000)
    assert kopf.startswith("vapid t=")
    token, k = kopf[len("vapid t="):].split(", k=")
    assert k == webpush.public_key()

    kopfteil, inhalt, signatur = token.split(".")
    claims = json.loads(_b64(inhalt))
    # aud ist der Ursprung des Push-Dienstes, nicht der ganze Endpunkt.
    assert claims["aud"] == "https://web.push.apple.com"
    assert claims["exp"] == 1_800_000_000 + 12 * 3600
    assert claims["sub"].startswith("mailto:")

    roh = _b64(signatur)
    der = encode_dss_signature(int.from_bytes(roh[:32], "big"), int.from_bytes(roh[32:], "big"))
    oeffentlich = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), _b64(k))
    oeffentlich.verify(der, f"{kopfteil}.{inhalt}".encode(), ec.ECDSA(hashes.SHA256()))


@pytest.mark.parametrize("endpoint,erlaubt", [
    ("https://web.push.apple.com/abc", True),
    ("https://fcm.googleapis.com/fcm/send/abc", True),
    ("https://updates.push.services.mozilla.com/wpush/v2/abc", True),
    ("https://db5p.notify.windows.com/w/?token=abc", True),
    ("http://web.push.apple.com/abc", False),
    ("https://web.push.apple.com:8443/abc", False),
    ("https://web.push.apple.com.evil.example/abc", False),
    ("https://localhost/abc", False),
    ("https://169.254.169.254/latest/meta-data", False),
])
def test_nur_bekannte_push_dienste_sind_als_ziel_erlaubt(endpoint, erlaubt):
    assert webpush.endpoint_allowed(endpoint) is erlaubt


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def test_oeffentlicher_schluessel_ohne_einrichtung_ist_leer(client, monkeypatch):
    monkeypatch.setattr(settings, "webpush_vapid_private_key", "")
    assert client.get("/api/notifications/webpush-key").json() == {"public_key": None}


def test_oeffentlicher_schluessel_mit_einrichtung(client, vapid):
    schluessel = client.get("/api/notifications/webpush-key").json()["public_key"]
    assert len(_b64(schluessel)) == 65


def test_web_abo_anmelden_speichert_die_schluessel(client):
    headers = register_user(client, "webpush1@example.com")
    resp = client.post(
        "/api/notifications/token",
        json={"platform": "web", "token": _APPLE, "p256dh": _UA_PUBLIC, "auth": _AUTH},
        headers=headers,
    )
    assert resp.status_code == 200
    db = TestingSessionLocal()
    try:
        eintrag = db.query(PushToken).filter(PushToken.token == _APPLE).one()
        assert (eintrag.platform, eintrag.web_p256dh, eintrag.web_auth) == ("web", _UA_PUBLIC, _AUTH)
    finally:
        db.close()


@pytest.mark.parametrize("abo", [
    {"platform": "web", "token": _APPLE},                          # ohne Schluessel
    {"platform": "web", "token": "https://intern.example/hook",    # fremdes Ziel
     "p256dh": _UA_PUBLIC, "auth": _AUTH},
])
def test_unvollstaendige_oder_fremde_web_abos_werden_abgelehnt(client, abo):
    headers = register_user(client, "webpush2@example.com")
    assert client.post("/api/notifications/token", json=abo, headers=headers).status_code == 422


# ---------------------------------------------------------------------------
# Zustellung
# ---------------------------------------------------------------------------

class _Antwort:
    def __init__(self, status_code):
        self.status_code = status_code
        self.text = ""


def _web_abo(email):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).one()
    db.add(PushToken(user_id=user.id, platform="web", token=_APPLE, web_p256dh=_UA_PUBLIC, web_auth=_AUTH))
    db.commit()
    return db, user


def test_zustellung_verschluesselt_und_signiert(client, vapid, monkeypatch):
    register_user(client, "webpush3@example.com")
    db, user = _web_abo("webpush3@example.com")
    gesendet = []
    monkeypatch.setattr(
        webpush.requests, "post",
        lambda url, **kw: gesendet.append((url, kw)) or _Antwort(201),
    )
    try:
        assert push.send(db, user, "Lena", "Heute Beintag?", "chats") == 1
    finally:
        db.close()

    url, kw = gesendet[0]
    assert url == _APPLE
    assert kw["headers"]["Content-Encoding"] == "aes128gcm"
    assert kw["headers"]["Authorization"].startswith("vapid t=")
    assert kw["allow_redirects"] is False
    # Klartext darf nirgends im Koerper stehen.
    assert b"Beintag" not in kw["data"]


def test_abgelaufenes_abo_wird_aufgeraeumt(client, vapid, monkeypatch):
    register_user(client, "webpush4@example.com")
    db, user = _web_abo("webpush4@example.com")
    monkeypatch.setattr(webpush.requests, "post", lambda url, **kw: _Antwort(410))
    try:
        assert push.send(db, user, "Lena", "Hallo", "chats") == 0
        assert db.query(PushToken).filter(PushToken.token == _APPLE).count() == 0
    finally:
        db.close()


def test_ohne_vapid_schluessel_wird_nichts_geschickt(client, monkeypatch):
    monkeypatch.setattr(settings, "webpush_vapid_private_key", "")
    register_user(client, "webpush5@example.com")
    db, user = _web_abo("webpush5@example.com")
    monkeypatch.setattr(
        webpush.requests, "post",
        lambda *a, **kw: pytest.fail("ohne Schluessel darf nichts rausgehen"),
    )
    try:
        assert push.send(db, user, "Lena", "Hallo", "chats") == 0
    finally:
        db.close()


def test_abholfach_anlass_geht_auch_an_die_web_app(client, vapid, monkeypatch):
    """Ein neues Match muss die Web-App erreichen - sie kann nichts abholen."""
    register_user(client, "webpush6@example.com")
    db, user = _web_abo("webpush6@example.com")
    angestossen = []
    monkeypatch.setattr(push, "_send_web_async", lambda *args: angestossen.append(args))
    monkeypatch.setattr(push.threading, "Thread", _SofortThread)
    try:
        neu = notifications.queue_push(
            db, user, NotificationTopic.new_match, "Neues Match", "Lena mag dich auch",
            dedupe_key="test-match-1", target="matches",
        )
        assert neu is True
        assert angestossen == [(user.id, "Neues Match", "Lena mag dich auch", "matches")]
    finally:
        db.close()


class _SofortThread:
    """Ersetzt threading.Thread: fuehrt das Ziel sofort im Test aus."""

    def __init__(self, target, args, daemon):
        self._target, self._args = target, args

    def start(self):
        self._target(*self._args)
