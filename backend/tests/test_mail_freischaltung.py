"""Freischalt- und Nachbesserungs-Mail fuehren mit einem Knopf direkt in die
Web-App (14.10.2026). Vorher stand dort nur "Oeffne FLEXR" ohne Link."""

from app import mailer
from app.config import settings


def _abfangen(monkeypatch):
    gesendet = []
    monkeypatch.setattr(
        mailer, "send_email_with_retry",
        lambda an, betreff, text, html_text, **kw: gesendet.append((betreff, text, html_text)) or True,
    )
    return gesendet


def test_freischaltung_hat_knopf_zur_app(monkeypatch):
    gesendet = _abfangen(monkeypatch)
    monkeypatch.setattr(settings, "frontend_url", "https://flexr.social")
    mailer.send_verification_decision("a@example.com", "Anna", "approved", lang="de")

    betreff, text, html_text = gesendet[0]
    assert 'href="https://flexr.social/app/"' in html_text
    assert "Jetzt loslegen" in html_text
    assert "Jetzt loslegen: https://flexr.social/app/" in text


def test_freischaltung_englisch(monkeypatch):
    gesendet = _abfangen(monkeypatch)
    mailer.send_verification_decision("a@example.com", "Anna", "approved", lang="en")
    assert "Get started" in gesendet[0][2]


def test_nachbesserung_hat_knopf_ablehnung_nicht(monkeypatch):
    gesendet = _abfangen(monkeypatch)
    mailer.send_verification_decision("a@example.com", "Anna", "reupload_required", reason="unscharf")
    mailer.send_verification_decision("a@example.com", "Anna", "rejected", reason="Ausweis abgelaufen")
    assert "Neue Aufnahme machen" in gesendet[0][2]
    assert "/app/" not in gesendet[1][2]
