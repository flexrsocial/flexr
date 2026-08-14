"""E-Mail-Bestätigung per Aktivierungslink.

Geprüft wird, DASS die Mail an die richtige Adresse geht, dass der Link
funktioniert und dass er die Alters- und Identitätsprüfung tatsächlich sperrt,
solange er nicht geklickt wurde - nicht, ob ein echter Mailserver sie annimmt.
Der Versand selbst läuft über app/mailer.send_email und ist hier gemockt.
"""

from datetime import datetime, timedelta

from app import mailer
from app.email_verification import TOKEN_TTL_HOURS, hash_token
from tests.conftest import GYM_WIEN, TestingSessionLocal, register_raw


def _register(client, email="neu@example.com", name="Neu Nutzer"):
    return client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "name": name,
            "birthdate": "1995-03-10",
            "plz": "1010",
            "city": "Wien",
            "gender": "mann",
            "gym": GYM_WIEN,
            "consent_sensitive_data": True,
            "consent_withdrawal_waiver": True,
        },
    )


def _abgefangene_mails(monkeypatch):
    """Faengt den Versand ab und stellt einen versandfaehigen Server dar.

    Beides gehoert zusammen: Ohne SMTP-Zugangsdaten verlangt der Server die
    Bestaetigung gar nicht erst (siehe verification.email_confirmation_enforced) -
    in den Tests hier soll sie aber verlangt werden.
    """
    from app.routers import verification as verification_router

    verschickt = []
    monkeypatch.setattr(
        mailer,
        "send_email",
        lambda **kwargs: verschickt.append(kwargs) or True,
    )
    monkeypatch.setattr(verification_router, "email_configured", lambda: True)
    return verschickt


def _token_aus(mail):
    """Zieht den Token aus dem Link in der Mail - so, wie ein Nutzer klickt."""
    marke = "?token="
    start = mail["text_body"].index(marke) + len(marke)
    return mail["text_body"][start:].split()[0]


def test_registrierung_verschickt_bestaetigungsmail(client, monkeypatch):
    verschickt = _abgefangene_mails(monkeypatch)

    resp = _register(client)
    assert resp.status_code == 200

    assert len(verschickt) == 1
    mail = verschickt[0]
    assert mail["to_address"] == "neu@example.com"
    assert "Bestätige" in mail["subject"]
    assert "Neu Nutzer" in mail["text_body"]
    # Der Kern der Mail: ein klickbarer Link mit Token.
    assert "/mail-bestaetigen?token=" in mail["text_body"]
    assert "/mail-bestaetigen?token=" in mail["html_body"]
    # Und der Ausblick auf das, was danach kommt - im aktuellen Wortlaut.
    assert "Live-Selfie" in mail["text_body"]
    assert "Lichtbildausweis" in mail["text_body"]


def test_token_liegt_nur_als_hash_in_der_datenbank(client, monkeypatch):
    """Der Token im Link ist ein Passwort auf Zeit."""
    verschickt = _abgefangene_mails(monkeypatch)
    _register(client, email="hash@example.com")
    token = _token_aus(verschickt[0])

    from app.models import EmailVerification

    db = TestingSessionLocal()
    try:
        eintrag = db.query(EmailVerification).one()
        assert eintrag.token_hash != token
        assert eintrag.token_hash == hash_token(token)
    finally:
        db.close()


def test_link_bestaetigt_die_adresse(client, monkeypatch):
    verschickt = _abgefangene_mails(monkeypatch)
    _register(client, email="klick@example.com")
    token = _token_aus(verschickt[0])

    resp = client.post("/api/auth/email/confirm", json={"token": token})
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == "klick@example.com"
    assert resp.json()["confirmed"] is True


def test_zweiter_klick_auf_denselben_link_scheitert(client, monkeypatch):
    """Der Token wird beim Einlösen verbraucht."""
    verschickt = _abgefangene_mails(monkeypatch)
    _register(client, email="zweimal@example.com")
    token = _token_aus(verschickt[0])

    assert client.post("/api/auth/email/confirm", json={"token": token}).status_code == 200
    zweiter = client.post("/api/auth/email/confirm", json={"token": token})
    assert zweiter.status_code == 400
    assert "ungültig" in zweiter.json()["detail"]


def test_abgelaufener_link_wird_abgelehnt(client, monkeypatch):
    verschickt = _abgefangene_mails(monkeypatch)
    _register(client, email="abgelaufen@example.com")
    token = _token_aus(verschickt[0])

    from app.models import EmailVerification

    db = TestingSessionLocal()
    try:
        eintrag = db.query(EmailVerification).one()
        eintrag.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    resp = client.post("/api/auth/email/confirm", json={"token": token})
    assert resp.status_code == 400
    assert "abgelaufen" in resp.json()["detail"]


def test_erfundener_token_wird_abgelehnt(client):
    resp = client.post("/api/auth/email/confirm", json={"token": "a" * 43})
    assert resp.status_code == 400


