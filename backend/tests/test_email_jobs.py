"""Taegliche E-Mail-Jobs.

Hier standen bis zum 10.09.2026 die beiden Probemonats-Mails ("laeuft in drei
Tagen ab" / "ist beendet"). Beide sind mit dem Probemonat selbst entfallen: Die
Plattform ist dauerhaft kostenlos, es laeuft nichts mehr ab, und eine Mail
darueber waere blanke Verunsicherung.

Was bleibt, ist die Zusicherung, dass der taegliche Job trotzdem laeuft und
seine Zaehlerform behaelt - die Aktivitaets-Benachrichtigungen haengen daran
und werden in ``test_benachrichtigungen.py`` im Einzelnen geprueft.
"""

from datetime import datetime, timedelta

from app.email_jobs import run_due_email_jobs
from app.models import User
from tests.conftest import TestingSessionLocal, register_user


NOW = datetime(2026, 8, 20, 7, 0, 0)  # 09:00 Uhr in Wien (MESZ)


def test_kein_probemonat_mehr_also_keine_probemonats_mails(client, monkeypatch):
    """Auch ein laengst "abgelaufenes" trial_ends_at loest nichts mehr aus.

    Der Wert steht bei Bestandskonten noch in der Spalte; entscheidend ist,
    dass ihn niemand mehr ausliest. Zur Sicherheit wird jeder Mailversand
    scharf gestellt: Geht irgendetwas raus, faellt der Test.
    """
    bald_headers = register_user(client, "bald@example.com")
    vorbei_headers = register_user(client, "vorbei@example.com")
    bald_id = client.get("/api/profiles/me", headers=bald_headers).json()["id"]
    vorbei_id = client.get("/api/profiles/me", headers=vorbei_headers).json()["id"]

    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.id == bald_id).one().trial_ends_at = (
            NOW + timedelta(days=3, hours=5)
        )
        db.query(User).filter(User.id == vorbei_id).one().trial_ends_at = (
            NOW - timedelta(hours=1)
        )
        db.commit()
    finally:
        db.close()

    def darf_nicht_rausgehen(*args, **kwargs):
        raise AssertionError("E-Mail zum abgeschafften Probemonat versendet")

    monkeypatch.setattr("app.email_jobs.mailer.send_email", darf_nicht_rausgehen)

    db = TestingSessionLocal()
    try:
        result = run_due_email_jobs(db, now=NOW)
    finally:
        db.close()

    # Die Zaehler bleiben in der Antwort stehen (der Aufrufer in scripts/ liest
    # sie), zeigen aber dauerhaft null.
    assert result["trial_ending_sent"] == 0
    assert result["trial_ended_sent"] == 0
    assert result["failed"] == 0


def test_der_taegliche_job_laeuft_weiter(client):
    """Ohne faellige Nachrichten kommt eine vollstaendige Zaehlerliste zurueck."""
    db = TestingSessionLocal()
    try:
        result = run_due_email_jobs(db, now=NOW)
    finally:
        db.close()

    for schluessel in ("trial_ending_sent", "trial_ended_sent", "failed"):
        assert schluessel in result
