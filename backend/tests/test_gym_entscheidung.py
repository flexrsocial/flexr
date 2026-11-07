"""Mails und Folgen bei Freigabe/Ablehnung eines Gym-Vorschlags (07.11.2026).

Bis dahin aenderte die Entscheidung nur den Status. Nach einer Ablehnung galt
das Gym nirgends mehr - leeres Deck, fuer andere unsichtbar, Profil nicht
speicherbar - und niemand erfuhr davon.
"""

from datetime import timedelta

import pytest

from app import mailer
from app.models import Gym, User
from app.timeutil import utcnow
from tests.conftest import TestingSessionLocal, create_admin, register_user

VORSCHLAG = {"name": "Kraftkeller Wels", "street": "Ringstraße", "house_number": "5",
             "plz": "4600", "city": "Wels"}
LABEL = "Kraftkeller Wels — Ringstraße 5, 4600 Wels"


@pytest.fixture
def mails(monkeypatch):
    liste = []

    def fake(email, name, gym_name, approved, lang="de"):
        liste.append({"email": email, "gym": gym_name, "approved": approved, "lang": lang})
        return True

    monkeypatch.setattr(mailer, "send_gym_decision", fake)
    return liste


def _vorschlag_mit_mitglied(client, email):
    client.post("/api/gyms/suggest", json=VORSCHLAG)
    headers = register_user(client, email, gym=LABEL)
    admin, _ = create_admin(client, email=f"admin-{email}")
    gyms = client.get("/api/admin/gyms?status=pending", headers=admin).json()
    gym = next(g for g in gyms if g["name"] == VORSCHLAG["name"])
    return headers, admin, gym


def test_admin_liste_zeigt_nutzerzahl(client, mails):
    _, admin, gym = _vorschlag_mit_mitglied(client, "zahl@example.com")
    assert gym["member_count"] == 1


def test_freigabe_schickt_bestaetigung(client, mails):
    _, admin, gym = _vorschlag_mit_mitglied(client, "frei@example.com")
    r = client.post(f"/api/admin/gyms/{gym['id']}/approve", headers=admin)
    assert r.status_code == 200
    assert r.json()["notified"] == 1
    assert mails == [{"email": "frei@example.com", "gym": "Kraftkeller Wels",
                      "approved": True, "lang": "de"}]

    # Erneutes Freigeben verschickt nichts mehr
    r = client.post(f"/api/admin/gyms/{gym['id']}/approve", headers=admin)
    assert r.json()["notified"] == 0
    assert len(mails) == 1


def test_ablehnung_informiert_und_hebt_wechselsperre_auf(client, mails):
    headers, admin, gym = _vorschlag_mit_mitglied(client, "abgelehnt@example.com")
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "abgelehnt@example.com").one()
        user.gym_changed_at = utcnow() - timedelta(days=5)
        db.commit()
    finally:
        db.close()
    assert client.get("/api/profiles/me", headers=headers).json()["gym_change_locked_until"]

    r = client.post(f"/api/admin/gyms/{gym['id']}/reject", headers=admin)
    assert r.json()["notified"] == 1
    assert mails[0]["approved"] is False

    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["gym_change_locked_until"] is None
    # Wechsel auf ein gelistetes Gym klappt sofort
    r = client.patch("/api/profiles/me", headers=headers,
                     json={"gym": "Testgym mit Adresse — Teststraße 12, 1010 Wien"})
    assert r.status_code == 200, r.text

    # Erneutes Ablehnen verschickt nichts mehr
    assert client.post(f"/api/admin/gyms/{gym['id']}/reject", headers=admin).json()["notified"] == 0


def test_gleichnamiges_gueltiges_studio_bleibt_unberuehrt(client, mails):
    """Ein Bestandsprofil mit dem blossen Namen "Testgym mit Adresse" zeigt auf
    das Seed-Studio - die Ablehnung eines gleichnamigen Vorschlags anderswo
    darf es weder anschreiben noch mitzaehlen."""
    register_user(client, "bestand@example.com", gym="Testgym mit Adresse")
    client.post("/api/gyms/suggest", json={"name": "Testgym mit Adresse", "street": "Andere",
                                          "house_number": "1", "plz": "8010", "city": "Graz"})
    admin, _ = create_admin(client, email="admin-gleichnamig@example.com")
    gym = next(g for g in client.get("/api/admin/gyms?status=pending", headers=admin).json()
               if g["name"] == "Testgym mit Adresse")
    assert gym["member_count"] == 0
    assert client.post(f"/api/admin/gyms/{gym['id']}/reject", headers=admin).json()["notified"] == 0
    assert mails == []


@pytest.mark.parametrize("approved,betreff", [(True, "Dein Gym ist jetzt in der Liste"),
                                              (False, "Bitte wähle dein Gym neu")])
def test_mailinhalt(monkeypatch, approved, betreff):
    gesendet = []
    monkeypatch.setattr(mailer, "send_email",
                        lambda to, subject, text, html=None: gesendet.append((subject, text, html)) or True)
    assert mailer.send_gym_decision("a@b.c", "Anna", "Kraftkeller", approved, "de")
    subject, text, html = gesendet[0]
    assert subject == betreff
    assert "Kraftkeller" in text and "Kraftkeller" in html
    if approved:
        assert "/app/open/" in text and "/app/open/account" not in text
    else:
        assert "/app/open/account" in text
        assert "3-Monats-Sperre" in text
