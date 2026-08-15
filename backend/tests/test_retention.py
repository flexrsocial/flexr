"""Die Aufbewahrungsfristen im Code und im Rechtstext müssen übereinstimmen.

Der Grundsatz des ganzen Audits: Der Code sagt, was passiert; die
Datenschutzerklärung beschreibt es. Läuft eines von beidem weg, ist der
Rechtstext falsch — und zwar in der Richtung, die am teuersten ist.

Diese Tests binden ``app/retention.py`` an die drei Stellen, die die Fristen
tatsächlich umsetzen, und an die öffentliche Tabelle in
``frontend/datenschutz.html``.
"""

import re
from datetime import timedelta
from pathlib import Path

import pytest

from app import retention

REPO = Path(__file__).resolve().parents[2]
DATENSCHUTZ = REPO / "frontend" / "datenschutz.html"


@pytest.fixture(scope="module")
def datenschutz_text():
    assert DATENSCHUTZ.exists(), "frontend/datenschutz.html fehlt"
    return DATENSCHUTZ.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Code gegen Code: retention.py gegen die Stellen, die wirklich rechnen
# ---------------------------------------------------------------------------


def test_karenzzeit_stimmt_mit_dem_loeschlauf_ueberein():
    from app.cleanup import GRACE_PERIOD_DAYS

    assert retention.ACCOUNT_GRACE_PERIOD_DAYS == GRACE_PERIOD_DAYS


def test_frist_fuer_verwaiste_aufnahmen_stimmt():
    from app.verification_service import ORPHAN_RETENTION_DAYS

    assert retention.VERIFICATION_ORPHAN_DAYS == ORPHAN_RETENTION_DAYS


def test_altersfenster_stimmt():
    from app.routers.auth import UNDERAGE_ATTEMPT_WINDOW

    assert UNDERAGE_ATTEMPT_WINDOW == timedelta(
        hours=retention.UNDERAGE_ATTEMPT_WINDOW_HOURS
    )


def test_gueltigkeit_der_ausweis_links_stimmt():
    from app.storage import DOCUMENT_VIEW_URL_TTL_SECONDS

    assert retention.DOCUMENT_VIEW_URL_TTL_SECONDS == DOCUMENT_VIEW_URL_TTL_SECONDS


def test_gueltigkeit_des_bestaetigungslinks_stimmt():
    from app.email_verification import TOKEN_TTL_HOURS

    assert retention.EMAIL_TOKEN_TTL_HOURS == TOKEN_TTL_HOURS


# ---------------------------------------------------------------------------
# Code gegen Rechtstext
# ---------------------------------------------------------------------------


def test_datenschutz_nennt_die_karenzzeit(datenschutz_text):
    assert f"{retention.ACCOUNT_GRACE_PERIOD_DAYS} Tage Karenz" in datenschutz_text


def test_datenschutz_nennt_die_frist_fuer_verwaiste_aufnahmen(datenschutz_text):
    assert f"{retention.VERIFICATION_ORPHAN_DAYS} Tagen" in datenschutz_text


def test_datenschutz_nennt_die_steuerliche_frist(datenschutz_text):
    assert f"{retention.TAX_RECORD_RETENTION_YEARS} Jahre" in datenschutz_text
    assert "§ 132 BAO" in datenschutz_text


def test_datenschutz_nennt_die_kurze_gueltigkeit_der_ausweis_links(datenschutz_text):
    assert f"{retention.DOCUMENT_VIEW_URL_TTL_SECONDS} Sekunden" in datenschutz_text


def test_datenschutz_nennt_das_altersfenster(datenschutz_text):
    assert f"{retention.UNDERAGE_ATTEMPT_WINDOW_HOURS} Stunden" in datenschutz_text


def test_datenschutz_nennt_die_legal_hold_frist(datenschutz_text):
    assert f"{retention.LEGAL_HOLD_DAYS} Tage" in datenschutz_text


# ---------------------------------------------------------------------------
# Behauptungen, die nicht wieder auftauchen dürfen
# ---------------------------------------------------------------------------


