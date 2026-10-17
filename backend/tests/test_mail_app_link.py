"""Knopf in die App in den Aktivitaets-Mails (Wunsch des Betreibers, 17.10.2026).

Neues Match, neue Profile, offene Likes und "Lange nicht gesehen" sagten nur
"in FLEXR" - ohne Link. Jetzt fuehrt ein Knopf (HTML) bzw. eine Link-Zeile
(Text) auf denselben Reiter wie die Push-Mitteilung.
"""

import pytest

from app import mailer
from app.config import settings
from app.message_texts import TEXTE

FAELLE = {
    "match": (lambda l: mailer.send_new_match("a@b.c", "Anna", "Ben", l), "matches", "match.cta"),
    "queue": (lambda l: mailer.send_queue_waiting("a@b.c", "Anna", 3, l), "swipe", "queue.cta"),
    "likes": (lambda l: mailer.send_pending_likes("a@b.c", "Anna", 5, l), "swipe", "likes.cta"),
    "inactive": (lambda l: mailer.send_inactivity_reminder("a@b.c", "Anna", 8, l), "swipe", "inactive.cta"),
}


@pytest.fixture
def gesendet(monkeypatch):
    liste = []

    def fake(to_address, subject, text_body, html_body=None, **_):
        liste.append((text_body, html_body or ""))
        return True

    monkeypatch.setattr(mailer, "send_email", fake)
    monkeypatch.setattr(settings, "frontend_url", "https://flexr.social/")
    return liste


@pytest.mark.parametrize("fall", sorted(FAELLE))
@pytest.mark.parametrize("lang", ["de", "en"])
def test_mail_fuehrt_auf_den_passenden_reiter(gesendet, fall, lang):
    senden, ziel, schluessel = FAELLE[fall]
    senden(lang)
    text, html = gesendet[-1]
    link = f"https://flexr.social/app/?open={ziel}"
    beschriftung = TEXTE[schluessel][lang]

    assert f'href="{link}"' in html
    assert f">{beschriftung}</a>" in html
    assert f"{beschriftung}: {link}" in text
