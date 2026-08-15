"""Aufbewahrungsfristen an einer Stelle.

Die Fristen standen bisher als Zahlen verstreut im Code (cleanup.py,
verification_service.py, storage.py) und als Prosa in der
Datenschutzerklärung — mit dem üblichen Ergebnis, dass beides auseinanderlief.
Die öffentliche Tabelle in ``frontend/datenschutz.html`` ist aus diesem Modul
abgeleitet; ``RETENTION_TABLE`` unten ist die Vorlage dafür.

Wichtig für die Textarbeit: Die Wahrheit steht im Code, nicht im Rechtstext.
Wer hier eine Frist ändert, muss ``frontend/datenschutz.html`` mitziehen —
darüber wacht ``backend/tests/test_retention.py``.
"""

from typing import Final, NamedTuple

# ---------------------------------------------------------------------------
# Fristen in Tagen (die Zahlen, mit denen der Code tatsächlich rechnet)
# ---------------------------------------------------------------------------

#: Karenzzeit zwischen Selbstlöschung und endgültiger Löschung.
#: Verwendet in cleanup.purge_deleted_users().
ACCOUNT_GRACE_PERIOD_DAYS: Final = 30

#: Aufnahmen aus abgebrochenen Verifizierungen ohne Einreichung.
#: Verwendet in verification_service.ORPHAN_RETENTION_DAYS.
VERIFICATION_ORPHAN_DAYS: Final = 14

#: Zeitfenster, in dem Registrierungsversuche unter 18 gezählt werden.
#: Verwendet in routers/auth.UNDERAGE_ATTEMPT_WINDOW (dort als timedelta).
UNDERAGE_ATTEMPT_WINDOW_HOURS: Final = 24

#: Gültigkeit des E-Mail-Bestätigungslinks.
EMAIL_TOKEN_TTL_HOURS: Final = 24

#: Gültigkeit einer Signed URL auf eine Ausweisaufnahme (Admin-Ansicht).
DOCUMENT_VIEW_URL_TTL_SECONDS: Final = 60

#: Steuerliche Aufbewahrung zahlungsbezogener Aufzeichnungen, § 132 BAO.
TAX_RECORD_RETENTION_YEARS: Final = 7

#: Behördliches Sicherungsersuchen (siehe strafverfolgung.html, Abschnitt 7).
LEGAL_HOLD_DAYS: Final = 90


class RetentionRow(NamedTuple):
    """Eine Zeile der öffentlichen Aufbewahrungstabelle."""

    kategorie: str
    frist: str
    ausloeser: str
    beleg: str  # wo im Code die Frist tatsächlich umgesetzt ist


# ---------------------------------------------------------------------------
# Die öffentliche Tabelle. Jede Zeile nennt die Stelle im Code, die sie belegt —
# eine Zeile ohne Beleg gehört nicht in die Datenschutzerklärung.
# ---------------------------------------------------------------------------

