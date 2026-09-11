"""E-Mail-Versand (SMTP).

Mit konfigurierten Zugangsdaten (SMTP_HOST, SMTP_USER, SMTP_PASSWORD in der
.env) wird echt versendet - über die Standardbibliothek, ohne zusätzliche
Abhängigkeit. Ohne Zugangsdaten landet die Nachricht nur im Server-Log
(Entwicklungs-/Testbetrieb), analog zu app/sms.py.

Ein Fehlschlag beim Versand darf nie den auslösenden Vorgang kippen: Wer sich
registriert hat, ist registriert - auch wenn der Mailserver gerade streikt.
Deshalb fängt send_email() alles ab und meldet nur, ob es geklappt hat.

Jede send_*-Funktion nimmt ein lang entgegen ("de" oder "en", Vorgabe
Deutsch). Die Saetze stehen in app/message_texts.py; hier steht nur das Geruest,
das in beiden Sprachen dasselbe ist. Die Aufrufer reichen user.language
durch - bei Mails an Leute ohne Konto (Ruecktritt, DSA-Meldung) die Sprache
der Formularseite, ueber die die Erklaerung kam.
"""

import html
import logging
import smtplib
import ssl
import textwrap
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr

from . import message_texts
from .config import settings
from .message_texts import (
    STANDARD,
    TEXTE,
    format_date,
    format_datetime,
    format_money,
    normalise,
    t,
)

logger = logging.getLogger("flexr.mail")