def test_pruefung_startet_erst_nach_bestaetigter_adresse(client, monkeypatch):
    """Die eigentliche Sperre: kein Selfie, keine Ausweisaufnahme vorher.

    Ein Mensch soll keine Ausweisaufnahme begutachten, solange nicht feststeht,
    dass die Adresse dem Nutzer gehört.
    """
    verschickt = _abgefangene_mails(monkeypatch)
    headers = register_raw(client, "gesperrt@example.com", confirm_email=False)

    gesperrt = client.post("/api/verification/start", headers=headers)
    assert gesperrt.status_code == 400
    assert "E-Mail" in gesperrt.json()["detail"]

    status = client.get("/api/verification/status", headers=headers).json()
    assert status["email_verified"] is False

    client.post("/api/auth/email/confirm", json={"token": _token_aus(verschickt[0])})

    status = client.get("/api/verification/status", headers=headers).json()
    assert status["email_verified"] is True
    # Jetzt scheitert der Start nur noch am fehlenden Profilfoto - also am
    # nächsten Schritt, nicht mehr an der Adresse.
    weiter = client.post("/api/verification/start", headers=headers)
    assert weiter.status_code == 400
    assert "Profilfoto" in weiter.json()["detail"]


def test_neuer_link_entwertet_den_alten(client, monkeypatch):
    verschickt = _abgefangene_mails(monkeypatch)
    headers = register_raw(client, "neuerlink@example.com", confirm_email=False)
    alter_token = _token_aus(verschickt[0])

    resp = client.post("/api/auth/email/resend", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["valid_hours"] == TOKEN_TTL_HOURS
    assert len(verschickt) == 2

    assert client.post("/api/auth/email/confirm", json={"token": alter_token}).status_code == 400
    neuer_token = _token_aus(verschickt[1])
    assert client.post("/api/auth/email/confirm", json={"token": neuer_token}).status_code == 200


def test_resend_fuer_bestaetigte_adresse_wird_abgelehnt(client, monkeypatch):
    _abgefangene_mails(monkeypatch)
    headers = register_raw(client, "schonfertig@example.com")

    resp = client.post("/api/auth/email/resend", headers=headers)
    assert resp.status_code == 400
    assert "bereits bestätigt" in resp.json()["detail"]


def test_profil_meldet_den_bestaetigungsstand(client, monkeypatch):
    verschickt = _abgefangene_mails(monkeypatch)
    headers = register_raw(client, "stand@example.com", confirm_email=False)

    assert client.get("/api/profiles/me", headers=headers).json()["email_verified"] is False
    client.post("/api/auth/email/confirm", json={"token": _token_aus(verschickt[0])})
    assert client.get("/api/profiles/me", headers=headers).json()["email_verified"] is True


def test_registrierung_laeuft_auch_ohne_mailserver_durch(client, monkeypatch):
    """Ein kaputter Mailserver darf die Registrierung nicht kippen."""

    def kaputt(*args, **kwargs):
        raise OSError("SMTP nicht erreichbar")

    monkeypatch.setattr(mailer.smtplib, "SMTP", kaputt)
    monkeypatch.setattr(mailer.settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(mailer.settings, "smtp_from", "noreply@flexr.social")

    resp = _register(client, email="robust@example.com")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_name_wird_im_html_maskiert():
    html = mailer._verify_html(
        "<script>alert(1)</script>", "https://flexr.social/mail-bestaetigen?token=x", 24
    )
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_ohne_smtp_blockiert_die_bestaetigung_niemanden(client, monkeypatch):
    """Ohne Mailversand darf die Bestätigung nicht verlangt werden.

    Der Mailer schreibt ohne SMTP-Zugangsdaten nur ins Log. Würde /start
    trotzdem eine bestätigte Adresse verlangen, käme ein frisch registriertes
    Konto nie aus dem Wartezustand heraus - es gäbe keinen Link zum Anklicken.
    Genau dieser Zustand herrschte auf dem Server (dort ist kein SMTP gesetzt),
    weshalb diese Weiche vor dem ersten Deploy eingebaut wurde.
    """
    from app.routers import verification as verification_router
    from tests.conftest import add_approved_photo

    monkeypatch.setattr(verification_router, "email_configured", lambda: False)

    headers = register_raw(client, "ohne-smtp@example.com", confirm_email=False)
    add_approved_photo(client, headers)

    status = client.get("/api/verification/status", headers=headers).json()
    assert status["email_verified"] is True, "ohne Mailversand steht keine Bestätigung an"

    assert client.post("/api/verification/start", headers=headers).status_code == 200


def test_mit_smtp_bleibt_die_bestaetigung_pflicht(client, monkeypatch):
    from app.routers import verification as verification_router
    from tests.conftest import add_approved_photo

    monkeypatch.setattr(verification_router, "email_configured", lambda: True)

    headers = register_raw(client, "mit-smtp@example.com", confirm_email=False)
    add_approved_photo(client, headers)

    status = client.get("/api/verification/status", headers=headers).json()
    assert status["email_verified"] is False

    resp = client.post("/api/verification/start", headers=headers)
    assert resp.status_code == 400
    assert "E-Mail" in resp.json()["detail"]
