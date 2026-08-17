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

TERMS_VERSION: Final = "2026-08-15"           # AGB
PRIVACY_VERSION: Final = "2026-08-15"         # Datenschutzerklärung
AUP_VERSION: Final = "2026-08-15"             # Nutzungsrichtlinien
LE_GUIDELINES_VERSION: Final = "2026-08-15"   # Strafverfolgungsrichtlinien
WITHDRAWAL_VERSION: Final = "2026-08-15"      # Widerrufsbelehrung


# ---------------------------------------------------------------------------
# Preis und Vertragsmodell
#
# Maßgeblich ist der Code, nicht dieser Block - er hält nur fest, was
# routers/billing.py und stripe_client.py tatsächlich tun, damit die Texte
# nicht davon abweichen:
#
#   * Bei der Registrierung wird KEIN Zahlungsmittel erhoben.
#   * Der Probemonat ist ein reines Datenbankfeld (User.trial_ends_at) und
#     wandelt sich NICHT von selbst in ein Abo um.
#   * Ein zahlungspflichtiger Vertrag entsteht erst durch den aktiven Abschluss
#     im Stripe-Checkout (POST /api/billing/checkout).
# ---------------------------------------------------------------------------

PRICE_EUR_PER_MONTH: Final = "5"
TRIAL_AUTO_CONVERTS: Final = False


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
