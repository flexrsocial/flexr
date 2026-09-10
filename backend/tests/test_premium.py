"""FLEXR Premium: dauerhaft gratis nutzbare Plattform, optionale Zusatzstufe.

Zwei Zustaende sind zu pruefen, und sie unterscheiden sich in *allem*:

* ``premium_enabled = False`` (Beta, so laeuft der Betrieb gerade):
  niemand hat Grenzen, niemand kann etwas kaufen.
* ``premium_enabled = True`` (nach der Beta): Standardnutzer stossen an
  Like-, Chat- und Umkreisgrenzen, Premium hebt sie auf.

Die conftest schaltet Premium global **ein** - der ausgeschaltete Zustand wird
hier gezielt per monkeypatch hergestellt.

Was hier bewusst *nicht* geprueft wird: dass ein abgelaufener Zeitraum jemanden
aussperrt. Genau das ist am 10.09.2026 abgeschafft worden, und der Test dafuer
ist mit der Bezahlwand verschwunden.
"""

from datetime import datetime, timedelta

import pytest

from app.config import settings
from app.models import Match, Message, Swipe, User
from tests.conftest import (
    TestingSessionLocal,
    register_user,
    register_user_with_photo,
)


def _set_premium(user_id: str, aktiv: bool = True) -> None:
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        user.is_subscribed = aktiv
        db.commit()
    finally:
        db.close()


def _user_id(client, headers) -> str:
    return client.get("/api/profiles/me", headers=headers).json()["id"]


def _fremde_likes(client, empfaenger_id: str, anzahl: int) -> None:
    """``anzahl`` fremde Konten liken den Empfaenger - direkt in der DB.

    Ueber die API waere das ``anzahl`` vollstaendige Registrierungen; hier geht
    es nur um die Swipe-Zeilen.
    """
    db = TestingSessionLocal()
    try:
        for i in range(anzahl):
            liker = User(
                email=f"liker{i}-{empfaenger_id[:6]}@example.com",
                password_hash="x",
                name=f"Liker {i}",
                birthdate=datetime(1995, 1, 1).date(),
                plz="1100",
                city="Wien",
                gender="mann",
                interest="frau",
                gym="McFit",
                sensitive_data_consent_at=datetime.utcnow(),
                verification_required=False,
            )
            db.add(liker)
            db.flush()
            db.add(
                Swipe(from_user_id=liker.id, to_user_id=empfaenger_id, action="like")
            )
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Beta: kein Preis, keine Grenzen
# ---------------------------------------------------------------------------

