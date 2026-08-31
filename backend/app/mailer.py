"""E-Mail-Versand (SMTP).

Mit konfigurierten Zugangsdaten (SMTP_HOST, SMTP_USER, SMTP_PASSWORD in der
.env) wird echt versendet - über die Standardbibliothek, ohne zusätzliche
Abhängigkeit. Ohne Zugangsdaten landet die Nachricht nur im Server-Log
(Entwicklungs-/Testbetrieb), analog zu app/sms.py.

Ein Fehlschlag beim Versand darf nie den auslösenden Vorgang kippen: Wer sich
registriert hat, ist registriert - auch wenn der Mailserver gerade streikt.
Deshalb fängt send_email() alles ab und meldet nur, ob es geklappt hat.
"""

import html
import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from zoneinfo import ZoneInfo

from .config import settings

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
# ---------------------------------------------------------------------------


def _default_footer_html() -> str:
    return f"""    <p style="margin:0;font-size:13px;line-height:1.6;color:#a0a0a8;">
      Fragen? Antworte einfach auf diese Mail oder schreib an
      <a href="mailto:{settings.support_email}" style="color:#e8e8ea;">{settings.support_email}</a>.
    </p>"""


def _operator_footer_html(full: bool = True) -> str:
    """Rechtlich vorgeschriebene Betreiberangaben - HTML-Fassung derselben
    OPERATOR_*-Felder aus app/legal.py wie in den Klartextmails
    (_subscription_text, _withdrawal_text, _notice_text). ``full=False``
    laesst Anschrift und Telefon weg, wie _notice_text es tut."""
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


def _email_shell(eyebrow: str, heading_html: str, body_html: str, footer_html: str | None = None) -> str:
    """Kartenoptik von _verify_html, generalisiert: heading_html und
    body_html kommen vom Aufrufer bereits maskiert/gerendert."""
    return f"""<!doctype html>
<html lang="de">
<body style="margin:0;padding:24px;background:#0f0f11;font-family:Helvetica,Arial,sans-serif;color:#e8e8ea;">
  <div style="max-width:520px;margin:0 auto;background:#17171a;border:1px solid #2a2a30;border-radius:16px;padding:28px;">
    <p style="margin:0 0 6px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#ff5a1f;">{html.escape(eyebrow)}</p>
    <h1 style="margin:0 0 18px;font-size:22px;line-height:1.3;color:#ffffff;">{heading_html}</h1>
{body_html}
{footer_html or _default_footer_html()}
  </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Bestätigungsmail (erste Mail nach der Registrierung)
# ---------------------------------------------------------------------------

VERIFY_SUBJECT = "Bestätige deine E-Mail-Adresse für FLEXR"


def _verify_text(name: str, link: str, hours: int) -> str:
    return f"""Hallo {name},

dein FLEXR-Profil ist angelegt. Bevor es weitergeht, bestätige bitte
einmalig deine E-Mail-Adresse:

{link}

Der Link gilt {hours} Stunden. Danach steht die einmalige Alters- und
Identitätsprüfung an - erst danach ist dein Konto freigeschaltet, und erst
dann startet dein Gratismonat. Die Prüfzeit geht dir also nicht ab.

Das brauchst du dafür:

  1. Ein Live-Selfie, frontal in die Kamera (direkt in der App aufgenommen)
  2. Eine Aufnahme deines amtlichen Lichtbildausweises

Die Prüfung erfolgt manuell durch einen Menschen - es kommt keine
automatische Gesichtserkennung zum Einsatz. Die Aufnahmen werden nach
Abschluss der Prüfung gelöscht.

Du hast dich nicht bei FLEXR angemeldet? Dann ignoriere diese Mail einfach.
Ohne Bestätigung passiert mit der Adresse nichts.

Fragen? Antworte einfach auf diese Mail oder schreib an {settings.support_email}.

Bis gleich im Gym,
dein FLEXR-Team
"""


def _verify_html(name: str, link: str, hours: int) -> str:
    # Der Name kommt vom Nutzer und landet in HTML - maskieren, sonst steht in
    # der Mail plötzlich fremdes Markup.
    name = html.escape(name)
    return f"""<!doctype html>
<html lang="de">
<body style="margin:0;padding:24px;background:#0f0f11;font-family:Helvetica,Arial,sans-serif;color:#e8e8ea;">
  <div style="max-width:520px;margin:0 auto;background:#17171a;border:1px solid #2a2a30;border-radius:16px;padding:28px;">
    <p style="margin:0 0 6px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#ff5a1f;">Erste Wiederholung</p>
    <h1 style="margin:0 0 18px;font-size:24px;line-height:1.25;color:#ffffff;">Willkommen bei FLEXR, {name}!</h1>
    <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">
      Dein Profil ist angelegt. Bevor es weitergeht, bestätige bitte einmalig
      deine E-Mail-Adresse. Der Link gilt {hours} Stunden.
    </p>
    <p style="margin:0 0 24px;">
      <a href="{link}" style="display:inline-block;background:#ff5a1f;color:#1a0a04;text-decoration:none;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:14px 22px;border-radius:12px;">E-Mail bestätigen</a>
    </p>
    <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#a0a0a8;">
      Klappt der Knopf nicht? Kopier diese Adresse in deinen Browser:<br>
      <span style="color:#e8e8ea;word-break:break-all;">{html.escape(link)}</span>
    </p>
    <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">
      Danach steht die einmalige <b>Alters- und Identitätsprüfung</b> an - erst
      danach ist dein Konto freigeschaltet, und erst dann startet dein
      Gratismonat. Die Prüfzeit geht dir also nicht ab.
    </p>
    <ol style="margin:0 0 22px;padding-left:20px;font-size:15px;line-height:1.7;">
      <li>Ein Live-Selfie, frontal in die Kamera (direkt in der App aufgenommen)</li>
      <li>Eine Aufnahme deines amtlichen Lichtbildausweises</li>
    </ol>
    <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#a0a0a8;">
      Die Prüfung erfolgt manuell durch einen Menschen - es kommt keine automatische
      Gesichtserkennung zum Einsatz. Die Aufnahmen werden nach Abschluss der Prüfung gelöscht.
    </p>
    <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#a0a0a8;">
      Du hast dich nicht bei FLEXR angemeldet? Dann ignoriere diese Mail einfach -
      ohne Bestätigung passiert mit der Adresse nichts.
    </p>
    <p style="margin:0;font-size:13px;line-height:1.6;color:#a0a0a8;">
      Fragen? Antworte einfach auf diese Mail oder schreib an
      <a href="mailto:{settings.support_email}" style="color:#e8e8ea;">{settings.support_email}</a>.
    </p>
  </div>
