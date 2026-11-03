"""Deutschland: fünfstellige PLZ neben den vierstelligen österreichischen.

Das Land ergibt sich aus der Länge (app/geo.py, ``country_for_plz``). Alte
App-Fassungen schicken weiterhin nur vier Stellen - die müssen unverändert
durchgehen.
"""

from app.geo import _PLZ_CITIES, coords_for_plz, country_for_plz, haversine_km
from tests.conftest import register_user


def test_country_follows_the_length():
    assert country_for_plz("1010") == "AT"
    assert country_for_plz("10115") == "DE"
    assert country_for_plz("01067") == "DE"
    for kaputt in ("", None, "123", "123456", "1o10"):
        assert country_for_plz(kaputt) is None


def test_lookup_german_cities(client):
    for plz, city in [("10115", "Berlin"), ("80331", "München"), ("20095", "Hamburg"),
                      ("50667", "Köln"), ("01067", "Dresden")]:
        resp = client.get(f"/api/geo/plz/{plz}")
        assert resp.status_code == 200, plz
        assert resp.json() == {"plz": plz, "city": city}


def test_lookup_rejects_six_digits(client):
    assert client.get("/api/geo/plz/123456").status_code == 422


def test_unknown_german_plz_returns_404(client):
    assert client.get("/api/geo/plz/00000").status_code == 404


def test_both_countries_are_loaded():
    laender = {country_for_plz(plz) for plz in _PLZ_CITIES}
    assert laender == {"AT", "DE"}
    assert sum(1 for plz in _PLZ_CITIES if len(plz) == 5) > 8000


def test_big_city_districts_are_not_on_one_point():
    """GeoNames legt Großstadt-PLZ teils auf denselben Punkt; ohne die
    OSM-Korrektur wäre die Entfernung innerhalb von Leipzig oder Frankfurt 0 km."""
    for a, b in [("04103", "04357"), ("60311", "60439"), ("80331", "81825")]:
        assert haversine_km(*coords_for_plz(a), *coords_for_plz(b)) > 2, (a, b)


def test_cross_border_distance_is_short():
    """Salzburg - Freilassing: wenige Kilometer, über die Grenze hinweg."""
    km = haversine_km(*coords_for_plz("5020"), *coords_for_plz("83395"))
    assert km < 15


def test_register_with_german_plz(client):
    headers = register_user(client, "berlin@example.com", plz="10115", city="Irgendwo")
    me = client.get("/api/profiles/me", headers=headers).json()
    assert me["plz"] == "10115"
    assert me["city"] == "Berlin"


def test_profile_update_to_german_plz(client):
    headers = register_user(client, "umzug@example.com")
    resp = client.patch("/api/profiles/me", json={"plz": "80331", "city": "x"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["city"] == "München"


def test_austrian_registration_is_unchanged(client):
    headers = register_user(client, "wien@example.com", plz="1010", city="Wien")
    assert client.get("/api/profiles/me", headers=headers).json()["city"] == "Wien"


def test_gym_suggestion_with_german_plz(client):
    headers = register_user(client, "gymvorschlag@example.com")
    resp = client.post(
        "/api/gyms/suggest",
        json={"name": "Testgym Mitte", "street": "Invalidenstraße", "house_number": "1",
              "plz": "10115"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["city"] == "Berlin"
    assert resp.json()["label"].endswith("10115 Berlin")
