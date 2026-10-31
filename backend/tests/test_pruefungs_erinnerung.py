"""Erinnerung an eine angefangene Alters- und Identitaetspruefung.

Anlass (31.10.2026): Zwei neue Konten hatten Profilfotos und Selfie, aber nie
einen Ausweis hochgeladen - und keine Mail holte sie zurueck.
"""

import json
from datetime import datetime, timedelta

from app.email_jobs import run_activity_notifications, run_due_email_jobs, run_verification_reminders
from app.models import Photo, PhotoStatus, User, VerificationRequest, VerificationStatus
from app.timeutil import utcnow
from tests.conftest import (
    TestingSessionLocal,
    add_required_photos,
    register_raw,
    register_user,
)

NOW = datetime(2026, 8, 20, 7, 0, 0)  # 09:00 Uhr in Wien (MESZ), Laufzeit des Tagesjobs

SELFIES = json.dumps([{"prompt": "Schau direkt in die Kamera", "object_key": "users/x/verify/a.jpg"}])


def _user_id(client, headers):
    return client.get("/api/profiles/me", headers=headers).json()["id"]


def _set_user(user_id, **fields):
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        for key, value in fields.items():
            setattr(user, key, value)
        db.commit()
    finally:
        db.close()


def _add_request(user_id, status, selfies=None, **fields):
    db = TestingSessionLocal()
    try:
        req = VerificationRequest(
            user_id=user_id,
            status=status,
            prompts=json.dumps(["Schau direkt in die Kamera"]),
            selfies=selfies,
            **fields,
        )
        db.add(req)
        db.commit()
        return req.id
    finally:
        db.close()


def _set_request(req_id, **fields):
    db = TestingSessionLocal()
    try:
        req = db.query(VerificationRequest).filter(VerificationRequest.id == req_id).one()
        for key, value in fields.items():
            setattr(req, key, value)
        db.commit()
    finally:
        db.close()


def _stuck(client, email, *, photos=True, inactive=timedelta(days=1)):
    """Konto mit bestaetigter Adresse, noch nicht freigeschaltet, seit
    ``inactive`` nicht mehr aktiv."""
    headers = register_raw(client, email, name=email.split("@")[0])
    if photos:
        add_required_photos(client, headers)
    user_id = _user_id(client, headers)
    _set_user(user_id, last_active_at=NOW - inactive)
    return user_id


def _run(at=NOW):
    db = TestingSessionLocal()
    try:
        return run_verification_reminders(db, at)
    finally:
        db.close()


def _capture(monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_verification_reminder",
        lambda email, name, step, missing=0, lang="de": mails.append((email, step, missing)) or True,
    )
    return mails


def test_selfie_da_ausweis_fehlt_genau_eine_erinnerung(client, monkeypatch):
    mails = _capture(monkeypatch)
    user_id = _stuck(client, "ausweis@example.com")
    _add_request(user_id, VerificationStatus.id_required, selfies=SELFIES)

    assert _run() == {"verification_reminded": 1}
    assert mails == [("ausweis@example.com", "document", 0)]

    # Die folgenden Tageslaeufe schicken nichts mehr - auch nicht, solange
    # das Konto in der Frist bleibt.
    for tag in range(1, 6):
        assert _run(NOW + timedelta(days=tag)) == {"verification_reminded": 0}
    assert len(mails) == 1


def test_neuer_schritt_neue_erinnerung(client, monkeypatch):
    """Erinnert beim Selfie; wer es danach macht und wieder haengen bleibt,
    wird beim Ausweis noch einmal erinnert."""
    mails = _capture(monkeypatch)
    user_id = _stuck(client, "schritt@example.com")
    req_id = _add_request(user_id, VerificationStatus.in_progress)

    _run()
    assert mails == [("schritt@example.com", "selfie", 0)]

    _set_request(req_id, status=VerificationStatus.id_required, selfies=SELFIES)
    _set_user(user_id, last_active_at=NOW + timedelta(days=1))
    _run(NOW + timedelta(days=2))
    assert mails[-1] == ("schritt@example.com", "document", 0)

    # Der Pruefer fordert einen neuen Ausweis an - wieder ein offener Schritt.
    _set_request(req_id, status=VerificationStatus.reupload_required)
    _set_user(user_id, last_active_at=NOW + timedelta(days=3))
    _run(NOW + timedelta(days=4))
    assert mails[-1] == ("schritt@example.com", "document", 0)
    assert len(mails) == 3


