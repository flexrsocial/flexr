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
from email.message import EmailMessage
from email.utils import formataddr

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


def send_subscription_confirmation(email: str, name: str) -> bool:
    """Vertragsbestätigung auf dauerhaftem Datenträger nach Zahlungsabschluss."""
    return send_email(
        to_address=email,
        subject=SUBSCRIPTION_SUBJECT,
        text_body=_subscription_text(name),
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
) -> str:
    from . import legal

    vertrag = contract_reference or "— keine Angabe —"
    return f"""Hallo {name},

deine Rücktrittserklärung ist bei uns eingegangen. Diese Mail ist die
Bestätigung nach § 13a Abs. 4 FAGG — bewahre sie auf.

  Aktenzeichen:      {reference}
  Eingegangen am:    {received_at} (Uhrzeit in MEZ/MESZ)
  Vertrag/Konto:     {vertrag}

Wortlaut deiner Erklärung:

{declaration_text}

Was jetzt passiert: Wir prüfen die Erklärung und wickeln einen bereits
bezahlten Zeitraum anteilig ab. Bereits geleistete Zahlungen erstatten wir
über dasselbe Zahlungsmittel, mit dem du bezahlt hast.

Wichtig, damit nichts durcheinandergerät: Ein Rücktritt ist etwas anderes als
eine Kündigung. Wenn du zusätzlich willst, dass ein laufendes Abo nicht weiter
verlängert wird, beende es bitte auch unter "Abo verwalten / kündigen" in
deinem Konto.

Fragen? Antworte einfach auf diese Mail.

{legal.OPERATOR_NAME}
{legal.OPERATOR_LEGAL_FORM}, {legal.OPERATOR_ROLE}
{legal.OPERATOR_STREET}, {legal.OPERATOR_ZIP} {legal.OPERATOR_CITY}
{legal.OPERATOR_EMAIL}
{legal.OPERATOR_PHONE}
"""


def send_withdrawal_confirmation(
    email: str,
    name: str,
    reference: str,
    received_at: str,
    declaration_text: str,
    contract_reference: str | None = None,
) -> bool:
    """Unverzügliche Bestätigung einer Rücktrittserklärung."""
    return send_email(
        to_address=email,
        subject=WITHDRAWAL_SUBJECT.format(reference=reference),
        text_body=_withdrawal_text(
            name, reference, received_at, declaration_text, contract_reference
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


def send_notice_acknowledgement(
    email: str, reference: str, received_at: str, category_label: str
) -> bool:
    """Empfangsbestätigung an den Melder, sofern er eine Adresse angegeben hat."""
    return send_email(
        to_address=email,
        subject=NOTICE_SUBJECT.format(reference=reference),
        text_body=_notice_text(reference, received_at, category_label),
    )

