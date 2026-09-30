"""Meldungen: keine Duplikate, Chat-Auszug ueberlebt das Aufloesen des Matches."""

from datetime import timedelta

from tests.conftest import TestingSessionLocal, create_admin
from tests.test_messages import make_match


def _melden(client, headers, user_id, grund="Belaestigung im Chat"):
    return client.post(
        "/api/reports", headers=headers, json={"reported_user_id": user_id, "reason": grund}
    )


def test_chat_auszug_bleibt_nach_unmatch_fuer_admin_sichtbar(client):
    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)
    client.post(f"/api/matches/{match_id}/messages", headers=headers_b,
                json={"content": "Schick mir deine Nummer: 0664 1234567"})
    client.post(f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": "Nein."})

    assert _melden(client, headers_a, user_b["id"]).status_code == 201
    # Der Gemeldete loest das Match auf - der Chat ist damit geloescht.
    assert client.delete(f"/api/matches/{match_id}", headers=headers_b).status_code == 200

    admin, _ = create_admin(client)
    reports = client.get("/api/admin/reports", headers=admin).json()
    assert len(reports) == 1
    ev = reports[0]["evidence"]
    assert [m["from"] for m in ev] == ["reported", "reporter"]
    # Original, nicht die fuer den Empfaenger zensierte Fassung
    assert "0664 1234567" in ev[0]["content"]


def test_wiederholte_meldung_legt_keine_zweite_akte_an(client, monkeypatch):
    gesendet = []
    monkeypatch.setattr("app.routers.safety.telegram.notify_admin_task", gesendet.append)
    _, (headers_a, _), (_, user_b) = make_match(client)

    erste = _melden(client, headers_a, user_b["id"]).json()
    for _ in range(5):
        zweite = _melden(client, headers_a, user_b["id"], "Fake-Profil").json()
    assert zweite["reference"] == erste["reference"]
    assert len(gesendet) == 1

    admin, _ = create_admin(client)
    reports = client.get("/api/admin/reports", headers=admin).json()
    assert len(reports) == 1
    assert "Belaestigung" in reports[0]["reason"] and "Fake-Profil" in reports[0]["reason"]


def test_nach_entscheidung_ist_neue_meldung_eine_neue_akte(client):
    _, (headers_a, _), (_, user_b) = make_match(client)
    erste = _melden(client, headers_a, user_b["id"]).json()
    admin, _ = create_admin(client)
    rid = client.get("/api/admin/reports", headers=admin).json()[0]["id"]
    client.post(f"/api/admin/reports/{rid}/decide", headers=admin,
                json={"outcome": "no_action", "decision_note": "Kein Verstoss."})
    zweite = _melden(client, headers_a, user_b["id"]).json()
    assert zweite["reference"] != erste["reference"]


def test_chat_auszug_wird_nach_frist_geleert(client):
    from app.cleanup import purge_old_report_evidence
    from app.models import Report
    from app.retention import REPORT_EVIDENCE_RETENTION_DAYS
    from app.timeutil import utcnow

    match_id, (headers_a, _), (headers_b, user_b) = make_match(client)
    client.post(f"/api/matches/{match_id}/messages", headers=headers_b, json={"content": "Hallo"})
    _melden(client, headers_a, user_b["id"])

    db = TestingSessionLocal()
    try:
        r = db.query(Report).one()
        assert r.evidence
        r.dismissed_at = utcnow() - timedelta(days=REPORT_EVIDENCE_RETENTION_DAYS + 1)
        db.commit()
        assert purge_old_report_evidence(db) == 1
        db.refresh(r)
        assert r.evidence is None
    finally:
        db.close()
