from app.models import User
from tests.conftest import (
    GYM_GRAZ,
    GYM_WIEN,
    TestingSessionLocal,
    register_user,
    register_user_with_photo,
)


def make_pair(client):
    """Zwei zueinander passende Nutzer in derselben Stadt anlegen - jeweils mit
    freigegebenem Foto, sonst tauchen sie im Deck des anderen nicht auf."""
    headers_a = register_user_with_photo(
        client, "swiper.a@example.com", name="A", gender="mann"
    )
    headers_b = register_user_with_photo(
        client, "swiper.b@example.com", name="B", gender="frau"
    )
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    user_b = client.get("/api/profiles/me", headers=headers_b).json()
    return (headers_a, user_a), (headers_b, user_b)


def test_deck_shows_compatible_users(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["id"] == user_b["id"] for p in deck)


def test_deck_shows_liker_beyond_own_search_radius(client):
    """Ein Premium-Konto (250 km) liked jemanden mit den freien 20 km
    Voreinstellung, der weiter als 50 km entfernt trainiert (Wien-Graz, rund
    145 km). Ohne eigene Ausnahme faende die geliketen Person den Liker nie im
    eigenen Deck - der Like waere nie erwiderbar, obwohl genau das Gegenteil
    versprochen wird (siehe incoming.lockedSub: "Ohne Premium tauchen sie ganz
    normal in deinem Deck auf")."""
    headers_a = register_user_with_photo(
        client, "premium.liker@example.com", name="A", gender="mann", gym=GYM_WIEN,
    )
    headers_b = register_user_with_photo(
        client, "free.liked@example.com", name="B", gender="frau", gym=GYM_GRAZ,
    )
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    user_b = client.get("/api/profiles/me", headers=headers_b).json()

    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.id == user_a["id"]).one().is_subscribed = True
        db.commit()
    finally:
        db.close()
    resp = client.patch(
        "/api/profiles/me", json={"search_radius_km": 250}, headers=headers_a
    )
    assert resp.json()["search_radius_km"] == 250

    # A findet B ueber den vollen Premium-Radius und liked sie.
    deck_a = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["id"] == user_b["id"] for p in deck_a)
    like = client.post(
        "/api/swipes", headers=headers_a, json={"to_user_id": user_b["id"], "action": "like"}
    )
    assert like.status_code == 200
    assert like.json()["matched"] is False

    # B sieht A trotzdem im eigenen Deck, obwohl Wien-Graz die freien 20 km
    # (und selbst die 50 km Obergrenze ohne Premium) klar ueberschreitet.
    deck_b = client.get("/api/swipes/deck", headers=headers_b).json()
    assert any(p["id"] == user_a["id"] for p in deck_b)


def test_mutual_like_creates_match(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)

    first = client.post(
        "/api/swipes",
        headers=headers_a,
        json={"to_user_id": user_b["id"], "action": "like"},
    )
    assert first.status_code == 200
    assert first.json()["matched"] is False

    second = client.post(
        "/api/swipes",
        headers=headers_b,
        json={"to_user_id": user_a["id"], "action": "like"},
    )
    assert second.status_code == 200
    assert second.json()["matched"] is True

    matches_a = client.get("/api/matches", headers=headers_a).json()
    assert any(m["profile"]["id"] == user_b["id"] for m in matches_a)
    matches_b = client.get("/api/matches", headers=headers_b).json()
    assert any(m["profile"]["id"] == user_a["id"] for m in matches_b)


def test_pass_does_not_create_match(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post(
        "/api/swipes", headers=headers_a, json={"to_user_id": user_b["id"], "action": "pass"}
    )
    matches_a = client.get("/api/matches", headers=headers_a).json()
    assert matches_a == []


def test_cannot_swipe_self(client):
    headers_a = register_user(client, "self@example.com")
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    resp = client.post(
        "/api/swipes", headers=headers_a, json={"to_user_id": user_a["id"], "action": "like"}
    )
    assert resp.status_code == 400


def test_swipe_on_unknown_user_returns_404(client):
    headers_a = register_user(client, "solo@example.com")
    resp = client.post(
        "/api/swipes",
        headers=headers_a,
        json={"to_user_id": "does-not-exist", "action": "like"},
    )
    assert resp.status_code == 404
