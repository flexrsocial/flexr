"""Kündigungsbutton nach § 312k BGB.

Geprüft wird, was die Vorschrift verlangt: ohne Anmeldung erreichbar, nur die
vorgesehenen Angaben, Grund bei außerordentlicher Kündigung, Bestätigung mit
Inhalt, Datum, Uhrzeit und Beendigungszeitpunkt - und dass ein zuordenbares
Web-Abo tatsächlich nicht mehr verlängert wird.
"""

from datetime import datetime

import pytest

from app import stripe_client, telegram
from app.models import CancellationDeclaration, User
from app.routers import cancellation
from tests.conftest import TestingSessionLocal, register_raw


@pytest.fixture
def mit_smtp(monkeypatch):
    monkeypatch.setattr(cancellation, "email_configured", lambda: True)


@pytest.fixture
def gemeldet(monkeypatch):
    texte = []
    monkeypatch.setattr(telegram, "notify_admin_task", lambda text: texte.append(text) or True)
    return texte


@pytest.fixture
def stripe_kuendigung(monkeypatch):
    aufrufe = []

    def kuendigen(sub_id):
        aufrufe.append(sub_id)
        return datetime(2026, 12, 3, 10, 0, 0)

    monkeypatch.setattr(stripe_client, "cancel_subscription_at_period_end", kuendigen)
    return aufrufe


def _payload(**overrides):
    basis = {"name": "Erika Mustermann", "email": "erika@example.com", "confirmed": True}
    basis.update(overrides)
    return basis


def _abo_setzen(email, sub_id="sub_de123"):
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        user.stripe_subscription_id = sub_id
        user.is_subscribed = True
        db.commit()
    finally:
        db.close()


