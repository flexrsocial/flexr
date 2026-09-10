"""Regressionstests zu den Befunden aus dem Journey-Durchgang vom 06.09.2026.

Fuenf Punkte, die beim Durchspielen der kompletten Nutzerreise und des
Admin-Dashboards aufgefallen sind:

1. Kontosperre: Der Server baut die begruendete Mitteilung nach Art. 17 DSA,
   die Web-App zeigte davon nur den Satz "Dein Konto wurde gesperrt."
2. Melden aus dem Chat: eigene Kopie des Melde-Helfers, die das Aktenzeichen
   aus der Empfangsbestaetigung (Art. 16 Abs. 4 DSA) verwarf.
3. Admin-Dashboard: selbstgeloeschte Konten waren waehrend der Karenzzeit
   nicht von aktiven zu unterscheiden.
4. Checkout: eine Stripe-Stoerung kam als nackter 500 heraus - ohne
   CORS-Header, im Browser also nur als "Failed to fetch".
5. Melden und Blockieren waren <div> statt <button> - per Tastatur weder
   erreichbar noch ausloesbar.
"""

from pathlib import Path

from tests.conftest import TestingSessionLocal, create_admin, register_user
from app.models import User
from app.routers import billing as billing_router


REPO = Path(__file__).resolve().parents[2]
APP_HTML = (REPO / "frontend" / "app" / "index.html").read_text(encoding="utf-8")
ADMIN_HTML = (REPO / "frontend" / "admin.html").read_text(encoding="utf-8")


# ---------- 1. Kontosperre: Begruendung erreicht den Betroffenen ----------

def test_login_einer_kontosperre_liefert_die_vollstaendige_begruendung(client):
    """Beim Ban ist der Login der einzige Kanal - ein Token bekommt der
    Gesperrte nicht. Grund, Umfang, Dauer und Widerspruchsweg muessen also
    dort ankommen."""
    admin_headers, _ = create_admin(client, email="ban.admin@example.com")
    register_user(client, "ban.betroffen@example.com", name="Betroffen")
    user_id = next(
        u["id"]
        for u in client.get("/api/admin/users", headers=admin_headers).json()
        if u["email"] == "ban.betroffen@example.com"
    )
    client.post(
        f"/api/admin/users/{user_id}/ban",
        headers=admin_headers,
        json={"reason": "Gefaelschte Identitaet."},
    )

    resp = client.post(
        "/api/auth/login",
        json={"email": "ban.betroffen@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 403
    detail = resp.json()["detail"]
    assert detail["reason"] == "account_banned"
    assert detail["moderation_reason"] == "Gefaelschte Identitaet."
    assert detail["appeal_hint"]
    assert detail["statement"]["measure"]
    assert detail["statement"]["duration"]


def test_webapp_zeigt_die_begruendung_der_kontosperre():
    # Der Renderer existiert und liest die Bestandteile des statement.
    assert "function moderationNoticeHtml(detail)" in APP_HTML
    assert "loginModerationNotice" in APP_HTML
    for feld in ("measure", "summary", "scope", "duration", "automated_detection", "legal_basis"):
        assert f"st.{feld}" in APP_HTML, feld
    # Login-Fehlerpfad und laufende Sitzung nutzen ihn beide.
    assert "err.detail.reason === 'account_banned'" in APP_HTML
    assert "data.detail.reason === 'account_banned'" in APP_HTML


# ---------- 2. Melden aus dem Chat mit Aktenzeichen ----------

def test_chat_meldung_nutzt_den_gemeinsamen_helfer():
    """Die eigene Kopie im Chat zeigte statt der Empfangsbestaetigung nur
    'Meldung gesendet'. Genau ein Aufrufer darf den Toast bauen.

    Der Text selbst steht seit dem 09.09.2026 im Woerterbuch
    (i18n-app.js: report.ackPlain); geprueft wird deshalb, dass es im Skript
    genau EINE Stelle gibt, die ihn verwendet."""
    assert APP_HTML.count("t('report.ackPlain')") == 1
    assert APP_HTML.count("t('report.ack', {ref: ack.reference})") == 1
    assert "reportUser(match.profile.id, match.profile.name)" in APP_HTML
    assert "blockUser(match.profile.id, match.profile.name" in APP_HTML


def test_meldung_liefert_ein_aktenzeichen(client):
    melder = register_user(client, "ack.melder@example.com")
    register_user(client, "ack.gemeldet@example.com", name="Gemeldet", gender="mann")
    ziel = next(
        u["id"]
        for u in client.get(
            "/api/admin/users",
            headers=create_admin(client, email="ack.admin@example.com")[0],
        ).json()
        if u["email"] == "ack.gemeldet@example.com"
    )
    resp = client.post(
        "/api/reports",
        headers=melder,
        json={"reported_user_id": ziel, "reason": "Fragt wiederholt nach Geld."},
    )
    assert resp.status_code == 201
    assert resp.json()["reference"]


# ---------- 3. Geloeschte Konten im Admin-Dashboard ----------

def test_admin_sieht_selbstgeloeschte_konten_als_solche(client):
    admin_headers, _ = create_admin(client, email="del.admin@example.com")
    headers = register_user(client, "del.sichtbar@example.com", name="Geloescht")
    client.request(
        "DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"}
    )

    eintrag = next(
        u
        for u in client.get("/api/admin/users", headers=admin_headers).json()
        if u["email"] == "del.sichtbar@example.com"
    )
    assert eintrag["deleted_at"] is not None

    detail = client.get(f"/api/admin/users/{eintrag['id']}", headers=admin_headers).json()
    assert detail["deleted_at"] is not None
    # 30-Tage-Karenz: der Termin der endgueltigen Loeschung steht daneben.
    assert detail["purge_at"] is not None
    assert detail["purge_at"] > detail["deleted_at"]


def test_stats_zaehlen_geloeschte_konten_getrennt(client):
    admin_headers, _ = create_admin(client, email="stats.admin@example.com")
    register_user(client, "stats.aktiv@example.com")
    headers = register_user(client, "stats.geloescht@example.com")

    vorher = client.get("/api/admin/stats", headers=admin_headers).json()
    client.request(
        "DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"}
    )
    nachher = client.get("/api/admin/stats", headers=admin_headers).json()

    assert nachher["total_users"] == vorher["total_users"] - 1
    assert nachher["deleted_users"] == vorher["deleted_users"] + 1


