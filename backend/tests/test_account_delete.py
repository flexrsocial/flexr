from datetime import datetime, timedelta

from tests.conftest import TestingSessionLocal, register_user
from tests.test_swipes_and_matches import make_pair
from app.cleanup import purge_deleted_users
from app.models import User


def test_delete_requires_correct_password(client):
    headers = register_user(client, "del.wrongpw@example.com")
    resp = client.request(
        "DELETE", "/api/profiles/me", headers=headers, json={"password": "falsches-passwort"}
    )
    assert resp.status_code == 400
    # Konto ist weiterhin aktiv
    assert client.get("/api/profiles/me", headers=headers).status_code == 200


def test_delete_deactivates_account(client):
    headers = register_user(client, "del.ok@example.com")
    resp = client.request(
        "DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"}
    )
    assert resp.status_code == 200
    assert resp.json()["purge_after_days"] == 30

    # Token sofort unbrauchbar
    assert client.get("/api/profiles/me", headers=headers).status_code == 403

    # Login gesperrt
    login = client.post(
        "/api/auth/login",
        json={"email": "del.ok@example.com", "password": "supersecret123"},
    )
    assert login.status_code == 403
    assert "gelöscht" in login.json()["detail"]


def test_deleted_user_hidden_from_deck_and_matches(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    # Match herstellen
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": user_b["id"], "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": user_a["id"], "action": "like"})
    assert len(client.get("/api/matches", headers=headers_a).json()) == 1

    # B löscht sein Konto
    client.request("DELETE", "/api/profiles/me", headers=headers_b, json={"password": "supersecret123"})

    # B verschwindet aus A-Sicht: Matches leer, Deck ohne B
    assert client.get("/api/matches", headers=headers_a).json() == []
    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    assert not any(p["id"] == user_b["id"] for p in deck)


def test_purge_removes_expired_accounts_only(client):
    headers = register_user(client, "del.purge@example.com")
    client.request("DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"})

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "del.purge@example.com").first()
        assert user.deleted_at is not None

        # Innerhalb der Karenz: Purge löscht nichts
        assert purge_deleted_users(db) == 0

        # Karenz abgelaufen: Purge entfernt das Konto endgültig
        user.deleted_at = datetime.utcnow() - timedelta(days=31)
        db.commit()
        assert purge_deleted_users(db) == 1
        assert db.query(User).filter(User.email == "del.purge@example.com").first() is None
    finally:
        db.close()


def test_login_triggers_purge(client):
    headers = register_user(client, "del.trigger@example.com")
    client.request("DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"})

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "del.trigger@example.com").first()
        user.deleted_at = datetime.utcnow() - timedelta(days=31)
        db.commit()
    finally:
        db.close()

    # Irgendein Login stößt den Purge an
    register_user(client, "del.other@example.com")
    client.post(
        "/api/auth/login",
        json={"email": "del.other@example.com", "password": "supersecret123"},
    )

    db = TestingSessionLocal()
    try:
        assert db.query(User).filter(User.email == "del.trigger@example.com").first() is None
    finally:
        db.close()
