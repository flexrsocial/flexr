"""Kopf aller HTML-Mails: Stichzeile links, Logo rechts oben (Wunsch des
Betreibers, 14.10.2026; seit 15.10.2026 das App-Icon statt der Wortmarke).

Gmail unter Android zeigte das Icon mit weisser Kachel: Die App dunkelt Mails
mit dem Chromium-Dunkelmodus ab, und der invertiert farbarme Bilder bis
64 x 64 CSS-px als "Icon". Darum ist das Bild 80 x 44 gross (Kachel rechts,
links durchsichtig) - test_logo_ist_fuer_den_dunkelmodus_kein_icon.

Es gibt drei HTML-Gerueste in app/mailer.py (_email_shell, _verify_html,
_decision_html). Geprueft wird ueber die versendeten Mails, nicht ueber die
Gerueste - so faellt auch ein kuenftiges viertes Geruest ohne Logo auf.
"""

from datetime import datetime
from pathlib import Path

import pytest

from app import mailer
from app.config import settings

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
TS = 1792000000

FAELLE = {
    "verification": lambda l: mailer.send_verification_email("a@b.c", "Anna", "https://x/y", 24, l),
    "newemail": lambda l: mailer.send_new_email_confirmation("a@b.c", "Anna", "https://x/y", 24, l),
    "reset": lambda l: mailer.send_password_reset("a@b.c", "Anna", "https://x/y", 30, l),
    "pwchanged": lambda l: mailer.send_password_changed("a@b.c", "Anna", l),
    "emailchanged": lambda l: mailer.send_email_changed("a@b.c", "Anna", "neu@b.c", l),
    "subconfirm": lambda l: mailer.send_subscription_confirmation("a@b.c", "Anna", l),
    "trialending": lambda l: mailer.send_trial_ending("a@b.c", "Anna", TS, l),
    "renewal": lambda l: mailer.send_renewal_reminder("a@b.c", "Anna", 1000, "eur", TS, l),
    "paid": lambda l: mailer.send_payment_succeeded("a@b.c", "Anna", 1000, "eur", None, l),
    "failed": lambda l: mailer.send_payment_failed("a@b.c", "Anna", 1000, "eur", TS, None, l),
    "cancelsched": lambda l: mailer.send_cancellation_scheduled("a@b.c", "Anna", TS, l),
    "subended": lambda l: mailer.send_subscription_ended("a@b.c", "Anna", l),
    "match": lambda l: mailer.send_new_match("a@b.c", "Anna", "Ben", l),
    "queue": lambda l: mailer.send_queue_waiting("a@b.c", "Anna", 3, l),
    "likes": lambda l: mailer.send_pending_likes("a@b.c", "Anna", 5, l),
    "inactive": lambda l: mailer.send_inactivity_reminder("a@b.c", "Anna", 8, l),
    "deletion": lambda l: mailer.send_account_deletion_confirmation(
        "a@b.c", "Anna", datetime(2026, 11, 13, 10, 0), 30, l),
    "verif_ok": lambda l: mailer.send_verification_decision("a@b.c", "Anna", "approved", None, False, l),
    "verif_no": lambda l: mailer.send_verification_decision("a@b.c", "Anna", "rejected", "x", False, l),
    "verifreq": lambda l: mailer.send_verification_required("a@b.c", "Anna", l),
    "verifremind": lambda l: mailer.send_verification_reminder("a@b.c", "Anna", "document", 2, l),
    "moderation": lambda l: mailer.send_moderation_decision("a@b.c", "Anna", "M", "Z", ["D"], True, l),
    "photorej": lambda l: mailer.send_photo_rejected("a@b.c", "Anna", "Grund", l),
    "report": lambda l: mailer.send_report_decision("a@b.c", "FX-1", "o", "r", l, name="Anna"),
    "withdrawal": lambda l: mailer.send_withdrawal_confirmation(
        "a@b.c", "Anna", "RT-1", "14.10.2026", "Text", "sub_1", True, l),
    "notice": lambda l: mailer.send_notice_acknowledgement("a@b.c", "DSA-1", "14.10.2026", "B", l, name="Anna"),
}


