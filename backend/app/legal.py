"""Betreiberangaben und Fassungsstände der Rechtstexte — an einer Stelle.

Bis zum 15.08.2026 stand als Rechtsträger auf sieben Webseiten, in der
Android-App und in der iOS-App die Zeichenfolge "flexr.social
Kleinunternehmen". Das ist keine Rechtsform und war als Bezeichnung des
Rechtsträgers falsch: hinter FLEXR steht eine natürliche Person, nicht ein
so benanntes Unternehmen. Beim Korrigieren fiel auf, dass die Angaben in den
drei Oberflächen ohnehin schon auseinandergelaufen waren.

Deshalb: eine Quelle. ``shared/betreiber.json`` im Repository-Wurzelverzeichnis
ist maßgeblich, dieses Modul spiegelt sie für den Server (Mails,
Rücktrittsbestätigungen). ``backend/tests/test_betreiber.py`` hält beide
zusammen, ``tools/check_betreiber.py`` prüft Web, Android und iOS dagegen.

Die Fassungsstände unten sind Vertragsinhalt: Welche AGB-Fassung ein Nutzer
akzeptiert hat, wird bei der Registrierung mitgeschrieben (siehe models.Consent).
Wer einen Rechtstext inhaltlich ändert, erhöht hier die Fassung.
"""

from typing import Final

# ---------------------------------------------------------------------------
# Marke
# ---------------------------------------------------------------------------

BRAND: Final = "FLEXR"
POSITIONING: Final = "Dating für Gym-People in Österreich"
DOMAIN: Final = "flexr.social"
SITE_URL: Final = "https://flexr.social"

# ---------------------------------------------------------------------------
# Rechtsträger
#
# Julian Pachernegg ist Einzelunternehmer und nicht im Firmenbuch eingetragen.
# Deshalb steht in den Rechtstexten weder eine Firmenbuchnummer noch ein
# Verweis auf § 14 UGB - der richtet sich an eingetragene Unternehmer.
# ---------------------------------------------------------------------------

OPERATOR_NAME: Final = "Julian Pachernegg"
OPERATOR_LEGAL_FORM: Final = "Einzelunternehmer"
OPERATOR_ROLE: Final = "Betreiber von FLEXR"
OPERATOR_STREET: Final = "Johann-Schrey-Weg 260"
OPERATOR_ZIP: Final = "8232"
OPERATOR_CITY: Final = "Grafendorf"
OPERATOR_COUNTRY: Final = "Österreich"
OPERATOR_EMAIL: Final = "flexr.social@proton.me"
# Geschäftliche Kontaktnummer, nur an gesetzlich/vertraglich erforderlichen
# Stellen zu verwenden (Impressum, vorvertragliche Anbieterinformation,
# Rücktrittsbelehrung, Vertragsbestätigung) - kein Marketingelement, siehe
# operator_block()/operator_inline(), die sie deshalb bewusst NICHT enthalten.
OPERATOR_PHONE: Final = "+43 676 874030574"

OPERATOR_SUBJECT: Final = "Betrieb der Online-Dating-Plattform FLEXR (flexr.social)"


def operator_block(separator: str = "\n") -> str:
    """Anschriftenblock, wie er in Rechtstexten und Mails erscheint."""
    return separator.join(
        [
            OPERATOR_NAME,
            f"{OPERATOR_LEGAL_FORM}, {OPERATOR_ROLE}",
            OPERATOR_STREET,
            f"{OPERATOR_ZIP} {OPERATOR_CITY}, {OPERATOR_COUNTRY}",
            OPERATOR_EMAIL,
        ]
    )


def operator_inline() -> str:
    """Einzeiler für Fließtext ("... betrieben von X, Y, Z")."""
    return (
        f"{OPERATOR_NAME}, {OPERATOR_LEGAL_FORM}, {OPERATOR_STREET}, "
        f"{OPERATOR_ZIP} {OPERATOR_CITY}, {OPERATOR_COUNTRY}"
    )


# ---------------------------------------------------------------------------
# Fassungsstände der Rechtstexte
#
# Format: JJJJ-MM-TT. Wird als Vertragsfassung gespeichert (Consent-Log) und
# steht sichtbar unter "Stand:" auf jeder Seite.
# ---------------------------------------------------------------------------

TERMS_VERSION: Final = "2026-09-10"           # AGB (Punkt 7/9: Gratis-Plattform + FLEXR Premium)
PRIVACY_VERSION: Final = "2026-08-19"          # Datenschutzerklärung
AUP_VERSION: Final = "2026-08-19"              # Nutzungsrichtlinien
LE_GUIDELINES_VERSION: Final = "2026-08-19"    # Strafverfolgungsrichtlinien
WITHDRAWAL_VERSION: Final = "2026-08-17"      # Widerrufsbelehrung
WITHDRAWAL_ACK_VERSION: Final = "2026-08-17"  # Checkout: Kenntnisnahme Erlöschen Rücktrittsrecht


