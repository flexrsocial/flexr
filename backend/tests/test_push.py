"""Echte Push-Zustellung: Token-Verwaltung und Versand.

Der Anlass war eine Meldung aus der Benutzung: Eine Chatnachricht kam auf dem
Android-Geraet nicht an, als sie geschrieben wurde, sondern erst eine Stunde
spaeter - im selben Moment, in dem die App von Hand gestartet wurde. Ursache
war kein Fehler, sondern die Decke des damaligen Entwurfs: Die Apps holten ihre
Benachrichtigungen selbst ab, fruehestens alle 15 Minuten, im Doze-Modus
seltener.

Geprueft wird hier deshalb vor allem, dass der neue Weg **niemandem im Weg
steht**: Ohne Zugangsdaten passiert nichts, und eine Nachricht muss trotzdem
ankommen.
"""

from app import push
from app.config import settings
from app.models import PushToken, User
from tests.conftest import TestingSessionLocal, register_user, register_user_with_photo


def _user(db, email):
    return db.query(User).filter(User.email == email).one()


# ---------------------------------------------------------------------------
# Token-Verwaltung
# ---------------------------------------------------------------------------

def test_token_anmelden_und_abmelden(client):
    headers = register_user(client, "push1@example.com")

    resp = client.post(
        "/api/notifications/token",
        json={"platform": "android", "token": "geraetetoken-aaa"},
        headers=headers,
    )
    assert resp.status_code == 200

    db = TestingSessionLocal()
    try:
        assert db.query(PushToken).filter(PushToken.token == "geraetetoken-aaa").count() == 1
    finally:
        db.close()

    resp = client.request(
        "DELETE",
        "/api/notifications/token",
        json={"platform": "android", "token": "geraetetoken-aaa"},
        headers=headers,
    )
    assert resp.status_code == 200

    db = TestingSessionLocal()
    try:
        assert db.query(PushToken).filter(PushToken.token == "geraetetoken-aaa").count() == 0
    finally:
        db.close()


def test_derselbe_token_zweimal_anmelden_bleibt_eine_zeile(client):
    """Die Apps melden bei jedem Start erneut an - das ist der Normalfall."""
    headers = register_user(client, "push2@example.com")
    for _ in range(3):
        client.post(
            "/api/notifications/token",
            json={"platform": "android", "token": "gleicher-token"},
            headers=headers,
        )

    db = TestingSessionLocal()
    try:
        assert db.query(PushToken).count() == 1
    finally:
        db.close()


def test_token_wandert_zum_neuen_konto(client):
    """Ein Geraet, zwei Konten nacheinander.

    Bliebe der Token beim alten Konto, bekaeme der Vorbesitzer die
    Benachrichtigungen des neuen Nutzers auf sein Geraet.
    """
    erst = register_user(client, "geraet-alt@example.com")
    zweit = register_user(client, "geraet-neu@example.com")

    client.post(
        "/api/notifications/token",
        json={"platform": "android", "token": "wanderer-token-lang"},
        headers=erst,
    )
    client.post(
        "/api/notifications/token",
        json={"platform": "android", "token": "wanderer-token-lang"},
        headers=zweit,
    )

    db = TestingSessionLocal()
    try:
        zeilen = db.query(PushToken).filter(PushToken.token == "wanderer-token-lang").all()
        assert len(zeilen) == 1, "der Kauf darf sich nicht vervielfaeltigen"
        assert zeilen[0].user_id == _user(db, "geraet-neu@example.com").id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Versand
# ---------------------------------------------------------------------------

def test_ohne_zugangsdaten_passiert_nichts(client, monkeypatch):
    """Und vor allem: es kracht nicht."""
    monkeypatch.setattr(settings, "fcm_service_account_file", "")
    monkeypatch.setattr(settings, "fcm_project_id", "")
    register_user(client, "ohnefcm@example.com")

    db = TestingSessionLocal()
    try:
        assert push.send(db, _user(db, "ohnefcm@example.com"), "Titel", "Text") == 0
    finally:
        db.close()


