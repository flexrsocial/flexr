from datetime import datetime, timedelta

from tests.conftest import TestingSessionLocal, register_user
from tests.test_swipes_and_matches import make_pair
from app import mailer
from app.cleanup import purge_deleted_users
from app.models import User
from app.routers import profiles as profiles_router


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
    detail = login.json()["detail"]
    assert detail["code"] == "account_deleted"
    assert "gelöscht" in detail["message"]
    assert "reactivate_until" in detail


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


def test_delete_sends_confirmation_mail(client, monkeypatch):
    verschickt = []
    monkeypatch.setattr(
        profiles_router.mailer,
        "send_account_deletion_confirmation",
        lambda email, name, purge_at, grace_days: verschickt.append(
            (email, name, purge_at, grace_days)
        )
        or True,
    )

    headers = register_user(client, "del.mail@example.com", name="Mail Test")
    resp = client.request(
        "DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"}
    )
    assert resp.status_code == 200

    assert len(verschickt) == 1
    email, name, purge_at, grace_days = verschickt[0]
    assert email == "del.mail@example.com"
    assert name == "Mail Test"
    assert grace_days == 30
    # purge_at liegt ~30 Tage nach der Loeschung
    assert timedelta(days=29) < (purge_at - datetime.utcnow()) < timedelta(days=31)


def test_reactivate_restores_login(client):
    headers = register_user(client, "del.reactivate@example.com")
    client.request("DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"})

    # Waehrend der Karenz: einfacher Login bleibt gesperrt
    login = client.post(
        "/api/auth/login",
        json={"email": "del.reactivate@example.com", "password": "supersecret123"},
    )
    assert login.status_code == 403
    assert login.json()["detail"]["code"] == "account_deleted"

    reactivate = client.post(
        "/api/auth/reactivate",
        json={"email": "del.reactivate@example.com", "password": "supersecret123"},
    )
    assert reactivate.status_code == 200
    new_token = reactivate.json()["access_token"]

    # Konto wieder erreichbar
    me = client.get("/api/profiles/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me.status_code == 200

    # Und ein normaler Login funktioniert jetzt wieder
    login_again = client.post(
        "/api/auth/login",
        json={"email": "del.reactivate@example.com", "password": "supersecret123"},
    )
    assert login_again.status_code == 200

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "del.reactivate@example.com").first()
        assert user.deleted_at is None
    finally:
        db.close()


def test_reactivate_requires_correct_password(client):
    headers = register_user(client, "del.reactivate.wrongpw@example.com")
    client.request("DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"})

    resp = client.post(
        "/api/auth/reactivate",
        json={"email": "del.reactivate.wrongpw@example.com", "password": "falsches-passwort"},
    )
    assert resp.status_code == 401

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "del.reactivate.wrongpw@example.com").first()
        assert user.deleted_at is not None
    finally:
        db.close()


def test_reactivate_rejects_account_that_was_never_deleted(client):
    register_user(client, "del.reactivate.active@example.com")

    resp = client.post(
        "/api/auth/reactivate",
        json={"email": "del.reactivate.active@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 400


def test_reactivate_fails_after_grace_period(client):
    headers = register_user(client, "del.reactivate.expired@example.com")
    client.request("DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"})

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "del.reactivate.expired@example.com").first()
        user.deleted_at = datetime.utcnow() - timedelta(days=31)
        db.commit()
    finally:
        db.close()

    # reactivate() raeumt die abgelaufene Karenz zuerst opportunistisch weg
    # (wie login()) - das Konto existiert danach schlicht nicht mehr.
    resp = client.post(
        "/api/auth/reactivate",
        json={"email": "del.reactivate.expired@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 401

    db = TestingSessionLocal()
    try:
        assert (
            db.query(User).filter(User.email == "del.reactivate.expired@example.com").first()
            is None
        )
    finally:
        db.close()
