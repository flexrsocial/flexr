"""Am Handy weitermachen: Einmal-Link per QR-Code (geraetewechsel.py).

Der Link meldet ein Geraet ohne Passwort an - deshalb hier die Grenzen:
einmal einloesbar, kurz gueltig, nur als Hash gespeichert, nur fuer Konten
in der Pruefung, ein neuer Code entwertet den alten.
"""

from datetime import timedelta

from app import geraetewechsel
from app.models import DeviceHandoff
from app.timeutil import utcnow
from tests.conftest import TestingSessionLocal, register_raw, register_user


def _ausstellen(client, headers):
    resp = client.post("/api/verification/handoff", headers=headers)
    assert resp.status_code == 200, resp.text
    daten = resp.json()
    return daten, daten["link"].split("#weiter=", 1)[1]


def _einloesen(client, token):
    return client.post("/api/auth/handoff", json={"token": token})


def test_code_meldet_das_handy_an(client):
    headers = register_raw(client, "qr.handy@example.com")
    daten, token = _ausstellen(client, headers)

    assert "/app/#weiter=" in daten["link"]
    assert daten["qr"].startswith("data:image/svg+xml;base64,")
    assert daten["ttl_minutes"] == geraetewechsel.TOKEN_TTL_MINUTES

    resp = _einloesen(client, token)
    assert resp.status_code == 200
    handy = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    ich = client.get("/api/profiles/me", headers=headers).json()["id"]
    assert client.get("/api/profiles/me", headers=handy).json()["id"] == ich


def test_code_gilt_nur_einmal(client):
    headers = register_raw(client, "qr.einmal@example.com")
    _, token = _ausstellen(client, headers)
    assert _einloesen(client, token).status_code == 200

    zweites = _einloesen(client, token)
    assert zweites.status_code == 400
    assert "abgelaufen oder wurde schon benutzt" in zweites.json()["detail"]


def test_abgelaufener_code(client):
    headers = register_raw(client, "qr.alt@example.com")
    _, token = _ausstellen(client, headers)
    db = TestingSessionLocal()
    try:
        eintrag = db.query(DeviceHandoff).one()
        eintrag.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()
    assert _einloesen(client, token).status_code == 400


def test_neuer_code_entwertet_den_alten(client):
    headers = register_raw(client, "qr.neu@example.com")
    _, alt = _ausstellen(client, headers)
    _, neu = _ausstellen(client, headers)
    assert _einloesen(client, alt).status_code == 400
    assert _einloesen(client, neu).status_code == 200


def test_nur_der_hash_wird_gespeichert(client):
    headers = register_raw(client, "qr.hash@example.com")
    _, token = _ausstellen(client, headers)
    db = TestingSessionLocal()
    try:
        gespeichert = db.query(DeviceHandoff).one().token_hash
    finally:
        db.close()
    assert token not in gespeichert and len(gespeichert) == 64


def test_freigeschaltetes_konto_bekommt_keinen_code(client):
    headers = register_user(client, "qr.frei@example.com")
    resp = client.post("/api/verification/handoff", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Dein Konto ist bereits freigeschaltet."


def test_freischaltung_zwischendurch_sperrt_den_code(client):
    """Wurde das Konto freigeschaltet, bevor der Code eingeloest ist, oeffnet
    er nichts mehr - ab da gilt der normale Login."""
    headers = register_raw(client, "qr.dazwischen@example.com")
    _, token = _ausstellen(client, headers)
    from tests.conftest import activate_user

    activate_user(client, headers)
    assert _einloesen(client, token).status_code == 400


def test_englische_fehlermeldung(client):
    resp = client.post(
        "/api/auth/handoff", json={"token": "x" * 43}, headers={"Accept-Language": "en"}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"].startswith("This code has expired")