@pytest.fixture
def gesendet(monkeypatch):
    liste = []

    def fake(to_address, subject, text_body, html_body=None, **_):
        liste.append(html_body or "")
        return True

    monkeypatch.setattr(mailer, "send_email", fake)
    monkeypatch.setattr(mailer, "send_email_with_retry", fake)
    monkeypatch.setattr(settings, "frontend_url", "https://flexr.social")
    return liste


def test_es_werden_alle_mailarten_geprueft():
    """Kommt eine neue send_*-Funktion dazu, gehoert sie hier in FAELLE."""
    alle = {n for n in dir(mailer) if n.startswith("send_")} - {"send_email", "send_email_with_retry"}
    geprueft = {n for f in FAELLE.values() for n in f.__code__.co_names if n.startswith("send_")}
    assert alle == geprueft, sorted(alle ^ geprueft)


@pytest.mark.parametrize("fall", sorted(FAELLE))
@pytest.mark.parametrize("lang", ["de", "en"])
def test_jede_mail_traegt_das_logo_rechts_oben(gesendet, fall, lang):
    FAELLE[fall](lang)
    html_body = gesendet[-1]
    assert 'src="https://flexr.social/icons/mail-icon-v2.png"' in html_body
    assert 'alt="FLEXR"' in html_body
    assert 'width="80" height="44"' in html_body
    # Logo steht im Kopf, vor der Ueberschrift - nicht irgendwo im Text.
    assert html_body.index("mail-icon-v2.png") < html_body.index("<h1")
    assert html_body.count("mail-icon-v2.png") == 1
    # Die Karte traegt Schrift und Textfarbe selbst - falls der Webmailer
    # die Stile am <body> verwirft (siehe _email_shell).
    assert 'padding:28px;font-family:Helvetica,Arial,sans-serif;color:#e8e8ea;"' in html_body


def test_logo_ist_fuer_den_dunkelmodus_kein_icon():
    """Chromium (Android-WebView, also die Gmail-App) haelt ein Bild fuer ein
    Icon, wenn es in beiden Richtungen hoechstens 64 CSS-px gross gezeichnet
    wird, und invertiert es dann im erzwungenen Dunkelmodus. Gemessen am
    15.10.2026: 64 x 64 wird invertiert, 66 x 44 nicht. Eine Seite muss
    also deutlich darueber liegen."""
    assert max(mailer.MAIL_LOGO_BREITE, mailer.MAIL_LOGO_HOEHE) >= 72


def test_logodatei_liegt_dort_wo_nginx_ausliefert():
    """/brand/ sperrt nginx (deploy/nginx-flexr.conf), /icons/ liefert es aus."""
    from PIL import Image

    datei = FRONTEND / mailer.MAIL_LOGO_PATH
    assert datei.is_file()
    bild = Image.open(datei)
    breite, hoehe = bild.size
    # Seitenverhaeltnis wie im Mailkopf, mindestens doppelt so viele Pixel
    # fuer hochaufloesende Displays.
    assert breite * mailer.MAIL_LOGO_HOEHE == hoehe * mailer.MAIL_LOGO_BREITE
    assert hoehe >= 2 * mailer.MAIL_LOGO_HOEHE
    assert bild.mode == "RGBA"
    # Links neben der Kachel ist alles durchsichtig, die Ecken der Kachel
    # auch (Outlook kennt kein border-radius); die Mitte der Kachel deckt.
    kachel_links = breite - hoehe
    assert max(bild.getpixel((x, y))[3] for x in range(kachel_links) for y in range(hoehe)) == 0
    assert bild.getpixel((kachel_links, 0))[3] < 32
    assert bild.getpixel((breite - 1, hoehe - 1))[3] < 32
    assert bild.getpixel((breite - hoehe // 2, hoehe // 2))[3] == 255
    # Die frueheren Fassungen bleiben liegen - bereits verschickte Mails
    # laden sie weiter.
    assert (FRONTEND / "icons" / "mail-logo-v1.png").is_file()
    assert (FRONTEND / "icons" / "mail-icon-v1.png").is_file()
    nginx = (FRONTEND.parent / "deploy" / "nginx-flexr.conf").read_text(encoding="utf-8")
    assert "location /icons/" in nginx
