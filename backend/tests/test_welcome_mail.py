"""Willkommensmail nach der Registrierung.

Geprüft wird, DASS die Mail an die richtige Adresse geht und zur Verifizierung
auffordert - nicht, ob ein echter Mailserver sie annimmt. Der Versand selbst
läuft über app/mailer.send_email und ist hier gemockt.
"""

from app import mailer
from tests.conftest import GYM_WIEN


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


def test_registrierung_verschickt_willkommensmail(client, monkeypatch):
    verschickt = []
    monkeypatch.setattr(
        mailer,
        "send_email",
        lambda **kwargs: verschickt.append(kwargs) or True,
    )

    resp = _register(client)
    assert resp.status_code == 200

    assert len(verschickt) == 1
    mail = verschickt[0]
    assert mail["to_address"] == "neu@example.com"
    assert "Willkommen" in mail["subject"]
    # Der Kern der Mail: die Aufforderung, die Prüfung noch zu erledigen.
    assert "Jetzt verifizieren" in mail["html_body"]
    assert "Selfies" in mail["text_body"]
    assert "Lichtbildausweis" in mail["text_body"]
    assert "Neu Nutzer" in mail["text_body"]


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
    html = mailer._welcome_html('<script>alert(1)</script>', "https://flexr.social")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