</body>
</html>
"""


def send_verification_email(email: str, name: str, link: str, ttl_hours: int = 24) -> bool:
    """Erste Mail nach der Registrierung: Adresse bestätigen.

    Ersetzt die frühere Willkommensmail - zwei Mails gleichzeitig wären eine zu
    viel, und die Aufforderung zur Verifizierung steht hier mit drin.
    """
    return send_email(
        to_address=email,
        subject=VERIFY_SUBJECT,
        text_body=_verify_text(name, link, ttl_hours),
        html_body=_verify_html(name, link, ttl_hours),
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

SUBSCRIPTION_SUBJECT = "Bestätigung deines FLEXR-Abos"


def _subscription_text(name: str) -> str:
    from . import legal

    return f"""Hallo {name},

danke für dein Abo. Diese Mail bestätigt den Vertragsabschluss.

  Leistung:            FLEXR-Mitgliedschaft (flexr.social)
  Preis:                {legal.PRICE_EUR_PER_MONTH} € pro Monat, Endpreis
  Abrechnung:           monatlich, automatische Verlängerung
  Laufzeit:             keine Mindestlaufzeit, monatlich kündbar
  Kündigen:             jederzeit im Konto unter "Abo verwalten / kündigen"

Du hast vor dem Abschluss ausdrücklich verlangt, dass wir mit der
kostenpflichtigen Leistung schon vor Ablauf der 14-tägigen Rücktrittsfrist
beginnen. Dein gesetzliches Rücktrittsrecht bleibt davon unberührt - bei
einem Rücktritt kann lediglich ein anteiliger Wertersatz für die bereits
erbrachte Leistung anfallen. Alles dazu, inklusive der Online-Funktion, steht
unter {legal.SITE_URL}/widerruf.html.

Fragen? Antworte einfach auf diese Mail.

{legal.OPERATOR_NAME}
{legal.OPERATOR_LEGAL_FORM}, {legal.OPERATOR_ROLE}
{legal.OPERATOR_STREET}, {legal.OPERATOR_ZIP} {legal.OPERATOR_CITY}
{legal.OPERATOR_EMAIL}
{legal.OPERATOR_PHONE}
"""


def _subscription_html(name: str) -> str:
    from . import legal

    body = "\n".join([
        _p("danke für dein Abo. Diese Mail bestätigt den Vertragsabschluss."),
        _kv_rows_html([
            ("Leistung", "FLEXR-Mitgliedschaft (flexr.social)"),
            ("Preis", f"{legal.PRICE_EUR_PER_MONTH} € pro Monat, Endpreis"),
            ("Abrechnung", "monatlich, automatische Verlängerung"),
            ("Laufzeit", "keine Mindestlaufzeit, monatlich kündbar"),
            ("Kündigen", 'jederzeit im Konto unter "Abo verwalten / kündigen"'),
        ]),
        _p(
            "Du hast vor dem Abschluss ausdrücklich verlangt, dass wir mit der "
            "kostenpflichtigen Leistung schon vor Ablauf der 14-tägigen "
            "Rücktrittsfrist beginnen. Dein gesetzliches Rücktrittsrecht bleibt "
            "davon unberührt - bei einem Rücktritt kann lediglich ein anteiliger "
            "Wertersatz für die bereits erbrachte Leistung anfallen. Alles dazu, "
            f"inklusive der Online-Funktion, steht unter {legal.SITE_URL}/widerruf.html."
        ),
    ])
    return _email_shell("Abo bestätigt", f"Hallo {html.escape(name)},", body, _operator_footer_html())


def send_subscription_confirmation(email: str, name: str) -> bool:
    """Vertragsbestätigung auf dauerhaftem Datenträger nach Zahlungsabschluss."""
    return send_email(
        to_address=email,
        subject=SUBSCRIPTION_SUBJECT,
        text_body=_subscription_text(name),
        html_body=_subscription_html(name),
    )


# ---------------------------------------------------------------------------
# Abo-Lebenszyklus (von Stripe-Webhooks ausgeloest)
# ---------------------------------------------------------------------------

VIENNA = ZoneInfo("Europe/Vienna")


def _date_from_unix(timestamp: int | None) -> str:
    if not timestamp:
        return "noch nicht bekannt"
    value = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(VIENNA)
    return value.strftime("%d.%m.%Y um %H:%M Uhr")


def _date_from_naive_utc(value: datetime) -> str:
    """Wie _date_from_unix, aber für naive UTC-Zeitstempel aus der DB (z.B.
    User.deleted_at) statt Unix-Timestamps aus Stripe-Payloads."""
    return value.replace(tzinfo=timezone.utc).astimezone(VIENNA).strftime("%d.%m.%Y")


def _money(amount_cents: int | None, currency: str | None) -> str:
    amount = (amount_cents or 0) / 100
    code = (currency or "EUR").upper()
    return f"{amount:.2f} {code}".replace(".", ",")


def _trial_ending_html(name: str, trial_end: int | None) -> str:
    from . import legal

    body = "\n".join([
        _p(
            f"dein FLEXR-Gratismonat endet am {_date_from_unix(trial_end)}. Danach "
            f"wird dein bereits abgeschlossenes Abo erstmals mit "
            f"{legal.PRICE_EUR_PER_MONTH} EUR pro Monat abgerechnet."
        ),
        _p(
            'Wenn du das nicht möchtest, kannst du das Abo vorher in FLEXR unter '
            '"Abo verwalten / kündigen" beenden. Bis zum Ende des Gratismonats '
            "bleibt dein Zugang erhalten."
        ),
    ])
    return _email_shell("Gratismonat endet bald", f"Hallo {html.escape(name)},", body)


def send_trial_ending(email: str, name: str, trial_end: int | None) -> bool:
    from . import legal

    body = f"""Hallo {name},

