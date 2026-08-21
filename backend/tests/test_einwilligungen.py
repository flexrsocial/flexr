"""Versionierte Einwilligungen und ihr Widerruf (Art. 7 DSGVO)."""

import pytest

from app import legal
from app.models import Consent
from tests.conftest import TestingSessionLocal, register_raw
from tests.test_swipes_and_matches import make_pair


def _consents(client, headers):
    """Neuesten Eintrag je Art zurückgeben. Die API liefert neueste zuerst -
    nach einem Widerruf + erneuter Einwilligung gibt es zwei Zeilen derselben
    Art; setdefault behält hier bewusst die erste (= neueste), nicht die
    letzte, wie es ein Dict-Comprehension täte."""
    resp = client.get("/api/profiles/me/consents", headers=headers)
    assert resp.status_code == 200
    result = {}
    for c in resp.json():
        result.setdefault(c["consent_type"], c)
    return result


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


@pytest.mark.parametrize("typ", ["sensitive_data", "verification_media"])
def test_jeder_widerrufbare_typ_hat_eine_folgenerklaerung(client, typ):
    """Ein Widerruf ohne Erklärung, was er bewirkt, wäre eine Falltür."""
    headers = register_raw(client, f"typ-{typ}@example.com")
    resp = client.post(
        "/api/profiles/me/consents/revoke", json={"consent_type": typ}, headers=headers
    )
    assert resp.status_code == 200
    assert len(resp.json()["consequence"]) > 40


def test_immediate_start_ist_nicht_widerrufbar(client):
    """§ 10/§ 18 Abs. 1 Z 1 FAGG-Erklärungen wirken fort, solange der Vertrag
    läuft - dafür gibt es keinen "Widerruf" mehr (siehe CheckoutConsent)."""
    headers = register_raw(client, "kein-widerruf-immediate-start@example.com")
    resp = client.post(
        "/api/profiles/me/consents/revoke",
        json={"consent_type": "immediate_start"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_widerruf_kann_zurueckgenommen_werden(client):
    """Ohne einen Weg zurück bliebe ein Konto nach dem Widerruf von
    sensitive_data dauerhaft mit leerem Deck zurück - reparierbar nur über
    die Kontolöschung. Das wäre unnötig hart."""
    headers = register_raw(client, "widerruf-zurueck@example.com")
    client.post(
        "/api/profiles/me/consents/revoke",
        json={"consent_type": "sensitive_data"},
        headers=headers,
    )
    eintraege = _consents(client, headers)
    assert eintraege["sensitive_data"]["active"] is False

    resp = client.post(
        "/api/profiles/me/consents/grant",
        json={"consent_type": "sensitive_data"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["granted"] is True

    eintraege = _consents(client, headers)
    assert eintraege["sensitive_data"]["active"] is True
    assert eintraege["sensitive_data"]["revoked_at"] is None


def test_erneute_einwilligung_erscheint_im_deck(client):
    """Der eigentliche Zweck: nach dem Widerruf verschwindet man aus fremden
    Decks, nach der erneuten Einwilligung taucht man wieder auf."""
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    deck = client.get("/api/swipes/deck", headers=headers_b).json()
    assert any(p["id"] == user_a["id"] for p in deck)

    client.post(
        "/api/profiles/me/consents/revoke",
        json={"consent_type": "sensitive_data"},
        headers=headers_a,
    )
    deck = client.get("/api/swipes/deck", headers=headers_b).json()
    assert all(p["id"] != user_a["id"] for p in deck)

    client.post(
        "/api/profiles/me/consents/grant",
        json={"consent_type": "sensitive_data"},
        headers=headers_a,
    )
    deck = client.get("/api/swipes/deck", headers=headers_b).json()
    assert any(p["id"] == user_a["id"] for p in deck)


def test_immediate_start_kann_nicht_erneut_erteilt_werden(client):
    headers = register_raw(client, "kein-grant-immediate-start@example.com")
    resp = client.post(
        "/api/profiles/me/consents/grant",
        json={"consent_type": "immediate_start"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_konto_ohne_consent_zeile_erscheint_nicht_im_deck(client):
    """Konten, die direkt in der DB angelegt wurden (z. B. per Skript, ohne
    über consents.grant() zu laufen) oder aus der Zeit vor der
    consents-Tabelle stammen, dürfen nicht stillschweigend so behandelt
    werden, als hätten sie nie eingewilligt - aber ohne nachgetragene
    Consent-Zeile (siehe Migration 9c4e1a7f2b83) verschwinden sie tatsächlich
    aus jedem Deck. Dieser Test hält genau dieses (unerwünschte, aber ohne
    Nachtrag reale) Verhalten fest, damit ein künftiger Nachtrag-Fix nicht
    versehentlich wieder verschwindet."""
    from app.models import Consent

    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    deck = client.get("/api/swipes/deck", headers=headers_b).json()
    assert any(p["id"] == user_a["id"] for p in deck)

    db = TestingSessionLocal()
    try:
        db.query(Consent).filter(
            Consent.user_id == user_a["id"], Consent.consent_type == "sensitive_data"
        ).delete()
        db.commit()
    finally:
        db.close()

    deck = client.get("/api/swipes/deck", headers=headers_b).json()
    assert all(p["id"] != user_a["id"] for p in deck)