RETENTION_TABLE: Final[tuple[RetentionRow, ...]] = (
    RetentionRow(
        "Konto- und Profildaten (E-Mail, Passwort-Hash, Name, Geburtsdatum, "
        "PLZ/Ort, Geschlecht, gesuchtes Geschlecht, Gym, Suchradius, Bio)",
        f"bis zur Löschung durch dich, danach {ACCOUNT_GRACE_PERIOD_DAYS} Tage Karenz",
        "Selbstlöschung im Konto-Bereich",
        "cleanup.purge_deleted_users",
    ),
    RetentionRow(
        "Profilfotos und Thumbnails",
        f"mit dem Konto, spätestens {ACCOUNT_GRACE_PERIOD_DAYS} Tage nach der Löschung; "
        "einzeln gelöschte Fotos sofort",
        "Löschung des Fotos oder des Kontos",
        "cleanup.storage_keys_for_photo",
    ),
    RetentionRow(
        "Verifizierungs-Selfie",
        "unmittelbar nach der Prüfentscheidung; bei Selbstlöschung sofort, "
        "ohne die Karenzzeit abzuwarten",
        "Entscheidung des Prüfers bzw. Kontolöschung",
        "verification_service.purge_uploads",
    ),
    RetentionRow(
        "Ausweisaufnahme",
        "unmittelbar nach der Prüfentscheidung; nie eingereichte Aufnahmen "
        f"spätestens nach {VERIFICATION_ORPHAN_DAYS} Tagen",
        "Entscheidung des Prüfers bzw. Ablauf der Frist",
        "cleanup.purge_stale_verification_uploads",
    ),
    RetentionRow(
        "Prüfergebnis (Status, Prüfgrund aus fester Liste, Zeitpunkte, Prüfkennung)",
        "mit dem Konto",
        "Kontolöschung",
        "models.VerificationRequest (ondelete CASCADE)",
    ),
    RetentionRow(
        "Chatnachrichten (Original und bereinigte Fassung), Matches, Swipes, "
        "Blockierungen",
        "mit dem Konto",
        "Kontolöschung",
        "models.Message / Match / Swipe (ondelete CASCADE)",
    ),
    RetentionRow(
        "Meldungen und Moderationsentscheidungen",
        "mit dem Konto der beteiligten Person",
        "Kontolöschung",
        "models.Report (ondelete CASCADE)",
    ),
    RetentionRow(
        "Geräte-ID und User-Agent (Mehrfachkonten-/Sperrumgehungsschutz)",
        "mit dem Konto",
        "Kontolöschung",
        "models.UserDevice (ondelete CASCADE)",
    ),
    RetentionRow(
        "Registrierungsversuche mit Geburtsdatum unter 18 (nur Geräte-ID und Zeitpunkt)",
        f"ausgewertet werden nur die letzten {UNDERAGE_ATTEMPT_WINDOW_HOURS} Stunden",
        "Zeitablauf",
        "routers.auth.UNDERAGE_ATTEMPT_WINDOW",
    ),
    RetentionRow(
        "Stripe-Kunden- und Abo-ID, Abostatus",
        f"zahlungsbezogene Aufzeichnungen {TAX_RECORD_RETENTION_YEARS} Jahre "
        "(§ 132 BAO); die IDs selbst mit dem Konto",
        "gesetzliche Aufbewahrungsfrist",
        "models.User.stripe_customer_id",
    ),
    RetentionRow(
        "Rücktrittserklärungen (§ 13a FAGG)",
        f"{TAX_RECORD_RETENTION_YEARS} Jahre als Nachweis der Vertragsabwicklung",
        "gesetzliche Aufbewahrungsfrist",
        "models.WithdrawalDeclaration",
    ),
    RetentionRow(
        "Einwilligungsnachweise (Art. 7 Abs. 1 DSGVO)",
        "solange die Einwilligung wirkt, danach als Widerrufsnachweis bis zur "
        "Kontolöschung",
        "Kontolöschung",
        "models.Consent (ondelete CASCADE)",
    ),
    RetentionRow(
        "DSA-Meldungen über das öffentliche Formular",
        f"{TAX_RECORD_RETENTION_YEARS} Jahre — sie hängen an keinem Konto und "
        "belegen die Erfüllung von Art. 16 DSA",
        "gesetzliche/regulatorische Nachweispflicht",
        "models.Notice",
    ),
    RetentionRow(
        "Server-Logs (IP-Adresse, Zeitstempel, angefragter Pfad)",
        "kurzlebig auf Systemebene, ohne Zuordnung zu einem Konto",
        "Rotation durch das Betriebssystem",
        "nginx/journald auf dem VPS — siehe LEGAL_REVIEW.md, T-04",
    ),
)


# ---------------------------------------------------------------------------
# Legal Hold
# ---------------------------------------------------------------------------

LEGAL_HOLD_NOTE: Final = (
    "Sichert eine Behörde Daten (§ 7 der Strafverfolgungsrichtlinien) oder liegt "
    "ein Fall nach Abschnitt 7 der Nutzungsrichtlinien vor, werden die betroffenen "
    "Daten von den automatischen Löschroutinen ausgenommen, bis der Anlass "
    f"weggefallen ist — die Sicherung gilt zunächst {LEGAL_HOLD_DAYS} Tage."
)
