"""Versionierte Einwilligungen und ihr Widerruf (Art. 7 DSGVO)."""

import pytest

from app import legal
from app.models import Consent
from tests.conftest import TestingSessionLocal, register_raw


def _consents(client, headers):
    resp = client.get("/api/profiles/me/consents", headers=headers)
    assert resp.status_code == 200
    return {c["consent_type"]: c for c in resp.json()}


def test_einwilligung_wird_mit_fassung_nachgewiesen(client):
    """Art. 7 Abs. 1: Nachweisbar muss sein, WOZU eingewilligt wurde - ein
    Zeitstempel ohne Textfassung leistet das nicht."""
    headers = register_raw(client, "nachweis@example.com")
    eintraege = _consents(client, headers)

    assert eintraege["sensitive_data"]["version"] == legal.PRIVACY_VERSION
    assert eintraege["sensitive_data"]["active"] is True
    assert eintraege["sensitive_data"]["revoked_at"] is None


def test_agb_annahme_steht_getrennt_von_der_einwilligung(client):
    """Die Annahme der AGB ist Vertragsschluss, keine datenschutzrechtliche
    Einwilligung. Beides zu vermischen wäre der klassische Fehler."""
    headers = register_raw(client, "getrennt@example.com")
    eintraege = _consents(client, headers)

    assert eintraege["terms"]["version"] == legal.TERMS_VERSION
    assert eintraege["sensitive_data"]["version"] == legal.PRIVACY_VERSION
    assert "terms" != "sensitive_data"  # zwei Einträge, nicht einer


def test_widerruf_geht_mit_einem_klick(client):
    """Art. 7 Abs. 3: Der Widerruf darf nicht schwerer sein als die Erteilung.
    Angehakt wird im Formular - also muss auch der Widerruf ein Aufruf sein,
    keine Mail an den Support."""
    headers = register_raw(client, "widerruf@example.com")

    resp = client.post(
        "/api/profiles/me/consents/revoke",
        json={"consent_type": "sensitive_data"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["revoked"] is True

    eintraege = _consents(client, headers)
    assert eintraege["sensitive_data"]["active"] is False
    assert eintraege["sensitive_data"]["revoked_at"] is not None


def test_widerruf_erklaert_die_folge(client):
    """Der Nutzer soll wissen, was er auslöst - Geschlecht und gesuchtes
    Geschlecht sind die Grundlage des Matchings."""
    headers = register_raw(client, "folge@example.com")

    resp = client.post(
        "/api/profiles/me/consents/revoke",
        json={"consent_type": "sensitive_data"},
        headers=headers,
    )
    folge = resp.json()["consequence"]
    assert "Matching" in folge
    assert "Konto" in folge


def test_widerruf_loescht_den_nachweis_nicht(client):
    """Sonst ließe sich später nicht mehr zeigen, dass überhaupt einmal
    eingewilligt wurde."""
    headers = register_raw(client, "nachweis2@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    client.post(
        "/api/profiles/me/consents/revoke",
        json={"consent_type": "sensitive_data"},
        headers=headers,
    )

    db = TestingSessionLocal()
    try:
        eintrag = (
            db.query(Consent)
            .filter(Consent.user_id == user_id, Consent.consent_type == "sensitive_data")
            .one()
        )
        assert eintrag.granted_at is not None
        assert eintrag.revoked_at is not None
    finally:
        db.close()


def test_doppelter_widerruf_ist_harmlos(client):
    headers = register_raw(client, "doppelt@example.com")
    payload = {"consent_type": "sensitive_data"}

    erste = client.post("/api/profiles/me/consents/revoke", json=payload, headers=headers)
    zweite = client.post("/api/profiles/me/consents/revoke", json=payload, headers=headers)

    assert erste.json()["revoked"] is True
    assert zweite.status_code == 200
    assert zweite.json()["revoked"] is False  # es gab nichts mehr zu widerrufen


def test_agb_annahme_ist_nicht_widerrufbar(client):
    """Ein Vertrag wird gekündigt, nicht widerrufen - "terms" darf im
    Widerrufs-Endpunkt gar nicht auftauchen."""
    headers = register_raw(client, "agb@example.com")
    resp = client.post(
        "/api/profiles/me/consents/revoke",
        json={"consent_type": "terms"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_einwilligung_wird_nicht_doppelt_angelegt(client):
    """Sonst entstünde bei jedem Speichern ein neuer Nachweis derselben
    Fassung."""
    from app import consents
    from app.models import ConsentType, User

    headers = register_raw(client, "einmal@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        consents.grant(db, user, ConsentType.sensitive_data)
        consents.grant(db, user, ConsentType.sensitive_data)

        anzahl = (
            db.query(Consent)
            .filter(Consent.user_id == user_id, Consent.consent_type == "sensitive_data")
            .count()
        )
        assert anzahl == 1
    finally:
        db.close()


def test_consents_verschwinden_mit_dem_konto():
    """Anders als die Rücktrittserklärung hängen Einwilligungen am Konto und
    haben ohne es keinen Zweck."""
    fk = next(iter(Consent.__table__.c.user_id.foreign_keys))
    assert fk.ondelete == "CASCADE"


@pytest.mark.parametrize("typ", ["sensitive_data", "verification_media", "immediate_start"])
def test_jeder_widerrufbare_typ_hat_eine_folgenerklaerung(client, typ):
    """Ein Widerruf ohne Erklärung, was er bewirkt, wäre eine Falltür."""
    headers = register_raw(client, f"typ-{typ}@example.com")
    resp = client.post(
        "/api/profiles/me/consents/revoke", json={"consent_type": typ}, headers=headers
    )
    assert resp.status_code == 200
    assert len(resp.json()["consequence"]) > 40
