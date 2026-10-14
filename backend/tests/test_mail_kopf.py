"""Kopf aller HTML-Mails: Stichzeile links, FLEXR-Wortmarke rechts oben
(Wunsch des Betreibers, 14.10.2026).

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
    assert 'src="https://flexr.social/icons/mail-logo-v1.png"' in html_body
    assert 'alt="FLEXR"' in html_body
    # Logo steht im Kopf, vor der Ueberschrift - nicht irgendwo im Text.
    assert html_body.index("mail-logo-v1.png") < html_body.index("<h1")
    assert html_body.count("mail-logo-v1.png") == 1


def test_logodatei_liegt_dort_wo_nginx_ausliefert():
    """/brand/ sperrt nginx (deploy/nginx-flexr.conf), /icons/ liefert es aus."""
    from PIL import Image

    datei = FRONTEND / mailer.MAIL_LOGO_PATH
    assert datei.is_file()
    breite, hoehe = Image.open(datei).size
    # width="120" height="33" im Mailkopf: dasselbe Seitenverhaeltnis
    assert abs(breite / hoehe - 120 / 33) < 0.05
    nginx = (FRONTEND.parent / "deploy" / "nginx-flexr.conf").read_text(encoding="utf-8")
    assert "location /icons/" in nginx