def email_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def send_email(to_address: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """Verschickt eine Nachricht und meldet, ob der Versand geklappt hat.

    Wirft nie - Aufrufer sollen sich nicht um den Mailserver kümmern müssen.
    """
    if not email_configured():
        # Mit dem Textkörper: Sonst wäre der Aktivierungslink im Entwicklungs-
        # betrieb nirgends abgreifbar und der Ablauf gar nicht testbar. Gleiches
        # Muster wie app/sms.py, das dort den Code selbst ins Log schreibt.
        # Der Zweig läuft ausschließlich ohne konfiguriertes SMTP.
        logger.warning(
            "[MAIL-DEV] Kein SMTP konfiguriert - Mail an %s unterdrückt: %s\n%s",
            to_address,
            subject,
            text_body,
        )
        return False

    message = EmailMessage()
    message["From"] = formataddr((settings.mail_from_name, settings.smtp_from))
    message["To"] = to_address
    message["Subject"] = subject
    message["Reply-To"] = settings.support_email
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        context = ssl.create_default_context()
        if settings.smtp_ssl:
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=15, context=context
            ) as server:
                _login_and_send(server, message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                if settings.smtp_starttls:
                    server.starttls(context=context)
                _login_and_send(server, message)
    except Exception:  # noqa: BLE001 - Versand darf den Aufrufer nie kippen
        logger.exception("Mailversand an %s fehlgeschlagen (%s)", to_address, subject)
        return False

    logger.info("Mail an %s verschickt: %s", to_address, subject)
    return True


def _login_and_send(server: smtplib.SMTP, message: EmailMessage) -> None:
    if settings.smtp_user:
        server.login(settings.smtp_user, settings.smtp_password)
    server.send_message(message)


def send_email_with_retry(
    to_address: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    attempts: int = 3,
    delay_seconds: float = 5.0,
) -> bool:
    """Wie send_email(), aber mit kurzen Wiederholungen bei Fehlschlag.

    Für Bestätigungen, die gesetzlich "unverzüglich" zugehen müssen (§ 13a
    Abs. 4 FAGG): Ein einzelner Verbindungsfehler soll nicht sofort dazu
    führen, dass niemand benachrichtigt wird. Läuft synchron mit time.sleep()
    zwischen den Versuchen - unproblematisch, weil der Aufrufer diese
    Funktion selbst als BackgroundTask nach der HTTP-Antwort ausführt, siehe
    routers/withdrawal.py.
    """
    import time

    if not email_configured():
        # Kein Konfigurationsfehler ist transient - Wiederholen bringt nichts.
        return send_email(to_address, subject, text_body, html_body)

    for versuch in range(1, attempts + 1):
        if send_email(to_address, subject, text_body, html_body):
            return True
        if versuch < attempts:
            logger.warning(
                "Mailversand an %s fehlgeschlagen, Versuch %d/%d - erneuter "
                "Versuch in %.0f s", to_address, versuch, attempts, delay_seconds,
            )
            time.sleep(delay_seconds)
    logger.error(
        "Mailversand an %s endgültig fehlgeschlagen nach %d Versuchen (%s) - "
        "manuell nachfassen.", to_address, attempts, subject,
    )
    return False


# ---------------------------------------------------------------------------
# Gemeinsame HTML-Kartenoptik fuer alle Mails.
#
# Bis 2026-08-23 hatte nur die Bestaetigungsmail (_verify_html unten) das
# offizielle Branding, der Rest der ueber 15 Mailfunktionen verschickte reinen
# Klartext. Alles hier gebaute soll optisch zu _verify_html passen (dieselbe
# dunkle Karte, derselbe orangene Eyebrow-Akzent), ohne deren bereits
# getestete Umsetzung anzufassen. text_body bleibt ueberall die inhaltlich
# massgebliche Fassung - html_body ist nur die Darstellung.
#
# Seit 2026-09-11 sind alle Mails zweisprachig. Die Saetze stehen in
# app/message_texts.py, das Geruest bleibt hier - es gibt es nur einmal, damit
# die beiden Sprachen beim naechsten Umbau nicht auseinanderlaufen. Jede
# Baufunktion nimmt deshalb ein `lang` entgegen und reicht es durch.
# ---------------------------------------------------------------------------


def _default_footer_html(lang: str = STANDARD) -> str:
    return f"""    <p style="margin:0;font-size:13px;line-height:1.6;color:#a0a0a8;">
      {html.escape(t("footer.questions", lang))}
      <a href="mailto:{settings.support_email}" style="color:#e8e8ea;">{settings.support_email}</a>.
    </p>"""


def _operator_footer_html(full: bool = True) -> str:
    """Rechtlich vorgeschriebene Betreiberangaben - HTML-Fassung derselben
    OPERATOR_*-Felder aus app/legal.py wie in den Klartextmails
    (_subscription_text, _withdrawal_text, _notice_text). ``full=False``
    laesst Anschrift und Telefon weg, wie _notice_text es tut.

    Bewusst nicht uebersetzt: Name, Rechtsform, Anschrift und Kontakt des
    Betreibers sind Eigennamen und Pflichtangaben nach § 5 ECG - sie lauten in
    jeder Sprache gleich."""
    from . import legal

    rows = [legal.OPERATOR_NAME, f"{legal.OPERATOR_LEGAL_FORM}, {legal.OPERATOR_ROLE}"]
    if full:
        rows.append(f"{legal.OPERATOR_STREET}, {legal.OPERATOR_ZIP} {legal.OPERATOR_CITY}")
    rows.append(legal.OPERATOR_EMAIL)
    if full:
        rows.append(legal.OPERATOR_PHONE)
    lines = "<br>".join(html.escape(row) for row in rows)
    return f"""    <p style="margin:0;font-size:13px;line-height:1.6;color:#a0a0a8;">
      {lines}
    </p>"""


def _operator_block_text() -> str:
    """Dieselben Betreiberangaben fuer die Klartextfassung."""
    from . import legal

    return (
        f"{legal.OPERATOR_NAME}\n"
        f"{legal.OPERATOR_LEGAL_FORM}, {legal.OPERATOR_ROLE}\n"
        f"{legal.OPERATOR_STREET}, {legal.OPERATOR_ZIP} {legal.OPERATOR_CITY}\n"
        f"{legal.OPERATOR_EMAIL}\n"
        f"{legal.OPERATOR_PHONE}\n"
    )


def _p(text: str) -> str:
    """Ein maskierter Absatz im Mail-Stil. \\n im Text wird zu <br>."""
    return (
        '    <p style="margin:0 0 18px;font-size:15px;line-height:1.6;">'
        f'{html.escape(text).replace(chr(10), "<br>")}</p>'
    )


def _p_raw(inner_html: str) -> str:
    """Wie _p(), nimmt aber bereits fertiges HTML entgegen (z.B. fuer Links -
    der Aufrufer maskiert dort selbst, was maskiert werden muss)."""
    return f'    <p style="margin:0 0 18px;font-size:15px;line-height:1.6;">{inner_html}</p>'


def _ul(items: list[str]) -> str:
    lis = "".join(f'<li style="margin:0 0 6px;">{html.escape(item)}</li>' for item in items)
    return f'    <ul style="margin:0 0 18px;padding-left:20px;font-size:15px;line-height:1.6;">{lis}</ul>'


def _kv_rows_html(rows: list[tuple[str, str]]) -> str:
    """Tabelle fuer Aktenzeichen/Betrag/Datum-Bloecke - HTML-Fassung der
    eingerueckten "Key:   Wert"-Zeilen in den Klartextmails."""

    def cell(text: str) -> str:
        return html.escape(text).replace(chr(10), "<br>")

    rows_html = "".join(
        f'<tr><td style="padding:2px 12px 2px 0;color:#a0a0a8;white-space:nowrap;'
        f'vertical-align:top;">{cell(k)}</td><td style="padding:2px 0;">{cell(v)}</td></tr>'
        for k, v in rows
    )
    return f'    <table style="border-collapse:collapse;font-size:14px;margin:0 0 18px;">{rows_html}</table>'


def _kv_rows_text(rows: list[tuple[str, str]]) -> str:
    """Dieselben Zeilen fuer die Klartextfassung, Spalten ausgerichtet.

    Frueher standen die Breiten fest im f-String ("  Aktenzeichen:      {ref}").
    Das ging, solange nur deutsche Beschriftungen vorkamen; "Reference number"
    ist laenger als "Aktenzeichen" und haette die Spalte gesprengt. Jetzt
    richtet sich die Breite nach der laengsten Beschriftung."""
    if not rows:
        return ""
    breite = max(len(k) for k, _ in rows) + 1
    return "\n".join(f"  {(k + ':').ljust(breite + 1)} {v}" for k, v in rows)


def _email_shell(
    eyebrow: str,
    heading_html: str,
    body_html: str,
    footer_html: str | None = None,
    lang: str = STANDARD,
) -> str:
    """Kartenoptik von _verify_html, generalisiert: heading_html und
    body_html kommen vom Aufrufer bereits maskiert/gerendert."""
    return f"""<!doctype html>
<html lang="{t("html.lang", lang)}">
<body style="margin:0;padding:24px;background:#0f0f11;font-family:Helvetica,Arial,sans-serif;color:#e8e8ea;">
  <div style="max-width:520px;margin:0 auto;background:#17171a;border:1px solid #2a2a30;border-radius:16px;padding:28px;">
    <p style="margin:0 0 6px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#ff5a1f;">{html.escape(eyebrow)}</p>
    <h1 style="margin:0 0 18px;font-size:22px;line-height:1.3;color:#ffffff;">{heading_html}</h1>
{body_html}
{footer_html if footer_html is not None else _default_footer_html(lang)}
  </div>
</body>
</html>
"""


def _greeting(name: str, lang: str) -> str:
    return t("greeting", lang, name=name)


def _greeting_html(name: str, lang: str) -> str:
    return t("greeting", lang, name=html.escape(name))


# ---------------------------------------------------------------------------
# Bestätigungsmail (erste Mail nach der Registrierung)
# ---------------------------------------------------------------------------

#: Bleibt als Modulkonstante erhalten, weil Tests und aeltere Aufrufer sie
#: lesen. Die tatsaechlich verschickte Zeile kommt aus dem Woerterbuch.
VERIFY_SUBJECT = TEXTE["verify.subject"]["de"]


def _nach_der_pruefung_satz(lang: str = STANDARD) -> str:
    """Was nach der Verifizierung auf den Nutzer wartet.

    Frueher standen hier zwei Fassungen, je nachdem ob die Mitgliedsgebuehr
    scharf war - die eine erwaehnte einen Gratismonat. Seit dem 10.09.2026 gibt
    es weder Gebuehr noch Gratismonat: FLEXR ist dauerhaft kostenlos, und daran
    aendert auch das Ende der Beta nichts. Damit bleibt eine Fassung.
    """
    return t("verify.afterCheck", lang)


def _verify_text(name: str, link: str, hours: int, lang: str = STANDARD) -> str:
    # Der Satz nach der Pruefung ist mal laenger, mal kuerzer - deshalb hier
    # umgebrochen statt fest im Text, damit die Nur-Text-Fassung ihre
    # Zeilenbreite behaelt.
    pruefung = textwrap.fill(
        t("verify.text.ttl", lang, hours=hours, after=_nach_der_pruefung_satz(lang)),
        width=76,
    )
    return f"""{_greeting(name, lang)}

{t("verify.text.intro", lang)}

{link}

{pruefung}

{t("verify.needed", lang)}

  1. {t("verify.step1", lang)}
  2. {t("verify.step2", lang)}

{textwrap.fill(t("verify.manual", lang), width=76)}

{textwrap.fill(t("verify.notYou", lang), width=76)}

{t("footer.questions", lang)} {settings.support_email}.

{t("verify.signoff", lang)}
{t("verify.signoffTeam", lang)}
"""


def _verify_html(name: str, link: str, hours: int, lang: str = STANDARD) -> str:
    # Der Name kommt vom Nutzer und landet in HTML - maskieren, sonst steht in
    # der Mail plötzlich fremdes Markup.
    name = html.escape(name)
    return f"""<!doctype html>
<html lang="{t("html.lang", lang)}">
<body style="margin:0;padding:24px;background:#0f0f11;font-family:Helvetica,Arial,sans-serif;color:#e8e8ea;">
  <div style="max-width:520px;margin:0 auto;background:#17171a;border:1px solid #2a2a30;border-radius:16px;padding:28px;">
    <p style="margin:0 0 6px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#ff5a1f;">{html.escape(t("verify.eyebrow", lang))}</p>
    <h1 style="margin:0 0 18px;font-size:24px;line-height:1.25;color:#ffffff;">{t("verify.heading", lang, name=name)}</h1>
    <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">
      {html.escape(t("verify.html.intro", lang, hours=hours))}
    </p>
    <p style="margin:0 0 24px;">
      <a href="{link}" style="display:inline-block;background:#ff5a1f;color:#1a0a04;text-decoration:none;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:14px 22px;border-radius:12px;">{html.escape(t("verify.cta", lang))}</a>
    </p>
    <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#a0a0a8;">
      {html.escape(t("verify.fallback", lang))}<br>
      <span style="color:#e8e8ea;word-break:break-all;">{html.escape(link)}</span>
    </p>
    <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">
      {t("verify.html.check", lang, after=html.escape(_nach_der_pruefung_satz(lang)))}
    </p>
    <ol style="margin:0 0 22px;padding-left:20px;font-size:15px;line-height:1.7;">
      <li>{html.escape(t("verify.step1", lang))}</li>
      <li>{html.escape(t("verify.step2", lang))}</li>
    </ol>
    <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#a0a0a8;">
      {html.escape(t("verify.manual", lang))}
    </p>
    <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#a0a0a8;">
      {html.escape(t("verify.notYou", lang))}
    </p>
    <p style="margin:0;font-size:13px;line-height:1.6;color:#a0a0a8;">
      {html.escape(t("footer.questions", lang))}
      <a href="mailto:{settings.support_email}" style="color:#e8e8ea;">{settings.support_email}</a>.
    </p>
  </div>
</body>
</html>
"""


def send_verification_email(
    email: str, name: str, link: str, ttl_hours: int = 24, lang: str = STANDARD
) -> bool:
    """Erste Mail nach der Registrierung: Adresse bestätigen.

    Ersetzt die frühere Willkommensmail - zwei Mails gleichzeitig wären eine zu
    viel, und die Aufforderung zur Verifizierung steht hier mit drin.
    """
    return send_email(
        to_address=email,
        subject=t("verify.subject", lang),
        text_body=_verify_text(name, link, ttl_hours, lang),
        html_body=_verify_html(name, link, ttl_hours, lang),
    )


# ---------------------------------------------------------------------------
# Vertragsbestätigung nach Abschluss des kostenpflichtigen Abos
#
# Wird nach "checkout.session.completed" verschickt (siehe routers/billing.py).
# FLEXR beginnt sofort mit der Leistung, deshalb steht hier auch der Hinweis
# auf die zuvor eingeholte ausdrückliche Erklärung dazu (§ 10 FAGG) sowie die
# Kontaktangaben inkl. Telefonnummer - keine hervorgehobene CTA, nur normale
# Kontaktdarstellung.
# ---------------------------------------------------------------------------

SUBSCRIPTION_SUBJECT = TEXTE["subscription.subject"]["de"]


def _subscription_rows(lang: str) -> list[tuple[str, str]]:
    from . import legal

    return [
        (t("subscription.kv.service", lang), t("subscription.kv.serviceValue", lang)),
        (
            t("subscription.kv.price", lang),
            t("subscription.kv.priceValue", lang, price=legal.PRICE_EUR_PER_MONTH),
        ),
        (t("subscription.kv.billing", lang), t("subscription.kv.billingValue", lang)),
        (t("subscription.kv.term", lang), t("subscription.kv.termValue", lang)),
        (t("subscription.kv.cancel", lang), t("subscription.kv.cancelValue", lang)),
    ]


def _withdrawal_url(lang: str) -> str:
    """Der Rechtstext existiert zweisprachig unter zwei Adressen."""
    from . import legal

    pfad = "/en/widerruf.html" if normalise(lang) == "en" else "/widerruf.html"
    return f"{legal.SITE_URL}{pfad}"


def _subscription_text(name: str, lang: str = STANDARD) -> str:
    return f"""{_greeting(name, lang)}

{t("subscription.intro", lang)}

{_kv_rows_text(_subscription_rows(lang))}

{textwrap.fill(t("subscription.immediateStart", lang, url=_withdrawal_url(lang)), width=76)}

{t("questions.reply", lang)}

{_operator_block_text()}"""


def _subscription_html(name: str, lang: str = STANDARD) -> str:
    body = "\n".join([
        _p(t("subscription.intro", lang)),
        _kv_rows_html(_subscription_rows(lang)),
        _p(t("subscription.immediateStart", lang, url=_withdrawal_url(lang))),
    ])
    return _email_shell(
        t("subscription.eyebrow", lang), _greeting_html(name, lang), body,
        _operator_footer_html(), lang,
    )


def send_subscription_confirmation(email: str, name: str, lang: str = STANDARD) -> bool:
    """Vertragsbestätigung auf dauerhaftem Datenträger nach Zahlungsabschluss."""
    return send_email(
        to_address=email,
        subject=t("subscription.subject", lang),
        text_body=_subscription_text(name, lang),
        html_body=_subscription_html(name, lang),
    )


# ---------------------------------------------------------------------------
# Abo-Lebenszyklus (von Stripe-Webhooks ausgeloest)
# ---------------------------------------------------------------------------

#: Bleibt exportiert - email_jobs.py rechnet damit den Stichtag aus.
VIENNA = message_texts.VIENNA


def _date_from_unix(timestamp: int | None, lang: str = STANDARD) -> str:
    return format_datetime(timestamp, lang)


def _date_from_naive_utc(value: datetime, lang: str = STANDARD) -> str:
    """Wie _date_from_unix, aber für naive UTC-Zeitstempel aus der DB (z.B.
    User.deleted_at) statt Unix-Timestamps aus Stripe-Payloads."""
    return format_date(value, lang)


def _money(amount_cents: int | None, currency: str | None, lang: str = STANDARD) -> str:
    return format_money(amount_cents, currency, lang)


def _trial_ending_html(name: str, trial_end: int | None, lang: str = STANDARD) -> str:
    from . import legal

    body = "\n".join([
        _p(t(
            "trial.intro", lang,
            date=_date_from_unix(trial_end, lang), price=legal.PRICE_EUR_PER_MONTH,
        )),
        _p(t("trial.optOut", lang)),
    ])
    return _email_shell(t("trial.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_trial_ending(
    email: str, name: str, trial_end: int | None, lang: str = STANDARD
) -> bool:
    from . import legal

    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("trial.intro", lang, date=_date_from_unix(trial_end, lang), price=legal.PRICE_EUR_PER_MONTH), width=76)}