# ---------------------------------------------------------------------------
# Preis und Vertragsmodell  (Stand 10.09.2026)
#
# Maßgeblich ist der Code, nicht dieser Block - er hält nur fest, was
# routers/billing.py, premium.py und stripe_client.py tatsächlich tun, damit
# die Texte nicht davon abweichen:
#
#   * **Die Nutzung von FLEXR ist unbefristet unentgeltlich.** Registrieren,
#     Profile sehen, liken, matchen und schreiben kosten nichts - dauerhaft,
#     nicht nur während der Beta. Es gibt keine Bezahlwand und keinen
#     Probemonat; kein Konto wird mangels Zahlung gesperrt.
#   * Bei der Registrierung wird KEIN Zahlungsmittel erhoben.
#   * Ein zahlungspflichtiger Vertrag entsteht ausschließlich durch den aktiven
#     Abschluss von FLEXR Premium im Stripe-Checkout
#     (POST /api/billing/checkout) - ein Dauerschuldverhältnis über
#     PRICE_EUR_PER_MONTH pro Monat, jederzeit zum Ende des laufenden
#     Abrechnungszeitraums kündbar (Stripe Billing Portal, POST /portal).
#   * Premium schaltet ausschließlich Zusatzfunktionen frei. Ohne Premium
#     gelten die Grenzen aus ``config.py`` (free_daily_likes,
#     free_open_chats, free_max_radius_km) - sie schränken den Umfang ein,
#     nicht den Zugang.
#
# Premium ist derzeit **noch nicht buchbar**: settings.premium_enabled steht
# auf False (Beta), /api/billing/checkout lehnt mit 409 ab, und die Grenzen für
# Standardnutzer greifen noch nicht. Die Rechtstexte nennen Preis und Grenzen
# deshalb ausdrücklich als "ab dem Ende der Beta-Phase".
#
# TRIAL_AUTO_CONVERTS bleibt als Konstante stehen, weil die Rechtstexte die
# Aussage "wandelt sich nicht selbsttätig in ein Abo um" weiterhin treffen -
# sie ist heute sogar trivial wahr, da es gar keinen Probezeitraum mehr gibt.
# ---------------------------------------------------------------------------

PRICE_EUR_PER_MONTH: Final = "10"
TRIAL_AUTO_CONVERTS: Final = False

# Grenzen des kostenlosen Kontos, wie sie in den Rechtstexten zugesagt sind.
# Sie spiegeln settings.free_* - hier gespiegelt, damit die Vertragsfassung
# nachvollziehbar bleibt, wenn die Betriebswerte später einmal steigen.
FREE_DAILY_LIKES: Final = "20"
FREE_OPEN_CHATS: Final = "3"
FREE_MAX_RADIUS_KM: Final = "50"


# ---------------------------------------------------------------------------
# § 13a FAGG — Online-Rücktrittsfunktion
#
# Die Pflicht, auf der Online-Benutzeroberfläche eine leicht auffindbare
# Rücktrittsfunktion bereitzustellen, tritt in Österreich am 1. Oktober 2026
# in Kraft. Die Funktion selbst (routers/withdrawal.py) läuft schon vorher
# und bleibt es auch danach - das gesetzliche Rücktrittsrecht besteht ja
# unabhängig vom Stichtag. Was sich ändert, ist nur die Hervorhebungspflicht:
# bis zum Stichtag genügt die normale, gleichrangige Nennung im Legal-Footer;
# ab dem Stichtag muss der Zugang als eigenständige Funktion erkennbar sein.
# Da diese Nennung schon jetzt dezent, aber als eigener Link erkennbar ist,
# braucht es keinen serverseitigen oder client-seitigen Umschalter - der
# bestehende Footer-Link erfüllt beide Phasen zugleich.
# ---------------------------------------------------------------------------

from datetime import date, datetime
from zoneinfo import ZoneInfo

WITHDRAWAL_FUNCTION_EFFECTIVE_DATE: Final = date(2026, 10, 1)
_VIENNA: Final = ZoneInfo("Europe/Vienna")


def withdrawal_function_legally_required() -> bool:
    """Ob die hervorgehobene Online-Rücktrittsfunktion nach § 13a FAGG bereits
    gesetzlich vorgeschrieben ist (Stichtag in Europe/Vienna)."""
    return datetime.now(_VIENNA).date() >= WITHDRAWAL_FUNCTION_EFFECTIVE_DATE