dein FLEXR-Gratismonat endet am {_date_from_unix(trial_end)}. Danach wird dein
bereits abgeschlossenes Abo erstmals mit {legal.PRICE_EUR_PER_MONTH} EUR pro
Monat abgerechnet.

Wenn du das nicht möchtest, kannst du das Abo vorher in FLEXR unter
"Abo verwalten / kündigen" beenden. Bis zum Ende des Gratismonats bleibt dein
Zugang erhalten.

Fragen? Antworte einfach auf diese Mail.

Dein FLEXR-Team
"""
    return send_email(email, "Dein FLEXR-Gratismonat endet bald", body, _trial_ending_html(name, trial_end))


def _renewal_reminder_html(name: str, amount_due: int | None, currency: str | None, charge_at: int | None) -> str:
    body = "\n".join([
        _p(
            f"dein FLEXR-Abo verlängert sich am {_date_from_unix(charge_at)} um "
            f"einen weiteren Monat. Der angekündigte Betrag ist "
            f"{_money(amount_due, currency)}."
        ),
        _p(
            'Du kannst dein Abo vorher jederzeit in FLEXR unter '
            '"Abo verwalten / kündigen" verwalten. Bei einer Kündigung bleibt '
            "der Zugang bis zum Ende des bereits bezahlten Zeitraums bestehen."
        ),
    ])
    return _email_shell("Abo verlängert sich", f"Hallo {html.escape(name)},", body)


def send_renewal_reminder(
    email: str,
    name: str,
    amount_due: int | None,
    currency: str | None,
    charge_at: int | None,
) -> bool:
    body = f"""Hallo {name},

dein FLEXR-Abo verlängert sich am {_date_from_unix(charge_at)} um einen
weiteren Monat. Der angekündigte Betrag ist {_money(amount_due, currency)}.

Du kannst dein Abo vorher jederzeit in FLEXR unter
"Abo verwalten / kündigen" verwalten. Bei einer Kündigung bleibt der Zugang
bis zum Ende des bereits bezahlten Zeitraums bestehen.

Dein FLEXR-Team
"""
    return send_email(
        email, "Deine nächste FLEXR-Aboverlängerung", body,
        _renewal_reminder_html(name, amount_due, currency, charge_at),
    )


def _payment_succeeded_html(name: str, amount_paid: int | None, currency: str | None, invoice_url: str | None) -> str:
    paragraphs = [
        _p(
            f"deine Zahlung über {_money(amount_paid, currency)} für FLEXR war "
            "erfolgreich. Dein Abo ist weiterhin aktiv."
        ),
    ]
    if invoice_url:
        link = html.escape(invoice_url)
        paragraphs.append(_p_raw(f'Rechnung/Beleg: <a href="{link}" style="color:#e8e8ea;">{link}</a>'))
    paragraphs.append(_p(
        'Du kannst dein Abo und deine Zahlungsdaten jederzeit in FLEXR unter '
        '"Abo verwalten / kündigen" verwalten.'
    ))
    return _email_shell("Zahlung erfolgreich", f"Hallo {html.escape(name)},", "\n".join(paragraphs))


def send_payment_succeeded(
    email: str,
    name: str,
    amount_paid: int | None,
    currency: str | None,
    invoice_url: str | None,
) -> bool:
    rechnung = f"\nRechnung/Beleg: {invoice_url}\n" if invoice_url else ""
    body = f"""Hallo {name},

deine Zahlung über {_money(amount_paid, currency)} für FLEXR war erfolgreich.
Dein Abo ist weiterhin aktiv.{rechnung}
Du kannst dein Abo und deine Zahlungsdaten jederzeit in FLEXR unter
"Abo verwalten / kündigen" verwalten.

Dein FLEXR-Team
"""
    return send_email(
        email, "Zahlung für FLEXR erfolgreich", body,
        _payment_succeeded_html(name, amount_paid, currency, invoice_url),
    )


def _payment_failed_html(
    name: str,
    amount_due: int | None,
    currency: str | None,
    next_attempt: int | None,
    invoice_url: str | None,
) -> str:
    next_text = (
        f"Der nächste Zahlungsversuch ist für {_date_from_unix(next_attempt)} vorgesehen."
        if next_attempt
        else "Stripe hat noch keinen weiteren Zahlungsversuch angekündigt."
    )
    paragraphs = [
        _p(
            f"die Zahlung über {_money(amount_due, currency)} für dein FLEXR-Abo "
            f"ist fehlgeschlagen. {next_text}"
        ),
        _p(
            'Bitte prüfe deine Zahlungsdaten in FLEXR unter "Abo verwalten / '
            'kündigen". Dein Zugang bleibt während der erneuten '
            "Zahlungsversuche vorerst aktiv."
        ),
    ]
    if invoice_url:
        link = html.escape(invoice_url)
        paragraphs.append(_p_raw(f'Offene Rechnung: <a href="{link}" style="color:#e8e8ea;">{link}</a>'))
    return _email_shell("Zahlung fehlgeschlagen", f"Hallo {html.escape(name)},", "\n".join(paragraphs))


def send_payment_failed(
    email: str,
    name: str,
    amount_due: int | None,
    currency: str | None,
    next_attempt: int | None,
    invoice_url: str | None,
) -> bool:
    next_text = (
        f"Der nächste Zahlungsversuch ist für {_date_from_unix(next_attempt)} vorgesehen."
        if next_attempt
        else "Stripe hat noch keinen weiteren Zahlungsversuch angekündigt."
    )
    rechnung = f"\nOffene Rechnung: {invoice_url}\n" if invoice_url else ""
    body = f"""Hallo {name},

