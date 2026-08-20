"""Probemonat und Aufräumen rund um die Alters- und Identitätsprüfung."""

from datetime import datetime, timedelta

import pytest

from app import storage as app_storage
from app.cleanup import purge_deleted_users, purge_stale_verification_uploads
from app.config import settings
from app.models import User, VerificationRequest
from tests.conftest import TestingSessionLocal, create_admin, register_raw
from tests.test_verification import FULL_CHECKLIST, _add_photo, _complete_submission


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


def _user(user_id) -> User:
    db = TestingSessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


# ---------- Probemonat ----------


def test_pending_review_does_not_consume_trial(client, storage_stub, monkeypatch):
    """Der Probemonat startet mit der Freischaltung neu - eine lange manuelle
    Prüfung darf keine Gratiszeit kosten."""
    mails = []
    monkeypatch.setattr(
        "app.routers.admin.mailer.send_verification_decision",
        lambda *args, **kwargs: mails.append((args, kwargs)) or True,
    )
    headers = register_raw(client, "trial@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    _add_photo(client, headers)
    _complete_submission(client, headers)

    # Prüfung dauert 10 Tage
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.created_at = datetime.utcnow() - timedelta(days=10)
        user.trial_ends_at = datetime.utcnow() + timedelta(
            days=settings.stripe_trial_days - 10
        )
        db.commit()
    finally:
        db.close()

    admin_headers, _ = create_admin(client, email="admin.trial@example.com")
    req_id = client.get("/api/admin/verifications", headers=admin_headers).json()[0]["id"]
    client.post(
        f"/api/admin/verifications/{req_id}/approve", headers=admin_headers, json=FULL_CHECKLIST
    )

    status = client.get("/api/billing/status", headers=headers).json()
    remaining_days = (
        datetime.fromisoformat(status["trial_ends_at"]) - datetime.utcnow()
    ).days
    # Volle Gratiszeit ab Freischaltung, nicht ab Registrierung
    assert remaining_days >= settings.stripe_trial_days - 1
    assert mails[0][0][2] == "approved"


def test_trial_is_not_extended_by_a_second_activation(client, storage_stub):
    """activate_account() ist einmalig - eine zweite Freigabe verlängert die
    Gratiszeit nicht."""
    from app.verification_service import activate_account

    headers = register_raw(client, "einmalig@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        activate_account(user)
        db.commit()
        first_end = user.trial_ends_at
        first_activation = user.activated_at

        user.trial_ends_at = datetime.utcnow() + timedelta(days=1)
        db.commit()
        activate_account(user)
        db.commit()
        assert user.activated_at == first_activation
        assert user.trial_ends_at < first_end
    finally:
        db.close()


# ---------- Aufräumen ----------


def test_abandoned_verification_is_cleaned_up(client, storage_stub):
    """Registrierung abgebrochen: Die Aufnahmen verschwinden nach der
    Aufbewahrungsfrist samt Vorgang."""
    from app.verification_service import ORPHAN_RETENTION_DAYS

    headers = register_raw(client, "abgebrochen@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    db = TestingSessionLocal()
    try:
        req = db.query(VerificationRequest).first()
        req_id = req.id
        # Vorgang steckt im offenen Ausweisschritt und ist überaltert
        req.status = "id_required"
        req.created_at = datetime.utcnow() - timedelta(days=ORPHAN_RETENTION_DAYS + 1)
        db.commit()
    finally:
        db.close()

    db = TestingSessionLocal()
    try:
        assert purge_stale_verification_uploads(db) == 1
        assert db.query(VerificationRequest).filter(VerificationRequest.id == req_id).first() is None
    finally:
        db.close()
    assert len(storage_stub) == 2


def test_submitted_verification_is_not_cleaned_up(client, storage_stub):
    """Eingereichte Vorgänge warten auf die Prüfung und werden nicht entsorgt."""
    headers = register_raw(client, "wartend@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    db = TestingSessionLocal()
    try:
        req = db.query(VerificationRequest).first()
        req.created_at = datetime.utcnow() - timedelta(days=365)
        db.commit()
        assert purge_stale_verification_uploads(db) == 0
        assert db.query(VerificationRequest).count() == 1
    finally:
        db.close()
    assert storage_stub == []


def test_self_deletion_removes_verification_files_immediately(client, storage_stub):
    """Ausweisaufnahmen überdauern die 30-Tage-Karenzzeit nicht."""
    headers = register_raw(client, "selbstloeschung@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    resp = client.request(
        "DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"}
    )
    assert resp.status_code == 200
    assert len(storage_stub) == 2

    db = TestingSessionLocal()
    try:
        req = db.query(VerificationRequest).first()
        assert req.selfies is None
        assert req.documents is None
    finally:
        db.close()


def test_admin_deletion_removes_verification_files(client, storage_stub, monkeypatch):
    deleted: list[str] = []
    monkeypatch.setattr("app.cleanup.delete_storage_objects", lambda keys: deleted.extend(keys))

    headers = register_raw(client, "adminloeschung@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    _add_photo(client, headers)
    _complete_submission(client, headers)

    admin_headers, _ = create_admin(client, email="admin.del@example.com")
    resp = client.delete(f"/api/admin/users/{user_id}", headers=admin_headers)
    assert resp.status_code == 200
    # Selfie + Ausweisaufnahme (die Profilfoto-URL zeigt auf die
    # Test-Basis-URL und liefert ebenfalls einen Schlüssel)
    assert any(k.startswith("verification-documents/") for k in deleted)
    assert sum(1 for k in deleted if "/verify/" in k) == 1


def test_purge_after_grace_period_removes_verification_files(client, storage_stub, monkeypatch):
    deleted: list[str] = []
    monkeypatch.setattr("app.cleanup.delete_storage_objects", lambda keys: deleted.extend(keys))

    headers = register_raw(client, "karenz@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    _add_photo(client, headers)
    _complete_submission(client, headers)

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.deleted_at = datetime.utcnow() - timedelta(days=31)
        db.commit()
        assert purge_deleted_users(db) == 1
    finally:
        db.close()
    assert any(k.startswith("verification-documents/") for k in deleted)


def test_abandoned_upload_without_db_entry_is_purged(client, storage_stub, monkeypatch):
    """Angefangene Uploads ohne Datenbankeintrag müssen mitgelöscht werden.

    Der Upload läuft per Presigned PUT direkt in den Storage; erst /submit
    schreibt den Schlüssel in die Datenbank. Bricht der Client dazwischen ab,
    kennt kein Datensatz die Aufnahme mehr - sie ist nur noch über ihren Prefix
    auffindbar. Ausgerechnet die Ausweisaufnahme bliebe sonst dauerhaft liegen.
    """
    headers = register_raw(client, "abgebrochen@example.com")
    _add_photo(client, headers)
    _complete_submission(client, headers)

    db = TestingSessionLocal()
    try:
        req_id = db.query(VerificationRequest).first().id
    finally:
        db.close()

    # Zweiter Anlauf nach einem gescheiterten Einreichen: die Datei liegt im
    # Storage, in der Datenbank steht sie nicht.
    verwaist = f"verification-documents/{req_id}/abgebrochen.jpg"
    monkeypatch.setattr(
        app_storage,
        "list_object_keys",
        lambda prefix: [verwaist] if prefix.endswith(f"{req_id}/") else [],
    )

    resp = client.request(
        "DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"}
    )
    assert resp.status_code == 200
    assert verwaist in storage_stub
