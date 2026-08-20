"""Melde- und Abhilfeverfahren nach Art. 16 DSA und Begründung nach Art. 17.

Der Unterschied zu tests/test_dsa_meldeverfahren.py: Dort geht es um die
Ein-Klick-Meldung aus der App heraus (POST /api/reports). Hier um das
förmliche Verfahren, das jedem offensteht - auch ohne Konto.
"""

import pytest

from tests.conftest import TestingSessionLocal, create_admin, register_raw


@pytest.fixture
def mit_smtp(monkeypatch):
    """Tut so, als wäre ein Mailserver eingerichtet - die Testumgebung hat
    keinen, und Tests zum Meldeverfahren sollen nicht stillschweigend im
    SMTP-losen Zweig landen."""
    from app.routers import notices

    monkeypatch.setattr(notices, "email_configured", lambda: True)


@pytest.fixture
def admin_headers(client):
    headers, _ = create_admin(client, email="dsa-admin@example.com")
    return headers


def _notice(**overrides):
    basis = {
        "category": "fraud",
        "explanation": (
            "Das Profil fordert im Chat wiederholt Paysafecard-Codes und "
            "behauptet eine Notlage. Das ist ein Betrugsversuch."
        ),
        "content_reference": "Profil 'Alex_Lifts', Chat vom 14.08.2026 gegen 21:30",
        "reporter_name": "Melderin Musterfrau",
        "reporter_email": "melderin@example.com",
        "good_faith": True,
    }
    basis.update(overrides)
    return basis


# ---------------------------------------------------------------------------
# Art. 16: Zugang zum Verfahren
# ---------------------------------------------------------------------------


def test_meldung_ohne_konto_moeglich(client, mit_smtp):
    """Art. 16 Abs. 1 DSA spricht von "Personen oder Einrichtungen" - ein Konto
    zu verlangen wäre eine Hürde, die die Vorschrift nicht kennt."""
    resp = client.post("/api/notices", json=_notice())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reference"].startswith("M-")
    assert body["acknowledgement_sent"] is True


def test_empfangsbestaetigung_nennt_aktenzeichen(client):
    """Art. 16 Abs. 4: unverzügliche Empfangsbestätigung."""
    from app.models import Notice

    resp = client.post("/api/notices", json=_notice())
    reference = resp.json()["reference"]
    assert reference in resp.json()["message"]

    db = TestingSessionLocal()
    try:
        notice = db.query(Notice).one()
        assert notice.acknowledged_at is not None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Art. 16 Abs. 2: was eine Meldung enthalten muss
# ---------------------------------------------------------------------------


def test_begruendung_muss_pruefbar_sein(client):
    """Art. 16 Abs. 2 lit. a verlangt eine Begründung, die eine Prüfung
    erlaubt. "ist illegal" ist keine."""
    resp = client.post("/api/notices", json=_notice(explanation="ist illegal"))
    assert resp.status_code == 422


def test_fundstelle_ist_pflicht(client):
    """Art. 16 Abs. 2 lit. b: die genaue elektronische Fundstelle."""
    resp = client.post("/api/notices", json=_notice(content_reference=""))
    assert resp.status_code == 422


def test_ohne_gutglaubenserklaerung_keine_meldung(client):
    """Art. 16 Abs. 2 lit. d."""
    resp = client.post("/api/notices", json=_notice(good_faith=False))
    assert resp.status_code == 422


def test_kontaktangaben_sind_regelfall_pflicht(client):
    """Ohne Adresse gibt es weder Empfangsbestätigung noch Entscheidung - das
    soll niemand versehentlich wählen."""
    resp = client.post(
        "/api/notices", json=_notice(reporter_name=None, reporter_email=None)
    )
    assert resp.status_code == 422


def test_csam_meldung_darf_anonym_sein(client):
    """Art. 16 Abs. 3 DSA nimmt Meldungen zu Straftaten nach den Artikeln 3
    bis 7 der Richtlinie 2011/93/EU von der Pflicht aus, Name und E-Mail
    anzugeben. Wer so etwas meldet, soll sich nicht ausweisen müssen."""
    resp = client.post(
        "/api/notices",
        json=_notice(
            category="csam",
            explanation=(
                "Auf dem dritten Profilfoto ist offenkundig ein Kind in "
                "eindeutiger Pose abgebildet."
            ),
            reporter_name=None,
            reporter_email=None,
        ),
    )
    assert resp.status_code == 201
    body = resp.json()
    # Ehrlich zurückmelden, dass ohne Adresse keine Entscheidung zustellbar ist.
    assert body["acknowledgement_sent"] is False
    assert "keine Entscheidung" in body["message"]


def test_dringende_kategorien_nennen_die_kuerzere_frist(client):
    """Wer eine Gefahr meldet, soll nicht 72 Stunden erwarten."""
    resp = client.post("/api/notices", json=_notice(category="threat"))
    assert "24 Stunden" in resp.json()["message"]

    resp = client.post("/api/notices", json=_notice(category="ip_infringement"))
    assert "72 Stunden" in resp.json()["message"]


# ---------------------------------------------------------------------------
# Art. 16 Abs. 5: Entscheidung und Begründung
# ---------------------------------------------------------------------------


