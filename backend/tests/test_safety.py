from tests.conftest import register_user


def make_pair(client):
    headers_a = register_user(
        client, "safety.a@example.com", name="A", gender="mann", interest="frau"
    )
    headers_b = register_user(
        client, "safety.b@example.com", name="B", gender="frau", interest="mann"
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