def test_nachricht_kommt_auch_ohne_push_an(client, monkeypatch):
    """Der wichtigste Test dieser Datei.

    Push ist eine Zugabe. Waere der Versand am Senden beteiligt, koennte ein
    Ausfall bei Google das Schreiben einer Nachricht verhindern - ein
    ungleich schlimmerer Fehler als der, der hier behoben wurde.
    """
    monkeypatch.setattr(settings, "premium_enabled", False)

    def _kracht(*args, **kwargs):
        raise RuntimeError("Google ist weg")

    monkeypatch.setattr(push, "send", _kracht)

    a = register_user_with_photo(client, "senderin@example.com")
    b_headers = register_user_with_photo(client, "empfaenger@example.com")
    b_id = client.get("/api/profiles/me", headers=b_headers).json()["id"]
    a_id = client.get("/api/profiles/me", headers=a).json()["id"]

    client.post("/api/swipes", json={"to_user_id": b_id, "action": "like"}, headers=a)
    treffer = client.post(
        "/api/swipes", json={"to_user_id": a_id, "action": "like"}, headers=b_headers
    )
    assert treffer.json()["matched"] is True

    match_id = client.get("/api/matches", headers=a).json()[0]["match_id"]
    resp = client.post(
        f"/api/matches/{match_id}/messages",
        json={"content": "Trainierst du heute?"},
        headers=a,
    )
    # Der Push kracht - die Nachricht steht trotzdem.
    assert resp.status_code == 201, resp.text
    assert resp.json()["content"] == "Trainierst du heute?"


def test_zugestellt_wird_der_zensierte_text(client, monkeypatch):
    """Was auf dem Sperrbildschirm steht, darf nicht mehr verraten als die App."""
    monkeypatch.setattr(settings, "premium_enabled", False)

    gesendet = {}

    def _merken(db, user, title, body, target=None):
        gesendet["titel"] = title
        gesendet["text"] = body
        gesendet["ziel"] = target
        return 1

    monkeypatch.setattr(push, "send", _merken)

    a = register_user_with_photo(client, "linksender@example.com")
    b_headers = register_user_with_photo(client, "linkempf@example.com")
    b_id = client.get("/api/profiles/me", headers=b_headers).json()["id"]
    a_id = client.get("/api/profiles/me", headers=a).json()["id"]
    client.post("/api/swipes", json={"to_user_id": b_id, "action": "like"}, headers=a)
    client.post("/api/swipes", json={"to_user_id": a_id, "action": "like"}, headers=b_headers)
    match_id = client.get("/api/matches", headers=a).json()[0]["match_id"]

    client.post(
        f"/api/matches/{match_id}/messages",
        json={"content": "Schreib mir auf whatsapp.com/12345"},
        headers=a,
    )

    assert gesendet["ziel"] == "chats"
    assert "whatsapp.com/12345" not in gesendet["text"], "zensiert, nicht im Original"


def test_langer_text_wird_gekuerzt(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", False)
    gesendet = {}
    monkeypatch.setattr(
        push, "send",
        lambda db, user, title, body, target=None: gesendet.update(text=body) or 1,
    )

    a = register_user_with_photo(client, "vielschreiber@example.com")
    b_headers = register_user_with_photo(client, "vielleser@example.com")
    b_id = client.get("/api/profiles/me", headers=b_headers).json()["id"]
    a_id = client.get("/api/profiles/me", headers=a).json()["id"]
    client.post("/api/swipes", json={"to_user_id": b_id, "action": "like"}, headers=a)
    client.post("/api/swipes", json={"to_user_id": a_id, "action": "like"}, headers=b_headers)
    match_id = client.get("/api/matches", headers=a).json()[0]["match_id"]

    from app.routers.messages import NOTIFICATION_PREVIEW_CHARS

    client.post(
        f"/api/matches/{match_id}/messages",
        json={"content": "A" * 400},
        headers=a,
    )
    assert len(gesendet["text"]) <= NOTIFICATION_PREVIEW_CHARS
    assert gesendet["text"].endswith("…")