die Zahlung über {_money(amount_due, currency)} für dein FLEXR-Abo ist
fehlgeschlagen. {next_text}

Bitte prüfe deine Zahlungsdaten in FLEXR unter "Abo verwalten / kündigen".
Dein Zugang bleibt während der erneuten Zahlungsversuche vorerst aktiv.{rechnung}
Dein FLEXR-Team
"""
    return send_email(
        email, "Zahlung für FLEXR fehlgeschlagen", body,
        _payment_failed_html(name, amount_due, currency, next_attempt, invoice_url),
    )


def _cancellation_scheduled_html(name: str, access_ends_at: int | None) -> str:
    body = "\n".join([
        _p(
            "deine Kündigung ist vorgemerkt. Es erfolgen keine weiteren "
            f"monatlichen Verlängerungen. Dein FLEXR-Zugang bleibt bis "
            f"{_date_from_unix(access_ends_at)} bestehen."
        ),
        _p("Du kannst die Kündigung bis dahin im Stripe-Kundenportal rückgängig machen."),
    ])
    return _email_shell("Kündigung vorgemerkt", f"Hallo {html.escape(name)},", body)


def send_cancellation_scheduled(
    email: str, name: str, access_ends_at: int | None
) -> bool:
    body = f"""Hallo {name},

deine Kündigung ist vorgemerkt. Es erfolgen keine weiteren monatlichen
Verlängerungen. Dein FLEXR-Zugang bleibt bis
{_date_from_unix(access_ends_at)} bestehen.

Du kannst die Kündigung bis dahin im Stripe-Kundenportal rückgängig machen.

Dein FLEXR-Team
"""
    return send_email(
        email, "Bestätigung deiner FLEXR-Kündigung", body,
        _cancellation_scheduled_html(name, access_ends_at),
    )


def _subscription_ended_html(name: str) -> str:
    body = _p(
        "dein FLEXR-Abo ist beendet. Es erfolgen keine weiteren Abbuchungen. "
        "Falls dein kostenloser Nutzungszeitraum ebenfalls abgelaufen ist, ist "
        "der Mitgliederzugang ab jetzt pausiert. Dein Konto bleibt bestehen "
        "und kann mit einem neuen Abo wieder aktiviert werden."
    )
    return _email_shell("Abo beendet", f"Hallo {html.escape(name)},", body)


def send_subscription_ended(email: str, name: str) -> bool:
    body = f"""Hallo {name},

dein FLEXR-Abo ist beendet. Es erfolgen keine weiteren Abbuchungen. Falls dein
kostenloser Nutzungszeitraum ebenfalls abgelaufen ist, ist der Mitgliederzugang
ab jetzt pausiert. Dein Konto bleibt bestehen und kann mit einem neuen Abo
wieder aktiviert werden.

Dein FLEXR-Team
"""
    return send_email(email, "Dein FLEXR-Abo ist beendet", body, _subscription_ended_html(name))


def _free_trial_ending_html(name: str, trial_end: datetime) -> str:
    end_text = trial_end.replace(tzinfo=timezone.utc).astimezone(VIENNA).strftime("%d.%m.%Y")
    body = "\n".join([
        _p(
            f"dein kostenloser FLEXR-Monat endet am {end_text}. Es erfolgt keine "
            "automatische Abbuchung: Du hast noch kein kostenpflichtiges Abo "
            "abgeschlossen."
        ),
        _p(
            'Wenn du FLEXR danach weiter nutzen möchtest, kannst du in der App '
            'unter "Mitgliedschaft" ein monatlich kündbares Abo abschließen. '
            "Ohne Abo wird dein Mitgliederzugang nach dem Gratismonat "
            "pausiert; dein Konto bleibt bestehen."
        ),
    ])
    return _email_shell("Gratismonat endet bald", f"Hallo {html.escape(name)},", body)


def send_free_trial_ending(email: str, name: str, trial_end: datetime) -> bool:
    end_text = trial_end.replace(tzinfo=timezone.utc).astimezone(VIENNA).strftime("%d.%m.%Y")
    body = f"""Hallo {name},

dein kostenloser FLEXR-Monat endet am {end_text}. Es erfolgt keine automatische
Abbuchung: Du hast noch kein kostenpflichtiges Abo abgeschlossen.

Wenn du FLEXR danach weiter nutzen möchtest, kannst du in der App unter
"Mitgliedschaft" ein monatlich kündbares Abo abschließen. Ohne Abo wird dein
Mitgliederzugang nach dem Gratismonat pausiert; dein Konto bleibt bestehen.

Dein FLEXR-Team
"""
    return send_email(
        email, "Dein kostenloser FLEXR-Monat endet bald", body,
        _free_trial_ending_html(name, trial_end),
    )


def _free_trial_ended_html(name: str) -> str:
    body = "\n".join([
        _p(
            "dein kostenloser FLEXR-Monat ist beendet. Weil du kein "
            "kostenpflichtiges Abo abgeschlossen hast, wurde nichts abgebucht "
            "und dein Mitgliederzugang ist jetzt pausiert. Dein Konto und "
            "dein Profil bleiben bestehen."
        ),
        _p(
            'Du kannst den Zugang jederzeit in FLEXR unter "Mitgliedschaft" '
            "mit einem monatlich kündbaren Abo wieder aktivieren."
        ),
    ])
    return _email_shell("Gratismonat beendet", f"Hallo {html.escape(name)},", body)


def send_free_trial_ended(email: str, name: str) -> bool:
    body = f"""Hallo {name},

dein kostenloser FLEXR-Monat ist beendet. Weil du kein kostenpflichtiges Abo
abgeschlossen hast, wurde nichts abgebucht und dein Mitgliederzugang ist jetzt
pausiert. Dein Konto und dein Profil bleiben bestehen.