VERBOTENE_AUSSAGEN = [
    # Stand vor dem 15.08.2026 - beide nicht belegbar.
    ("Eastern Europe (EEUR) — EU, kein Drittstaatentransfer",
     "R2-Standort-Hinweis ist keine Zusicherung der EU-Speicherung"),
    ("Mit allen Auftragsverarbeitern bestehen Auftragsverarbeitungsverträge",
     "pauschale AVV-Zusicherung ohne Beleg"),
    ("vollständige und unwiderrufliche Löschung",
     "Backups und Legal Holds machen die Aussage unhaltbar"),
]


@pytest.mark.parametrize("aussage,grund", VERBOTENE_AUSSAGEN)
def test_entfernte_behauptungen_bleiben_entfernt(datenschutz_text, aussage, grund):
    assert aussage not in datenschutz_text, f"steht wieder drin ({grund})"


def test_keine_pauschale_dreissig_tage_aussage(datenschutz_text):
    """"Alle Daten werden 30 Tage nach Kontolöschung gelöscht" wäre falsch:
    Zahlungsbezogene Aufzeichnungen bleiben sieben Jahre."""
    muster = re.compile(r"alle Daten[^.]{0,60}30 Tage", re.IGNORECASE)
    assert not muster.search(datenschutz_text)


def test_datenschutz_nennt_google_fonts_nicht_mehr_als_gegenwart(datenschutz_text):
    """Die Schriften liegen seit dem 15.08.2026 lokal. Der Text darf das
    Gegenteil nicht behaupten - er darf die Vergangenheit aber erwähnen."""
    assert "fonts.googleapis.com" not in datenschutz_text


def test_frontend_laedt_keine_fremden_schriften():
    """Die eigentliche Prüfung: Was der Text sagt, muss im HTML stimmen."""
    for name in ("index.html", "app/index.html", "admin.html", "legal.css"):
        pfad = REPO / "frontend" / name
        assert pfad.exists(), f"{name} fehlt"
        text = pfad.read_text(encoding="utf-8")
        assert "fonts.googleapis.com/css2" not in text, f"{name} lädt Google Fonts"
        assert "fonts.gstatic.com" not in text, f"{name} lädt Google Fonts"


def test_alle_retention_zeilen_haben_einen_beleg():
    """Eine Zeile in der öffentlichen Tabelle ohne Stelle im Code, die sie
    umsetzt, ist eine Behauptung."""
    for zeile in retention.RETENTION_TABLE:
        assert zeile.beleg, f"Zeile ohne Beleg: {zeile.kategorie}"
        assert len(zeile.frist) > 5


def test_frontend_laedt_ueberhaupt_keine_fremden_hosts():
    """Kein einziger Fremdaufruf im ausgelieferten HTML.

    Am 15.08.2026 waren es zwei: Google Fonts in index.html und admin.html, und
    acht Unsplash-Fotos im Demo-Deck der App. Letzteres fiel erst auf, als die
    neue Content-Security-Policy sie blockierte - die Datenschutzerklaerung
    hatte beide Empfaenger nie genannt.

    Geprueft wird auf Hosts in Attributwerten, nicht auf jedes Vorkommen im
    Text: Kommentare duerfen die Vergangenheit erwaehnen.
    """
    import re

    ERLAUBT = {"flexr.social", "photos.flexr.social", "www.flexr.social",
               "schema.org", "stripe.com", "www.dsb.gv.at", "www.ris.bka.gv.at"}

    for name in ("index.html", "app/index.html", "admin.html", "legal.css",
                 "agb.html", "datenschutz.html", "impressum.html", "faq.html",
                 "widerruf.html", "meldung.html", "sicherheit.html",
                 "nutzungsrichtlinien.html", "strafverfolgung.html"):
        pfad = REPO / "frontend" / name
        text = pfad.read_text(encoding="utf-8")
        # href/src/url() mit absolutem Ziel
        ziele = re.findall(r'(?:href|src)="https?://([^/"]+)', text)
        ziele += re.findall(r"url\(['\"]?https?://([^/'\")]+)", text)
        fremd = {h for h in ziele if h not in ERLAUBT}
        assert not fremd, f"{name} laedt von fremden Hosts: {sorted(fremd)}"
