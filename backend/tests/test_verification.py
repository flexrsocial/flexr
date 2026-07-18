from tests.conftest import TestingSessionLocal, create_admin, register_user
from app.routers import admin as admin_router


def _add_photo(client, headers):
    """Verifizierung setzt mindestens ein Profilfoto voraus."""
    presign = client.post(
        "/api/profiles/me/photos/presign", headers=headers, json={"content_type": "image/jpeg"}
    ).json()
    resp = client.post(
        "/api/profiles/me/photos", headers=headers, json={"object_key": presign["object_key"]}
    )
    assert resp.status_code == 200


def _start_and_submit(client, headers):
    start = client.post("/api/verification/start", headers=headers)
    assert start.status_code == 200, start.text
    prompts = start.json()["prompts"]
    assert len(prompts) == 3

    me = client.get("/api/profiles/me", headers=headers).json()
    selfies = [
        {"prompt": p, "object_key": f"users/{me['id']}/verify/selfie{i}.jpg"}
        for i, p in enumerate(prompts)
    ]
    submit = client.post("/api/verification/submit", headers=headers, json={"selfies": selfies})
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == "submitted"
    return prompts


def test_verification_requires_photo(client):
    headers = register_user(client, "nophoto@example.com")
    resp = client.post("/api/verification/start", headers=headers)
    assert resp.status_code == 400


def test_full_verification_flow_approve(client, monkeypatch):
    deleted_keys = []
    monkeypatch.setattr(admin_router.storage, "delete_object", lambda k: deleted_keys.append(k))

    headers = register_user(client, "verify@example.com")
    _add_photo(client, headers)
    _start_and_submit(client, headers)

    status = client.get("/api/verification/status", headers=headers).json()
    assert status["status"] == "submitted"

    admin_headers, _ = create_admin(client)
    pending = client.get("/api/admin/verifications", headers=admin_headers).json()
    assert len(pending) == 1
    assert len(pending[0]["selfie_urls"]) == 3
    assert len(pending[0]["profile_photo_urls"]) == 1

    resp = client.post(
        f"/api/admin/verifications/{pending[0]['id']}/approve", headers=admin_headers
    )
    assert resp.status_code == 200

    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["is_verified"] is True
    assert client.get("/api/verification/status", headers=headers).json()["status"] == "approved"
    assert len(deleted_keys) == 3  # Selfies nach der Entscheidung gelöscht


def test_verification_reject_allows_restart(client, monkeypatch):
    monkeypatch.setattr(admin_router.storage, "delete_object", lambda k: None)

    headers = register_user(client, "rejected@example.com")
    _add_photo(client, headers)
    _start_and_submit(client, headers)

    admin_headers, _ = create_admin(client, email="admin2@example.com")
    pending = client.get("/api/admin/verifications", headers=admin_headers).json()
    client.post(f"/api/admin/verifications/{pending[0]['id']}/reject", headers=admin_headers)

    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["is_verified"] is False
    assert client.get("/api/verification/status", headers=headers).json()["status"] == "rejected"

    # Nach Ablehnung darf neu gestartet werden
    resp = client.post("/api/verification/start", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_submit_with_wrong_prompts_rejected(client):
    headers = register_user(client, "wrongpose@example.com")
    _add_photo(client, headers)
    start = client.post("/api/verification/start", headers=headers)
    me = client.get("/api/profiles/me", headers=headers).json()

    selfies = [
        {"prompt": f"Erfundene Pose {i}", "object_key": f"users/{me['id']}/verify/s{i}.jpg"}
        for i in range(3)
    ]
    resp = client.post("/api/verification/submit", headers=headers, json={"selfies": selfies})
    assert resp.status_code == 400


def test_submit_with_foreign_object_key_rejected(client):
    headers = register_user(client, "foreignkey@example.com")
    _add_photo(client, headers)
    prompts = client.post("/api/verification/start", headers=headers).json()["prompts"]

    selfies = [
        {"prompt": p, "object_key": f"users/andere-user-id/verify/s{i}.jpg"}
        for i, p in enumerate(prompts)
    ]
    resp = client.post("/api/verification/submit", headers=headers, json={"selfies": selfies})
    assert resp.status_code == 400


def test_cannot_start_while_submitted(client):
    headers = register_user(client, "double@example.com")
    _add_photo(client, headers)
    _start_and_submit(client, headers)
    resp = client.post("/api/verification/start", headers=headers)
    assert resp.status_code == 400


def test_start_is_idempotent_while_in_progress(client):
    headers = register_user(client, "idem@example.com")
    _add_photo(client, headers)
    first = client.post("/api/verification/start", headers=headers).json()
    second = client.post("/api/verification/start", headers=headers).json()
    assert first["prompts"] == second["prompts"]


def test_verified_badge_visible_in_deck(client, monkeypatch):
    monkeypatch.setattr(admin_router.storage, "delete_object", lambda k: None)

    headers_a = register_user(client, "badge.m@example.com", gender="mann")
    headers_b = register_user(client, "badge.f@example.com", name="Verifizierte", gender="frau")
    _add_photo(client, headers_b)
    _start_and_submit(client, headers_b)

    admin_headers, _ = create_admin(client, email="admin3@example.com")
    pending = client.get("/api/admin/verifications", headers=admin_headers).json()
    client.post(f"/api/admin/verifications/{pending[0]['id']}/approve", headers=admin_headers)

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    verified = next(p for p in deck if p["name"] == "Verifizierte")
    assert verified["is_verified"] is True