{textwrap.fill(t("trial.optOut", lang), width=76)}

{t("questions.reply", lang)}

{t("signoff", lang)}
"""
    return send_email(
        email, t("trial.subject", lang), body, _trial_ending_html(name, trial_end, lang)
    )


def _renewal_reminder_html(
    name: str, amount_due: int | None, currency: str | None, charge_at: int | None,
    lang: str = STANDARD,
) -> str:
    body = "\n".join([
        _p(t(
            "renewal.intro", lang,
            date=_date_from_unix(charge_at, lang),
            amount=_money(amount_due, currency, lang),
        )),
        _p(t("renewal.manage", lang)),
    ])
    return _email_shell(t("renewal.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_renewal_reminder(
    email: str,
    name: str,
    amount_due: int | None,
    currency: str | None,
    charge_at: int | None,
    lang: str = STANDARD,
) -> bool:
    intro = t(
        "renewal.intro", lang,
        date=_date_from_unix(charge_at, lang), amount=_money(amount_due, currency, lang),
    )
    body = f"""{_greeting(name, lang)}

{textwrap.fill(intro, width=76)}

{textwrap.fill(t("renewal.manage", lang), width=76)}

{t("signoff", lang)}
"""
    return send_email(
        email, t("renewal.subject", lang), body,
        _renewal_reminder_html(name, amount_due, currency, charge_at, lang),
    )


def _payment_succeeded_html(
    name: str, amount_paid: int | None, currency: str | None, invoice_url: str | None,
    lang: str = STANDARD,
) -> str:
    paragraphs = [
        _p(t("paid.intro", lang, amount=_money(amount_paid, currency, lang))),
    ]
    if invoice_url:
        link = html.escape(invoice_url)
        label = html.escape(t("paid.invoice", lang))
        paragraphs.append(_p_raw(f'{label}: <a href="{link}" style="color:#e8e8ea;">{link}</a>'))
    paragraphs.append(_p(t("paid.manage", lang)))
    return _email_shell(
        t("paid.eyebrow", lang), _greeting_html(name, lang), "\n".join(paragraphs), lang=lang
    )


def send_payment_succeeded(
    email: str,
    name: str,
    amount_paid: int | None,
    currency: str | None,
    invoice_url: str | None,
    lang: str = STANDARD,
) -> bool:
    rechnung = f'\n{t("paid.invoice", lang)}: {invoice_url}\n' if invoice_url else ""
    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("paid.intro", lang, amount=_money(amount_paid, currency, lang)), width=76)}
{rechnung}
{textwrap.fill(t("paid.manage", lang), width=76)}

{t("signoff", lang)}
"""
    return send_email(
        email, t("paid.subject", lang), body,
        _payment_succeeded_html(name, amount_paid, currency, invoice_url, lang),
    )


