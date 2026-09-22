"""Admin-Tool im Browser: HttpOnly-Cookie statt Token im localStorage."""

import pytest

from app.config import settings
from app.security import ADMIN_COOKIE
from tests.conftest import create_admin


@pytest.fixture(autouse=True)
def _http(monkeypatch):
    # Der Testclient spricht http - ein Secure-Cookie schickte er nie zurueck.
    monkeypatch.setattr(settings, "frontend_url", "http://localhost:5173")


def _login(client):
    create_admin(client)
    return client.post(
        "/api/admin/auth/login",
        json={"email": "admin@example.com", "password": "adminsecret123"},
    )


def test_login_setzt_httponly_cookie(client, monkeypatch):
    monkeypatch.setattr(settings, "frontend_url", "https://flexr.social")
    r = _login(client)
    assert r.status_code == 200
    kopf = r.headers["set-cookie"].lower()
    assert f"{ADMIN_COOKIE}=" in kopf
    assert "httponly" in kopf
    assert "samesite=strict" in kopf
    assert "path=/api/admin" in kopf
    assert "secure" in kopf


def test_cookie_reicht_zum_lesen(client):
    _login(client)
    assert client.get("/api/admin/stats").status_code == 200


def test_schreiben_per_cookie_braucht_admin_header(client):
    _login(client)
    ohne = client.post("/api/admin/auth/totp/setup")
    mit = client.post("/api/admin/auth/totp/setup", headers={"X-Flexr-Admin": "1"})
    assert ohne.status_code == 403
    assert mit.status_code == 200


def test_logout_loescht_cookie(client):
    _login(client)
    client.post("/api/admin/auth/logout")
    assert client.get("/api/admin/stats").status_code == 401


def test_bearer_token_geht_weiterhin(client):
    token = _login(client).json()["access_token"]
    client.cookies.clear()
    r = client.post("/api/admin/auth/totp/setup", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_admin_html_ohne_inline_skript_und_mit_strenger_csp():
    import re
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    html = (repo / "frontend" / "admin.html").read_text(encoding="utf-8")
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html), "Inline-Skript in admin.html"
    assert not re.search(r"\son[a-z]+=\"", html), "Inline-Eventhandler in admin.html"
    js = (repo / "frontend" / "admin.js").read_text(encoding="utf-8")
    assert "localStorage.setItem('flexr_admin_token'" not in js

    nginx = (repo / "deploy" / "nginx-flexr.conf").read_text(encoding="utf-8")
    block = nginx.split("location = /admin.html {", 1)[1].split("\n    }", 1)[0]
    policies = re.findall(r'add_header Content-Security-Policy "([^"]+)"', block)
    assert any("script-src 'self'" in p and "unsafe-inline" not in p for p in policies)
