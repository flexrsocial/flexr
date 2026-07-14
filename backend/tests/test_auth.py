from tests.conftest import register_user


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_and_login(client):
    headers = register_user(client, "alice@example.com")
    me = client.get("/api/profiles/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["name"] == "Test User"

    login = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "supersecret123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_register_duplicate_email(client):
    register_user(client, "bob@example.com")
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "bob@example.com",
            "password": "supersecret123",
            "name": "Bob Zwei",
            "age": 30,
            "city": "Wien",
            "gender": "mann",
            "interest": "frau",
            "gym": "McFit",
        },
    )
    assert resp.status_code == 409


def test_register_rejects_unsupported_city(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "carol@example.com",
            "password": "supersecret123",
            "name": "Carol",
            "age": 25,
            "city": "Berlin",
            "gender": "frau",
            "interest": "mann",
            "gym": "McFit",
        },
    )
    assert resp.status_code == 400


def test_login_wrong_password(client):
    register_user(client, "dave@example.com")
    resp = client.post(
        "/api/auth/login",
        json={"email": "dave@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 401


def test_protected_endpoint_requires_token(client):
    resp = client.get("/api/profiles/me")
    assert resp.status_code == 401
