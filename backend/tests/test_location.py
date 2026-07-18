from tests.conftest import register_user

# PLZ-Koordinaten (aus dem gebündelten GeoNames-Datensatz):
# 1010/1100 Wien ~ (48.21, 16.37), 8010 Graz ~ (47.08, 15.47) -> ~145 km Distanz


def test_deck_filters_by_plz_distance(client):
    headers_a = register_user(client, "wien.m@example.com", gender="mann", plz="1010", city="Wien")
    register_user(client, "wien.f@example.com", name="Wienerin", gender="frau", plz="1100", city="Wien")
    register_user(client, "graz.f@example.com", name="Grazerin", gender="frau", plz="8010", city="Graz")

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    names = [p["name"] for p in deck]
    assert "Wienerin" in names  # ~0 km, im 20-km-Standardradius
    assert "Grazerin" not in names  # ~145 km, draußen


def test_deck_includes_distance_km(client):
    headers_a = register_user(client, "dist.m@example.com", gender="mann", plz="1010", city="Wien")
    register_user(client, "dist.f@example.com", name="Nahe", gender="frau", plz="1100", city="Wien")

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    assert len(deck) == 1
    assert isinstance(deck[0]["distance_km"], int)
    assert deck[0]["distance_km"] <= 20


def test_larger_radius_includes_faraway_profiles(client):
    headers_a = register_user(client, "radius.m@example.com", gender="mann", plz="1010", city="Wien")
    register_user(client, "radius.f@example.com", name="Grazerin", gender="frau", plz="8010", city="Graz")

    resp = client.patch("/api/profiles/me", headers=headers_a, json={"search_radius_km": 250})
    assert resp.status_code == 200
    assert resp.json()["search_radius_km"] == 250

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    names = [p["name"] for p in deck]
    assert "Grazerin" in names
    graz = next(p for p in deck if p["name"] == "Grazerin")
    assert 100 < graz["distance_km"] < 250


def test_gps_position_overrides_plz(client):
    # Nutzer ist lt. PLZ in Wien, per GPS aber in Graz -> sieht Grazer Profile
    headers_a = register_user(client, "gps.m@example.com", gender="mann", plz="1010", city="Wien")
    register_user(client, "gps.f@example.com", name="Grazerin", gender="frau", plz="8010", city="Graz")

    resp = client.post(
        "/api/profiles/me/location", headers=headers_a, json={"lat": 47.08, "lon": 15.47}
    )
    assert resp.status_code == 200
    assert resp.json()["has_gps_location"] is True

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["name"] == "Grazerin" for p in deck)


def test_clearing_gps_falls_back_to_plz(client):
    headers_a = register_user(client, "clear.m@example.com", gender="mann", plz="1010", city="Wien")
    register_user(client, "clear.f@example.com", name="Wienerin", gender="frau", plz="1100", city="Wien")

    client.post("/api/profiles/me/location", headers=headers_a, json={"lat": 47.08, "lon": 15.47})
    deck_gps = client.get("/api/swipes/deck", headers=headers_a).json()
    assert not any(p["name"] == "Wienerin" for p in deck_gps)  # von Graz aus zu weit

    resp = client.delete("/api/profiles/me/location", headers=headers_a)
    assert resp.status_code == 200
    assert resp.json()["has_gps_location"] is False

    deck_plz = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["name"] == "Wienerin" for p in deck_plz)


def test_radius_validation(client):
    headers = register_user(client, "val.m@example.com")
    assert client.patch("/api/profiles/me", headers=headers, json={"search_radius_km": 1}).status_code == 422
    assert client.patch("/api/profiles/me", headers=headers, json={"search_radius_km": 9999}).status_code == 422


def test_location_validation(client):
    headers = register_user(client, "locval.m@example.com")
    assert client.post("/api/profiles/me/location", headers=headers, json={"lat": 91, "lon": 0}).status_code == 422
    assert client.post("/api/profiles/me/location", headers=headers, json={"lat": 0, "lon": 181}).status_code == 422
