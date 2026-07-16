from tests.conftest import register_user


def make_pair(client):
    """Zwei zueinander passende Nutzer in derselben Stadt anlegen."""
    headers_a = register_user(
        client, "swiper.a@example.com", name="A", gender="mann"
    )
    headers_b = register_user(
        client, "swiper.b@example.com", name="B", gender="frau"
    )
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    user_b = client.get("/api/profiles/me", headers=headers_b).json()
    return (headers_a, user_a), (headers_b, user_b)


def test_deck_shows_compatible_users(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["id"] == user_b["id"] for p in deck)


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
    assert any(p["id"] == user_b["id"] for p in matches_a)
    matches_b = client.get("/api/matches", headers=headers_b).json()
    assert any(p["id"] == user_a["id"] for p in matches_b)


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
