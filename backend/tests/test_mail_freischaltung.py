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


def test_freischaltung_sagt_wenn_die_fotos_noch_in_pruefung_sind(monkeypatch):
    """Fotos werden getrennt moderiert (14.10.2026): Wer freigeschaltet ist,
    aber noch kein freigegebenes Foto hat, erscheint in keiner Suche - die
    Freischalt-Mail sagt das, statt nur "Jetzt loslegen"."""
    gesendet = _abfangen(monkeypatch)
    mailer.send_verification_decision("a@example.com", "Anna", "approved", lang="de", photos_pending=True)
    mailer.send_verification_decision("a@example.com", "Anna", "approved", lang="en", photos_pending=True)
    mailer.send_verification_decision("a@example.com", "Anna", "approved", lang="de")

    _, text_de, html_de = gesendet[0]
    assert "Deine Profilfotos werden noch geprüft" in text_de
    assert "Deine Profilfotos werden noch geprüft" in html_de
    assert "you appear in the search" in gesendet[1][1]
    assert "Profilfotos werden noch geprüft" not in gesendet[2][1]


def test_foto_ablehnung_sagt_wenn_kein_foto_mehr_frei_ist(monkeypatch):
    gesendet = _abfangen(monkeypatch)
    mailer.send_photo_rejected("a@example.com", "Anna", "Keine Person erkennbar.", "de", hidden=True)
    mailer.send_photo_rejected("a@example.com", "Anna", "Keine Person erkennbar.", "de")

    # Der Klartext ist auf 76 Zeichen umbrochen.
    def text(i):
        return " ".join(gesendet[i][1].split())

    assert "in der Suche nicht sichtbar" in text(0)
    assert "in der Suche nicht sichtbar" in gesendet[0][2]
    assert "in der Suche nicht sichtbar" not in text(1)
