"""Fehlermeldungen der API in der Sprache des Clients (app/api_i18n.py)."""

import ast
from pathlib import Path

from app import api_i18n
from tests.conftest import register_user

APP = Path(__file__).resolve().parent.parent / "app"


def _text(node):
    """Literal oder f-String als Muster mit {platzhalter}."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            v.value if isinstance(v, ast.Constant) else "{x}" for v in node.values
        )
    return None


def _http_exception_texte():
    for datei in APP.rglob("*.py"):
        for node in ast.walk(ast.parse(datei.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "id", getattr(node.func, "attr", None))
            if name != "HTTPException":
                continue
            kandidaten = list(node.args[1:2]) + [k.value for k in node.keywords if k.arg == "detail"]
            for kandidat in kandidaten:
                text = _text(kandidat)
                if text is not None:
                    yield datei.name, node.lineno, text


def test_jede_http_meldung_hat_eine_englische_fassung():
    fehlend = []
    for datei, zeile, text in _http_exception_texte():
        probe = text.replace("{x}", "7")
        if not api_i18n.has_translation(probe):
            fehlend.append(f"{datei}:{zeile}: {text}")
    assert not fehlend, "Ohne Uebersetzung in app/api_i18n.py:\n" + "\n".join(fehlend)


def test_muster_uebernimmt_platzhalter():
    assert api_i18n.translate("Maximal 6 Fotos erlaubt.", "en") == "A maximum of 6 photos is allowed."
    assert api_i18n.translate("Maximal 6 Fotos erlaubt.", "de") == "Maximal 6 Fotos erlaubt."
    assert api_i18n.translate("Ganz neuer Text.", "en") == "Ganz neuer Text."


def test_login_fehler_englisch_mit_accept_language(client):
    register_user(client, "sprache@example.com")
    body = {"email": "sprache@example.com", "password": "falsch123"}
    de = client.post("/api/auth/login", json=body)
    en = client.post("/api/auth/login", json=body, headers={"Accept-Language": "en"})
    assert de.json()["detail"] == "E-Mail oder Passwort falsch."
    assert en.json()["detail"] == "Incorrect email or password."


def test_detail_objekt_behaelt_code(client):
    h = register_user(client, "objekt@example.com")
    r = client.post("/api/swipes/rewind", headers={**h, "Accept-Language": "en-GB,en;q=0.9"})
    detail = r.json()["detail"]
    if isinstance(detail, dict):
        assert "code" in detail
        assert "ü" not in detail["message"]


def test_validierungsfehler_lesbar(client):
    de = client.post("/api/auth/login", json={"email": "kaputt", "password": "x"})
    en = client.post("/api/auth/login", json={"email": "kaputt", "password": "x"},
                     headers={"Accept-Language": "en"})
    assert de.status_code == en.status_code == 422
    assert de.json()["detail"][0]["msg"] == "Ungültige E-Mail-Adresse."
    assert en.json()["detail"][0]["msg"] == "Invalid email address."
    # Struktur bleibt: Clients, die auf type/loc schauen, merken nichts.
    assert de.json()["detail"][0]["loc"][-1] == "email"


def test_eigene_pruefung_ohne_value_error_praefix(client):
    r = client.post("/api/auth/password/reset", json={"token": "x" * 20, "new_password": "ä" * 40})
    assert r.json()["detail"][0]["msg"] == "Das Passwort darf höchstens 72 Bytes lang sein."
