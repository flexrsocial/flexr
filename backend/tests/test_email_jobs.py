from datetime import datetime, timedelta

from app.email_jobs import run_due_email_jobs
from app.models import User
from tests.conftest import TestingSessionLocal, register_user


NOW = datetime(2026, 8, 20, 7, 0, 0)  # 09:00 Uhr in Wien (MESZ)


def _set_trial(user_id, trial_ends_at):
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        user.trial_ends_at = trial_ends_at
        user.is_subscribed = False
        user.stripe_subscription_id = None
        db.commit()
    finally:
        db.close()


def test_kostenloser_probemonat_erinnert_vorher_und_nachher_einmal(
    client, monkeypatch
):
    ending_headers = register_user(client, "ending@example.com")
    ended_headers = register_user(client, "ended@example.com")
    ending_id = client.get("/api/profiles/me", headers=ending_headers).json()["id"]
    ended_id = client.get("/api/profiles/me", headers=ended_headers).json()["id"]
    _set_trial(ending_id, NOW + timedelta(days=3, hours=5))
    _set_trial(ended_id, NOW - timedelta(hours=1))

    calls = []
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_free_trial_ending",
        lambda email, name, trial_end: calls.append(("ending", email)) or True,
    )
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_free_trial_ended",
        lambda email, name: calls.append(("ended", email)) or True,
    )

    db = TestingSessionLocal()
    try:
        run_due_email_jobs(db, now=NOW)
        run_due_email_jobs(db, now=NOW)
    finally:
        db.close()

    assert calls == [
        ("ending", "ending@example.com"),
        ("ended", "ended@example.com"),
    ]


def test_job_ueberspringt_laufendes_abo_und_unbestaetigte_adresse(
    client, monkeypatch
):
    subscribed_headers = register_user(client, "subscriber@example.com")
    unverified_headers = register_user(client, "unverified@example.com")
    subscribed_id = client.get(
        "/api/profiles/me", headers=subscribed_headers
    ).json()["id"]
    unverified_id = client.get(
        "/api/profiles/me", headers=unverified_headers
    ).json()["id"]

    db = TestingSessionLocal()
    try:
        subscribed = db.query(User).filter(User.id == subscribed_id).one()
        subscribed.trial_ends_at = NOW + timedelta(days=3)
        subscribed.is_subscribed = True
        subscribed.stripe_subscription_id = "sub_active"
        unverified = db.query(User).filter(User.id == unverified_id).one()
        unverified.trial_ends_at = NOW + timedelta(days=3)
        unverified.email_verified_at = None
        db.commit()
    finally:
        db.close()

    calls = []
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_free_trial_ending",
        lambda *args: calls.append(args) or True,
    )

    db = TestingSessionLocal()
    try:
        run_due_email_jobs(db, now=NOW)
    finally:
        db.close()

    assert calls == []