Du kannst den Zugang jederzeit in FLEXR unter "Mitgliedschaft" mit einem
monatlich kündbaren Abo wieder aktivieren.

Dein FLEXR-Team
"""
    return send_email(email, "Dein kostenloser FLEXR-Monat ist beendet", body, _free_trial_ended_html(name))


# ---------------------------------------------------------------------------
# Aktivitäts-Benachrichtigungen (neues Match, wartende Profile, Inaktivität)
#
# Anders als die Abrechnungs- und Moderationsmails sind das die einzigen
# abbestellbaren Nachrichten: jede hat im Profil unter "Benachrichtigungen"
# einen eigenen Schalter (siehe notifications.py). Der Hinweis darauf steht
# deshalb in jedem dieser drei Texte.
# ---------------------------------------------------------------------------

_NOTIFY_OPT_OUT = (
    'Du kannst diese Benachrichtigung jederzeit in FLEXR unter '
    '"Benachrichtigungen" im Profil abschalten.'
)


def _new_match_html(name: str, match_name: str) -> str:
    body = "\n".join([
        _p(
            f"{html.escape(match_name)} hat dich auch geliked - ihr habt ein "
            "Match. Ab jetzt könnt ihr euch in FLEXR schreiben."
        ),
        _p(_NOTIFY_OPT_OUT),
    ])
    return _email_shell("Neues Match", f"Hallo {html.escape(name)},", body)


def send_new_match(email: str, name: str, match_name: str) -> bool:
    body = f"""Hallo {name},

{match_name} hat dich auch geliked - ihr habt ein Match. Ab jetzt könnt ihr euch
in FLEXR schreiben.

{_NOTIFY_OPT_OUT}

Dein FLEXR-Team
"""
    return send_email(
        email, f"Neues Match mit {match_name}", body, _new_match_html(name, match_name),
    )


def _queue_waiting_html(name: str, count: int) -> str:
    body = "\n".join([
        _p(
            f"In deinem Suchradius warten gerade {count} neue Profile darauf, "
            "von dir bewertet zu werden."
        ),
        _p(_NOTIFY_OPT_OUT),
    ])
    return _email_shell("Neue Profile", f"Hallo {html.escape(name)},", body)


def send_queue_waiting(email: str, name: str, count: int) -> bool:
    body = f"""Hallo {name},

in deinem Suchradius warten gerade {count} neue Profile darauf, von dir bewertet
zu werden.

{_NOTIFY_OPT_OUT}

Dein FLEXR-Team
"""
    return send_email(
        email, f"{count} neue Profile in deinem Umkreis", body,
        _queue_waiting_html(name, count),
    )


def _inactivity_html(name: str, days: int) -> str:
    body = "\n".join([
        _p(
            f"du warst {days} Tage nicht mehr in FLEXR. In der Zwischenzeit "
            "können neue Profile in deinem Umkreis dazugekommen sein."
        ),
        _p(_NOTIFY_OPT_OUT),
    ])
    return _email_shell("Lange nicht gesehen", f"Hallo {html.escape(name)},", body)


def send_inactivity_reminder(email: str, name: str, days: int) -> bool:
    body = f"""Hallo {name},

du warst {days} Tage nicht mehr in FLEXR. In der Zwischenzeit können neue Profile
in deinem Umkreis dazugekommen sein.

{_NOTIFY_OPT_OUT}

Dein FLEXR-Team
"""
    return send_email(
        email, "Lange nicht gesehen bei FLEXR", body, _inactivity_html(name, days),
    )


# ---------------------------------------------------------------------------
# Bestätigung der Selbstlöschung (30-Tage-Karenzzeit)
#
# Wird unmittelbar bei DELETE /api/profiles/me verschickt (siehe
# routers/profiles.py). Erklärt, was mit der Karenzzeit passiert und dass eine
# Reaktivierung per erneutem Login möglich ist (siehe routers/auth.reactivate).
# ---------------------------------------------------------------------------

DELETION_SUBJECT = "Bestätigung: Dein FLEXR-Konto wurde gelöscht"


def _deletion_text(name: str, purge_date: str, grace_days: int) -> str:
    return f"""Hallo {name},

dein FLEXR-Konto wurde soeben deaktiviert. Diese Mail bestätigt deinen
Löschauftrag.

Was das bedeutet:

  - Dein Profil ist ab sofort für andere Mitglieder unsichtbar, ein Login
    ist vorerst nicht mehr möglich.
  - Deine Konto- und Profildaten bleiben noch bis zum {purge_date}
    gespeichert ({grace_days} Tage Karenzzeit) und werden danach
    unwiderruflich gelöscht.
  - Dein Verifizierungs-Selfie und deine Ausweisaufnahme wurden bereits
    jetzt gelöscht, ohne auf die Karenzzeit zu warten.

Meinung geändert? Bis zum {purge_date} kannst du dein Konto reaktivieren:
Melde dich einfach mit deiner E-Mail-Adresse und deinem bisherigen Passwort
erneut an - der Login bietet dir die Reaktivierung dann von selbst an. Nach
Ablauf der Frist ist das nicht mehr möglich, und die Daten sind endgültig
weg.

Warst du das nicht? Dann kennt jemand dein Passwort - antworte umgehend auf
diese Mail oder schreib an {settings.support_email}, wir kümmern uns darum.

Einzelheiten zur Löschung stehen in unserer Datenschutzerklärung.