def test_pruefung_nie_gestartet_erinnert_an_selfie(client, monkeypatch):
    mails = _capture(monkeypatch)
    _stuck(client, "nie@example.com")

    _run()
    assert mails == [("nie@example.com", "selfie", 0)]


def test_fehlende_fotos_werden_genannt(client, monkeypatch):
    """Wie bei Juergen am 30.10.2026: Selfie da, aber nur noch ein gueltiges
    Foto. Der Pruefbildschirm verlangt erst die Fotos - die Mail auch."""
    mails = _capture(monkeypatch)
    user_id = _stuck(client, "foto@example.com", photos=False)
    db = TestingSessionLocal()
    try:
        # Ein freigegebenes und ein abgelehntes Foto - abgelehnte zaehlen nicht.
        db.add(Photo(user_id=user_id, url="https://cdn.example.test/a.jpg", position=0,
                     status=PhotoStatus.approved))
        db.add(Photo(user_id=user_id, url="https://cdn.example.test/b.jpg", position=1,
                     status=PhotoStatus.rejected))
        db.commit()
    finally:
        db.close()
    _add_request(user_id, VerificationStatus.id_required, selfies=SELFIES)

    _run()
    assert mails == [("foto@example.com", "document", 2)]


def test_nicht_zu_frueh_und_nicht_ewig(client, monkeypatch):
    mails = _capture(monkeypatch)
    frisch = _stuck(client, "frisch@example.com", inactive=timedelta(hours=12))
    alt = _stuck(client, "alt@example.com", inactive=timedelta(days=15))
    _add_request(frisch, VerificationStatus.id_required, selfies=SELFIES)
    _add_request(alt, VerificationStatus.id_required, selfies=SELFIES)

    _run()
    assert mails == []

    # Am naechsten Morgen ist das frische Konto faellig.
    _run(NOW + timedelta(days=1))
    assert mails == [("frisch@example.com", "document", 0)]


def test_keine_erinnerung_wenn_nichts_zu_tun_ist(client, monkeypatch):
    mails = _capture(monkeypatch)

    eingereicht = _stuck(client, "eingereicht@example.com")
    _add_request(eingereicht, VerificationStatus.submitted, selfies=SELFIES,
                 submitted_at=NOW - timedelta(days=1))

    # Entschieden nach der Registrierung (die laeuft im Test zur echten Uhrzeit,
    # nicht zu NOW) - damit ist die Ablehnung bindend.
    abgelehnt = _stuck(client, "abgelehnt@example.com")
    _add_request(abgelehnt, VerificationStatus.rejected, selfies=None,
                 decided_at=utcnow())

    unbestaetigt = _stuck(client, "unbestaetigt@example.com")
    _set_user(unbestaetigt, email_verified_at=None)

    geloescht = _stuck(client, "geloescht@example.com")
    _set_user(geloescht, deleted_at=NOW - timedelta(hours=1))

    gesperrt = _stuck(client, "gesperrt@example.com")
    _set_user(gesperrt, is_banned=True)

    freigeschaltet_headers = register_user(client, "frei@example.com")
    _set_user(_user_id(client, freigeschaltet_headers), last_active_at=NOW - timedelta(days=2))

    _run()
    assert mails == []


