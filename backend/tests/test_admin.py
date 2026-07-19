from tests.conftest import create_admin, register_user


def test_admin_login_wrong_password(client):
    create_admin(client, email="wrongpw@example.com")
    resp = client.post(
        "/api/admin/auth/login",
        json={"email": "wrongpw@example.com", "password": "falsch"},
    )
    assert resp.status_code == 401


def test_regular_user_token_cannot_access_admin_endpoints(client):
    user_headers = register_user(client, "notadmin@example.com")
    resp = client.get("/api/admin/users", headers=user_headers)
    assert resp.status_code == 401


def test_admin_token_cannot_access_user_endpoints(client):
    admin_headers, _ = create_admin(client, email="adminonly@example.com")
    resp = client.get("/api/profiles/me", headers=admin_headers)
    assert resp.status_code == 401


def test_admin_list_and_detail_users(client):
    admin_headers, _ = create_admin(client, email="admin2@example.com")
    register_user(client, "listed@example.com", name="Listed User")

    listing = client.get("/api/admin/users", headers=admin_headers)
    assert listing.status_code == 200
    users = listing.json()
    assert any(u["email"] == "listed@example.com" for u in users)

    user_id = next(u["id"] for u in users if u["email"] == "listed@example.com")
    detail = client.get(f"/api/admin/users/{user_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Listed User"


def test_admin_search_users(client):
    admin_headers, _ = create_admin(client, email="admin3@example.com")
    register_user(client, "findme@example.com", name="Findable")
    register_user(client, "other@example.com", name="Other")

    resp = client.get("/api/admin/users", headers=admin_headers, params={"q": "findable"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["email"] == "findme@example.com"


def test_admin_ban_blocks_login_and_unban_restores(client):
    admin_headers, _ = create_admin(client, email="admin4@example.com")
    register_user(client, "tobeban@example.com")

    users = client.get("/api/admin/users", headers=admin_headers).json()
    user_id = next(u["id"] for u in users if u["email"] == "tobeban@example.com")

    ban_resp = client.post(f"/api/admin/users/{user_id}/ban", headers=admin_headers)
    assert ban_resp.status_code == 200
    assert ban_resp.json()["is_banned"] is True

    login_resp = client.post(
        "/api/auth/login",
        json={"email": "tobeban@example.com", "password": "supersecret123"},
    )
    assert login_resp.status_code == 403

    unban_resp = client.post(f"/api/admin/users/{user_id}/unban", headers=admin_headers)
    assert unban_resp.status_code == 200
    assert unban_resp.json()["is_banned"] is False

    login_resp2 = client.post(
        "/api/auth/login",
        json={"email": "tobeban@example.com", "password": "supersecret123"},
    )
    assert login_resp2.status_code == 200


def test_admin_delete_user_cascades(client):
    admin_headers, _ = create_admin(client, email="admin5@example.com")
    headers_a = register_user(
        client, "cascade.a@example.com", name="A", gender="mann"
    )
    headers_b = register_user(
        client, "cascade.b@example.com", name="B", gender="frau"
    )
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    user_b = client.get("/api/profiles/me", headers=headers_b).json()

    # Swipe, Match, Report und Block erzeugen, damit wir Cascade-Delete testen
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": user_b["id"], "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": user_a["id"], "action": "like"})
    client.post(
        "/api/reports",
        headers=headers_a,
        json={"reported_user_id": user_b["id"], "reason": "Testmeldung"},
    )
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})

    delete_resp = client.delete(f"/api/admin/users/{user_b['id']}", headers=admin_headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    detail_resp = client.get(f"/api/admin/users/{user_b['id']}", headers=admin_headers)
    assert detail_resp.status_code == 404


def test_photo_starts_pending_and_hidden_from_deck(client):
    admin_headers, _ = create_admin(client, email="admin6@example.com")
    headers_a = register_user(
        client, "photodeck.a@example.com", name="A", gender="mann"
    )
    headers_b = register_user(
        client, "photodeck.b@example.com", name="B", gender="frau"
    )
    user_b = client.get("/api/profiles/me", headers=headers_b).json()

    presign = client.post(
        "/api/profiles/me/photos/presign",
        headers=headers_b,
        json={"content_type": "image/jpeg"},
    ).json()
    add_resp = client.post(
        "/api/profiles/me/photos", headers=headers_b, json={"object_key": presign["object_key"]}
    )
    assert add_resp.json()["photos"][0]["status"] == "pending"

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    candidate = next(p for p in deck if p["id"] == user_b["id"])
    assert candidate["photos"] == []

    pending = client.get("/api/admin/photos", headers=admin_headers, params={"status": "pending"})
    assert pending.status_code == 200
    photo_id = next(p["id"] for p in pending.json() if p["user_id"] == user_b["id"])

    approve_resp = client.post(f"/api/admin/photos/{photo_id}/approve", headers=admin_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    deck_after = client.get("/api/swipes/deck", headers=headers_a).json()
    candidate_after = next(p for p in deck_after if p["id"] == user_b["id"])
    assert len(candidate_after["photos"]) == 1

    reject_resp = client.post(f"/api/admin/photos/{photo_id}/reject", headers=admin_headers)
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    deck_after_reject = client.get("/api/swipes/deck", headers=headers_a).json()
    candidate_after_reject = next(p for p in deck_after_reject if p["id"] == user_b["id"])
    assert candidate_after_reject["photos"] == []


def test_admin_reports_list(client):
    admin_headers, _ = create_admin(client, email="admin7@example.com")
    headers_a = register_user(
        client, "reportlist.a@example.com", name="A", gender="mann"
    )
    headers_b = register_user(
        client, "reportlist.b@example.com", name="B", gender="frau"
    )
    user_b = client.get("/api/profiles/me", headers=headers_b).json()
    client.post(
        "/api/reports",
        headers=headers_a,
        json={"reported_user_id": user_b["id"], "reason": "Beispielgrund"},
    )

    resp = client.get("/api/admin/reports", headers=admin_headers)
    assert resp.status_code == 200
    reports = resp.json()
    assert any(r["reported_id"] == user_b["id"] and r["reason"] == "Beispielgrund" for r in reports)


def test_admin_dismiss_report(client):
    admin_headers, _ = create_admin(client, email="admin.dismiss@example.com")
    headers_a = register_user(client, "dismiss.a@example.com", name="A", gender="mann")
    headers_b = register_user(client, "dismiss.b@example.com", name="B", gender="frau")
    user_b = client.get("/api/profiles/me", headers=headers_b).json()
    client.post(
        "/api/reports",
        headers=headers_a,
        json={"reported_user_id": user_b["id"], "reason": "Nichts dran"},
    )

    reports = client.get("/api/admin/reports", headers=admin_headers).json()
    assert len(reports) == 1
    report_id = reports[0]["id"]
    assert client.get("/api/admin/stats", headers=admin_headers).json()["open_reports"] == 1

    resp = client.post(f"/api/admin/reports/{report_id}/dismiss", headers=admin_headers)
    assert resp.status_code == 200

    # Verschwindet aus der offenen Liste und aus dem Stats-Zähler
    assert client.get("/api/admin/reports", headers=admin_headers).json() == []
    assert client.get("/api/admin/stats", headers=admin_headers).json()["open_reports"] == 0


def test_admin_dismiss_unknown_report_404(client):
    admin_headers, _ = create_admin(client, email="admin.dismiss404@example.com")
    resp = client.post("/api/admin/reports/gibt-es-nicht/dismiss", headers=admin_headers)
    assert resp.status_code == 404


def test_admin_stats(client):
    admin_headers, _ = create_admin(client, email="admin8@example.com")
    register_user(client, "stats.a@example.com")

    resp = client.get("/api/admin/stats", headers=admin_headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_users"] >= 1
    assert stats["trial_users"] >= 1