Dein FLEXR-Team
"""


def _deletion_html(name: str, purge_date: str, grace_days: int) -> str:
    body = "\n".join([
        _p("Dein FLEXR-Konto wurde soeben deaktiviert. Diese Mail bestätigt deinen Löschauftrag."),
        _ul([
            "Dein Profil ist ab sofort für andere Mitglieder unsichtbar, ein "
            "Login ist vorerst nicht mehr möglich.",
            f"Deine Konto- und Profildaten bleiben noch bis zum {purge_date} "
            f"gespeichert ({grace_days} Tage Karenzzeit) und werden danach "
            "unwiderruflich gelöscht.",
            "Dein Verifizierungs-Selfie und deine Ausweisaufnahme wurden "
            "bereits jetzt gelöscht, ohne auf die Karenzzeit zu warten.",
        ]),
        _p(
            f"Meinung geändert? Bis zum {purge_date} kannst du dein Konto "
            "reaktivieren: Melde dich einfach mit deiner E-Mail-Adresse und "
            "deinem bisherigen Passwort erneut an - der Login bietet dir die "
            "Reaktivierung dann von selbst an. Nach Ablauf der Frist ist das "
            "nicht mehr möglich, und die Daten sind endgültig weg."
        ),
        _p(
            "Warst du das nicht? Dann kennt jemand dein Passwort - antworte "
            f"umgehend auf diese Mail oder schreib an {settings.support_email}, "
            "wir kümmern uns darum."
        ),
        _p("Einzelheiten zur Löschung stehen in unserer Datenschutzerklärung."),
    ])
    return _email_shell("Konto gelöscht", f"Hallo {html.escape(name)},", body)


def send_account_deletion_confirmation(
    email: str, name: str, purge_at: datetime, grace_days: int
) -> bool:
    """Bestätigung der Selbstlöschung, mit kurzen Wiederholungen bei Fehlschlag.

    Analog zur Rücktrittsbestätigung: Die Löschung selbst ist zu diesem
    Zeitpunkt schon in der DB vollzogen (deleted_at gesetzt) - ein einzelner
    SMTP-Aussetzer soll die Bestätigung trotzdem nicht kippen lassen.
    """
    purge_date = _date_from_naive_utc(purge_at)
    return send_email_with_retry(
        to_address=email,
        subject=DELETION_SUBJECT,
        text_body=_deletion_text(name, purge_date, grace_days),
        html_body=_deletion_html(name, purge_date, grace_days),
        attempts=2,
        delay_seconds=1,
    )


# ---------------------------------------------------------------------------
# Verifizierung und Moderation
# ---------------------------------------------------------------------------


def _decision_html(name: str, eyebrow: str, detail: str) -> str:
    """Gebrandete Fassung im selben Look wie _verify_html - fuer kurze
    Status-Mails ohne eigenen Call-to-Action-Link."""
    name_safe = html.escape(name)
    detail_html = html.escape(detail).replace("\n", "<br>")
    return f"""<!doctype html>
<html lang="de">
<body style="margin:0;padding:24px;background:#0f0f11;font-family:Helvetica,Arial,sans-serif;color:#e8e8ea;">
  <div style="max-width:520px;margin:0 auto;background:#17171a;border:1px solid #2a2a30;border-radius:16px;padding:28px;">
    <p style="margin:0 0 6px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#ff5a1f;">{html.escape(eyebrow)}</p>
    <h1 style="margin:0 0 18px;font-size:22px;line-height:1.3;color:#ffffff;">Hallo {name_safe},</h1>
    <p style="margin:0 0 22px;font-size:15px;line-height:1.6;">
      {detail_html}
    </p>
    <p style="margin:0;font-size:13px;line-height:1.6;color:#a0a0a8;">
      Öffne FLEXR, um deinen aktuellen Status und die nächsten Schritte zu sehen.
      Fragen? Antworte einfach auf diese Mail oder schreib an
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
) -> bool:
    if outcome == "approved":
        subject = "Dein FLEXR-Konto ist freigeschaltet"
        eyebrow = "Freigeschaltet"
        detail = (
            "Deine Alters- und Identitätsprüfung wurde bestätigt. "
            "Dein Konto ist jetzt freigeschaltet."
        )
    elif outcome == "reupload_required":
        subject = "FLEXR braucht eine neue Verifizierungsaufnahme"
        eyebrow = "Nachbesserung nötig"
        umfang = "Selfie und Ausweisaufnahme" if redo_selfie else "Ausweisaufnahme"
        detail = f"Bitte lade {umfang} erneut hoch. Grund: {reason or 'Aufnahme nicht verwertbar.'}"
    else:
        subject = "Deine FLEXR-Verifizierung wurde abgelehnt"
        eyebrow = "Verifizierung abgelehnt"
        detail = f"Die Prüfung konnte nicht bestätigt werden. Grund: {reason or 'Prüfung nicht erfolgreich.'}"
    body = f"""Hallo {name},

{detail}

Öffne FLEXR, um deinen aktuellen Status und die nächsten Schritte zu sehen.
Bei Fragen antworte auf diese Mail.

Dein FLEXR-Team
"""
    return send_email_with_retry(
        email, subject, body, _decision_html(name, eyebrow, detail), attempts=2, delay_seconds=1,
    )


def _verification_required_html(name: str) -> str:
    body = "\n".join([
        _p(
            "für dein FLEXR-Konto ist eine Alters- und Identitätsprüfung "
            "erforderlich. Dein Konto ist bis zum Abschluss vorübergehend "
            "pausiert."
        ),
        _p(
            "Öffne FLEXR und folge dort den Schritten für Live-Selfie und "
            "amtlichen Lichtbildausweis. Die Prüfung erfolgt manuell; es "
            "findet keine automatische Gesichtserkennung statt. Die "
            "Prüfaufnahmen werden anschließend gelöscht."
        ),
    ])
    return _email_shell("Prüfung erforderlich", f"Hallo {html.escape(name)},", body)


def send_verification_required(email: str, name: str) -> bool:
    body = f"""Hallo {name},

für dein FLEXR-Konto ist eine Alters- und Identitätsprüfung erforderlich. Dein
Konto ist bis zum Abschluss vorübergehend pausiert.

Öffne FLEXR und folge dort den Schritten für Live-Selfie und amtlichen
Lichtbildausweis. Die Prüfung erfolgt manuell; es findet keine automatische
Gesichtserkennung statt. Die Prüfaufnahmen werden anschließend gelöscht.

Bei Fragen antworte auf diese Mail.

Dein FLEXR-Team
"""
    return send_email_with_retry(
        email,
        "Alters- und Identitätsprüfung für dein FLEXR-Konto",
        body,
        _verification_required_html(name),
        attempts=2,
        delay_seconds=1,
    )


