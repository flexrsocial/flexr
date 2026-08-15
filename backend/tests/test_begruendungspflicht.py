"""Begründung von Moderationsmaßnahmen (Art. 17 DSA).

Vorher bestand eine Begründung aus einem einzigen Satz, und eine abgelehnte
Fotofreigabe kam ganz ohne aus. Art. 17 Abs. 3 verlangt mehr: Maßnahme und
Umfang, Dauer, die zugrunde liegenden Tatsachen, ob eine Meldung Anlass war,
ob automatisiert erkannt wurde, die konkrete Rechts- oder Vertragsgrundlage und
den Rechtsbehelf.
"""

import pytest

from app.models import ModerationAction, ModerationBasis, ModerationSource, User
from app.moderation import apply_restriction, clear_restriction, statement_of_reasons
from tests.conftest import TestingSessionLocal, create_admin, register_raw


@pytest.fixture
def admin_headers(client):
    headers, _ = create_admin(client, email="mod-admin@example.com")
    return headers


def _user(**felder) -> User:
    """Ein Nutzerobjekt ohne Datenbank - statement_of_reasons liest nur Felder."""
    user = User()
    for name, wert in felder.items():
        setattr(user, name, wert)
    return user


# ---------------------------------------------------------------------------
# Art. 17 Abs. 3: die Bestandteile der Begründung
# ---------------------------------------------------------------------------


def test_vollstaendige_begruendung_nennt_alle_bestandteile():
    from datetime import datetime, timedelta

    user = _user()
    apply_restriction(
        user,
        ModerationAction.mute,
        "Wiederholte Zahlungsaufforderungen im Chat.",
        muted_until=datetime.utcnow() + timedelta(days=7),
        facts="Am 14.08.2026 in drei Chats nach Paysafecard-Codes gefragt.",
        source=ModerationSource.user_notice,
        automated=True,
        basis=ModerationBasis.terms,
        basis_detail="Nutzungsrichtlinien, Abschnitt 3 (Betrug und Scam)",
    )

    aus = statement_of_reasons(user, ModerationAction.mute)

    assert "keine Nachrichten senden" in aus["measure"]
    assert aus["scope"] == "Senden von Nachrichten"
    assert "befristet bis" in aus["duration"]
    assert "Paysafecard" in aus["facts"]
    assert "Meldung" in aus["source"]
    assert "automatisiertes Mittel beteiligt" in aus["automated_detection"]
    assert "Abschnitt 3" in aus["legal_basis"]
    assert "widersprechen" in aus["appeal_hint"]


def test_ban_ist_unbefristet_und_sagt_das_auch():
    user = _user()
    apply_restriction(
        user,
        ModerationAction.ban,
        "Fake-Profil.",
        source=ModerationSource.own_initiative,
        basis=ModerationBasis.terms,
        basis_detail="Nutzungsrichtlinien, Abschnitt 6",
    )

    aus = statement_of_reasons(user, ModerationAction.ban)
    assert aus["scope"] == "gesamtes Konto"
    assert "unbefristet" in aus["duration"]
    assert "keine Meldung" in aus["source"]


def test_fehlende_angaben_werden_weggelassen_statt_erfunden():
    """Bestandsmaßnahmen aus der Zeit vor der Umstellung haben die neuen Felder
    nicht. Dann fehlt der Punkt - erfunden wird nichts."""
    user = _user()
    apply_restriction(user, ModerationAction.ban, "Verstoß gegen die Regeln.")

    aus = statement_of_reasons(user, ModerationAction.ban)
    assert "facts" not in aus
    assert "source" not in aus
    assert "legal_basis" not in aus
    # Was immer geht, steht trotzdem drin.
    assert aus["summary"] == "Verstoß gegen die Regeln."
    assert aus["appeal_hint"]


def test_ohne_automatisierte_erkennung_wird_das_ausdruecklich_gesagt():
    """Art. 17 Abs. 3 lit. c verlangt die Angabe - "nichts dazu" wäre keine."""
    user = _user()
    apply_restriction(user, ModerationAction.ban, "Grund.", automated=False)

    aus = statement_of_reasons(user, ModerationAction.ban)
    assert "kein automatisiertes Mittel" in aus["automated_detection"]


def test_aufheben_raeumt_die_begruendung_mit_weg():
    """Sonst bliebe eine Begründung stehen, zu der es keine Maßnahme mehr gibt."""
    user = _user()
    apply_restriction(
        user,
        ModerationAction.ban,
        "Grund.",
        facts="Tatsachen.",
        source=ModerationSource.user_notice,
        automated=True,
        basis=ModerationBasis.illegal_content,
        basis_detail="§ 107 StGB",
    )
    clear_restriction(user, ModerationAction.ban)

    assert user.moderation_reason is None
    assert user.moderation_facts is None
    assert user.moderation_source is None
    assert user.moderation_automated is False
    assert user.moderation_basis is None
    assert user.moderation_basis_detail is None


def test_gesperrter_nutzer_bekommt_die_begruendung_beim_login(client, admin_headers):
    """Beim Ban ist der Login der einzige Kanal - ein Token bekommt er nicht."""
    headers = register_raw(client, "gesperrt@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    client.post(
        f"/api/admin/users/{user_id}/ban",
        json={"reason": "Fake-Profil mit fremden Fotos."},
        headers=admin_headers,
    )

    resp = client.post(
        "/api/auth/login",
        json={"email": "gesperrt@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 403
    detail = resp.json()["detail"]
    # Die alten Felder bleiben - ausgelieferte Apps lesen sie.
    assert detail["moderation_reason"] == "Fake-Profil mit fremden Fotos."
    assert detail["appeal_hint"]
    # Neu daneben: die vollständige Begründung.
    assert detail["statement"]["measure"]
    assert detail["statement"]["scope"] == "gesamtes Konto"


# ---------------------------------------------------------------------------
# Fotoablehnung
# ---------------------------------------------------------------------------


def test_abgelehntes_foto_bekommt_einen_grund(client, admin_headers):
    """Vorher verschwand das Foto kommentarlos, und der Nutzer lud es ratlos
    noch einmal hoch."""
    from app.models import Photo

    headers = register_raw(client, "foto@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    db = TestingSessionLocal()
    try:
        foto = Photo(user_id=user_id, url="https://fotos.invalid/a.jpg", position=0)
        db.add(foto)
        db.commit()
        foto_id = foto.id
    finally:
        db.close()

    resp = client.post(
        f"/api/admin/photos/{foto_id}/reject",
        json={"reason": "contact_details", "note": None},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["reason"] == "contact_details"

    db = TestingSessionLocal()
    try:
        foto = db.query(Photo).filter(Photo.id == foto_id).one()
        assert foto.status.value == "rejected"
        assert foto.rejection_reason == "contact_details"
        assert foto.rejected_at is not None
    finally:
        db.close()


def test_ablehnung_ohne_grund_bleibt_moeglich(client, admin_headers):
    """Das ausgelieferte Admin-Tool schickt noch keinen Grund mit. Es darf in
    dem Moment nicht kaputtgehen, in dem der Server neu ist - der Nutzer
    bekommt dann den allgemeinen Hinweis statt gar keinen."""
    from app.models import Photo

    headers = register_raw(client, "foto2@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    db = TestingSessionLocal()
    try:
        foto = Photo(user_id=user_id, url="https://fotos.invalid/b.jpg", position=0)
        db.add(foto)
        db.commit()
        foto_id = foto.id
    finally:
        db.close()

    resp = client.post(f"/api/admin/photos/{foto_id}/reject", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["reason"] == "unusable"
