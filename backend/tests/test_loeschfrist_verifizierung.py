"""Konten ohne eingereichten Ausweis: Wochenmail mit Löschdatum, Löschung nach
30 Tagen (Regel seit 08.11.2026, siehe app/verification_deadline.py)."""

import json
from datetime import date, datetime, timedelta

import pytest

from app import cleanup, email_jobs
from app import verification_deadline as frist
from app.models import EmailNotification, Photo, User, VerificationRequest, VerificationStatus
from tests.conftest import TestingSessionLocal, add_required_photos, register_raw, register_user

# Registrierung nach Einführung der Regel, 10:00 Uhr in Wien.
REG = datetime(2026, 11, 20, 9, 0, 0)


@pytest.fixture
def mails(monkeypatch):
    gesendet = []
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_deletion_warning",
        lambda email, name, datum, lang="de": gesendet.append((email, datum)) or True,
    )
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_verification_reminder",
        lambda *a, **k: gesendet.append((a[0], "erinnerung")) or True,
    )
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_id_second_reminder",
        lambda *a, **k: gesendet.append((a[0], "zweite")) or True,
    )
    return gesendet


def _konto(client, email, created_at=REG, **felder):
    headers = register_raw(client, email, name=email.split("@")[0])
    add_required_photos(client, headers)
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        user.created_at = created_at
        user.last_active_at = created_at
        # Wie bei einer echten Registrierung (auth.register): Prüfpflicht ab
        # dem Registrierungszeitpunkt.
        user.verification_required_at = created_at
        for k, v in felder.items():
            setattr(user, k, v)
        db.commit()
        return user.id
    finally:
        db.close()


def _vorgang(user_id, status, **felder):
    db = TestingSessionLocal()
    try:
        db.add(VerificationRequest(
            user_id=user_id, status=status, prompts=json.dumps(["x"]), **felder
        ))
        db.commit()
    finally:
        db.close()


def _warnungen(at):
    db = TestingSessionLocal()
    try:
        return email_jobs.run_deletion_warnings(db, at)["deletion_warned"]
    finally:
        db.close()


def _loeschen(at):
    db = TestingSessionLocal()
    try:
        return cleanup.purge_unverified_accounts(db, now=at)
    finally:
        db.close()


def _gibt_es(user_id):
    db = TestingSessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).count() == 1
    finally:
        db.close()


def test_loeschdatum_ist_registrierung_plus_30_tage_in_wien():
    assert frist.deletion_date(REG) == date(2026, 12, 20)
    # 23:30 UTC ist in Wien schon der nächste Tag.
    assert frist.deletion_date(datetime(2026, 11, 20, 23, 30)) == date(2026, 12, 21)


def test_vier_wochenmails_dann_loeschung(client, mails):
    user_id = _konto(client, "frist@example.com")

    assert _warnungen(REG + timedelta(days=1)) == 0
    assert _warnungen(REG + timedelta(days=6)) == 0
    for woche in range(1, 5):
        assert _warnungen(REG + timedelta(days=7 * woche)) == 1
        assert _warnungen(REG + timedelta(days=7 * woche, hours=5)) == 0  # nur einmal
    assert _warnungen(REG + timedelta(days=29)) == 0
    assert [m for m in mails if m[0] == "frist@example.com"] == [
        ("frist@example.com", date(2026, 12, 20))
    ] * 4

    # Am Vortag noch nicht, am Löschtag ab Mitternacht (Wien) schon.
    assert _loeschen(datetime(2026, 12, 19, 22, 59)) == 0
    assert _gibt_es(user_id)
    assert _loeschen(datetime(2026, 12, 19, 23, 1)) == 1
    assert not _gibt_es(user_id)
    db = TestingSessionLocal()
    try:
        assert db.query(Photo).filter(Photo.user_id == user_id).count() == 0
    finally:
        db.close()


def test_ausgefallener_job_schickt_nur_die_aktuelle_woche(client, mails):
    _konto(client, "ausfall@example.com")
    assert _warnungen(REG + timedelta(days=22)) == 1  # Woche 3, nicht 1-3
    assert _warnungen(REG + timedelta(days=23)) == 0


def test_eingereichter_ausweis_stoppt_frist(client, mails):
    user_id = _konto(client, "eingereicht@example.com")
    _vorgang(user_id, VerificationStatus.submitted, submitted_at=REG + timedelta(days=3))
    assert _warnungen(REG + timedelta(days=7)) == 0
    assert _loeschen(REG + timedelta(days=60)) == 0
    assert _gibt_es(user_id)


def test_bindend_abgelehnt_wird_nicht_geloescht(client, mails):
    user_id = _konto(client, "abgelehnt@example.com")
    _vorgang(user_id, VerificationStatus.rejected, submitted_at=REG + timedelta(days=2),
             decided_at=REG + timedelta(days=3))
    assert _loeschen(REG + timedelta(days=60)) == 0


def test_freigeschaltet_und_gesperrt_bleiben(client, mails):
    aktiv = register_user(client, "aktiv@example.com")  # noqa: F841
    gesperrt = _konto(client, "gesperrt@example.com", is_banned=True)
    db = TestingSessionLocal()
    try:
        u = db.query(User).filter(User.email == "aktiv@example.com").one()
        u.created_at = REG
        db.commit()
    finally:
        db.close()
    assert _warnungen(REG + timedelta(days=7)) == 0
    assert _loeschen(REG + timedelta(days=60)) == 0
    assert _gibt_es(gesperrt)