def _moderation_decision_html(
    name: str, measure: str, summary: str, details: list[str] | None, appeal: bool
) -> str:
    parts = [_p(measure), _p(f"Begründung: {summary}")]
    detail_items = [line for line in (details or []) if line]
    if detail_items:
        parts.append(_p("Einzelheiten:"))
        parts.append(_ul(detail_items))
    if appeal:
        parts.append(_p(
            "Du kannst der Entscheidung formlos per Antwort auf diese Mail "
            "widersprechen. Wir prüfen sie dann erneut und antworten "
            "begründet. Der Rechtsweg bleibt unbenommen."
        ))
    return _email_shell("Kontomitteilung", f"Hallo {html.escape(name)},", "\n".join(parts))


def send_moderation_decision(
    email: str,
    name: str,
    measure: str,
    summary: str,
    details: list[str] | None = None,
    appeal: bool = True,
) -> bool:
    detail_text = "\n".join(f"- {line}" for line in (details or []) if line)
    if detail_text:
        detail_text = "\n\nEinzelheiten:\n" + detail_text
    appeal_text = ""
    if appeal:
        appeal_text = (
            "\n\nDu kannst der Entscheidung formlos per Antwort auf diese Mail "
            "widersprechen.\nWir prüfen sie dann erneut und antworten begründet. "
            "Der Rechtsweg bleibt\nunbenommen."
        )
    body = f"""Hallo {name},

{measure}

Begründung: {summary}{detail_text}{appeal_text}

Dein FLEXR-Team
"""
    return send_email_with_retry(
        email, "Wichtige Mitteilung zu deinem FLEXR-Konto", body,
        _moderation_decision_html(name, measure, summary, details, appeal),
        attempts=2, delay_seconds=1,
    )


def _photo_rejected_html(name: str, reason: str) -> str:
    body = "\n".join([
        _p("Ein Profilfoto wurde nicht freigegeben und aus deinem sichtbaren Profil entfernt."),
        _p(f"Begründung: {reason}"),
        _p(
            "Du kannst ein neues Foto hochladen. Wenn du die Entscheidung für "
            "falsch hältst, antworte bitte auf diese Mail."
        ),
    ])
    return _email_shell("Foto abgelehnt", f"Hallo {html.escape(name)},", body)


def send_photo_rejected(email: str, name: str, reason: str) -> bool:
    body = f"""Hallo {name},

ein Profilfoto wurde nicht freigegeben und aus deinem sichtbaren Profil
entfernt.

Begründung: {reason}

Du kannst ein neues Foto hochladen. Wenn du die Entscheidung für falsch
hältst, antworte bitte auf diese Mail.

Dein FLEXR-Team
"""
    return send_email_with_retry(
        email, "Ein FLEXR-Profilfoto wurde abgelehnt", body, _photo_rejected_html(name, reason),
        attempts=2, delay_seconds=1,
    )


def _report_decision_html(reference: str, outcome: str, reason: str) -> str:
    body = "\n".join([
        _p(f"wir haben deine Meldung {reference} geprüft."),
        _kv_rows_html([("Ergebnis", outcome), ("Begründung", reason)]),
        _p(
            "Du kannst der Entscheidung formlos per Antwort auf diese Mail "
            "widersprechen. Der Rechtsweg bleibt unbenommen."
        ),
    ])
    return _email_shell("Meldung entschieden", "Hallo,", body)


def send_report_decision(
    email: str, reference: str, outcome: str, reason: str
) -> bool:
    body = f"""Hallo,

wir haben deine Meldung {reference} geprüft.

Ergebnis: {outcome}
Begründung: {reason}

Du kannst der Entscheidung formlos per Antwort auf diese Mail widersprechen.
Der Rechtsweg bleibt unbenommen.

Dein FLEXR-Team
"""
    return send_email_with_retry(
        email, f"Entscheidung zu deiner FLEXR-Meldung {reference}", body,
        _report_decision_html(reference, outcome, reason),
        attempts=2, delay_seconds=1,
    )


# ---------------------------------------------------------------------------
# Rücktrittsbestätigung (§ 13a Abs. 4 FAGG)
#
# Die Bestätigung muss auf einem dauerhaften Datenträger erfolgen und den
# Inhalt der Erklärung samt Datum und Uhrzeit wiedergeben. Deshalb steht der
# Wortlaut hier vollständig in der Mail und nicht nur ein "Wir haben Ihren
# Widerruf erhalten".
# ---------------------------------------------------------------------------

WITHDRAWAL_SUBJECT = "Bestätigung deines Rücktritts ({reference}) — FLEXR"


def _withdrawal_text(
    name: str,
    reference: str,
    received_at: str,
    declaration_text: str,
    contract_reference: str | None,
    subscription_stopped: bool = False,
) -> str:
    from . import legal

    vertrag = contract_reference or "— keine Angabe —"
    if subscription_stopped:
        folge = (
            "Was jetzt passiert: Ein zugeordnetes laufendes Abo ist bereits an der "
            "weiteren Verlängerung gehindert - es wird nicht erneut abgebucht. Wir "
            "prüfen die Erklärung und wickeln einen bereits bezahlten Zeitraum "
            "anteilig ab; bereits geleistete Zahlungen erstatten wir über dasselbe "
            "Zahlungsmittel, mit dem du bezahlt hast."
        )
    else:
        folge = (
            "Was jetzt passiert: Wir prüfen die Erklärung, ordnen sie deinem Vertrag "
            "zu und verhindern eine weitere Verlängerung. Bereits geleistete "
            "Zahlungen erstatten wir über dasselbe Zahlungsmittel, mit dem du "
            "bezahlt hast."
        )
    return f"""Hallo {name},

deine Rücktrittserklärung ist bei uns eingegangen. Diese Mail ist die
Bestätigung nach § 13a Abs. 4 FAGG — bewahre sie auf.

  Aktenzeichen:      {reference}
  Eingegangen am:    {received_at} (Uhrzeit in MEZ/MESZ)
  Vertrag/Konto:     {vertrag}

Wortlaut deiner Erklärung:

{declaration_text}

{folge}

Fragen? Antworte einfach auf diese Mail.

{legal.OPERATOR_NAME}
{legal.OPERATOR_LEGAL_FORM}, {legal.OPERATOR_ROLE}
{legal.OPERATOR_STREET}, {legal.OPERATOR_ZIP} {legal.OPERATOR_CITY}
{legal.OPERATOR_EMAIL}
{legal.OPERATOR_PHONE}
"""


