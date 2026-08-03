from tests.conftest import register_user, register_user_with_photo


def make_pair(client):
    # Freigegebenes Foto auf beiden Seiten: das Deck zeigt nur Profile mit Foto.
    headers_a = register_user_with_photo(
        client, "safety.a@example.com", name="A", gender="mann"
    )
    headers_b = register_user_with_photo(
        client, "safety.b@example.com", name="B", gender="frau"
    )
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    user_b = client.get("/api/profiles/me", headers=headers_b).json()
    return (headers_a, user_a), (headers_b, user_b)


def test_report_user(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    resp = client.post(
        "/api/reports",
        headers=headers_a,
        json={"reported_user_id": user_b["id"], "reason": "Unangemessenes Verhalten"},
    )
    assert resp.status_code == 201


def test_cannot_report_self(client):
    headers_a = register_user(client, "reportself@example.com")
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    resp = client.post(
        "/api/reports",
        headers=headers_a,
        json={"reported_user_id": user_a["id"], "reason": "Test"},
    )
    assert resp.status_code == 400


def test_block_removes_user_from_deck(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)

    deck_before = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["id"] == user_b["id"] for p in deck_before)

    block_resp = client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})
    assert block_resp.status_code == 201

    deck_after = client.get("/api/swipes/deck", headers=headers_a).json()
    assert not any(p["id"] == user_b["id"] for p in deck_after)

    # Blockierung wirkt in beide Richtungen
    deck_of_b = client.get("/api/swipes/deck", headers=headers_b).json()
    assert not any(p["id"] == user_a["id"] for p in deck_of_b)


def test_unblock_restores_visibility(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})

    unblock_resp = client.delete(f"/api/blocks/{user_b['id']}", headers=headers_a)
    assert unblock_resp.status_code == 200

    deck_after = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["id"] == user_b["id"] for p in deck_after)


def test_list_blocks(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})
    resp = client.get("/api/blocks", headers=headers_a)
    assert resp.status_code == 200
    assert user_b["id"] in resp.json()


def test_blocked_profiles_carry_name_and_photo(client):
    """Ohne Name und Bild lässt sich eine Blockierung in der Oberfläche nicht
    sinnvoll wieder aufheben - GET /api/blocks liefert nur IDs."""
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})

    resp = client.get("/api/blocks/profiles", headers=headers_a)
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["id"] == user_b["id"]
    assert entries[0]["name"] == "B"
    assert entries[0]["photo_url"]

    client.delete(f"/api/blocks/{user_b['id']}", headers=headers_a)
    assert client.get("/api/blocks/profiles", headers=headers_a).json() == []


def test_blocked_profiles_empty_without_blocks(client):
    headers = register_user(client, "noblocks@example.com")
    resp = client.get("/api/blocks/profiles", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []
