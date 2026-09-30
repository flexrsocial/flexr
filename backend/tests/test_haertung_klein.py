"""Kleine Haertungen aus dem Audit vom 30.09.2026."""

from app.models import PushToken
from tests.conftest import DEFAULT_USER, TestingSessionLocal, register_user


def test_fremden_push_token_nicht_abmelden(client):
    opfer = register_user(client, "push-opfer@example.com")
    angreifer = register_user(client, "push-angreifer@example.com")
    client.post("/api/notifications/token", headers=opfer,
                json={"platform": "android", "token": "opfer-token-123"})
    client.request("DELETE", "/api/notifications/token", headers=angreifer,
                   json={"platform": "android", "token": "opfer-token-123"})
    db = TestingSessionLocal()
    try:
        assert db.query(PushToken).filter(PushToken.token == "opfer-token-123").count() == 1
    finally:
        db.close()


def test_gym_vorschlag_mit_platzhalter_trifft_kein_fremdes_gym(client):
    erstes = client.post("/api/gyms/suggest", json={
        "name": "Echtes Gym", "street": "Weg", "house_number": "1", "plz": "4020"}).json()
    zweites = client.post("/api/gyms/suggest", json={
        "name": "%%", "street": "Weg", "house_number": "2", "plz": "4020"})
    assert zweites.status_code == 201
    assert zweites.json()["id"] != erstes["id"]


def test_gym_vorschlag_gross_klein_bleibt_duplikat(client):
    erstes = client.post("/api/gyms/suggest", json={
        "name": "Kraftwerk", "street": "Weg", "house_number": "1", "plz": "4020"}).json()
    zweites = client.post("/api/gyms/suggest", json={
        "name": "KRAFTWERK", "street": "Weg", "house_number": "1", "plz": "4020"}).json()
    assert zweites["id"] == erstes["id"]


def test_ort_hat_laengengrenze(client):
    resp = client.post("/api/auth/register", json={
        **DEFAULT_USER, "email": "langort@example.com", "city": "x" * 5000})
    assert resp.status_code == 422


def test_kontoloeschung_ist_gedrosselt(client):
    from app.rate_limit import limiter

    headers = register_user(client, "drossel@example.com")
    limiter.enabled = True
    try:
        codes = [
            client.request("DELETE", "/api/profiles/me", headers=headers,
                           json={"password": "falsch-falsch"}).status_code
            for _ in range(12)
        ]
    finally:
        limiter.enabled = False
    assert codes[0] == 400
    assert 429 in codes
