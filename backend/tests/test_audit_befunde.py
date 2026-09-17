"""Regressionstests zur Durchsicht vom 17.09.2026.

Jeder Test hier gehört zu genau einem Befund aus der Prüfung von Nutzerweg,
Admin-Werkzeugen und Rechtstexten. Sie stehen bewusst zusammen und nicht
verstreut in den Themendateien: Wer einen davon rot sieht, soll ohne Suche
wissen, welcher Fehler zurück ist.
"""

from datetime import datetime

import pytest

from app import storage as app_storage
from app.config import settings
from app.models import Photo, PhotoStatus, User, VerificationStatus
from tests.conftest import (
    TestingSessionLocal,
    activate_user,
    add_approved_photo,
    create_admin,
    register_user,
    register_user_with_photo,
)


def _user(email: str) -> User:
    db = TestingSessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def _user_id(client, headers) -> str:
    return client.get("/api/profiles/me", headers=headers).json()["id"]


# ---------------------------------------------------------------------------
# Premium: Der Schalter ist der einzige Hebel
# ---------------------------------------------------------------------------

def test_premium_funktionen_sind_in_der_beta_fuer_alle_offen(client, monkeypatch):
    """Ohne Premium-Schalter darf keine Bezahlwand erscheinen.

    Vorher prueften ``/swipes/incoming`` und ``/swipes/rewind`` direkt
    ``User.is_premium``. Das ist bei ausgeschaltetem Schalter fuer *jeden*
    falsch - die Beta lieferte also allen Nutzern ``premium_required`` und
    einen 403, obwohl premium.py festhaelt, dass dann fuer alle alles offen
    ist. Genau danach sucht auch die App-Pruefung bei Apple.
    """
    monkeypatch.setattr(settings, "premium_enabled", False)

    headers = register_user_with_photo(client, "beta-offen@example.com")

    eingehend = client.get("/api/swipes/incoming", headers=headers)
    assert eingehend.status_code == 200
    assert eingehend.json()["premium_required"] is False

    ziel = _user_id(client, register_user_with_photo(client, "beta-ziel@example.com"))
    client.post(
        "/api/swipes", json={"to_user_id": ziel, "action": "pass"}, headers=headers
    )
    zurueck = client.post("/api/swipes/rewind", headers=headers)
    assert zurueck.status_code == 200


# ---------------------------------------------------------------------------
# Sperren
# ---------------------------------------------------------------------------

def test_sperre_verhindert_auch_den_swipe(client):
    """Eine Sperre muss den Swipe selbst abweisen, nicht nur das Deck filtern.

    Sonst entsteht aus einem vor der Sperre geladenen Deck (oder einem
    wiederholten POST) noch ein Match - samt Benachrichtigung an genau die
    Person, die gerade gesperrt hat.
    """
    a = register_user_with_photo(client, "sperrt@example.com")
    b = register_user_with_photo(client, "gesperrt@example.com", gender="frau")
    a_id, b_id = _user_id(client, a), _user_id(client, b)

    # A liked B, danach sperrt A.
    client.post("/api/swipes", json={"to_user_id": b_id, "action": "like"}, headers=a)
    assert client.post(
        "/api/blocks", json={"user_id": b_id}, headers=a
    ).status_code == 201

    # B versucht trotzdem zurueckzuliken - kein Match, kein Kontakt.
    antwort = client.post(
        "/api/swipes", json={"to_user_id": a_id, "action": "like"}, headers=b
    )
    assert antwort.status_code == 404
    assert client.get("/api/matches", headers=b).json() == []
    assert client.get("/api/matches", headers=a).json() == []


# ---------------------------------------------------------------------------
# Rücktritt: fremde request_id darf nichts preisgeben
# ---------------------------------------------------------------------------

