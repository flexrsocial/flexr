"""Zugriffsschutz rund um die Alters- und Identitätsprüfung.

Kernaussagen: Ein Nutzer kann sein eigenes Prüfergebnis nicht setzen, keine
fremden Ausweisaufnahmen erreichen, und Admin-Endpunkte sind ohne
Admin-Anmeldung dicht.
"""

import pytest

from app import storage as app_storage
from tests.conftest import TestingSessionLocal, create_admin, register_raw, register_user
from tests.test_verification import (
    FULL_CHECKLIST,
    _add_photo,
    _complete_submission,
    _submit_selfies,
)


@pytest.fixture
def storage_stub(monkeypatch):
    deleted: list[str] = []
    monkeypatch.setattr(
        app_storage, "delete_objects_verified", lambda keys: deleted.extend(keys) or []
    )
    monkeypatch.setattr(
        app_storage,
        "inspect_uploaded_image",
        lambda key: {"ok": True, "size": 1234, "detected": "image/jpeg"},
    )
    return deleted


ADMIN_ROUTES = [
    ("GET", "/api/admin/verifications", None),
    ("POST", "/api/admin/verifications/irgendwas/approve", FULL_CHECKLIST),
    ("POST", "/api/admin/verifications/irgendwas/reject", {"reason_code": "other"}),
    ("POST", "/api/admin/verifications/irgendwas/request-reupload", {"reason_code": "other"}),
    ("POST", "/api/admin/users/irgendwer/require-verification", None),
]


@pytest.mark.parametrize("method,path,body", ADMIN_ROUTES)
def test_admin_routes_reject_anonymous(client, method, path, body):
    resp = client.request(method, path, json=body)
    assert resp.status_code == 401


@pytest.mark.parametrize("method,path,body", ADMIN_ROUTES)
def test_admin_routes_reject_normal_user_token(client, method, path, body):
    """Ein normales Nutzer-Token ist kein Admin-Token - der Scope wird geprüft."""
    headers = register_user(client, "kein.admin@example.com")
    resp = client.request(method, path, headers=headers, json=body)
    assert resp.status_code == 401


def test_user_cannot_set_own_verification_result(client, storage_stub):
    """Weder über das Profil noch über die Registrierung lassen sich
    age_verified, is_verified oder die Freischaltung setzen (Mass Assignment)."""
    headers = register_raw(client, "selbstfreigabe@example.com")

    resp = client.patch(
        "/api/profiles/me",
        headers=headers,
        json={
            "age_verified": True,
            "is_verified": True,
            "verification_required": False,
            "activated_at": "2020-01-01T00:00:00",
            "trial_ends_at": "2099-01-01T00:00:00",
        },
    )
    # Unbekannte Felder werden ignoriert, nicht übernommen
    assert resp.status_code == 200
    me = resp.json()
    assert me["age_verified"] is False
    assert me["is_verified"] is False
    assert me["is_account_activated"] is False
    assert client.get("/api/swipes/deck", headers=headers).status_code == 403


def test_register_ignores_client_supplied_verification_fields(client):
    from tests.conftest import DEFAULT_USER

    payload = {
        **DEFAULT_USER,
        "email": "schummel@example.com",
        "name": "Schummel",
        "age_verified": True,
        "verification_required": False,
        "is_verified": True,
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["age_verified"] is False
    assert me["is_account_activated"] is False


def test_user_cannot_submit_document_for_foreign_request(client, storage_stub):
    """Der Objektschlüssel muss aus einer Presign-Anfrage des eigenen Vorgangs
    stammen - ein fremder Vorgangs-Prefix wird abgelehnt."""
    headers_a = register_raw(client, "opfer@example.com")
    _add_photo(client, headers_a)
    _complete_submission(client, headers_a)

    from app.models import VerificationRequest

    db = TestingSessionLocal()
    try:
        foreign_req_id = db.query(VerificationRequest).first().id
    finally:
        db.close()

    headers_b = register_raw(client, "angreifer@example.com", gender="frau")
    _add_photo(client, headers_b)
    _submit_selfies(client, headers_b)

    resp = client.post(
        "/api/verification/document/submit",
        headers=headers_b,
        json={
            "document_type": "passport",
            "front_object_key": f"verification-documents/{foreign_req_id}/geklaut.jpg",
        },
    )
    assert resp.status_code == 400


def test_documents_never_get_a_public_url(client, storage_stub):
    """Ausweisaufnahmen liegen außerhalb des öffentlichen Foto-Prefix und
    bekommen im Admin-Tool nur eine kurzlebige Signed URL."""
    headers = register_raw(client, "privat@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.privat@example.com")
    entry = client.get("/api/admin/verifications", headers=admin_headers).json()[0]

    from app.config import settings

    for doc in entry["document_urls"]:
        assert not doc["url"].startswith(settings.s3_public_base_url)
        # Signierte URL: enthält Ablaufzeit und Signatur
        assert "X-Amz-Signature" in doc["url"]
        assert "X-Amz-Expires" in doc["url"]
    for selfie in entry["selfie_urls"]:
        assert "X-Amz-Signature" in selfie["url"]


def test_verification_endpoints_require_authentication(client):
    for method, path, body in [
        ("GET", "/api/verification/status", None),
        ("POST", "/api/verification/start", None),
        ("POST", "/api/verification/document/presign", {"content_type": "image/jpeg", "byte_size": 1}),
        (
            "POST",
            "/api/verification/document/submit",
            {"document_type": "passport", "front_object_key": "x"},
        ),
    ]:
        resp = client.request(method, path, json=body)
        assert resp.status_code == 401, path


def test_document_presign_requires_selfie_step_first(client):
    """Ohne abgeschlossenen Selfie-Schritt gibt es keine Upload-URL - so
    entstehen keine Ausweisaufnahmen ohne zugehörigen Vorgang."""
    headers = register_raw(client, "reihenfolge@example.com")
    _add_photo(client, headers)
    resp = client.post(
        "/api/verification/document/presign",
        headers=headers,
        json={"content_type": "image/jpeg", "byte_size": 1000},
    )
    assert resp.status_code == 400
