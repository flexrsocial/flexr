"""Alters- und Identitätsprüfung: Selfies + amtlicher Lichtbildausweis,
entschieden von einem Menschen.

Der Objekt-Storage existiert im Test nicht - Upload-Prüfung und Löschung werden
deshalb über app.storage gepatcht. Gegen echte Bilder wird nie getestet.
"""

import pytest

from app import storage as app_storage
from tests.conftest import (
    TestingSessionLocal,
    add_approved_photo,
    create_admin,
    register_raw,
    register_user,
)

FULL_CHECKLIST = {
    "selfie_matches_profile_photos": True,
    "selfie_matches_document": True,
    "document_shows_min_age": True,
    "document_dob_matches_registration": True,
    "document_legible": True,
    "document_plausible": True,
}


@pytest.fixture
def storage_stub(monkeypatch):
    """Ersetzt die Storage-Zugriffe und protokolliert, was gelöscht wurde."""
    deleted: list[str] = []

    def fake_delete(keys):
        deleted.extend(keys)
        return []  # nichts blieb übrig = Löschung bestätigt

    monkeypatch.setattr(app_storage, "delete_objects_verified", fake_delete)
    monkeypatch.setattr(
        app_storage,
        "inspect_uploaded_image",
        lambda key: {"ok": True, "size": 1234, "detected": "image/jpeg"},
    )
    return deleted


def _add_photo(client, headers):
    """Verifizierung setzt mindestens ein Profilfoto voraus."""
    presign = client.post(
        "/api/profiles/me/photos/presign", headers=headers, json={"content_type": "image/jpeg"}
    ).json()
    resp = client.post(
        "/api/profiles/me/photos", headers=headers, json={"object_key": presign["object_key"]}
    )
    assert resp.status_code == 200


def _submit_selfies(client, headers):
    start = client.post("/api/verification/start", headers=headers)
    assert start.status_code == 200, start.text
    prompts = start.json()["prompts"]
    assert len(prompts) == 1

    me = client.get("/api/profiles/me", headers=headers).json()
    selfies = [
        {"prompt": p, "object_key": f"users/{me['id']}/verify/selfie{i}.jpg"}
        for i, p in enumerate(prompts)
    ]
    submit = client.post("/api/verification/submit", headers=headers, json={"selfies": selfies})
    assert submit.status_code == 200, submit.text
    # Nach den Selfies fehlt noch der Ausweis - erst danach geht es in die Prüfung.
    assert submit.json()["status"] == "id_required"
    assert submit.json()["next_step"] == "document"
    return prompts


def _submit_document(client, headers, document_type="passport", back=False):
    presign = client.post(
        "/api/verification/document/presign",
        headers=headers,
        json={"content_type": "image/jpeg", "byte_size": 500_000},
    )
    assert presign.status_code == 200, presign.text
    front_key = presign.json()["object_key"]
    assert front_key.startswith("verification-documents/")

    body = {"document_type": document_type, "front_object_key": front_key}
    if back:
        back_key = client.post(
            "/api/verification/document/presign",
            headers=headers,
            json={"content_type": "image/jpeg", "byte_size": 500_000},
        ).json()["object_key"]
        body["back_object_key"] = back_key

    resp = client.post("/api/verification/document/submit", headers=headers, json=body)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "submitted"
    return body


def _complete_submission(client, headers, **kwargs):
    _submit_selfies(client, headers)
    return _submit_document(client, headers, **kwargs)


# ---------- Ablauf ----------


def test_verification_requires_photo(client):
    headers = register_raw(client, "nophoto@example.com")
    resp = client.post("/api/verification/start", headers=headers)
    assert resp.status_code == 400


def test_new_account_is_not_activated_before_review(client, storage_stub):
    headers = register_raw(client, "gated@example.com")
    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["verification_required"] is True
    assert me["is_account_activated"] is False
    assert me["age_verified"] is False

    # Dating-Funktionen sind gesperrt, das Profil bleibt erreichbar
    for path in ("/api/swipes/deck", "/api/matches"):
        resp = client.get(path, headers=headers)
        assert resp.status_code == 403, path
        assert resp.json()["detail"]["code"] == "verification_required"


