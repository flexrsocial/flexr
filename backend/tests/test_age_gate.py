"""Altersgrenze: Berechnung, Registrierungs-Gate und Schutz gegen
systematisches Durchprobieren."""

from datetime import date, timedelta

import pytest

from app.age import age_on, is_adult, is_plausible_birthdate
from tests.conftest import DEFAULT_USER


# ---------- Berechnung ----------


@pytest.mark.parametrize(
    "birthdate,today,expected",
    [
        # 17 Jahre: Geburtstag war schon, aber erst 17-mal
        (date(2009, 3, 1), date(2026, 8, 7), 17),
        # Genau am 18. Geburtstag
        (date(2008, 8, 7), date(2026, 8, 7), 18),
        # Einen Tag vor dem 18. Geburtstag
        (date(2008, 8, 8), date(2026, 8, 7), 17),
        # Deutlich über 18
        (date(1990, 1, 1), date(2026, 8, 7), 36),
        # Geburtstag später im Jahr - kein "Jahr minus Jahr"
        (date(2008, 12, 31), date(2026, 1, 1), 17),
    ],
)
def test_age_on(birthdate, today, expected):
    assert age_on(birthdate, today) == expected


def test_leap_day_birthday_in_non_leap_year():
    """Am 29. Februar Geborene werden in Nicht-Schaltjahren am 1. März älter."""
    leap_born = date(2008, 2, 29)
    assert age_on(leap_born, date(2026, 2, 28)) == 17
    assert age_on(leap_born, date(2026, 3, 1)) == 18
    # Im Schaltjahr selbst zählt der 29. Februar
    assert age_on(leap_born, date(2028, 2, 29)) == 20


def test_is_adult_boundary():
    today = date(2026, 8, 7)
    assert is_adult(date(2008, 8, 7), today) is True
    assert is_adult(date(2008, 8, 8), today) is False


def test_implausible_birthdates():
    today = date(2026, 8, 7)
    assert is_plausible_birthdate(today + timedelta(days=1), today) is False  # Zukunft
    assert is_plausible_birthdate(date(1900, 1, 1), today) is False           # zu alt
    assert is_plausible_birthdate(date(1990, 1, 1), today) is True


# ---------- Registrierung ----------


def _payload(birthdate, email="agegate@example.com"):
    return {**DEFAULT_USER, "email": email, "name": "Test", "birthdate": birthdate}


def test_register_blocks_minor(client):
    seventeen = (date.today().replace(year=date.today().year - 17)).isoformat()
    resp = client.post("/api/auth/register", json=_payload(seventeen))
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "underage"
    assert "mindestens 18 Jahre alt" in resp.json()["detail"]["message"]


def test_register_allows_exact_18th_birthday(client):
    today = date.today()
    try:
        eighteenth = today.replace(year=today.year - 18)
    except ValueError:  # 29. Februar
        eighteenth = today.replace(year=today.year - 18, day=28)
    resp = client.post(
        "/api/auth/register", json=_payload(eighteenth.isoformat(), "exactly18@example.com")
    )
    assert resp.status_code == 200, resp.text


def test_register_rejects_future_and_implausible_birthdate(client):
    future = (date.today() + timedelta(days=1)).isoformat()
    assert client.post("/api/auth/register", json=_payload(future, "future@example.com")).status_code == 422
    assert client.post(
        "/api/auth/register", json=_payload("1890-01-01", "ancient@example.com")
    ).status_code == 422


def test_register_rejects_malformed_date(client):
    resp = client.post("/api/auth/register", json=_payload("nicht-ein-datum", "bad@example.com"))
    assert resp.status_code == 422


# ---------- Vorabprüfung im Formular ----------


def test_age_check_endpoint(client):
    seventeen = (date.today().replace(year=date.today().year - 17)).isoformat()
    resp = client.post("/api/auth/age-check", json={"birthdate": seventeen})
    assert resp.status_code == 200
    assert resp.json()["eligible"] is False
    assert "mindestens 18" in resp.json()["message"]

    resp = client.post("/api/auth/age-check", json={"birthdate": "1990-01-01"})
    assert resp.json()["eligible"] is True
    assert resp.json()["verification_required"] is True