def test_ruecktritt_gibt_fremde_erklaerung_nicht_heraus(client):
    """Die request_id kommt vom Client und ist frei waehlbar.

    Ungebunden nachgeschlagen lieferte ein Treffer die fremde Erklaerung im
    Klartext zurueck - mit Name, Vertragsbezug und den eigenen Worten des
    Erklaerenden.
    """
    erste = client.post(
        "/api/withdrawal",
        json={
            "name": "Erste Person",
            "email": "erste@example.com",
            "contract_reference": "erste@example.com",
            "message": "Vertraulicher Satz der ersten Person.",
            "confirmed": True,
            "request_id": "doppelklick-123",
        },
    )
    assert erste.status_code == 201, erste.text

    fremde = client.post(
        "/api/withdrawal",
        json={
            "name": "Zweite Person",
            "email": "zweite@example.com",
            "contract_reference": "zweite@example.com",
            "confirmed": True,
            "request_id": "doppelklick-123",
        },
    )
    # Die Erklaerung darf nie scheitern, aber sie muss die eigene sein.
    assert fremde.status_code == 201, fremde.text
    text = fremde.json()["declaration_text"]
    assert "Erste Person" not in text
    assert "Vertraulicher Satz" not in text
    assert fremde.json()["reference"] != erste.json()["reference"]


def test_ruecktritt_bleibt_fuer_dieselbe_person_idempotent(client):
    """Der Doppelklick-Schutz selbst muss erhalten bleiben."""
    daten = {
        "name": "Selbe Person",
        "email": "selbe@example.com",
        "contract_reference": "selbe@example.com",
        "confirmed": True,
        "request_id": "derselbe-klick",
    }
    eins = client.post("/api/withdrawal", json=daten)
    zwei = client.post("/api/withdrawal", json=daten)
    assert eins.status_code == 201, eins.text
    assert zwei.status_code == 201, zwei.text
    assert eins.json()["reference"] == zwei.json()["reference"]


# ---------------------------------------------------------------------------
# Foto-Moderation
# ---------------------------------------------------------------------------

def test_abgelehntes_foto_verschwindet_aus_dem_speicher(client, monkeypatch):
    """Was die Moderation entfernt, darf nicht unter seiner URL abrufbar bleiben.

    Die Zeile bleibt als Begruendungsnachweis stehen, die Bilddatei nicht:
    Unter den Ablehnungsgruenden stehen Nacktheit, Gewalt und "zeigt
    offenkundig eine minderjaehrige Person".
    """
    geloescht: list[str] = []
    monkeypatch.setattr(
        app_storage, "delete_objects_verified", lambda keys: geloescht.extend(keys) or []
    )

    headers = register_user(client, "fotomod@example.com")
    add_approved_photo(client, headers, url="https://cdn.example.test/heikel.jpg")

    db = TestingSessionLocal()
    try:
        foto = db.query(Photo).join(User).filter(User.email == "fotomod@example.com").first()
        foto_id = foto.id
    finally:
        db.close()

    admin_headers, _ = create_admin(client, email="admin.foto@example.com")
    antwort = client.post(
        f"/api/admin/photos/{foto_id}/reject",
        headers=admin_headers,
        json={"reason": "nudity"},
    )
    assert antwort.status_code == 200

    db = TestingSessionLocal()
    try:
        foto = db.query(Photo).filter(Photo.id == foto_id).first()
        # Zeile bleibt - Begruendung, Zeitpunkt und Konto sind der Nachweis.
        assert foto is not None
        assert foto.status == PhotoStatus.rejected
        assert foto.rejection_reason == "nudity"
    finally:
        db.close()


def test_freigabe_loescht_eine_frueher_erteilte_ablehnung(client):
    """Sonst haengt an einem sichtbaren Foto weiter die Begruendung, aus der
    es einmal entfernt wurde."""
    headers = register_user(client, "wiederfrei@example.com")
    add_approved_photo(client, headers, url="https://cdn.example.test/wieder.jpg")

    db = TestingSessionLocal()
    try:
        foto_id = (
            db.query(Photo).join(User).filter(User.email == "wiederfrei@example.com").first().id
        )
    finally:
        db.close()

    admin_headers, _ = create_admin(client, email="admin.wieder@example.com")
    client.post(
        f"/api/admin/photos/{foto_id}/reject",
        headers=admin_headers,
        json={"reason": "not_account_holder"},
    )
    client.post(f"/api/admin/photos/{foto_id}/approve", headers=admin_headers)

    db = TestingSessionLocal()
    try:
        foto = db.query(Photo).filter(Photo.id == foto_id).first()
        assert foto.status == PhotoStatus.approved
        assert foto.rejection_reason is None
        assert foto.rejection_note is None
        assert foto.rejected_at is None
    finally:
        db.close()