def test_ohne_premium_schalter_ist_alles_unbegrenzt(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", False)
    headers = register_user(client, "beta@example.com")

    status = client.get("/api/billing/status", headers=headers).json()
    assert status["premium_enabled"] is False
    assert status["is_premium"] is False
    # None = unbegrenzt. Die Oberflaeche blendet den Zaehler daran aus.
    assert status["likes_remaining"] is None
    assert status["open_chats_remaining"] is None
    assert status["max_radius_km"] == 250

    # Das Deck war frueher der Endpunkt hinter der Bezahlwand.
    assert client.get("/api/swipes/deck", headers=headers).status_code == 200


def test_checkout_erst_nach_der_beta(client, monkeypatch):
    """Kein Vertrag ueber Funktionen, die es gerade ohnehin unbegrenzt gibt."""
    monkeypatch.setattr(settings, "premium_enabled", False)
    headers = register_user(client, "zufrueh@example.com")

    resp = client.post(
        "/api/billing/checkout",
        json={"immediate_start": True, "withdrawal_ack": True},
        headers=headers,
    )
    assert resp.status_code == 409
    assert "Beta" in resp.json()["detail"]

    # Und es bleibt keine Einwilligungs-Buchung zurueck.
    db = TestingSessionLocal()
    try:
        from app.models import CheckoutConsent

        assert db.query(CheckoutConsent).count() == 0
    finally:
        db.close()


def test_waehrend_der_beta_traegt_niemand_ein_premium_abzeichen(client, monkeypatch):
    """Ein Abo aus der Zeit der alten Gebuehr ist in der Beta wirkungslos.

    Sonst haetten Altkonten ein Abzeichen und Vorteile, waehrend die Grenzen
    fuer alle anderen gar nicht gelten - eine Auszeichnung fuer nichts.
    """
    monkeypatch.setattr(settings, "premium_enabled", False)
    headers = register_user(client, "altabo@example.com")
    _set_premium(_user_id(client, headers))

    status = client.get("/api/billing/status", headers=headers).json()
    assert status["is_premium"] is False
    # Kuendbar bleibt es trotzdem - dafuer steht has_stripe_subscription.
    assert status["has_stripe_subscription"] is True


# ---------------------------------------------------------------------------
# Nach der Beta: Like-Kontingent
# ---------------------------------------------------------------------------

def test_like_kontingent_ist_aufgebraucht(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_daily_likes", 2)

    headers = register_user_with_photo(client, "sparsam@example.com")
    ziele = [
        _user_id(client, register_user_with_photo(client, f"ziel{i}@example.com"))
        for i in range(3)
    ]

    assert client.post(
        "/api/swipes", json={"to_user_id": ziele[0], "action": "like"}, headers=headers
    ).status_code == 200
    zweiter = client.post(
        "/api/swipes", json={"to_user_id": ziele[1], "action": "like"}, headers=headers
    )
    assert zweiter.status_code == 200
    assert zweiter.json()["likes_remaining"] == 0

    dritter = client.post(
        "/api/swipes", json={"to_user_id": ziele[2], "action": "like"}, headers=headers
    )
    assert dritter.status_code == 403
    assert dritter.json()["detail"]["code"] == "like_limit_reached"
    assert dritter.json()["detail"]["next_like_at"] is not None


def test_pass_kostet_kein_kontingent(client, monkeypatch):
    """Wer weiterblaettert, soll nicht sparen muessen."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_daily_likes", 1)

    headers = register_user_with_photo(client, "blaetterer@example.com")
    ziele = [
        _user_id(client, register_user_with_photo(client, f"pziel{i}@example.com"))
        for i in range(3)
    ]

    for ziel in ziele[:2]:
        assert client.post(
            "/api/swipes", json={"to_user_id": ziel, "action": "pass"}, headers=headers
        ).status_code == 200

    # Das eine Like ist trotz zweier Passes noch da.
    assert client.post(
        "/api/swipes", json={"to_user_id": ziele[2], "action": "like"}, headers=headers
    ).status_code == 200


def test_premium_likt_ohne_grenze(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_daily_likes", 1)

    headers = register_user_with_photo(client, "grosszuegig@example.com")
    _set_premium(_user_id(client, headers))
    ziele = [
        _user_id(client, register_user_with_photo(client, f"gziel{i}@example.com"))
        for i in range(3)
    ]

    for ziel in ziele:
        resp = client.post(
            "/api/swipes", json={"to_user_id": ziel, "action": "like"}, headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["likes_remaining"] is None


def test_alte_likes_fallen_aus_dem_fenster(client, monkeypatch):
    """Das Kontingent laeuft rollierend ueber 24 Stunden, nicht pro Kalendertag."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_daily_likes", 1)

    headers = register_user_with_photo(client, "geduldig@example.com")
    user_id = _user_id(client, headers)
    ziel_a = _user_id(client, register_user_with_photo(client, "fziel-a@example.com"))
    ziel_b = _user_id(client, register_user_with_photo(client, "fziel-b@example.com"))

    assert client.post(
        "/api/swipes", json={"to_user_id": ziel_a, "action": "like"}, headers=headers
    ).status_code == 200

    # Den einen Like 25 Stunden zurueckdatieren.
    db = TestingSessionLocal()
    try:
        swipe = db.query(Swipe).filter(Swipe.from_user_id == user_id).one()
        swipe.created_at = datetime.utcnow() - timedelta(hours=25)
        db.commit()
    finally:
        db.close()

    assert client.post(
        "/api/swipes", json={"to_user_id": ziel_b, "action": "like"}, headers=headers
    ).status_code == 200


# ---------------------------------------------------------------------------
# Nach der Beta: offene Unterhaltungen
# ---------------------------------------------------------------------------

def _match_mit(client, headers_a, headers_b) -> str:
    """Gegenseitiges Like -> Match, gibt die match_id zurueck."""
    a = _user_id(client, headers_a)
    b = _user_id(client, headers_b)
    client.post("/api/swipes", json={"to_user_id": a, "action": "like"}, headers=headers_b)
    client.post("/api/swipes", json={"to_user_id": b, "action": "like"}, headers=headers_a)
    matches = client.get("/api/matches", headers=headers_a).json()
    return next(m["match_id"] for m in matches if m["profile"]["id"] == b)


def test_chat_kontingent_greift_beim_vierten_gespraech(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_open_chats", 2)

    headers = register_user_with_photo(client, "vielredner@example.com")
    partner = [
        register_user_with_photo(client, f"partner{i}@example.com") for i in range(3)
    ]
    matches = [_match_mit(client, headers, p) for p in partner]

    for match_id in matches[:2]:
        assert client.post(
            f"/api/matches/{match_id}/messages",
            json={"content": "Servus!"},
            headers=headers,
        ).status_code == 201

    dritter = client.post(
        f"/api/matches/{matches[2]}/messages",
        json={"content": "Servus!"},
        headers=headers,
    )
    assert dritter.status_code == 403
    assert dritter.json()["detail"]["code"] == "chat_limit_reached"


def test_in_laufenden_gespraechen_ist_die_nachrichtenzahl_frei(client, monkeypatch):
    """Die Grenze steht am Anfang eines Chats, nicht mittendrin."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_open_chats", 1)

    headers = register_user_with_photo(client, "ausdauernd@example.com")
    partner = register_user_with_photo(client, "zuhoerer@example.com")
    match_id = _match_mit(client, headers, partner)

    for i in range(5):
        assert client.post(
            f"/api/matches/{match_id}/messages",
            json={"content": f"Nachricht {i}"},
            headers=headers,
        ).status_code == 201


def test_match_aufloesen_gibt_den_chatplatz_frei(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_open_chats", 1)

    headers = register_user_with_photo(client, "aufraeumer@example.com")
    erster = register_user_with_photo(client, "erster@example.com")
    zweiter = register_user_with_photo(client, "zweiter@example.com")

    match_a = _match_mit(client, headers, erster)
    match_b = _match_mit(client, headers, zweiter)

    assert client.post(
        f"/api/matches/{match_a}/messages", json={"content": "Hi"}, headers=headers
    ).status_code == 201
    assert client.post(
        f"/api/matches/{match_b}/messages", json={"content": "Hi"}, headers=headers
    ).status_code == 403

    assert client.delete(f"/api/matches/{match_a}", headers=headers).status_code in (200, 204)

    assert client.post(
        f"/api/matches/{match_b}/messages", json={"content": "Hi"}, headers=headers
    ).status_code == 201


# ---------------------------------------------------------------------------
# Nach der Beta: Suchumkreis
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("premium,erwartet", [(False, 50), (True, 250)])
def test_umkreis_wird_auf_das_erlaubte_gekappt(client, monkeypatch, premium, erwartet):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "free_max_radius_km", 50)

    headers = register_user(client, f"umkreis-{premium}@example.com")
    if premium:
        _set_premium(_user_id(client, headers))

    resp = client.patch(
        "/api/profiles/me", json={"search_radius_km": 250}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["search_radius_km"] == erwartet


# ---------------------------------------------------------------------------
# Premium-Funktionen
# ---------------------------------------------------------------------------

def test_eingehende_likes_zeigen_ohne_premium_nur_die_zahl(client, monkeypatch):
    """Die Anzahl darf jeder sehen - sie ist der beste Grund fuer Premium."""
    monkeypatch.setattr(settings, "premium_enabled", True)

    headers = register_user_with_photo(client, "begehrt@example.com")
    _fremde_likes(client, _user_id(client, headers), 3)

    ohne = client.get("/api/swipes/incoming", headers=headers).json()
    assert ohne["count"] == 3
    assert ohne["premium_required"] is True
    assert ohne["profiles"] == []

    _set_premium(_user_id(client, headers))
    mit = client.get("/api/swipes/incoming", headers=headers).json()
    assert mit["count"] == 3
    assert mit["premium_required"] is False
    assert len(mit["profiles"]) == 3


def test_rewind_nur_mit_premium(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)

    headers = register_user_with_photo(client, "reumuetig@example.com")
    ziel = _user_id(client, register_user_with_photo(client, "verpasst@example.com"))
    client.post(
        "/api/swipes", json={"to_user_id": ziel, "action": "pass"}, headers=headers
    )

    verboten = client.post("/api/swipes/rewind", headers=headers)
    assert verboten.status_code == 403
    assert verboten.json()["detail"]["code"] == "premium_required"

    _set_premium(_user_id(client, headers))
    erlaubt = client.post("/api/swipes/rewind", headers=headers)
    assert erlaubt.status_code == 200
    assert erlaubt.json()["to_user_id"] == ziel

    # Der Swipe ist weg - das Profil kann wieder im Deck auftauchen.
    db = TestingSessionLocal()
    try:
        assert db.query(Swipe).filter(Swipe.to_user_id == ziel).count() == 0
    finally:
        db.close()


def test_rewind_faellt_bei_bestehendem_match_aus(client, monkeypatch):
    """Ein Match der Gegenseite darf nicht einseitig verschwinden."""
    monkeypatch.setattr(settings, "premium_enabled", True)

    headers = register_user_with_photo(client, "zuspaet@example.com")
    partner = register_user_with_photo(client, "gematcht@example.com")
    _set_premium(_user_id(client, headers))
    _match_mit(client, headers, partner)

    resp = client.post("/api/swipes/rewind", headers=headers)
    assert resp.status_code == 409

    db = TestingSessionLocal()
    try:
        assert db.query(Match).count() == 1
    finally:
        db.close()


def test_premium_abzeichen_steht_im_fremdprofil(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)

    betrachter = register_user_with_photo(client, "betrachter@example.com")
    gesehen = register_user_with_photo(
        client, "gesehen@example.com", gender="frau"
    )
    _set_premium(_user_id(client, gesehen))

    deck = client.get("/api/swipes/deck", headers=betrachter).json()
    treffer = [p for p in deck if p["id"] == _user_id(client, gesehen)]
    assert treffer and treffer[0]["is_premium"] is True


def test_status_liefert_preis_und_grenzen(client, monkeypatch):
    """Die Clients rechnen nichts selbst aus - alles kommt von hier."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    headers = register_user(client, "preisschild@example.com")

    status = client.get("/api/billing/status", headers=headers).json()
    assert status["price_cents"] == settings.premium_price_cents
    assert status["currency"] == settings.premium_currency
    assert status["free_daily_likes"] == settings.free_daily_likes
    assert status["free_open_chats"] == settings.free_open_chats
    assert status["free_max_radius_km"] == settings.free_max_radius_km
    assert status["likes_remaining"] == settings.free_daily_likes