def test_age_check_does_not_count_as_an_attempt(client):
    """Die Vorabprüfung im Formular darf keine Versuche erzeugen.

    Ein Datumsfeld meldet schon während der Eingabe vollständige
    Zwischenwerte - daraus dürfen keine Registrierungsversuche werden.
    """
    from app.models import UnderageSignupAttempt
    from tests.conftest import TestingSessionLocal

    device = {"X-Device-Id": "test-device-agecheck-only"}
    seventeen = (date.today().replace(year=date.today().year - 17)).isoformat()
    for _ in range(5):
        client.post("/api/auth/age-check", json={"birthdate": seventeen}, headers=device)

    db = TestingSessionLocal()
    try:
        assert db.query(UnderageSignupAttempt).count() == 0
    finally:
        db.close()

    # Registrierung mit gültigem Datum bleibt möglich
    assert client.post(
        "/api/auth/register", json=_payload("1990-01-01", "typo.fix@example.com"), headers=device
    ).status_code == 200


def test_single_underage_submission_stays_correctable(client):
    """Ein Tippfehler beim Abschicken bleibt sofort korrigierbar."""
    device = {"X-Device-Id": "test-device-underage-1"}
    seventeen = (date.today().replace(year=date.today().year - 17)).isoformat()

    first = client.post(
        "/api/auth/register", json=_payload(seventeen, "vertippt@example.com"), headers=device
    )
    assert first.status_code == 403
    assert first.json()["detail"]["code"] == "underage"

    corrected = client.post(
        "/api/auth/register", json=_payload("1990-01-01", "korrigiert@example.com"), headers=device
    )
    assert corrected.status_code == 200


def test_repeated_underage_submissions_block_the_device(client):
    """Systematisches Ausprobieren der Altersgrenze läuft in die Sperre."""
    from datetime import datetime, timedelta

    from app.models import UnderageSignupAttempt
    from tests.conftest import TestingSessionLocal

    device = {"X-Device-Id": "test-device-underage-2"}
    seventeen = (date.today().replace(year=date.today().year - 17)).isoformat()

    resp = client.post("/api/auth/register", json=_payload(seventeen, "m1@example.com"), headers=device)
    assert resp.status_code == 403

    # Der zweite Versuch muss außerhalb des Entprell-Fensters liegen, sonst
    # zählt er als Wiederholung derselben Eingabe.
    db = TestingSessionLocal()
    try:
        entry = db.query(UnderageSignupAttempt).first()
        entry.created_at = datetime.utcnow() - timedelta(minutes=5)
        db.commit()
    finally:
        db.close()

    resp = client.post("/api/auth/register", json=_payload(seventeen, "m2@example.com"), headers=device)
    assert resp.status_code == 403

    # Ab jetzt ist auch ein volljähriges Datum von diesem Gerät gesperrt
    resp = client.post(
        "/api/auth/register", json=_payload("1990-01-01", "danach2@example.com"), headers=device
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "signup_blocked"


def test_double_submit_counts_as_one_attempt(client):
    """Doppelklick oder Wiederholung nach Netzfehler darf nicht sperren."""
    from app.models import UnderageSignupAttempt
    from tests.conftest import TestingSessionLocal

    device = {"X-Device-Id": "test-device-doppelklick"}
    seventeen = (date.today().replace(year=date.today().year - 17)).isoformat()

    for email in ("d1@example.com", "d2@example.com", "d3@example.com"):
        assert client.post(
            "/api/auth/register", json=_payload(seventeen, email), headers=device
        ).json()["detail"]["code"] == "underage"

    db = TestingSessionLocal()
    try:
        assert db.query(UnderageSignupAttempt).count() == 1
    finally:
        db.close()

    # Korrektur bleibt möglich
    assert client.post(
        "/api/auth/register", json=_payload("1990-01-01", "danach3@example.com"), headers=device
    ).status_code == 200


def test_underage_attempts_store_no_personal_data(client):
    """Protokolliert wird nur, DASS ein Versuch stattfand - kein Geburtsdatum,
    keine E-Mail, kein Name."""
    from app.models import UnderageSignupAttempt
    from tests.conftest import TestingSessionLocal

    device = {"X-Device-Id": "test-device-underage-3"}
    seventeen = (date.today().replace(year=date.today().year - 17)).isoformat()
    client.post("/api/auth/register", json=_payload(seventeen, "x@example.com"), headers=device)

    db = TestingSessionLocal()
    try:
        rows = db.query(UnderageSignupAttempt).all()
        assert len(rows) == 1
        columns = {c.name for c in UnderageSignupAttempt.__table__.columns}
        assert columns == {"id", "device_id", "created_at"}
    finally:
        db.close()