def test_neuer_ausweis_angefordert_frist_beginnt_neu(client, mails):
    user_id = _konto(client, "neu@example.com")
    rueckfrage = REG + timedelta(days=28)
    _vorgang(user_id, VerificationStatus.reupload_required, submitted_at=None,
             decided_at=rueckfrage)
    assert _loeschen(REG + timedelta(days=31)) == 0
    assert _warnungen(rueckfrage + timedelta(days=7)) == 1
    assert mails[-1] == ("neu@example.com", frist.deletion_date(rueckfrage))
    assert _loeschen(rueckfrage + timedelta(days=30)) == 1


def test_bestandskonto_bekommt_einen_monat_ab_einfuehrung(client, mails):
    user_id = _konto(client, "alt@example.com", created_at=datetime(2026, 9, 1, 8, 0))
    # Sofort Mail 0 mit dem 08.12.2026, nicht über Nacht gelöscht.
    assert _loeschen(datetime(2026, 11, 8, 6, 0)) == 0
    assert _warnungen(datetime(2026, 11, 8, 8, 0)) == 1
    assert mails[-1] == ("alt@example.com", date(2026, 12, 8))
    assert _warnungen(datetime(2026, 11, 9, 8, 0)) == 0
    assert _warnungen(datetime(2026, 11, 15, 8, 0)) == 1
    assert _loeschen(datetime(2026, 12, 7, 12, 0)) == 0
    assert _loeschen(datetime(2026, 12, 8, 0, 0)) == 1
    assert not _gibt_es(user_id)


def test_unbestaetigte_adresse_keine_mail_aber_loeschung(client, mails):
    user_id = _konto(client, "tippfehler@example.com", email_verified_at=None)
    assert _warnungen(REG + timedelta(days=7)) == 0
    assert _loeschen(REG + timedelta(days=30)) == 1
    assert not _gibt_es(user_id)


def test_keine_zwei_mails_am_selben_morgen(client, mails):
    """Fällt die Wochenmail auf den Tag einer Schritt-Erinnerung, geht nur sie raus."""
    _konto(client, "doppelt@example.com")
    db = TestingSessionLocal()
    try:
        email_jobs.run_due_email_jobs(db, REG + timedelta(days=7))
    finally:
        db.close()
    assert [m[1] for m in mails if m[0] == "doppelt@example.com"] == [date(2026, 12, 20)]


def test_notbremse_loescht_nichts(client, mails, monkeypatch):
    monkeypatch.setattr(cleanup, "UNVERIFIED_MAX_PER_RUN", 1)
    a = _konto(client, "a@example.com")
    b = _konto(client, "b@example.com")
    with pytest.raises(cleanup.UnverifiedPurgeBlocked):
        _loeschen(REG + timedelta(days=30))
    assert _gibt_es(a) and _gibt_es(b)


def test_mail_nennt_das_loeschdatum(monkeypatch):
    from app import mailer

    gesendet = {}
    monkeypatch.setattr(
        mailer, "send_email",
        lambda to, subject, text, html_body=None, **k: gesendet.update(
            subject=subject, text=text, html=html_body) or True,
    )
    assert mailer.send_deletion_warning("x@example.com", "Alex", date(2026, 12, 8), "de")
    assert gesendet["subject"] == "Dein FLEXR-Konto wird am 08.12.2026 gelöscht"
    assert "am 08.12.2026 endgültig gelöscht" in gesendet["text"]
    assert "08.12.2026" in gesendet["html"]
    mailer.send_deletion_warning("x@example.com", "Alex", date(2026, 12, 8), "en")
    assert gesendet["subject"] == "Your FLEXR account will be deleted on 8 December 2026"


def test_datenschutz_und_agb_nennen_die_frist():
    from pathlib import Path

    from app.retention import UNVERIFIED_ACCOUNT_DAYS

    frontend = Path(__file__).resolve().parents[2] / "frontend"
    assert f"{UNVERIFIED_ACCOUNT_DAYS} Tage nach der Registrierung" in (
        frontend / "datenschutz.html").read_text(encoding="utf-8")
    assert f"{UNVERIFIED_ACCOUNT_DAYS} days after registration" in (
        frontend / "en" / "datenschutz.html").read_text(encoding="utf-8")
    assert f"{UNVERIFIED_ACCOUNT_DAYS} Tagen nach der Registrierung" in (
        frontend / "agb.html").read_text(encoding="utf-8")
    assert f"{UNVERIFIED_ACCOUNT_DAYS} days of\n      registration" in (
        frontend / "en" / "agb.html").read_text(encoding="utf-8")


def test_nachtraeglich_verlangte_pruefung_faellt_nicht_unter_die_frist(client, mails):
    """Bestandskonto, für das ein Admin die Prüfung nachfordert: keine
    Lösch-Mail, keine Löschung - es hat Matches und Chats, und AGB 5 g spricht
    von 30 Tagen nach der Registrierung."""
    user_id = _konto(
        client, "bestand@example.com",
        created_at=datetime(2026, 9, 1, 8, 0),
        verification_required_at=REG,
    )
    assert _warnungen(REG + timedelta(days=7)) == 0
    assert _loeschen(REG + timedelta(days=60)) == 0
    assert _gibt_es(user_id)
