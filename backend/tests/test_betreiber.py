"""Die Betreiberangaben dürfen nicht wieder auseinanderlaufen.

Vor dem 15.08.2026 stand der Rechtsträger an fünfzehn Stellen im Repository -
in sieben HTML-Seiten, in der Android-App, in der iOS-App und in zwei
Store-Texten. Sie stimmten nicht mehr überein, und keine davon nannte einen
zulässigen Rechtsträger ("flexr.social Kleinunternehmen" ist keine Rechtsform).

Dieser Test hält ``shared/betreiber.json`` und ``app/legal.py`` zusammen.
Für Web, Android und iOS macht ``tools/check_betreiber.py`` dasselbe.
"""

import json
from pathlib import Path

import pytest

from app import legal

REPO = Path(__file__).resolve().parents[2]
BETREIBER_JSON = REPO / "shared" / "betreiber.json"


@pytest.fixture(scope="module")
def daten():
    return json.loads(BETREIBER_JSON.read_text(encoding="utf-8"))


def test_quelle_existiert():
    assert BETREIBER_JSON.exists(), (
        "shared/betreiber.json fehlt - sie ist die Quelle für alle "
        "Betreiberangaben."
    )


def test_legal_py_spiegelt_die_quelle(daten):
    rt = daten["rechtstraeger"]
    assert legal.OPERATOR_NAME == rt["name"]
    assert legal.OPERATOR_LEGAL_FORM == rt["rechtsform"]
    assert legal.OPERATOR_ROLE == rt["rolle"]
    assert legal.OPERATOR_STREET == rt["strasse"]
    assert legal.OPERATOR_ZIP == rt["plz"]
    assert legal.OPERATOR_CITY == rt["ort"]
    assert legal.OPERATOR_COUNTRY == rt["land"]
    assert legal.OPERATOR_EMAIL == rt["email"]
    assert legal.BRAND == daten["marke"]
    assert legal.DOMAIN == daten["domain"]
    assert legal.POSITIONING == daten["positionierung"]


def test_rechtstraeger_ist_eine_natuerliche_person(daten):
    """Kein Firmenbucheintrag heißt: kein § 14 UGB und keine
    Firmenbuchnummer im Impressum."""
    assert daten["rechtstraeger"]["im_firmenbuch"] is False


def test_kleinunternehmerregelung_ist_keine_rechtsform(daten):
    """Sie ist eine umsatzsteuerliche Sache und gehört deshalb unter
    "Umsatzsteuer", nicht unter "Rechtsform"."""
    assert "Kleinunternehmer" not in daten["rechtstraeger"]["rechtsform"]
    assert "Kleinunternehmen" not in daten["rechtstraeger"]["rechtsform"]
    assert daten["umsatzsteuer"]["grundlage"] == "§ 6 Abs. 1 Z 27 UStG"


def test_keine_gewerbeanmeldung_erforderlich(daten):
    """Vom Betreiber abschließend geklärt: für den Betrieb von FLEXR ist keine
    Gewerbeanmeldung nötig. Es dürfen daher weder Gewerbedaten noch ein
    "wird noch geklärt"-Hinweis im Impressum auftauchen."""
    assert daten["gewerbe_erforderlich"] is False
    assert "gewerbe" not in daten


def test_operator_block_ist_vollstaendig():
    block = legal.operator_block()
    for teil in ("Julian Pachernegg", "Einzelunternehmer", "Johann-Schrey-Weg 260",
                 "8232 Grafendorf", "flexr.social@proton.me"):
        assert teil in block


def test_trial_wandelt_sich_nicht_von_selbst_um():
    """Der Merkposten in legal.py muss dem entsprechen, was billing.py tut -
    sonst laufen Rechtstext und Code wieder auseinander.

    Belegt wird das durch den Registrierungspfad: RegisterRequest kennt kein
    Zahlungsmittelfeld, und ohne hinterlegtes Zahlungsmittel kann aus dem
    Probemonat kein Abo werden.
    """
    from app.schemas import RegisterRequest

    assert legal.TRIAL_AUTO_CONVERTS is False
    felder = set(RegisterRequest.model_fields)
    for zahlungsfeld in ("payment_method", "payment_method_id", "stripe_token", "card"):
        assert zahlungsfeld not in felder