def test_admin_entscheidet_mit_begruendung(client, admin_headers, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.routers.admin.mailer.send_report_decision",
        lambda *args, **kwargs: mails.append((args, kwargs)) or True,
    )
    from app.models import Notice

    client.post("/api/notices", json=_notice())

    offen = client.get("/api/admin/notices", headers=admin_headers).json()
    assert len(offen) == 1
    notice_id = offen[0]["id"]

    resp = client.post(
        f"/api/admin/notices/{notice_id}/decide",
        json={
            "outcome": "action_taken",
            "decision_reason": (
                "Das Profil wurde gesperrt. Die Chatverläufe belegen wiederholte "
                "Zahlungsaufforderungen; das verstößt gegen Abschnitt 3 der "
                "Nutzungsrichtlinien."
            ),
            "decision_automated": False,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["reporter_can_be_informed"] is True

    db = TestingSessionLocal()
    try:
        notice = db.query(Notice).one()
        assert notice.outcome == "action_taken"
        assert notice.decided_at is not None
        assert "Abschnitt 3" in notice.decision_reason
    finally:
        db.close()
    assert mails[0][0][0] == "melderin@example.com"
    assert "M-" in mails[0][0][1]


def test_entschiedene_meldung_faellt_aus_der_offenen_liste(client, admin_headers):
    client.post("/api/notices", json=_notice())
    notice_id = client.get("/api/admin/notices", headers=admin_headers).json()[0]["id"]

    client.post(
        f"/api/admin/notices/{notice_id}/decide",
        json={"outcome": "no_action", "decision_reason": "Kein Verstoß feststellbar."},
        headers=admin_headers,
    )

    assert client.get("/api/admin/notices", headers=admin_headers).json() == []
    alle = client.get("/api/admin/notices?open_only=false", headers=admin_headers).json()
    assert len(alle) == 1


def test_anonyme_meldung_meldet_ehrlich_dass_niemand_erreichbar_ist(
    client, admin_headers
):
    """Sonst hält der Admin die Sache für erledigt, obwohl die Entscheidung
    nirgends ankommt."""
    client.post(
        "/api/notices",
        json=_notice(
            category="csam",
            explanation="Auf dem Foto ist offenkundig ein Kind abgebildet.",
            reporter_name=None,
            reporter_email=None,
        ),
    )
    notice_id = client.get("/api/admin/notices", headers=admin_headers).json()[0]["id"]

    resp = client.post(
        f"/api/admin/notices/{notice_id}/decide",
        json={
            "outcome": "forwarded",
            "decision_reason": "An die Strafverfolgungsbehörden weitergegeben.",
        },
        headers=admin_headers,
    )
    assert resp.json()["reporter_can_be_informed"] is False


# ---------------------------------------------------------------------------
# Art. 16 Abs. 5 aus Sicht des Melders: "Meine Meldungen"
# ---------------------------------------------------------------------------


def test_melder_sieht_stand_der_eigenen_meldung(client, admin_headers):
    """frontend/sicherheit.html versprach diese Ansicht schon, bevor es sie
    gab. Jetzt gibt es sie."""
    melder = register_raw(client, "melder@example.com")
    gemeldet = register_raw(client, "boese@example.com")
    gemeldet_id = client.get("/api/profiles/me", headers=gemeldet).json()["id"]

    client.post(
        "/api/reports",
        json={"reported_user_id": gemeldet_id, "reason": "Belästigung im Chat"},
        headers=melder,
    )

    offen = client.get("/api/reports/mine", headers=melder).json()
    assert len(offen) == 1
    assert offen[0]["status"] == "open"
    assert offen[0]["outcome"] is None
    assert offen[0]["reference"]

    report_id = client.get("/api/admin/reports", headers=admin_headers).json()[0]["id"]
    client.post(
        f"/api/admin/reports/{report_id}/decide",
        json={
            "outcome": "action_taken",
            "decision_note": "Das gemeldete Konto wurde befristet stummgeschaltet.",
        },
        headers=admin_headers,
    )

    entschieden = client.get("/api/reports/mine", headers=melder).json()
    assert entschieden[0]["status"] == "decided"
    assert entschieden[0]["outcome"] == "action_taken"
    assert "stummgeschaltet" in entschieden[0]["decision_note"]


def test_melder_sieht_nur_die_eigenen_meldungen(client):
    melder = register_raw(client, "eins@example.com")
    anderer = register_raw(client, "zwei@example.com")
    ziel = register_raw(client, "ziel@example.com")
    ziel_id = client.get("/api/profiles/me", headers=ziel).json()["id"]

    client.post(
        "/api/reports",
        json={"reported_user_id": ziel_id, "reason": "Spam"},
        headers=melder,
    )

    assert client.get("/api/reports/mine", headers=anderer).json() == []


def test_ohne_smtp_wird_keine_empfangsbestaetigung_versprochen(client, monkeypatch):
    """Art. 16 Abs. 4 DSA verlangt eine Empfangsbestätigung. Kann sie gerade
    nicht rausgehen, soll der Melder sich das Aktenzeichen notieren, statt auf
    eine Mail zu warten, die nie kommt."""
    from app.routers import notices

    monkeypatch.setattr(notices, "email_configured", lambda: False)

    body = client.post("/api/notices", json=_notice()).json()
    assert body["acknowledgement_sent"] is False
    assert "keine Bestätigungsmail" in body["message"]
    assert body["reference"] in body["message"]


def test_mit_smtp_geht_die_bestaetigung_raus(client, monkeypatch):
    from app.routers import notices

    monkeypatch.setattr(notices, "email_configured", lambda: True)
    body = client.post("/api/notices", json=_notice()).json()
    assert body["acknowledgement_sent"] is True
    assert "melderin@example.com" in body["message"]