def _next_attempt_text(next_attempt: int | None, lang: str) -> str:
    if next_attempt:
        return t("failed.nextAttempt", lang, date=_date_from_unix(next_attempt, lang))
    return t("failed.noNextAttempt", lang)


def _payment_failed_html(
    name: str,
    amount_due: int | None,
    currency: str | None,
    next_attempt: int | None,
    invoice_url: str | None,
    lang: str = STANDARD,
) -> str:
    paragraphs = [
        _p(t(
            "failed.intro", lang,
            amount=_money(amount_due, currency, lang),
            next=_next_attempt_text(next_attempt, lang),
        )),
        _p(t("failed.check", lang)),
    ]
    if invoice_url:
        link = html.escape(invoice_url)
        label = html.escape(t("failed.openInvoice", lang))
        paragraphs.append(_p_raw(f'{label}: <a href="{link}" style="color:#e8e8ea;">{link}</a>'))
    return _email_shell(
        t("failed.eyebrow", lang), _greeting_html(name, lang), "\n".join(paragraphs), lang=lang
    )


def send_payment_failed(
    email: str,
    name: str,
    amount_due: int | None,
    currency: str | None,
    next_attempt: int | None,
    invoice_url: str | None,
    lang: str = STANDARD,
) -> bool:
    intro = t(
        "failed.intro", lang,
        amount=_money(amount_due, currency, lang),
        next=_next_attempt_text(next_attempt, lang),
    )
    rechnung = f'\n{t("failed.openInvoice", lang)}: {invoice_url}\n' if invoice_url else ""
    body = f"""{_greeting(name, lang)}

{textwrap.fill(intro, width=76)}

{textwrap.fill(t("failed.check", lang), width=76)}
{rechnung}
{t("signoff", lang)}
"""
    return send_email(
        email, t("failed.subject", lang), body,
        _payment_failed_html(name, amount_due, currency, next_attempt, invoice_url, lang),
    )


