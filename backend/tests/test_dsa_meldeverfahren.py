"""Melde- und Begründungspflichten nach dem Digital Services Act.

Art. 16: Meldung bekommt eine Empfangsbestätigung mit Aktenzeichen, der Melder
erfährt die Entscheidung. Art. 17: Jede Beschränkung eines Kontos wird begründet
und mit dem Hinweis auf den Widerspruch versehen.
"""

from tests.conftest import create_admin, register_user


def _report(client, headers, reported_user_id, reason="Fake-Profil mit fremden Fotos"):
    return client.post(
        "/api/reports",
        headers=headers,
        json={"reported_user_id": reported_user_id, "reason": reason},
    )


def test_report_returns_acknowledgement_with_reference(client):
    """Art. 16 Abs. 4: unverzügliche Empfangsbestätigung."""
    headers_a = register_user(client, "dsa.melder@example.com", name="A")
    headers_b = register_user(client, "dsa.gemeldet@example.com", name="B", gender="frau")
    user_b = client.get("/api/profiles/me", headers=headers_b).json()

    resp = _report(client, headers_a, user_b["id"])
    assert resp.status_code == 201
    body = resp.json()
    assert body["reported"] is True
    assert len(body["reference"]) == 8
    assert body["reference"].isupper()
    assert "72 Stunden" in body["message"]


def test_decision_is_recorded_with_reason(client):
    """Art. 16 Abs. 5: Die Entscheidung samt Begründung wird festgehalten. Eine
    Nutzeransicht dafür gibt es bewusst nicht mehr - der Nachweis bleibt in der
    Datenbank und die Meldung verschwindet aus der offenen Liste."""
    admin_headers, _ = create_admin(client, email="dsa.admin@example.com")
    headers_a = register_user(client, "dsa.melder2@example.com", name="A")
    headers_b = register_user(client, "dsa.gemeldet2@example.com", name="B", gender="frau")
    user_b = client.get("/api/profiles/me", headers=headers_b).json()

    reference = _report(client, headers_a, user_b["id"]).json()["reference"]

    offen = client.get("/api/admin/reports", headers=admin_headers).json()
    assert len(offen) == 1
    assert offen[0]["reference"] == reference

    resp = client.post(
        f"/api/admin/reports/{offen[0]['id']}/decide",
        headers=admin_headers,
        json={"outcome": "action_taken", "decision_note": "Profil gesperrt, Fotos entfernt."},
    )
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "action_taken"

    # Abgeschlossene Meldungen verschwinden aus der offenen Liste ...
    assert client.get("/api/admin/reports", headers=admin_headers).json() == []
    # ... bleiben aber als Nachweis erhalten.
    from app.models import Report
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        gespeichert = db.query(Report).one()
        assert gespeichert.outcome == "action_taken"
        assert gespeichert.decision_note == "Profil gesperrt, Fotos entfernt."
        assert gespeichert.dismissed_at is not None
    finally:
        db.close()


def test_decision_requires_a_note(client):
    """Ohne Text an den Melder lässt sich eine Meldung nicht abschließen."""
    admin_headers, _ = create_admin(client, email="dsa.admin2@example.com")
    headers_a = register_user(client, "dsa.melder4@example.com", name="A")
    headers_b = register_user(client, "dsa.gemeldet4@example.com", name="B", gender="frau")
    user_b = client.get("/api/profiles/me", headers=headers_b).json()
    _report(client, headers_a, user_b["id"])

    report_id = client.get("/api/admin/reports", headers=admin_headers).json()[0]["id"]
    resp = client.post(
        f"/api/admin/reports/{report_id}/decide",
        headers=admin_headers,
        json={"outcome": "no_action"},
    )
    assert resp.status_code == 422


def test_mute_notice_carries_reason_and_appeal(client):
    """Art. 17: Die laufende Beschränkung ist begründet abrufbar."""
    admin_headers, _ = create_admin(client, email="dsa.admin3@example.com")
    headers = register_user(client, "dsa.gemutet@example.com", name="M")
    user = client.get("/api/profiles/me", headers=headers).json()

    # Ohne Maßnahme gibt es keine Mitteilung
    assert client.get("/api/moderation/notice", headers=headers).json() is None

    client.post(
        f"/api/admin/users/{user['id']}/mute",
        headers=admin_headers,
        json={"days": 2, "reason": "Wiederholte Belaestigung"},
    )

    notice = client.get("/api/moderation/notice", headers=headers).json()
    assert notice["action"] == "mute"
    assert notice["reason"] == "Wiederholte Belaestigung"
    assert notice["muted_until"] is not None
    assert "flexr.social@proton.me" in notice["appeal_hint"]

    # Aufheben räumt die Begründung mit weg
    client.post(f"/api/admin/users/{user['id']}/unmute", headers=admin_headers)
    assert client.get("/api/moderation/notice", headers=headers).json() is None


def test_ban_reason_reaches_the_user_at_login(client):
    admin_headers, _ = create_admin(client, email="dsa.admin4@example.com")
    register_user(client, "dsa.gebannt@example.com", name="G")
    users = client.get("/api/admin/users", headers=admin_headers).json()
    user_id = next(u["id"] for u in users if u["email"] == "dsa.gebannt@example.com")

    client.post(
        f"/api/admin/users/{user_id}/ban",
        headers=admin_headers,
        json={"reason": "Gewerbliche Werbung trotz Verwarnung"},
    )

    resp = client.post(
        "/api/auth/login",
        json={"email": "dsa.gebannt@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 403
    detail = resp.json()["detail"]
    assert detail["moderation_action"] == "ban"
    assert detail["moderation_reason"] == "Gewerbliche Werbung trotz Verwarnung"
    assert "Rechtsweg" in detail["appeal_hint"]


def test_ban_without_reason_is_rejected(client):
    admin_headers, _ = create_admin(client, email="dsa.admin5@example.com")
    register_user(client, "dsa.ohnegrund@example.com", name="O")
    users = client.get("/api/admin/users", headers=admin_headers).json()
    user_id = next(u["id"] for u in users if u["email"] == "dsa.ohnegrund@example.com")

    resp = client.post(f"/api/admin/users/{user_id}/ban", headers=admin_headers, json={})
    assert resp.status_code == 422
