from tests.conftest import DEFAULT_USER, create_admin, register_user


def test_gym_list_and_search(client):
    resp = client.get("/api/gyms")
    assert resp.status_code == 200
    gyms = resp.json()
    # Reine Legacy-Namen ohne Adresse tauchen nicht in der Auswahl auf ...
    assert not any(g["name"] == "McFit" for g in gyms)
    # ... nur Einträge mit vollständiger Adresse.
    assert any(g["name"] == "Testgym mit Adresse" for g in gyms)

    resp = client.get("/api/gyms?q=Testgym")
    assert resp.status_code == 200
    hits = resp.json()
    assert len(hits) == 1
    assert hits[0]["label"] == "Testgym mit Adresse — Teststraße 12, 1010 Wien"

    # PLZ-Suche
    assert client.get("/api/gyms?q=1010").json()[0]["name"] == "Testgym mit Adresse"


def test_register_with_unknown_gym_rejected(client):
    resp = client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "fakegym2@example.com", "name": "Fake",
              "gym": "Erfundenes Gym 3000"},
    )
    assert resp.status_code == 400


def test_suggest_gym_and_register_with_it(client):
    resp = client.post(
        "/api/gyms/suggest",
        json={"name": "Eisenschmiede Graz", "street": "Herrengasse",
              "house_number": "7", "plz": "8010", "city": "Graz"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["label"] == "Eisenschmiede Graz — Herrengasse 7, 8010 Graz"

    # Vorschlag ist noch nicht in der öffentlichen Liste (pending)
    assert client.get("/api/gyms?q=Eisenschmiede").json() == []

    # Aber der Vorschlagende kann sich sofort damit registrieren
    resp = client.post(
        "/api/auth/register",
        json={**DEFAULT_USER, "email": "eisen@example.com", "name": "Eisen",
              "gym": "Eisenschmiede Graz"},
    )
    assert resp.status_code == 200


def test_duplicate_suggestion_returns_existing(client):
    payload = {"name": "Doppelgym", "street": "Weg", "house_number": "1", "plz": "4020"}
    first = client.post("/api/gyms/suggest", json=payload).json()
    second = client.post("/api/gyms/suggest", json=payload)
    assert second.status_code == 201
    assert second.json()["id"] == first["id"]


def test_admin_approves_suggestion(client):
    client.post(
        "/api/gyms/suggest",
        json={"name": "Freigabegym", "street": "Hauptplatz", "house_number": "3",
              "plz": "5020", "city": "Salzburg"},
    )
    admin_headers, _ = create_admin(client, email="gymadmin@example.com")

    pending = client.get("/api/admin/gyms?status=pending", headers=admin_headers).json()
    assert any(g["name"] == "Freigabegym" for g in pending)
    gym_id = next(g["id"] for g in pending if g["name"] == "Freigabegym")

    resp = client.post(f"/api/admin/gyms/{gym_id}/approve", headers=admin_headers)
    assert resp.status_code == 200

    # Jetzt öffentlich in der Liste
    assert any(g["name"] == "Freigabegym" for g in client.get("/api/gyms?q=Freigabe").json())


def test_admin_rejects_suggestion(client):
    client.post(
        "/api/gyms/suggest",
        json={"name": "Spamgym", "street": "Nirgendwo", "house_number": "0", "plz": "9020"},
    )
    admin_headers, _ = create_admin(client, email="gymadmin2@example.com")
    pending = client.get("/api/admin/gyms?status=pending", headers=admin_headers).json()
    gym_id = next(g["id"] for g in pending if g["name"] == "Spamgym")

    resp = client.post(f"/api/admin/gyms/{gym_id}/reject", headers=admin_headers)
    assert resp.status_code == 200
    assert not any(g["name"] == "Spamgym" for g in client.get("/api/gyms?q=Spamgym").json())

    # Abgelehntes Gym kann nicht erneut vorgeschlagen werden
    resp = client.post(
        "/api/gyms/suggest",
        json={"name": "Spamgym", "street": "Nirgendwo", "house_number": "0", "plz": "9020"},
    )
    assert resp.status_code == 400


def test_profile_update_validates_against_gym_table(client):
    headers = register_user(client, "gymupdate@example.com")
    assert client.patch(
        "/api/profiles/me", headers=headers, json={"gym": "Testgym mit Adresse"}
    ).status_code == 200
    assert client.patch(
        "/api/profiles/me", headers=headers, json={"gym": "Gibtsnicht"}
    ).status_code == 400