def _cancellation_scheduled_html(
    name: str, access_ends_at: int | None, lang: str = STANDARD
) -> str:
    body = "\n".join([
        _p(t("cancelled.intro", lang, date=_date_from_unix(access_ends_at, lang))),
        _p(t("cancelled.undo", lang)),
    ])
    return _email_shell(t("cancelled.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_cancellation_scheduled(
    email: str, name: str, access_ends_at: int | None, lang: str = STANDARD
) -> bool:
    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("cancelled.intro", lang, date=_date_from_unix(access_ends_at, lang)), width=76)}

{textwrap.fill(t("cancelled.undo", lang), width=76)}

{t("signoff", lang)}
"""
    return send_email(
        email, t("cancelled.subject", lang), body,
        _cancellation_scheduled_html(name, access_ends_at, lang),
    )


def _subscription_ended_html(name: str, lang: str = STANDARD) -> str:
    body = _p(t("ended.intro", lang))
    return _email_shell(t("ended.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_subscription_ended(email: str, name: str, lang: str = STANDARD) -> bool:
    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("ended.intro", lang), width=76)}

{t("signoff", lang)}
"""
    return send_email(
        email, t("ended.subject", lang), body, _subscription_ended_html(name, lang)
    )


# Die Mails "Dein Gratismonat läuft ab" und "... ist beendet" standen hier bis
# zum 10.09.2026. Es gibt keinen Probemonat mehr, weil die Plattform dauerhaft
# kostenlos ist - siehe email_jobs.run_daily_emails(). Wer je eine
# Premium-bezogene Mail braucht: Stripe erzeugt dafuer Ereignisse, der passende
# Ort ist routers/billing.handle_stripe_event().


# ---------------------------------------------------------------------------
# Aktivitäts-Benachrichtigungen (neues Match, wartende Profile, Inaktivität,
# offene Likes ohne Match)
#
# Anders als die Abrechnungs- und Moderationsmails sind das die einzigen
# abbestellbaren Nachrichten: jede hat im Profil unter "Benachrichtigungen"
# einen eigenen Schalter (siehe notifications.py). Der Hinweis darauf steht
# deshalb in jedem dieser Texte.
# ---------------------------------------------------------------------------


def _notify_opt_out(lang: str = STANDARD) -> str:
    return t("notify.optOut", lang)


#: Bleibt als Modulkonstante erhalten - Tests lesen sie.
_NOTIFY_OPT_OUT = TEXTE["notify.optOut"]["de"]


def _new_match_html(name: str, match_name: str, lang: str = STANDARD) -> str:
    body = "\n".join([
        _p(t("match.intro", lang, other=match_name)),
        _p(_notify_opt_out(lang)),
    ])
    return _email_shell(t("match.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_new_match(email: str, name: str, match_name: str, lang: str = STANDARD) -> bool:
    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("match.intro", lang, other=match_name), width=76)}

{textwrap.fill(_notify_opt_out(lang), width=76)}

{t("signoff", lang)}
"""
    return send_email(
        email, t("match.subject", lang, other=match_name), body,
        _new_match_html(name, match_name, lang),
    )


def _queue_waiting_html(name: str, count: int, lang: str = STANDARD) -> str:
    body = "\n".join([
        _p(t("queue.intro", lang, count=count)),
        _p(_notify_opt_out(lang)),
    ])
    return _email_shell(t("queue.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_queue_waiting(email: str, name: str, count: int, lang: str = STANDARD) -> bool:
    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("queue.intro", lang, count=count), width=76)}

{textwrap.fill(_notify_opt_out(lang), width=76)}

{t("signoff", lang)}
"""
    return send_email(
        email, t("queue.subject", lang, count=count), body,
        _queue_waiting_html(name, count, lang),
    )


def _pending_likes_intro(count: int, lang: str) -> str:
    # Ein/mehrere Mitglieder: Deutsch und Englisch beugen an verschiedenen
    # Stellen ("hat"/"haben" gegen "liked"/"liked"), deshalb zwei ganze Saetze
    # statt zusammengesetzter Wortbausteine.
    schluessel = "likes.intro.one" if count == 1 else "likes.intro.many"
    return t(schluessel, lang, count=count)


