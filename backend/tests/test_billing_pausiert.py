"""Ausgesetzte Abogebuehr: FLEXR ist waehrend der Beta fuer alle kostenlos.

Der kostenpflichtige Pfad bleibt vollstaendig im Code und wird von den
uebrigen Tests weiter geprueft (conftest setzt BILLING_ENABLED=true). Hier
steht das Gegenstueck: Was passiert, wenn ``settings.billing_enabled`` False
ist - der Zustand, in dem der Betrieb derzeit laeuft.
"""

from datetime import datetime, timedelta

from app.config import settings
from app.email_jobs import run_due_email_jobs
from app.models import User
from tests.conftest import TestingSessionLocal, register_user


NOW = datetime(2026, 8, 20, 7, 0, 0)  # 09:00 Uhr in Wien (MESZ)


def _abgelaufener_probemonat(user_id, tage=40):
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        user.trial_ends_at = datetime.utcnow() - timedelta(days=tage)
        user.is_subscribed = False
        user.stripe_subscription_id = None
        db.commit()
    finally:
        db.close()


def test_abgelaufener_probemonat_sperrt_nicht_mehr_aus(client, monkeypatch):
    """Bestandskonto, dessen Probemonat laengst vorbei ist: voller Zugang."""
    monkeypatch.setattr(settings, "billing_enabled", False)
    headers = register_user(client, "bestand@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    _abgelaufener_probemonat(user_id)

    status = client.get("/api/billing/status", headers=headers).json()
    assert status["is_active"] is True
    assert status["is_subscribed"] is False
    assert status["billing_enabled"] is False

    # Das Deck ist der Endpunkt hinter der Bezahlwand (402 bei abgelaufenem
    # Probemonat) - er muss jetzt normal antworten.
    assert client.get("/api/swipes/deck", headers=headers).status_code == 200


def test_bezahlwand_greift_wieder_wenn_die_gebuehr_aktiviert_wird(
    client, monkeypatch
):
    """Gegenprobe: Derselbe Nutzer, nur der Schalter umgelegt."""
    monkeypatch.setattr(settings, "billing_enabled", True)
    headers = register_user(client, "spaeter@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    _abgelaufener_probemonat(user_id)

    status = client.get("/api/billing/status", headers=headers).json()
    assert status["is_active"] is False
    assert status["billing_enabled"] is True
    assert client.get("/api/swipes/deck", headers=headers).status_code == 402


def test_checkout_wird_abgelehnt_solange_nichts_kostet(client, monkeypatch):
    """Kein Vertrag ueber eine Leistung, die es gerade gratis gibt."""
    monkeypatch.setattr(settings, "billing_enabled", False)
    headers = register_user(client, "checkout@example.com")

    resp = client.post(
        "/api/billing/checkout",
        json={"immediate_start": True, "withdrawal_ack": True},
        headers=headers,
    )
    assert resp.status_code == 409
    assert "kostenlos" in resp.json()["detail"]

    # Und es bleibt auch keine Einwilligungs-Buchung zurueck.
    db = TestingSessionLocal()
    try:
        from app.models import CheckoutConsent

        assert db.query(CheckoutConsent).count() == 0
    finally:
        db.close()


def test_keine_probemonat_mails_waehrend_der_gratisphase(client, monkeypatch):
    """"Dein Probemonat laeuft ab" waere falsch - es laeuft nichts ab."""
    monkeypatch.setattr(settings, "billing_enabled", False)
    ending_headers = register_user(client, "ending-frei@example.com")
    ended_headers = register_user(client, "ended-frei@example.com")
    ending_id = client.get("/api/profiles/me", headers=ending_headers).json()["id"]
    ended_id = client.get("/api/profiles/me", headers=ended_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.id == ending_id).one().trial_ends_at = (
            NOW + timedelta(days=3, hours=5)
        )
        db.query(User).filter(User.id == ended_id).one().trial_ends_at = (
            NOW - timedelta(hours=1)
        )
        db.commit()
    finally:
        db.close()

    def darf_nicht_rausgehen(*args, **kwargs):
        raise AssertionError("Probemonat-Mail trotz ausgesetzter Gebuehr versendet")

    monkeypatch.setattr(
        "app.email_jobs.mailer.send_free_trial_ending", darf_nicht_rausgehen
    )
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_free_trial_ended", darf_nicht_rausgehen
    )

    db = TestingSessionLocal()
    try:
        result = run_due_email_jobs(db, now=NOW)
    finally:
        db.close()

    assert result["trial_ending_sent"] == 0
    assert result["trial_ended_sent"] == 0