def test_neu_angeforderte_pruefung_beginnt_beim_selfie(client, monkeypatch):
    """Bestandskonto, das ein Admin nach einer frueheren Freigabe erneut in die
    Pruefung holt: Die alte Entscheidung blockiert nicht."""
    mails = _capture(monkeypatch)
    user_id = _stuck(client, "nachgefordert@example.com")
    _add_request(user_id, VerificationStatus.approved, decided_at=NOW - timedelta(days=30))
    _set_user(user_id, verification_required_at=NOW - timedelta(days=2))

    _run()
    assert mails == [("nachgefordert@example.com", "selfie", 0)]


def test_gescheiterter_versand_wird_am_naechsten_tag_wiederholt(client, monkeypatch):
    versuche = []
    monkeypatch.setattr(
        "app.email_jobs.mailer.send_verification_reminder",
        lambda email, name, step, missing=0, lang="de": versuche.append(email) or len(versuche) > 1,
    )
    user_id = _stuck(client, "wackelig@example.com")
    _add_request(user_id, VerificationStatus.id_required, selfies=SELFIES)

    assert _run() == {"verification_reminded": 0}
    assert _run(NOW + timedelta(days=1)) == {"verification_reminded": 1}
    assert _run(NOW + timedelta(days=2)) == {"verification_reminded": 0}
    assert versuche == ["wackelig@example.com", "wackelig@example.com"]


def test_nicht_freigeschaltete_bekommen_keine_inaktivitaetsmail(client, monkeypatch):
    """Vorher ging nach sieben Tagen "Lange nicht gesehen, neue Profile
    warten" an Konten, die gar kein Deck haben."""
    inaktiv = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_inactivity_reminder",
        lambda email, name, days, lang="de": inaktiv.append(email) or True,
    )
    _stuck(client, "wartend@example.com", inactive=timedelta(days=8))

    db = TestingSessionLocal()
    try:
        run_activity_notifications(db, NOW)
    finally:
        db.close()
    assert inaktiv == []


def test_tagesjob_meldet_den_zaehler(client, monkeypatch):
    _capture(monkeypatch)
    user_id = _stuck(client, "zaehler@example.com")
    _add_request(user_id, VerificationStatus.id_required, selfies=SELFIES)

    db = TestingSessionLocal()
    try:
        result = run_due_email_jobs(db, now=NOW)
    finally:
        db.close()
    assert result["verification_reminded"] == 1
    assert result["failed"] == 0


# --- Inhalt der Mail ---------------------------------------------------------

def _sent_mail(monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.mailer.send_email",
        lambda to, subject, text, html=None: sent.append((to, subject, text, html)) or True,
    )
    return sent


def test_mail_nennt_den_fehlenden_ausweis(monkeypatch):
    from app import mailer

    sent = _sent_mail(monkeypatch)
    assert mailer.send_verification_reminder("a@example.com", "Goran", "document")
    to, subject, text, html = sent[0]
    assert subject == "Dein FLEXR-Konto ist fast startklar"
    assert "Hallo Goran," in text
    assert "es fehlt nur noch ein Foto deines Ausweises" in text
    assert "/app/open/" in text and "/app/open/" in html
    assert "schwärzen" in text
    assert "Konto in der" in text  # Ausstieg ueber die Kontoloeschung


def test_mail_nennt_fehlende_fotos_zuerst(monkeypatch):
    from app import mailer

    sent = _sent_mail(monkeypatch)
    mailer.send_verification_reminder("j@example.com", "Jürgen", "document", missing_photos=2)
    text = sent[0][2].replace("\n", " ")
    assert "bitte lade noch 2 weitere hoch" in text
    assert "Danach fehlt nur noch ein Foto deines Ausweises." in text


def test_mail_auf_englisch(monkeypatch):
    from app import mailer

    sent = _sent_mail(monkeypatch)
    mailer.send_verification_reminder("e@example.com", "Sam", "selfie", lang="en")
    to, subject, text, html = sent[0]
    assert subject == "Your FLEXR account is almost ready"
    assert "Hi Sam," in text
    assert "a selfie and a photo of your ID" in text.replace("\n", " ")
    assert 'lang="en"' in html
