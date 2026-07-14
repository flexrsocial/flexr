from tests.conftest import register_user


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


def test_max_five_photos(client):
    headers = register_user(client, "photo3@example.com")
    for _ in range(5):
        presign = client.post(
            "/api/profiles/me/photos/presign",
            headers=headers,
            json={"content_type": "image/jpeg"},
        ).json()
        client.post(
            "/api/profiles/me/photos", headers=headers, json={"object_key": presign["object_key"]}
        )

    sixth = client.post(
        "/api/profiles/me/photos/presign",
        headers=headers,
        json={"content_type": "image/jpeg"},
    )
    assert sixth.status_code == 400
