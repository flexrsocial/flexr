from tests.conftest import TestingSessionLocal, create_admin, register_user
from tests.test_swipes_and_matches import make_pair


def _make_match(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": user_b["id"], "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": user_a["id"], "action": "like"})
    match_id = client.get("/api/matches", headers=headers_a).json()[0]["match_id"]
    return match_id, headers_a, headers_b


# ---------- Verworfene Telefonprüfung ----------

def test_phone_verification_is_not_exposed(client):
    assert client.post("/api/phone/request", json={"phone": "+436761234567"}).status_code == 404
    assert client.post("/api/phone/confirm", json={"code": "123456"}).status_code == 404


# ---------- Geräteprüfung ----------

def test_device_recorded_on_register(client):
    payload_headers = {"X-Device-Id": "test-device-registration-1"}
    from tests.conftest import DEFAULT_USER

    resp = client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "device@example.com", "name": "Device User"},
        headers=payload_headers,
    )
    assert resp.status_code == 200

    from app.models import User, UserDevice

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "device@example.com").first()
        device = db.query(UserDevice).filter(UserDevice.user_id == user.id).first()
        assert device is not None
        assert device.device_id == "test-device-registration-1"
    finally:
        db.close()


def test_banned_device_blocks_new_registration(client):
    from tests.conftest import DEFAULT_USER

    device = {"X-Device-Id": "banned-device-42"}
    resp = client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "tobebanned@example.com", "name": "Bald Gesperrt"},
        headers=device,
    )
    assert resp.status_code == 200

    # Nutzer sperren
    from app.models import User

    db = TestingSessionLocal()
    try:
        u = db.query(User).filter(User.email == "tobebanned@example.com").first()
        u.is_banned = True
        db.commit()
    finally:
        db.close()

    # Neuregistrierung vom selben Gerät wird blockiert
    resp = client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "evasion@example.com", "name": "Zweitkonto"},
        headers=device,
    )
    assert resp.status_code == 403

    # Anderes Gerät funktioniert weiterhin
    resp = client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "cleandevice@example.com", "name": "Sauber"},
        headers={"X-Device-Id": "clean-device-77"},
    )
    assert resp.status_code == 200


def test_admin_sees_devices_and_shared_accounts(client):
    from tests.conftest import DEFAULT_USER

    device = {"X-Device-Id": "shared-device-99"}
    client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "share1@example.com", "name": "Konto Eins"},
        headers=device,
    )
    client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "share2@example.com", "name": "Konto Zwei"},
        headers=device,
    )

    from app.models import User

    db = TestingSessionLocal()
    try:
        uid = db.query(User).filter(User.email == "share1@example.com").first().id
    finally:
        db.close()

    admin_headers, _ = create_admin(client)
    detail = client.get(f"/api/admin/users/{uid}", headers=admin_headers).json()
    assert len(detail["devices"]) == 1
    assert detail["devices"][0]["device_id"] == "shared-device-99"
    assert "Konto Zwei" in detail["devices"][0]["shared_with"]


# ---------- Automatische Inhalts-Sicherheitsprüfung ----------

def test_disposable_email_rejected(client):
    from tests.conftest import DEFAULT_USER

    resp = client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "spam@mailinator.com", "name": "Spam"},
    )
    assert resp.status_code == 400


def test_bio_with_url_rejected_at_registration(client):
    from tests.conftest import DEFAULT_USER

    resp = client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "biourl@example.com", "name": "Bio Url",
              "bio": "Folgt mir auf https://scam.example.com"},
    )
    assert resp.status_code == 400


def test_bio_with_phone_rejected_at_update(client):
    headers = register_user(client, "biophone@example.com")
    resp = client.patch("/api/profiles/me", headers=headers, json={"bio": "Ruf mich an: +43 676 1234567"})
    assert resp.status_code == 400


def test_normal_bio_accepted(client):
    headers = register_user(client, "bionormal@example.com")
    resp = client.patch(
        "/api/profiles/me", headers=headers,
        json={"bio": "Trainiere 4x die Woche 💪 Suche jemanden für Beintag und Brunch."},
    )
    assert resp.status_code == 200


def test_scam_message_gets_flagged_but_delivered(client):
    match_id, headers_a, headers_b = _make_match(client)
    resp = client.post(
        f"/api/matches/{match_id}/messages", headers=headers_a,
        json={"content": "Schick mir Geld per Western Union, dann besuch ich dich."},
    )
    assert resp.status_code == 201  # zugestellt, nicht blockiert

    msgs = client.get(f"/api/matches/{match_id}/messages", headers=headers_b).json()
    assert len(msgs) == 1  # Empfang bestätigt

    admin_headers, _ = create_admin(client)
    flagged = client.get("/api/admin/flagged-messages", headers=admin_headers).json()
    assert len(flagged) == 1
    assert "western union" in flagged[0]["flag_reason"].lower()

    # Flag durch Admin auflösen
    resp = client.post(
        f"/api/admin/flagged-messages/{flagged[0]['id']}/clear", headers=admin_headers
    )
    assert resp.status_code == 200
    assert client.get("/api/admin/flagged-messages", headers=admin_headers).json() == []


def test_normal_message_not_flagged(client):
    match_id, headers_a, _ = _make_match(client)
    client.post(
        f"/api/matches/{match_id}/messages", headers=headers_a,
        json={"content": "Hey! Wann bist du wieder im Gym? Meine Nummer: +43 676 999"},
    )
    admin_headers, _ = create_admin(client, email="adminmsg@example.com")
    assert client.get("/api/admin/flagged-messages", headers=admin_headers).json() == []
