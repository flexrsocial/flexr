"""Was die App-Stores verbieten - und woran der Server sich daran haelt.

FLEXR Premium wird ueber Stripe im Browser verkauft. Aus einer App heraus
darf derselbe Abschluss nicht angeboten werden (App Review Guideline 3.1.1,
Google-Play-Payments-Policy; ausfuehrlich in ``app/clients.py``).

Der Server entscheidet das, nicht der Client: Die veroeffentlichten
App-Fassungen und der iOS-Build, der bei Apple in Pruefung liegt, kennen die
Regel nicht - sie zeigen einen Kauf-Knopf, sobald ihnen jemand
``premium_enabled=true`` meldet. Genau deshalb meldet der Server ihnen das
nicht.

Die User-Agents unten sind aus dem nginx-Zugriffsprotokoll der Produktion
abgeschrieben, nicht erfunden: Sie stammen von URLSession bzw. OkHttp, nicht
aus FLEXR-Code.
"""

from app.config import settings
from tests.conftest import register_user

IOS_AGENT = "FLEXR/24 CFNetwork/3896.100.1.2.1 Darwin/27.0.0"
ANDROID_AGENT = "okhttp/4.12.0"
BROWSER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _status(client, headers, agent=None, client_header=None):
    kopf = dict(headers)
    if agent:
        kopf["User-Agent"] = agent
    if client_header:
        kopf["X-Flexr-Client"] = client_header
    return client.get("/api/billing/status", headers=kopf).json()


# ---------------------------------------------------------------------------
# Wem Premium angeboten wird
# ---------------------------------------------------------------------------

def test_im_browser_ist_premium_kaufbar(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    headers = register_user(client, "browser@example.com")

    status = _status(client, headers, BROWSER_AGENT)
    assert status["checkout_available"] is True
    assert status["premium_enabled"] is True


def test_in_den_apps_wird_nichts_angeboten(client, monkeypatch):
    """Der entscheidende Test: Auch der alte Client sieht keinen Kauf.

    ``premium_enabled`` ist das Feld, an dem die veroeffentlichten Fassungen
    ihren Abschluss-Knopf aufhaengen - es muss in der App falsch sein, sonst
    nuetzt das neue ``checkout_available`` nichts.
    """
    monkeypatch.setattr(settings, "premium_enabled", True)
    headers = register_user(client, "app@example.com")

    for agent in (IOS_AGENT, ANDROID_AGENT):
        status = _status(client, headers, agent)
        assert status["checkout_available"] is False, agent
        assert status["premium_enabled"] is False, agent
        assert status["billing_enabled"] is False, agent


def test_neue_app_fassungen_weisen_sich_selbst_aus(client, monkeypatch):
    """Neue Fassungen schicken ``X-Flexr-Client`` - unabhaengig vom Agenten."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    headers = register_user(client, "header@example.com")

    for kennung in ("ios", "android"):
        status = _status(client, headers, BROWSER_AGENT, client_header=kennung)
        assert status["checkout_available"] is False, kennung


def test_checkout_aus_der_app_wird_abgelehnt(client, monkeypatch):
    """Und zwar ohne zu verraten, wo es sonst ginge - auch das waere 3.1.1."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    headers = register_user(client, "appkauf@example.com")

    resp = client.post(
        "/api/billing/checkout",
        json={"immediate_start": True, "withdrawal_ack": True},
        headers={**headers, "User-Agent": IOS_AGENT},
    )
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert "flexr.social" not in detail.lower()
    assert "browser" not in detail.lower()

    # Keine Einwilligungs-Buchung ohne Vertrag - wie beim abgeschalteten Premium.
    from tests.conftest import TestingSessionLocal
    from app.models import CheckoutConsent

    db = TestingSessionLocal()
    try:
        assert db.query(CheckoutConsent).count() == 0
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Was sich davon NICHT unterscheidet
# ---------------------------------------------------------------------------

def test_grenzen_gelten_am_konto_nicht_am_geraet(client, monkeypatch):
    """Sonst hebt man sie auf, indem man die App statt des Browsers nimmt."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_daily_likes", 20)
    headers = register_user(client, "geraet@example.com")

    aus_app = _status(client, headers, IOS_AGENT)
    aus_browser = _status(client, headers, BROWSER_AGENT)

    assert aus_app["limits_active"] is True
    assert aus_app["likes_remaining"] == aus_browser["likes_remaining"] == 20
    assert aus_app["free_open_chats"] == aus_browser["free_open_chats"]
    assert aus_app["max_radius_km"] == aus_browser["max_radius_km"]


def test_abzeichen_und_vorteile_gelten_auch_in_der_app(client, monkeypatch):
    """Im Browser gekauft, in der App nutzbar - das verbietet kein Store.

    Untersagt ist der Abschluss in der App, nicht die Leistung daraus.
    """
    monkeypatch.setattr(settings, "premium_enabled", True)
    headers = register_user(client, "abo-in-app@example.com")

    from tests.conftest import TestingSessionLocal
    from app.models import User

    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.id == user_id).one().is_subscribed = True
        db.commit()
    finally:
        db.close()

    status = _status(client, headers, IOS_AGENT)
    assert status["is_premium"] is True
    assert status["likes_remaining"] is None      # unbegrenzt
    assert status["checkout_available"] is False  # trotzdem kein Verkauf
    # Kuendbar bleibt es in der App ebenfalls - siehe create_portal().
    assert status["has_stripe_subscription"] is True


def test_beta_abzeichen_haengt_nicht_mehr_an_premium(client, monkeypatch):
    """Premium scharf, FLEXR trotzdem als Beta gekennzeichnet."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "beta_active", True)
    headers = register_user(client, "betaflag@example.com")

    for agent in (BROWSER_AGENT, IOS_AGENT, ANDROID_AGENT):
        assert _status(client, headers, agent)["beta_active"] is True, agent


# ---------------------------------------------------------------------------
# Der Wortlaut an der Grenze
# ---------------------------------------------------------------------------

def test_meldung_an_der_grenze_wirbt_in_der_app_nicht(client, monkeypatch):
    """Auch "hol dir Premium" ist eine Aufforderung im Sinne von 3.1.1."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_open_chats", 0)
    headers = register_user(client, "wortlaut@example.com")

    # free_open_chats = 0: schon die erste Unterhaltung stoesst an die Grenze.
    # Gebraucht wird nur die Meldung, nicht ein echtes Match - dafuer genuegt
    # der direkte Aufruf mit einer unbekannten match_id, der vorher an der
    # Match-Pruefung scheitert. Deshalb hier ueber premium.ensure_chat_allowed
    # selbst, mit einer Anfrage, die sich als App ausweist.
    from app import premium
    from app.models import User
    from fastapi import HTTPException
    from starlette.requests import Request
    from tests.conftest import TestingSessionLocal

    def _anfrage(agent: str) -> Request:
        return Request({
            "type": "http",
            "headers": [(b"user-agent", agent.encode())],
        })

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "wortlaut@example.com").one()

        for agent, erwartet in ((IOS_AGENT, False), (BROWSER_AGENT, True)):
            try:
                premium.ensure_chat_allowed(db, user, "egal", _anfrage(agent))
                raise AssertionError("Grenze haette greifen muessen")
            except HTTPException as fehler:
                text = fehler.detail["message"]
                assert ("Premium" in text) is erwartet, (agent, text)
    finally:
        db.close()