def _withdrawal_html(
    name: str,
    reference: str,
    received_at: str,
    declaration_text: str,
    contract_reference: str | None,
    subscription_stopped: bool = False,
) -> str:
    vertrag = contract_reference or "— keine Angabe —"
    if subscription_stopped:
        folge = (
            "Was jetzt passiert: Ein zugeordnetes laufendes Abo ist bereits an "
            "der weiteren Verlängerung gehindert - es wird nicht erneut "
            "abgebucht. Wir prüfen die Erklärung und wickeln einen bereits "
            "bezahlten Zeitraum anteilig ab; bereits geleistete Zahlungen "
            "erstatten wir über dasselbe Zahlungsmittel, mit dem du bezahlt hast."
        )
    else:
        folge = (
            "Was jetzt passiert: Wir prüfen die Erklärung, ordnen sie deinem "
            "Vertrag zu und verhindern eine weitere Verlängerung. Bereits "
            "geleistete Zahlungen erstatten wir über dasselbe Zahlungsmittel, "
            "mit dem du bezahlt hast."
        )
    declaration_html = html.escape(declaration_text).replace(chr(10), "<br>")
    body = "\n".join([
        _p(
            "deine Rücktrittserklärung ist bei uns eingegangen. Diese Mail "
            "ist die Bestätigung nach § 13a Abs. 4 FAGG — bewahre sie auf."
        ),
        _kv_rows_html([
            ("Aktenzeichen", reference),
            ("Eingegangen am", f"{received_at} (Uhrzeit in MEZ/MESZ)"),
            ("Vertrag/Konto", vertrag),
        ]),
        _p("Wortlaut deiner Erklärung:"),
        f'    <blockquote style="margin:0 0 18px;padding:2px 16px;'
        f'border-left:2px solid #2a2a30;font-size:14px;line-height:1.6;'
        f'color:#c8c8ce;">{declaration_html}</blockquote>',
        _p(folge),
    ])
    return _email_shell("Rücktritt bestätigt", f"Hallo {html.escape(name)},", body, _operator_footer_html())


def send_withdrawal_confirmation(
    email: str,
    name: str,
    reference: str,
    received_at: str,
    declaration_text: str,
    contract_reference: str | None = None,
    subscription_stopped: bool = False,
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
        subject=WITHDRAWAL_SUBJECT.format(reference=reference),
        text_body=_withdrawal_text(
            name, reference, received_at, declaration_text, contract_reference,
            subscription_stopped,
        ),
        html_body=_withdrawal_html(
            name, reference, received_at, declaration_text, contract_reference,
            subscription_stopped,
        ),
    )


# ---------------------------------------------------------------------------
# Empfangsbestätigung einer DSA-Meldung (Art. 16 Abs. 4)
# ---------------------------------------------------------------------------

NOTICE_SUBJECT = "Deine Meldung an FLEXR ({reference})"


def _notice_text(reference: str, received_at: str, category_label: str) -> str:
    from . import legal

    return f"""Hallo,

deine Meldung ist bei uns eingegangen.

  Aktenzeichen:   {reference}
  Eingegangen am: {received_at}
  Kategorie:      {category_label}

Ein Mensch sieht sich die Meldung an — in der Regel binnen 72 Stunden, bei
Gefahr für eine Person sofort. Du bekommst danach eine begründete Entscheidung
an diese Adresse.

Diese Bestätigung erfolgt nach Art. 16 Abs. 4 der Verordnung (EU) 2022/2065
(Gesetz über digitale Dienste). Wenn du der Entscheidung später widersprechen
willst, genügt eine formlose Antwort auf diese Mail unter Angabe des
Aktenzeichens.

{legal.OPERATOR_NAME}
{legal.OPERATOR_LEGAL_FORM}, {legal.OPERATOR_ROLE}
{legal.OPERATOR_EMAIL}
"""


def _notice_html(reference: str, received_at: str, category_label: str) -> str:
    body = "\n".join([
        _p("deine Meldung ist bei uns eingegangen."),
        _kv_rows_html([
            ("Aktenzeichen", reference),
            ("Eingegangen am", received_at),
            ("Kategorie", category_label),
        ]),
        _p(
            "Ein Mensch sieht sich die Meldung an — in der Regel binnen 72 "
            "Stunden, bei Gefahr für eine Person sofort. Du bekommst danach "
            "eine begründete Entscheidung an diese Adresse."
        ),
        _p(
            "Diese Bestätigung erfolgt nach Art. 16 Abs. 4 der Verordnung "
            "(EU) 2022/2065 (Gesetz über digitale Dienste). Wenn du der "
            "Entscheidung später widersprechen willst, genügt eine formlose "
            "Antwort auf diese Mail unter Angabe des Aktenzeichens."
        ),
    ])
    return _email_shell("Meldung eingegangen", "Hallo,", body, _operator_footer_html(full=False))


def send_notice_acknowledgement(
    email: str, reference: str, received_at: str, category_label: str
) -> bool:
    """Empfangsbestätigung an den Melder, sofern er eine Adresse angegeben hat."""
    return send_email(
        to_address=email,
        subject=NOTICE_SUBJECT.format(reference=reference),
        text_body=_notice_text(reference, received_at, category_label),
        html_body=_notice_html(reference, received_at, category_label),
    )