def _pending_likes_html(name: str, count: int, lang: str = STANDARD) -> str:
    body = "\n".join([
        _p(_pending_likes_intro(count, lang)),
        _p(_notify_opt_out(lang)),
    ])
    return _email_shell(t("likes.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_pending_likes(email: str, name: str, count: int, lang: str = STANDARD) -> bool:
    subject = (
        t("likes.subject.one", lang) if count == 1
        else t("likes.subject.many", lang, count=count)
    )
    body = f"""{_greeting(name, lang)}

{textwrap.fill(_pending_likes_intro(count, lang), width=76)}

{textwrap.fill(_notify_opt_out(lang), width=76)}

{t("signoff", lang)}
"""
    return send_email(email, subject, body, _pending_likes_html(name, count, lang))


def _inactivity_html(name: str, days: int, lang: str = STANDARD) -> str:
    body = "\n".join([
        _p(t("inactive.intro", lang, days=days)),
        _p(_notify_opt_out(lang)),
    ])
    return _email_shell(t("inactive.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_inactivity_reminder(
    email: str, name: str, days: int, lang: str = STANDARD
) -> bool:
    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("inactive.intro", lang, days=days), width=76)}

{textwrap.fill(_notify_opt_out(lang), width=76)}

{t("signoff", lang)}
"""
    return send_email(
        email, t("inactive.subject", lang), body, _inactivity_html(name, days, lang),
    )


# ---------------------------------------------------------------------------
# Bestätigung der Selbstlöschung (30-Tage-Karenzzeit)
#
# Wird unmittelbar bei DELETE /api/profiles/me verschickt (siehe
# routers/profiles.py). Erklärt, was mit der Karenzzeit passiert und dass eine
# Reaktivierung per erneutem Login möglich ist (siehe routers/auth.reactivate).
# ---------------------------------------------------------------------------

DELETION_SUBJECT = TEXTE["deletion.subject"]["de"]


def _deletion_points(purge_date: str, grace_days: int, lang: str) -> list[str]:
    return [
        t("deletion.point1", lang),
        t("deletion.point2", lang, date=purge_date, days=grace_days),
        t("deletion.point3", lang),
    ]


def _deletion_text(
    name: str, purge_date: str, grace_days: int, lang: str = STANDARD
) -> str:
    punkte = "\n".join(
        textwrap.fill(p, width=72, initial_indent="  - ", subsequent_indent="    ")
        for p in _deletion_points(purge_date, grace_days, lang)
    )
    return f"""{_greeting(name, lang)}

{textwrap.fill(t("deletion.intro", lang), width=76)}

{t("deletion.whatItMeans", lang)}

{punkte}

{textwrap.fill(t("deletion.reactivate", lang, date=purge_date), width=76)}

{textwrap.fill(t("deletion.notYou", lang, support=settings.support_email), width=76)}

{t("deletion.privacy", lang)}

{t("signoff", lang)}
"""


def _deletion_html(
    name: str, purge_date: str, grace_days: int, lang: str = STANDARD
) -> str:
    body = "\n".join([
        _p(t("deletion.intro", lang)),
        _ul(_deletion_points(purge_date, grace_days, lang)),
        _p(t("deletion.reactivate", lang, date=purge_date)),
        _p(t("deletion.notYou", lang, support=settings.support_email)),
        _p(t("deletion.privacy", lang)),
    ])
    return _email_shell(t("deletion.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_account_deletion_confirmation(
    email: str, name: str, purge_at: datetime, grace_days: int, lang: str = STANDARD
) -> bool:
    """Bestätigung der Selbstlöschung, mit kurzen Wiederholungen bei Fehlschlag.

    Analog zur Rücktrittsbestätigung: Die Löschung selbst ist zu diesem
    Zeitpunkt schon in der DB vollzogen (deleted_at gesetzt) - ein einzelner
    SMTP-Aussetzer soll die Bestätigung trotzdem nicht kippen lassen.
    """
    purge_date = _date_from_naive_utc(purge_at, lang)
    return send_email_with_retry(
        to_address=email,
        subject=t("deletion.subject", lang),
        text_body=_deletion_text(name, purge_date, grace_days, lang),
        html_body=_deletion_html(name, purge_date, grace_days, lang),
        attempts=2,
        delay_seconds=1,
    )


# ---------------------------------------------------------------------------
# Verifizierung und Moderation
# ---------------------------------------------------------------------------


def _decision_html(name: str, eyebrow: str, detail: str, lang: str = STANDARD) -> str:
    """Gebrandete Fassung im selben Look wie _verify_html - fuer kurze
    Status-Mails ohne eigenen Call-to-Action-Link."""
    name_safe = html.escape(name)
    detail_html = html.escape(detail).replace("\n", "<br>")
    return f"""<!doctype html>
<html lang="{t("html.lang", lang)}">
<body style="margin:0;padding:24px;background:#0f0f11;font-family:Helvetica,Arial,sans-serif;color:#e8e8ea;">
  <div style="max-width:520px;margin:0 auto;background:#17171a;border:1px solid #2a2a30;border-radius:16px;padding:28px;">
    <p style="margin:0 0 6px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#ff5a1f;">{html.escape(eyebrow)}</p>
    <h1 style="margin:0 0 18px;font-size:22px;line-height:1.3;color:#ffffff;">{t("greeting", lang, name=name_safe)}</h1>
    <p style="margin:0 0 22px;font-size:15px;line-height:1.6;">
      {detail_html}
    </p>
    <p style="margin:0;font-size:13px;line-height:1.6;color:#a0a0a8;">
      {html.escape(t("decision.openApp", lang))}
      <a href="mailto:{settings.support_email}" style="color:#e8e8ea;">{settings.support_email}</a>.
    </p>
  </div>
</body>
</html>
"""


def send_verification_decision(
    email: str,
    name: str,
    outcome: str,
    reason: str | None = None,
    redo_selfie: bool = False,
    lang: str = STANDARD,
) -> bool:
    if outcome == "approved":
        subject = t("verified.subject", lang)
        eyebrow = t("verified.eyebrow", lang)
        detail = t("verified.detail", lang)
    elif outcome == "reupload_required":
        subject = t("reupload.subject", lang)
        eyebrow = t("reupload.eyebrow", lang)
        umfang = t("reupload.both" if redo_selfie else "reupload.idOnly", lang)
        detail = t(
            "reupload.detail", lang,
            what=umfang, reason=reason or t("reupload.fallbackReason", lang),
        )
    else:
        subject = t("rejected.subject", lang)
        eyebrow = t("rejected.eyebrow", lang)
        detail = t(
            "rejected.detail", lang, reason=reason or t("rejected.fallbackReason", lang)
        )
    body = f"""{_greeting(name, lang)}

{detail}

{t("decision.openApp.text", lang)}

{t("signoff", lang)}
"""
    return send_email_with_retry(
        email, subject, body, _decision_html(name, eyebrow, detail, lang),
        attempts=2, delay_seconds=1,
    )


def _verification_required_html(name: str, lang: str = STANDARD) -> str:
    body = "\n".join([
        _p(t("required.intro", lang)),
        _p(t("required.steps", lang)),
    ])
    return _email_shell(t("required.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_verification_required(email: str, name: str, lang: str = STANDARD) -> bool:
    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("required.intro", lang), width=76)}

{textwrap.fill(t("required.steps", lang), width=76)}

{t("required.questions", lang)}

{t("signoff", lang)}
"""
    return send_email_with_retry(
        email,
        t("required.subject", lang),
        body,
        _verification_required_html(name, lang),
        attempts=2,
        delay_seconds=1,
    )


def _moderation_decision_html(
    name: str, measure: str, summary: str, details: list[str] | None, appeal: bool,
    lang: str = STANDARD,
) -> str:
    parts = [_p(measure), _p(f'{t("moderation.reasonLabel", lang)}: {summary}')]
    detail_items = [line for line in (details or []) if line]
    if detail_items:
        parts.append(_p(t("moderation.detailsLabel", lang)))
        parts.append(_ul(detail_items))
    if appeal:
        parts.append(_p(t("moderation.appeal", lang)))
    return _email_shell(
        t("moderation.eyebrow", lang), _greeting_html(name, lang), "\n".join(parts), lang=lang
    )


def send_moderation_decision(
    email: str,
    name: str,
    measure: str,
    summary: str,
    details: list[str] | None = None,
    appeal: bool = True,
    lang: str = STANDARD,
) -> bool:
    detail_text = "\n".join(f"- {line}" for line in (details or []) if line)
    if detail_text:
        detail_text = f'\n\n{t("moderation.detailsLabel", lang)}\n' + detail_text
    appeal_text = ""
    if appeal:
        appeal_text = "\n\n" + textwrap.fill(t("moderation.appeal", lang), width=76)
    body = f"""{_greeting(name, lang)}

{measure}

{t("moderation.reasonLabel", lang)}: {summary}{detail_text}{appeal_text}

{t("signoff", lang)}
"""
    return send_email_with_retry(
        email, t("moderation.subject", lang), body,
        _moderation_decision_html(name, measure, summary, details, appeal, lang),
        attempts=2, delay_seconds=1,
    )


def _photo_rejected_html(name: str, reason: str, lang: str = STANDARD) -> str:
    body = "\n".join([
        _p(t("photo.intro", lang)),
        _p(f'{t("photo.reasonLabel", lang)}: {reason}'),
        _p(t("photo.retry", lang)),
    ])
    return _email_shell(t("photo.eyebrow", lang), _greeting_html(name, lang), body, lang=lang)


def send_photo_rejected(email: str, name: str, reason: str, lang: str = STANDARD) -> bool:
    body = f"""{_greeting(name, lang)}

{textwrap.fill(t("photo.intro", lang), width=76)}

{t("photo.reasonLabel", lang)}: {reason}

{textwrap.fill(t("photo.retry", lang), width=76)}

{t("signoff", lang)}
"""
    return send_email_with_retry(
        email, t("photo.subject", lang), body, _photo_rejected_html(name, reason, lang),
        attempts=2, delay_seconds=1,
    )


def _report_decision_html(
    reference: str, outcome: str, reason: str, lang: str = STANDARD
) -> str:
    body = "\n".join([
        _p(t("report.intro", lang, reference=reference)),
        _kv_rows_html([
            (t("report.outcomeLabel", lang), outcome),
            (t("report.reasonLabel", lang), reason),
        ]),
        _p(t("report.appeal", lang)),
    ])
    return _email_shell(
        t("report.eyebrow", lang), t("greeting.plain", lang), body, lang=lang
    )


def send_report_decision(
    email: str, reference: str, outcome: str, reason: str, lang: str = STANDARD
) -> bool:
    body = f"""{t("greeting.plain", lang)}

{t("report.intro", lang, reference=reference)}

{t("report.outcomeLabel", lang)}: {outcome}
{t("report.reasonLabel", lang)}: {reason}

{textwrap.fill(t("report.appeal", lang), width=76)}

{t("signoff", lang)}
"""
    return send_email_with_retry(
        email, t("report.subject", lang, reference=reference), body,
        _report_decision_html(reference, outcome, reason, lang),
        attempts=2, delay_seconds=1,
    )


# ---------------------------------------------------------------------------
# Rücktrittsbestätigung (§ 13a Abs. 4 FAGG)
#
# Die Bestätigung muss auf einem dauerhaften Datenträger erfolgen und den
# Inhalt der Erklärung samt Datum und Uhrzeit wiedergeben. Deshalb steht der
# Wortlaut hier vollständig in der Mail und nicht nur ein "Wir haben Ihren
# Widerruf erhalten".
#
# Der Wortlaut selbst (declaration_text) wird NICHT uebersetzt: Er ist der
# Nachweis, nicht die Darstellung - gespeichert wurde, was gespeichert wurde
# (siehe routers/withdrawal.build_declaration_text). Uebersetzt wird nur, was
# ihn umgibt.
# ---------------------------------------------------------------------------

WITHDRAWAL_SUBJECT = TEXTE["withdrawal.subject"]["de"]


def _withdrawal_rows(
    reference: str, received_at: str, contract_reference: str | None, lang: str
) -> list[tuple[str, str]]:
    return [
        (t("withdrawal.kv.reference", lang), reference),
        (
            t("withdrawal.kv.receivedAt", lang),
            t("withdrawal.kv.timezone", lang, received=received_at),
        ),
        (
            t("withdrawal.kv.contract", lang),
            contract_reference or t("value.none", lang),
        ),
    ]


def _withdrawal_folge(subscription_stopped: bool, lang: str) -> str:
    return t("withdrawal.stopped" if subscription_stopped else "withdrawal.pending", lang)


def _withdrawal_text(
    name: str,
    reference: str,
    received_at: str,
    declaration_text: str,
    contract_reference: str | None,
    subscription_stopped: bool = False,
    lang: str = STANDARD,
) -> str:
    return f"""{_greeting(name, lang)}

{textwrap.fill(t("withdrawal.intro", lang), width=76)}

{_kv_rows_text(_withdrawal_rows(reference, received_at, contract_reference, lang))}

{t("withdrawal.wording", lang)}

{declaration_text}

{textwrap.fill(_withdrawal_folge(subscription_stopped, lang), width=76)}

{t("questions.reply", lang)}

{_operator_block_text()}"""


def _withdrawal_html(
    name: str,
    reference: str,
    received_at: str,
    declaration_text: str,
    contract_reference: str | None,
    subscription_stopped: bool = False,
    lang: str = STANDARD,
) -> str:
    declaration_html = html.escape(declaration_text).replace(chr(10), "<br>")
    body = "\n".join([
        _p(t("withdrawal.intro", lang)),
        _kv_rows_html(_withdrawal_rows(reference, received_at, contract_reference, lang)),
        _p(t("withdrawal.wording", lang)),
        f'    <blockquote style="margin:0 0 18px;padding:2px 16px;'
        f'border-left:2px solid #2a2a30;font-size:14px;line-height:1.6;'
        f'color:#c8c8ce;">{declaration_html}</blockquote>',
        _p(_withdrawal_folge(subscription_stopped, lang)),
    ])
    return _email_shell(
        t("withdrawal.eyebrow", lang), _greeting_html(name, lang), body,
        _operator_footer_html(), lang,
    )


def send_withdrawal_confirmation(
    email: str,
    name: str,
    reference: str,
    received_at: str,
    declaration_text: str,
    contract_reference: str | None = None,
    subscription_stopped: bool = False,
    lang: str = STANDARD,
) -> bool:
    """Unverzügliche Bestätigung einer Rücktrittserklärung.

    § 13a Abs. 4 FAGG verlangt diese Bestätigung "unverzüglich" - ein
    einzelner SMTP-Fehlschlag (Netzwerk-Hänger, Server kurz nicht erreichbar)
    darf sie deshalb nicht endgültig verhindern. send_email_with_retry()
    versucht es mit kurzen Pausen erneut, bevor endgültig aufgegeben wird;
    die Erklärung selbst ist zu diesem Zeitpunkt schon gespeichert (siehe
    routers/withdrawal.py) und geht so oder so nicht verloren.

    Rechtsverbindlich ist text_body (Wortlaut der Erklärung, unveraendert);
    html_body ist nur eine gebrandete Darstellung desselben Inhalts.
    """
    return send_email_with_retry(
        to_address=email,
        subject=t("withdrawal.subject", lang, reference=reference),
        text_body=_withdrawal_text(
            name, reference, received_at, declaration_text, contract_reference,
            subscription_stopped, lang,
        ),
        html_body=_withdrawal_html(
            name, reference, received_at, declaration_text, contract_reference,
            subscription_stopped, lang,
        ),
    )


# ---------------------------------------------------------------------------
# Empfangsbestätigung einer DSA-Meldung (Art. 16 Abs. 4)
# ---------------------------------------------------------------------------

NOTICE_SUBJECT = TEXTE["notice.subject"]["de"]


def _notice_rows(
    reference: str, received_at: str, category_label: str, lang: str
) -> list[tuple[str, str]]:
    return [
        (t("notice.kv.reference", lang), reference),
        (t("notice.kv.receivedAt", lang), received_at),
        (t("notice.kv.category", lang), category_label),
    ]


def _notice_text(
    reference: str, received_at: str, category_label: str, lang: str = STANDARD
) -> str:
    from . import legal

    return f"""{t("greeting.plain", lang)}

{t("notice.intro", lang)}

{_kv_rows_text(_notice_rows(reference, received_at, category_label, lang))}

{textwrap.fill(t("notice.review", lang), width=76)}

{textwrap.fill(t("notice.legalBasis", lang), width=76)}

{legal.OPERATOR_NAME}
{legal.OPERATOR_LEGAL_FORM}, {legal.OPERATOR_ROLE}
{legal.OPERATOR_EMAIL}
"""


def _notice_html(
    reference: str, received_at: str, category_label: str, lang: str = STANDARD
) -> str:
    body = "\n".join([
        _p(t("notice.intro", lang)),
        _kv_rows_html(_notice_rows(reference, received_at, category_label, lang)),
        _p(t("notice.review", lang)),
        _p(t("notice.legalBasis", lang)),
    ])
    return _email_shell(
        t("notice.eyebrow", lang), t("greeting.plain", lang), body,
        _operator_footer_html(full=False), lang,
    )


def send_notice_acknowledgement(
    email: str, reference: str, received_at: str, category_label: str,
    lang: str = STANDARD,
) -> bool:
    """Empfangsbestätigung an den Melder, sofern er eine Adresse angegeben hat."""
    return send_email(
        to_address=email,
        subject=t("notice.subject", lang, reference=reference),
        text_body=_notice_text(reference, received_at, category_label, lang),
        html_body=_notice_html(reference, received_at, category_label, lang),
    )