def test_kuendigung_ohne_anmeldung_moeglich(client, mit_smtp, gemeldet):
    resp = client.post("/api/cancellation", json=_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reference"].startswith("K-")
    assert body["confirmation_sent"] is True
    assert "zum nächstmöglichen Zeitpunkt" in body["declaration_text"]
    assert "Erklärt am:" in body["declaration_text"]
    assert any("kein Web-Abo zugeordnet" in t for t in gemeldet)


def test_jetzt_kuendigen_muss_gedrueckt_sein(client):
    assert client.post("/api/cancellation", json=_payload(confirmed=False)).status_code == 422


def test_ausserordentlich_braucht_grund(client):
    resp = client.post("/api/cancellation", json=_payload(kind="ausserordentlich", reason="  "))
    assert resp.status_code == 422
    resp = client.post("/api/cancellation", json=_payload(kind="ausserordentlich", reason="Dienst dauerhaft nicht erreichbar"))
    assert resp.status_code == 201
    assert "Grund: Dienst dauerhaft nicht erreichbar" in resp.json()["declaration_text"]


def test_angemeldet_wird_web_abo_zum_periodenende_gekuendigt(client, mit_smtp, gemeldet, stripe_kuendigung):
    headers = register_raw(client, "abo-de@example.com")
    _abo_setzen("abo-de@example.com")
    resp = client.post("/api/cancellation", json=_payload(email="abo-de@example.com"), headers=headers)
    assert resp.status_code == 201, resp.text
    assert stripe_kuendigung == ["sub_de123"]
    assert resp.json()["effective_at"].startswith("2026-12-03")
    assert any("automatisch zum Periodenende" in t for t in gemeldet)


def test_ohne_anmeldung_ueber_konto_email_zugeordnet(client, mit_smtp, gemeldet, stripe_kuendigung):
    """Entscheidung vom 03.11.2026: Passt die E-Mail zu einem Konto mit
    Web-Abo, wird auch ohne Anmeldung gekündigt - die Bestätigung geht an
    genau diese Adresse, Missbrauch fiele also dem Inhaber auf."""
    register_raw(client, "ohnelogin@example.com")
    _abo_setzen("ohnelogin@example.com", "sub_ohne")
    resp = client.post("/api/cancellation", json=_payload(email="OhneLogin@Example.com"))
    assert resp.status_code == 201
    assert stripe_kuendigung == ["sub_ohne"]

    db = TestingSessionLocal()
    try:
        erkl = db.query(CancellationDeclaration).one()
        assert erkl.user_id is not None
        assert erkl.subscription_cancelled_at is not None
    finally:
        db.close()


def test_wunschtermin_und_ausserordentlich_nicht_automatisch(client, mit_smtp, gemeldet, stripe_kuendigung):
    register_raw(client, "termin@example.com")
    _abo_setzen("termin@example.com")
    resp = client.post("/api/cancellation", json=_payload(email="termin@example.com", requested_end="2027-03-31"))
    assert resp.status_code == 201
    assert "31.03.2027" in resp.json()["declaration_text"]
    resp = client.post("/api/cancellation", json=_payload(
        email="termin@example.com", kind="ausserordentlich", reason="Preiserhöhung"))
    assert resp.status_code == 201
    assert stripe_kuendigung == []
    assert any("Wunschtermin 31.03.2027" in t for t in gemeldet)
    assert any("AUSSERORDENTLICH" in t for t in gemeldet)


def test_stripe_fehler_kippt_die_kuendigung_nicht(client, mit_smtp, gemeldet, monkeypatch):
    register_raw(client, "kaputt@example.com")
    _abo_setzen("kaputt@example.com")

    def kaputt(sub_id):
        raise RuntimeError("Stripe nicht erreichbar")

    monkeypatch.setattr(stripe_client, "cancel_subscription_at_period_end", kaputt)
    resp = client.post("/api/cancellation", json=_payload(email="kaputt@example.com"))
    assert resp.status_code == 201
    assert resp.json()["effective_at"] is None


def test_doppelklick_legt_keine_zweite_erklaerung_an(client, mit_smtp, gemeldet):
    p = _payload(request_id="11111111-2222-3333-4444-555555555555")
    erste = client.post("/api/cancellation", json=p).json()
    zweite = client.post("/api/cancellation", json=p).json()
    assert erste["reference"] == zweite["reference"]
    db = TestingSessionLocal()
    try:
        assert db.query(CancellationDeclaration).count() == 1
    finally:
        db.close()


def test_fremde_request_id_gibt_keine_fremden_daten_heraus(client, mit_smtp, gemeldet):
    rid = "aaaaaaaa-2222-3333-4444-555555555555"
    client.post("/api/cancellation", json=_payload(request_id=rid))
    fremd = client.post("/api/cancellation", json=_payload(
        request_id=rid, name="Jemand Anderes", email="anderer@example.com")).json()
    assert "Erika" not in fremd["declaration_text"]


def test_ohne_smtp_ehrlicher_hinweis(client, gemeldet, monkeypatch):
    monkeypatch.setattr(cancellation, "email_configured", lambda: False)
    body = client.post("/api/cancellation", json=_payload()).json()
    assert body["confirmation_sent"] is False
    assert "keine Bestätigungsmail" in body["message"]


def test_englische_erklaerung(client, mit_smtp, gemeldet):
    body = client.post("/api/cancellation", json=_payload(language="en")).json()
    assert body["declaration_text"].startswith("I hereby cancel")
    assert "at the earliest possible date" in body["declaration_text"]


def test_bestaetigungsmail_nennt_vertragsende():
    from app import mailer

    text = mailer._cancellation_text(
        "Erika", "K-ABCDEF12", "03.11.2026, 12:00:00 Uhr (CET)", "Wortlaut", None,
        "ordentlich", "mit Ablauf des 03.12.2026", True, "de",
    )
    assert "Vertragsende" in text and "03.12.2026" in text
    assert "Eingegangen am" in text and "12:00:00" in text
    assert "Wortlaut" in text


def test_kuendigungsseite_existiert_und_ist_ueberall_verlinkt():
    from pathlib import Path

    frontend = Path(__file__).resolve().parents[2] / "frontend"
    seite = (frontend / "kuendigen.html").read_text(encoding="utf-8")
    assert "Verträge hier kündigen" in seite and "Jetzt kündigen" in seite
    assert (frontend / "en" / "kuendigen.html").exists()
    # § 312k Abs. 1 BGB: ständig verfügbar - also auf jeder Seite mit dem
    # Rücktritts-Link auch der Kündigungs-Link.
    ohne = []
    for html in list(frontend.glob("*.html")) + list((frontend / "en").glob("*.html")) + [frontend / "app" / "index.html"]:
        inhalt = html.read_text(encoding="utf-8")
        if "data-widerruf-link" in inhalt and "kuendigen.html" not in inhalt:
            ohne.append(html.name)
    assert ohne == []