def test_full_flow_pending_to_approved(client, storage_stub):
    headers = register_raw(client, "verify@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    status = client.get("/api/verification/status", headers=headers).json()
    assert status["status"] == "submitted"
    assert status["next_step"] == "wait"

    admin_headers, admin_id = create_admin(client)
    pending = client.get("/api/admin/verifications", headers=admin_headers).json()
    assert len(pending) == 1
    entry = pending[0]
    # Konsolidierte Prüfansicht: Accountdaten, Selfies, Profilfotos, Ausweis
    assert entry["user_birthdate"] == "1997-06-15"
    assert entry["user_age"] >= 18
    assert len(entry["selfie_urls"]) == 1
    assert len(entry["profile_photo_urls"]) == 1
    assert entry["document_type"] == "passport"
    assert [d["side"] for d in entry["document_urls"]] == ["front"]

    resp = client.post(
        f"/api/admin/verifications/{entry['id']}/approve",
        headers=admin_headers,
        json=FULL_CHECKLIST,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["documents_deleted"] is True
    assert resp.json()["cleanup_pending"] is False

    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["is_verified"] is True
    assert me["age_verified"] is True
    assert me["is_account_activated"] is True
    assert client.get("/api/verification/status", headers=headers).json()["status"] == "approved"

    # Konto ist freigeschaltet: Deck ist wieder erreichbar
    assert client.get("/api/swipes/deck", headers=headers).status_code == 200

    # Selfie + Ausweisaufnahme wurden gelöscht
    assert len(storage_stub) == 2

    from app.models import User, VerificationRequest

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == entry["user_id"]).first()
        assert user.verification_method == "manual_id"
        assert user.age_verified_at is not None
        req = db.query(VerificationRequest).filter(VerificationRequest.id == entry["id"]).first()
        # Keine Verweise auf Bilder mehr, dafür die Prüf-Metadaten
        assert req.selfies is None
        assert req.documents is None
        assert req.reviewed_by == admin_id
        assert req.cleanup_pending is False
    finally:
        db.close()


def test_id_card_requires_back_side(client, storage_stub):
    headers = register_raw(client, "idcard@example.com")
    _add_photo(client, headers)
    _submit_selfies(client, headers)

    front_key = client.post(
        "/api/verification/document/presign",
        headers=headers,
        json={"content_type": "image/jpeg", "byte_size": 1000},
    ).json()["object_key"]
    resp = client.post(
        "/api/verification/document/submit",
        headers=headers,
        json={"document_type": "id_card", "front_object_key": front_key},
    )
    assert resp.status_code == 400
    assert "Rückseite" in resp.json()["detail"]

    # Mit Rückseite geht es durch
    _submit_document(client, headers, document_type="id_card", back=True)


def test_reupload_flow(client, storage_stub):
    headers = register_raw(client, "reupload@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.reupload@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]
    resp = client.post(
        f"/api/admin/verifications/{req_id}/request-reupload",
        headers=admin_headers,
        json={"reason_code": "document_unreadable", "redo_selfie": False},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "reupload_required"
    # Nur die Ausweisaufnahme wurde ersetzt, das Selfie bleibt gültig
    assert len(storage_stub) == 1

    status = client.get("/api/verification/status", headers=headers).json()
    assert status["status"] == "reupload_required"
    assert status["next_step"] == "document"
    assert "lesbar" in status["reason"]

    # Konto weiterhin gesperrt
    assert client.get("/api/swipes/deck", headers=headers).status_code == 403

    # Neuer Ausweis-Upload bringt den Vorgang zurück in die Prüfung
    _submit_document(client, headers)
    assert client.get("/api/verification/status", headers=headers).json()["status"] == "submitted"


def test_reupload_with_new_selfies(client, storage_stub):
    headers = register_raw(client, "reselfie@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.reselfie@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]
    client.post(
        f"/api/admin/verifications/{req_id}/request-reupload",
        headers=admin_headers,
        json={"reason_code": "selfie_unusable", "redo_selfie": True},
    )
    # Selfie + Ausweis gelöscht
    assert len(storage_stub) == 2

    status = client.get("/api/verification/status", headers=headers).json()
    assert status["next_step"] == "selfie"

    # Neustart liefert wieder eine Pose
    restart = client.post("/api/verification/start", headers=headers)
    assert restart.status_code == 200
    assert len(restart.json()["prompts"]) == 1


def test_final_rejection_blocks_account_and_restart(client, storage_stub):
    headers = register_raw(client, "rejected@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.reject@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]
    resp = client.post(
        f"/api/admin/verifications/{req_id}/reject",
        headers=admin_headers,
        json={"reason_code": "underage"},
    )
    assert resp.status_code == 200
    assert len(storage_stub) == 2  # alles gelöscht

    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["is_verified"] is False
    assert me["age_verified"] is False
    assert me["is_account_activated"] is False
    assert client.get("/api/swipes/deck", headers=headers).status_code == 403

    # Kein Neuanlauf auf Zuruf - sonst wäre die Altersprüfung wirkungslos
    restart = client.post("/api/verification/start", headers=headers)
    assert restart.status_code == 400


def test_approve_requires_full_checklist(client, storage_stub):
    headers = register_raw(client, "checklist@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.checklist@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]

    incomplete = {**FULL_CHECKLIST, "document_dob_matches_registration": False}
    resp = client.post(
        f"/api/admin/verifications/{req_id}/approve", headers=admin_headers, json=incomplete
    )
    assert resp.status_code == 422

    # Konto bleibt gesperrt
    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["is_account_activated"] is False


def test_failed_deletion_keeps_cleanup_pending(client, monkeypatch):
    """Bleibt eine Aufnahme im Storage liegen, gilt die Freigabe nicht als
    vollständig abgearbeitet - der Aufräumlauf versucht es erneut."""
    monkeypatch.setattr(
        app_storage,
        "inspect_uploaded_image",
        lambda key: {"ok": True, "size": 10, "detected": "image/jpeg"},
    )
    monkeypatch.setattr(app_storage, "delete_objects_verified", lambda keys: list(keys))

    headers = register_raw(client, "cleanup@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.cleanup@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]
    resp = client.post(
        f"/api/admin/verifications/{req_id}/approve", headers=admin_headers, json=FULL_CHECKLIST
    )
    assert resp.status_code == 200
    assert resp.json()["documents_deleted"] is False
    assert resp.json()["cleanup_pending"] is True

    # Freigabe gilt trotzdem - der Nutzer wartet nicht auf einen Storage-Fehler
    assert client.get("/api/profiles/me", headers=headers).json()["is_account_activated"] is True

    stats = client.get("/api/admin/stats", headers=admin_headers).json()
    assert stats["pending_verification_cleanups"] == 1

    # Zweiter Anlauf mit funktionierendem Storage räumt auf
    deleted: list[str] = []
    monkeypatch.setattr(
        app_storage, "delete_objects_verified", lambda keys: deleted.extend(keys) or []
    )
    from app.cleanup import purge_stale_verification_uploads

    db = TestingSessionLocal()
    try:
        purge_stale_verification_uploads(db)
        from app.models import VerificationRequest

        req = db.query(VerificationRequest).filter(VerificationRequest.id == req_id).first()
        assert req.cleanup_pending is False
        assert req.documents is None
    finally:
        db.close()
    assert len(deleted) == 2


def test_document_rejected_when_not_an_image(client, monkeypatch):
    """Der vom Client behauptete Content-Type zählt nicht - geprüft wird das
    tatsächlich hochgeladene Objekt."""
    monkeypatch.setattr(
        app_storage,
        "inspect_uploaded_image",
        lambda key: {"ok": False, "size": 40, "detected": None},
    )
    deleted: list[str] = []
    monkeypatch.setattr(
        app_storage, "delete_objects_verified", lambda keys: deleted.extend(keys) or []
    )

    headers = register_raw(client, "notanimage@example.com")
    _add_photo(client, headers)
    _submit_selfies(client, headers)

    key = client.post(
        "/api/verification/document/presign",
        headers=headers,
        json={"content_type": "image/jpeg", "byte_size": 40},
    ).json()["object_key"]
    resp = client.post(
        "/api/verification/document/submit",
        headers=headers,
        json={"document_type": "passport", "front_object_key": key},
    )
    assert resp.status_code == 400
    assert key in deleted  # die untaugliche Datei wird sofort entfernt


def test_oversized_document_rejected_before_upload(client, storage_stub):
    headers = register_raw(client, "toobig@example.com")
    _add_photo(client, headers)
    _submit_selfies(client, headers)

    resp = client.post(
        "/api/verification/document/presign",
        headers=headers,
        json={"content_type": "image/jpeg", "byte_size": app_storage.MAX_DOCUMENT_BYTES + 1},
    )
    assert resp.status_code == 400


def test_user_can_withdraw_submitted_documents(client, storage_stub):
    headers = register_raw(client, "withdraw@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    resp = client.request("DELETE", "/api/verification/document", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "id_required"
    assert len(storage_stub) == 1  # nur die Ausweisaufnahme


# ---------- Bestandskonten ----------


def test_existing_account_stays_usable(client):
    """Bestandskonten (verification_required False) bleiben unverändert nutzbar."""
    from app.models import User

    headers = register_user(client, "legacy@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.verification_required = False
        user.activated_at = None
        db.commit()
    finally:
        db.close()

    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["verification_required"] is False
    assert me["is_account_activated"] is True
    assert client.get("/api/swipes/deck", headers=headers).status_code == 200


def test_admin_can_require_verification_for_existing_account(client):
    headers = register_user(client, "nachfordern@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    admin_headers, _ = create_admin(client, email="admin.require@example.com")
    resp = client.post(f"/api/admin/users/{user_id}/require-verification", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_account_activated"] is False

    assert client.get("/api/swipes/deck", headers=headers).status_code == 403


def test_nachgeforderte_verification_can_be_started_after_an_old_decision(client, storage_stub):
    """Ein Bestandskonto mit früher abgeschlossener Prüfung muss den neu
    angeforderten Durchlauf tatsächlich beginnen können.

    Ohne diese Unterscheidung wäre die Nachforderung eine Sackgasse: Die alte
    Entscheidung würde den Start blockieren und das Konto bliebe für immer
    gesperrt.
    """
    headers = register_raw(client, "altbestand@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.altbestand@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]
    client.post(
        f"/api/admin/verifications/{req_id}/approve", headers=admin_headers, json=FULL_CHECKLIST
    )
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    # Solange nichts nachgefordert wurde, bleibt die Entscheidung bindend
    assert client.post("/api/verification/start", headers=headers).status_code == 400

    client.post(f"/api/admin/users/{user_id}/require-verification", headers=admin_headers)
    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["is_account_activated"] is False
    assert me["is_verified"] is False  # Haken hängt an der bestandenen Prüfung

    # Jetzt startet ein frischer Vorgang
    resp = client.post("/api/verification/start", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "in_progress"
    assert len(resp.json()["prompts"]) == 1


def test_rejected_account_cannot_restart_without_admin(client, storage_stub):
    """Gegenprobe: Ohne Nachforderung bleibt eine Ablehnung endgültig."""
    headers = register_raw(client, "endgueltig@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.endgueltig@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]
    client.post(
        f"/api/admin/verifications/{req_id}/reject",
        headers=admin_headers,
        json={"reason_code": "person_mismatch"},
    )
    assert client.post("/api/verification/start", headers=headers).status_code == 400


# ---------- Bestehende Zusicherungen ----------


def test_submit_with_wrong_prompts_rejected(client):
    headers = register_raw(client, "wrongpose@example.com")
    _add_photo(client, headers)
    client.post("/api/verification/start", headers=headers)
    me = client.get("/api/profiles/me", headers=headers).json()

    selfies = [
        {"prompt": f"Erfundene Pose {i}", "object_key": f"users/{me['id']}/verify/s{i}.jpg"}
        for i in range(1)
    ]
    resp = client.post("/api/verification/submit", headers=headers, json={"selfies": selfies})
    assert resp.status_code == 400


def test_submit_with_foreign_object_key_rejected(client):
    headers = register_raw(client, "foreignkey@example.com")
    _add_photo(client, headers)
    prompts = client.post("/api/verification/start", headers=headers).json()["prompts"]

    selfies = [
        {"prompt": p, "object_key": f"users/andere-user-id/verify/s{i}.jpg"}
        for i, p in enumerate(prompts)
    ]
    resp = client.post("/api/verification/submit", headers=headers, json={"selfies": selfies})
    assert resp.status_code == 400


def test_cannot_start_while_submitted(client, storage_stub):
    headers = register_raw(client, "double@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)
    resp = client.post("/api/verification/start", headers=headers)
    assert resp.status_code == 400


def test_start_is_idempotent_while_in_progress(client):
    headers = register_raw(client, "idem@example.com")
    _add_photo(client, headers)
    first = client.post("/api/verification/start", headers=headers).json()
    second = client.post("/api/verification/start", headers=headers).json()
    assert first["prompts"] == second["prompts"]


def test_verified_badge_visible_in_deck(client, storage_stub):
    headers_a = register_user(client, "badge.m@example.com", gender="mann")
    headers_b = register_raw(client, "badge.f@example.com", name="Verifizierte", gender="frau")
    add_approved_photo(client, headers_b)
    _complete_submission(client, headers_b)

    admin_headers, _ = create_admin(client, email="admin.badge@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]
    client.post(
        f"/api/admin/verifications/{req_id}/approve", headers=admin_headers, json=FULL_CHECKLIST
    )

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    verified = next(p for p in deck if p["name"] == "Verifizierte")
    assert verified["is_verified"] is True


def test_unverified_profile_hidden_from_deck(client, storage_stub):
    headers_a = register_user(client, "seeker@example.com", gender="mann")
    headers_b = register_raw(client, "unfertig@example.com", name="Unfertig", gender="frau")
    add_approved_photo(client, headers_b)

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    assert all(p["name"] != "Unfertig" for p in deck)