def test_kennzahlen_bleiben_untereinander_stimmig(client):
    """Auf dem Dashboard stand "14 im Probemonat" bei 13 Nutzern gesamt -
    Die Kennzahl (heute free_users, frueher trial_users) zaehlte
    selbstgeloeschte Konten weiter mit."""
    admin_headers, _ = create_admin(client, email="stimmig.admin@example.com")
    headers = register_user(client, "stimmig.geloescht@example.com")
    client.request(
        "DELETE", "/api/profiles/me", headers=headers, json={"password": "supersecret123"}
    )

    stats = client.get("/api/admin/stats", headers=admin_headers).json()
    assert stats["free_users"] <= stats["total_users"]
    assert stats["active_subscriptions"] <= stats["total_users"]
    assert stats["banned_users"] <= stats["total_users"]


def test_admin_ui_kennzeichnet_geloeschte_konten():
    assert "u.deleted_at" in ADMIN_HTML
    assert "Gelöscht" in ADMIN_HTML
    assert "In Löschung" in ADMIN_HTML
    assert "u.purge_at" in ADMIN_HTML


# ---------- 4. Checkout-Stoerung mit brauchbarer Antwort ----------

def test_checkout_stoerung_liefert_502_statt_500(client, monkeypatch):
    """Ein unbehandelter 500 verliert die CORS-Header der Anwendung; im
    Browser kam nur 'Failed to fetch' an."""
    headers = register_user(client, "checkout.stoerung@example.com")

    def kaputt(*args, **kwargs):
        raise RuntimeError("Stripe nicht erreichbar")

    monkeypatch.setattr(billing_router, "create_checkout_session", kaputt)
    resp = client.post(
        "/api/billing/checkout",
        headers=headers,
        json={"immediate_start": True, "withdrawal_ack": True},
    )
    assert resp.status_code == 502
    assert "nichts abgebucht" in resp.json()["detail"]


def test_portal_stoerung_liefert_502_statt_500(client, monkeypatch):
    headers = register_user(client, "portal.stoerung@example.com")
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "portal.stoerung@example.com").first()
        user.stripe_customer_id = "cus_test"
        db.commit()
    finally:
        db.close()

    def kaputt(*args, **kwargs):
        raise RuntimeError("Stripe nicht erreichbar")

    monkeypatch.setattr(billing_router, "create_portal_session", kaputt)
    resp = client.post("/api/billing/portal", headers=headers)
    assert resp.status_code == 502


def test_checkout_ueberschreibt_die_alte_fehlermeldung():
    """Nach dem Anhaken blieb 'Bitte bestätige beide Erklärungen' stehen,
    waehrend der echte Fehler nur als Toast vorbeizog."""
    stelle = APP_HTML.index("async function confirmImmediateStartAndSubscribe()")
    abschnitt = APP_HTML[stelle:stelle + 1800]
    # Der Text der Meldung steht im Woerterbuch (istart.err) - die Reihenfolge
    # bleibt der Punkt: erst leeren, dann die neue Meldung setzen.
    assert abschnitt.index("$('istartErr').textContent = '';") < abschnitt.index(
        "$('istartErr').textContent = t('istart.err');"
    )
    assert "$('istartErr').textContent = msg;" in abschnitt


# ---------- 5. Melden und Blockieren per Tastatur erreichbar ----------

def test_schutzfunktionen_sind_echte_buttons():
    """Melden, Blockieren und "Match auflösen" waren <div> mit aria-label:
    per Tastatur weder erreichbar noch ausloesbar. Ausgerechnet die
    gesetzlich vorgeschriebenen Schutzfunktionen - waehrend der
    Zurueck-Pfeil daneben im selben Kopf ein echter <button> war."""
    for kennung in (
        'id="btnReportChat"',
        'id="btnBlockChat"',
        'id="btnChatMenu"',
        'class="flag-btn btnReportCard"',
        'class="flag-btn btnBlockCard"',
        'class="flag-btn btnUnmatchCard"',
    ):
        stelle = APP_HTML.index(kennung)
        # Rueckwaerts bis zum oeffnenden Tag suchen
        anfang = APP_HTML.rindex("<", 0, stelle)
        assert APP_HTML.startswith("<button type=\"button\"", anfang), kennung

    # aria-expanded darf nicht als feste Behauptung im Markup stehenbleiben
    assert "function setChatMenu(offen)" in APP_HTML
    assert "setAttribute('aria-expanded'" in APP_HTML
