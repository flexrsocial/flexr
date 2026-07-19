from tests.conftest import register_user


def test_update_gym_and_bio(client):
    headers = register_user(client, "update@example.com")
    resp = client.patch(
        "/api/profiles/me",
        headers=headers,
        json={"gym": "Clever Fit", "bio": "Neue Bio 🏋️💪🔥"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["gym"] == "Clever Fit"
    assert body["bio"] == "Neue Bio 🏋️💪🔥"  # Emojis müssen erhalten bleiben


def test_update_plz_and_city_together(client):
    headers = register_user(client, "move@example.com")
    resp = client.patch(
        "/api/profiles/me",
        headers=headers,
        json={"plz": "8010", "city": "Graz"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["plz"] == "8010"
    assert body["city"] == "Graz"


def test_update_plz_without_city_rejected(client):
    headers = register_user(client, "moveonly@example.com")
    resp = client.patch("/api/profiles/me", headers=headers, json={"plz": "8010"})
    assert resp.status_code == 400


def test_update_invalid_gym_rejected(client):
    headers = register_user(client, "fakegym@example.com")
    resp = client.patch(
        "/api/profiles/me", headers=headers, json={"gym": "Garagen-Gym 3000"}
    )
    assert resp.status_code == 400


def test_update_invalid_plz_rejected(client):
    headers = register_user(client, "badplz@example.com")
    resp = client.patch(
        "/api/profiles/me", headers=headers, json={"plz": "12", "city": "Wien"}
    )
    assert resp.status_code == 422


def test_empty_bio_clears_bio(client):
    headers = register_user(client, "clearbio@example.com", bio="Alte Bio")
    resp = client.patch("/api/profiles/me", headers=headers, json={"bio": ""})
    assert resp.status_code == 200
    assert resp.json()["bio"] is None


def test_untouched_fields_stay(client):
    headers = register_user(client, "stay@example.com")
    before = client.get("/api/profiles/me", headers=headers).json()
    resp = client.patch("/api/profiles/me", headers=headers, json={"bio": "Nur die Bio neu"})
    after = resp.json()
    assert after["bio"] == "Nur die Bio neu"
    assert after["gym"] == before["gym"]
    assert after["city"] == before["city"]
    assert after["plz"] == before["plz"]
