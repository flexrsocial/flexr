from tests.conftest import register_user
from tests.test_swipes_and_matches import make_pair


def make_match(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": user_b["id"], "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": user_a["id"], "action": "like"})

    match_id = client.get("/api/matches", headers=headers_a).json()[0]["match_id"]
    return match_id, (headers_a, user_a), (headers_b, user_b)


def test_send_and_list_messages(client):
    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)

    resp = client.post(
        f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": "Hey!"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["content"] == "Hey!"
    assert body["sender_id"] == user_a["id"]
    assert body["read_at"] is None

    resp = client.post(
        f"/api/matches/{match_id}/messages", headers=headers_b, json={"content": "Hi zurück!"}
    )
    assert resp.status_code == 201

    messages = client.get(f"/api/matches/{match_id}/messages", headers=headers_a).json()
    assert [m["content"] for m in messages] == ["Hey!", "Hi zurück!"]


def test_reading_messages_marks_them_read(client):
    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)
    client.post(f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": "Hey!"})

    matches_b = client.get("/api/matches", headers=headers_b).json()
    assert matches_b[0]["unread_count"] == 1
    assert matches_b[0]["last_message"]["content"] == "Hey!"

    # B liest den Chat -> Nachricht gilt als gelesen
    messages = client.get(f"/api/matches/{match_id}/messages", headers=headers_b).json()
    assert messages[0]["read_at"] is not None

    matches_b_after = client.get("/api/matches", headers=headers_b).json()
    assert matches_b_after[0]["unread_count"] == 0


def test_cannot_message_a_match_you_are_not_part_of(client):
    match_id, _, _ = make_match(client)
    headers_c = register_user(client, "outsider@example.com", name="C", gender="mann")

    resp = client.get(f"/api/matches/{match_id}/messages", headers=headers_c)
    assert resp.status_code == 404

    resp = client.post(
        f"/api/matches/{match_id}/messages", headers=headers_c, json={"content": "Hallo"}
    )
    assert resp.status_code == 404


def test_unknown_match_returns_404(client):
    headers_a = register_user(client, "solo2@example.com")
    resp = client.get("/api/matches/does-not-exist/messages", headers=headers_a)
    assert resp.status_code == 404


def test_blocking_disables_chat_and_hides_match(client):
    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)
    client.post(f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": "Hey!"})

    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})

    # Match verschwindet aus der Liste
    matches_a = client.get("/api/matches", headers=headers_a).json()
    assert matches_a == []
    matches_b = client.get("/api/matches", headers=headers_b).json()
    assert matches_b == []

    # Chat ist für beide Seiten gesperrt, auch per direktem match_id-Zugriff
    resp = client.get(f"/api/matches/{match_id}/messages", headers=headers_a)
    assert resp.status_code == 403
    resp = client.get(f"/api/matches/{match_id}/messages", headers=headers_b)
    assert resp.status_code == 403
    resp = client.post(
        f"/api/matches/{match_id}/messages", headers=headers_b, json={"content": "Noch da?"}
    )
    assert resp.status_code == 403


def test_empty_message_rejected(client):
    match_id, (headers_a, _), _ = make_match(client)
    resp = client.post(f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": ""})
    assert resp.status_code == 422


def test_unmatch_removes_match_and_messages(client):
    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)
    client.post(f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": "Hallo!"})

    resp = client.delete(f"/api/matches/{match_id}", headers=headers_a)
    assert resp.status_code == 200

    # Für beide Seiten verschwunden
    assert client.get("/api/matches", headers=headers_a).json() == []
    assert client.get("/api/matches", headers=headers_b).json() == []

    # Chat nicht mehr erreichbar
    assert client.get(f"/api/matches/{match_id}/messages", headers=headers_a).status_code == 404


def test_unmatch_keeps_person_out_of_deck(client):
    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)
    client.delete(f"/api/matches/{match_id}", headers=headers_a)

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    assert all(p["id"] != user_b["id"] for p in deck)


def test_unmatch_requires_participation(client):
    match_id, _, _ = make_match(client)
    headers_c = register_user(client, "unmatch.outsider@example.com", name="C", gender="mann")
    assert client.delete(f"/api/matches/{match_id}", headers=headers_c).status_code == 404


def test_unmatch_unknown_match_404(client):
    headers = register_user(client, "unmatch.solo@example.com")
    assert client.delete("/api/matches/gibt-es-nicht", headers=headers).status_code == 404
