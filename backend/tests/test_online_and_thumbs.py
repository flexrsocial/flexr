from datetime import datetime, timedelta

from tests.conftest import TestingSessionLocal, register_user
from tests.test_messages import make_match


def test_matches_show_online_flag_for_active_user(client):
    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)
    # Beide haben gerade Requests gemacht -> beide gelten als online
    matches_a = client.get("/api/matches", headers=headers_a).json()
    assert matches_a[0]["is_online"] is True


def test_matches_show_offline_after_inactivity(client):
    from app.models import User

    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)
    db = TestingSessionLocal()
    try:
        other = db.query(User).filter(User.id == user_b["id"]).first()
        other.last_seen_at = datetime.utcnow() - timedelta(minutes=10)
        db.commit()
    finally:
        db.close()

    matches_a = client.get("/api/matches", headers=headers_a).json()
    assert matches_a[0]["is_online"] is False


def test_photo_with_thumbnail(client):
    headers = register_user(client, "thumb@example.com")
    user = client.get("/api/profiles/me", headers=headers).json()

    presign_full = client.post(
        "/api/profiles/me/photos/presign", headers=headers, json={"content_type": "image/jpeg"}
    ).json()
    presign_thumb = client.post(
        "/api/profiles/me/photos/presign", headers=headers, json={"content_type": "image/jpeg"}
    ).json()

    add = client.post(
        "/api/profiles/me/photos",
        headers=headers,
        json={
            "object_key": presign_full["object_key"],
            "thumb_object_key": presign_thumb["object_key"],
        },
    )
    assert add.status_code == 200, add.text
    photo = add.json()["photos"][0]
    assert photo["thumb_url"] is not None
    assert presign_thumb["object_key"] in photo["thumb_url"]


def test_photo_without_thumbnail_still_works(client):
    headers = register_user(client, "nothumb@example.com")
    presign = client.post(
        "/api/profiles/me/photos/presign", headers=headers, json={"content_type": "image/jpeg"}
    ).json()
    add = client.post(
        "/api/profiles/me/photos", headers=headers, json={"object_key": presign["object_key"]}
    )
    assert add.status_code == 200
    assert add.json()["photos"][0]["thumb_url"] is None


def test_foreign_thumb_object_key_rejected(client):
    headers = register_user(client, "evilthumb@example.com")
    presign = client.post(
        "/api/profiles/me/photos/presign", headers=headers, json={"content_type": "image/jpeg"}
    ).json()
    resp = client.post(
        "/api/profiles/me/photos",
        headers=headers,
        json={
            "object_key": presign["object_key"],
            "thumb_object_key": "users/someone-else/thumb.jpg",
        },
    )
    assert resp.status_code == 400
