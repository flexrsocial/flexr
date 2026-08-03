from tests.conftest import register_user


def _add_photo(client, headers):
    presign = client.post(
        "/api/profiles/me/photos/presign", headers=headers, json={"content_type": "image/jpeg"}
    ).json()
    resp = client.post(
        "/api/profiles/me/photos", headers=headers, json={"object_key": presign["object_key"]}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_presign_and_register_photo(client):
    headers = register_user(client, "photo@example.com")
    user = client.get("/api/profiles/me", headers=headers).json()

    presign = client.post(
        "/api/profiles/me/photos/presign",
        headers=headers,
        json={"content_type": "image/jpeg"},
    )
    assert presign.status_code == 200
    body = presign.json()
    assert body["object_key"].startswith(f"users/{user['id']}/")
    assert "upload_url" in body

    add = client.post(
        "/api/profiles/me/photos",
        headers=headers,
        json={"object_key": body["object_key"]},
    )
    assert add.status_code == 200
    assert len(add.json()["photos"]) == 1


def test_cannot_register_photo_with_foreign_object_key(client):
    headers = register_user(client, "photo2@example.com")
    resp = client.post(
        "/api/profiles/me/photos",
        headers=headers,
        json={"object_key": "users/someone-else/evil.jpg"},
    )
    assert resp.status_code == 400


def test_max_six_photos(client):
    headers = register_user(client, "photo3@example.com")
    for _ in range(6):
        presign = client.post(
            "/api/profiles/me/photos/presign",
            headers=headers,
            json={"content_type": "image/jpeg"},
        ).json()
        resp = client.post(
            "/api/profiles/me/photos", headers=headers, json={"object_key": presign["object_key"]}
        )
        assert resp.status_code == 200

    seventh = client.post(
        "/api/profiles/me/photos/presign",
        headers=headers,
        json={"content_type": "image/jpeg"},
    )
    assert seventh.status_code == 400


def test_positions_stay_unique_after_delete_and_readd(client):
    """Web und App nehmen photos[0] als Hauptfoto. Wird ein Foto aus der Mitte
    gelöscht und ein neues angelegt, dürfen keine zwei Fotos dieselbe Position
    bekommen - sonst ist die Reihenfolge und damit das Hauptfoto zufällig."""
    headers = register_user(client, "photopos@example.com")
    for _ in range(3):
        _add_photo(client, headers)

    photos = client.get("/api/profiles/me", headers=headers).json()["photos"]
    assert [p["position"] for p in photos] == [0, 1, 2]

    # mittleres Foto löschen -> verbleibende Positionen rutschen auf 0,1 nach
    after_delete = client.delete(
        f"/api/profiles/me/photos/{photos[1]['id']}", headers=headers
    ).json()
    assert [p["position"] for p in after_delete["photos"]] == [0, 1]

    after_add = _add_photo(client, headers)
    positions = [p["position"] for p in after_add["photos"]]
    assert positions == [0, 1, 2], positions


def test_photo_order_is_stable(client):
    """Die Reihenfolge aus /me muss nach Position sortiert sein, nicht nach
    Einfüge-Zufall der Datenbank."""
    headers = register_user(client, "photoorder@example.com")
    for _ in range(4):
        _add_photo(client, headers)

    photos = client.get("/api/profiles/me", headers=headers).json()["photos"]
    assert [p["position"] for p in photos] == sorted(p["position"] for p in photos)

    # Erstes Foto löschen: das bisher zweite muss zum Hauptfoto werden
    second_url = photos[1]["url"]
    client.delete(f"/api/profiles/me/photos/{photos[0]['id']}", headers=headers)
    after = client.get("/api/profiles/me", headers=headers).json()["photos"]
    assert after[0]["url"] == second_url
    assert [p["position"] for p in after] == [0, 1, 2]
