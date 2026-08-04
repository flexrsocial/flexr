from tests.conftest import (
    GYM_GRAZ,
    GYM_OHNE_ADRESSE,
    GYM_WIEN,
    GYM_WIEN_2,
    register_user,
    register_user_with_photo,
)

# Die Umkreissuche geht von der Adresse des eingetragenen Gyms aus, nicht vom
# Wohnort. PLZ-Koordinaten aus dem gebündelten GeoNames-Datensatz:
# 1010/1100 Wien ~ (48.21, 16.37), 8010 Graz ~ (47.08, 15.47) -> ~145 km.


def test_deck_filters_by_gym_distance(client):
    headers_a = register_user(client, "wien.m@example.com", gender="mann", gym=GYM_WIEN)
    register_user_with_photo(client, "wien.f@example.com", name="Wienerin",
                             gender="frau", gym=GYM_WIEN_2)
    register_user_with_photo(client, "graz.f@example.com", name="Grazerin",
                             gender="frau", gym=GYM_GRAZ)

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    names = [p["name"] for p in deck]
    assert "Wienerin" in names   # ~4 km, im 20-km-Standardradius
    assert "Grazerin" not in names  # ~145 km, draußen


def test_home_address_does_not_influence_the_deck(client):
    """Der Wohnort ist für die Suche unerheblich: Wer in Wien wohnt, aber in
    Graz trainiert, gehört ins Grazer Deck - und nicht ins Wiener."""
    # Beide wohnen in Wien, trainieren aber in Graz
    headers_a = register_user(client, "pendler.m@example.com", gender="mann",
                              plz="1100", city="Wien", gym=GYM_GRAZ)
    register_user_with_photo(client, "pendler.f@example.com", name="Grazerin",
                             gender="frau", plz="1100", city="Wien", gym=GYM_GRAZ)
    # Wohnt und trainiert in Wien
    register_user_with_photo(client, "wienerin@example.com", name="Wienerin",
                             gender="frau", plz="1100", city="Wien", gym=GYM_WIEN)

    names = [p["name"] for p in client.get("/api/swipes/deck", headers=headers_a).json()]
    assert "Grazerin" in names
    assert "Wienerin" not in names


def test_deck_includes_distance_km(client):
    headers_a = register_user(client, "dist.m@example.com", gender="mann", gym=GYM_WIEN)
    register_user_with_photo(client, "dist.f@example.com", name="Nahe",
                             gender="frau", gym=GYM_WIEN_2)

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    assert len(deck) == 1
    assert isinstance(deck[0]["distance_km"], int)
    assert deck[0]["distance_km"] <= 20


def test_larger_radius_includes_faraway_gyms(client):
    headers_a = register_user(client, "radius.m@example.com", gender="mann", gym=GYM_WIEN)
    register_user_with_photo(client, "radius.f@example.com", name="Grazerin",
                             gender="frau", gym=GYM_GRAZ)

    resp = client.patch("/api/profiles/me", headers=headers_a, json={"search_radius_km": 250})
    assert resp.status_code == 200
    assert resp.json()["search_radius_km"] == 250

    deck = client.get("/api/swipes/deck", headers=headers_a).json()
    graz = next(p for p in deck if p["name"] == "Grazerin")
    assert 100 < graz["distance_km"] < 250


def test_gym_without_address_is_excluded_from_search(client):
    """Bestandsprofile mit blankem Gym-Namen haben keinen eindeutigen Punkt:
    sie sehen kein Deck und tauchen in fremden nicht auf."""
    legacy = register_user(client, "legacy.m@example.com", gender="mann",
                           gym=GYM_OHNE_ADRESSE)
    register_user_with_photo(client, "legacy.f@example.com", name="Wienerin",
                             gender="frau", gym=GYM_WIEN)
    assert client.get("/api/swipes/deck", headers=legacy).json() == []

    # ... und umgekehrt: das Bestandsprofil erscheint bei niemandem
    other = register_user(client, "sieht.f@example.com", gender="frau", gym=GYM_WIEN)
    register_user_with_photo(client, "legacy2.m@example.com", name="Bestandsmann",
                             gender="mann", gym=GYM_OHNE_ADRESSE)
    names = [p["name"] for p in client.get("/api/swipes/deck", headers=other).json()]
    assert "Bestandsmann" not in names


def test_choosing_a_gym_with_address_restores_search(client):
    """Sobald das Gym neu aus der Liste gewählt wird, ist das Profil wieder dabei."""
    legacy = register_user(client, "back.m@example.com", gender="mann",
                           gym=GYM_OHNE_ADRESSE)
    register_user_with_photo(client, "back.f@example.com", name="Wienerin",
                             gender="frau", gym=GYM_WIEN)
    assert client.get("/api/swipes/deck", headers=legacy).json() == []

    assert client.patch("/api/profiles/me", headers=legacy,
                        json={"gym": GYM_WIEN_2}).status_code == 200
    names = [p["name"] for p in client.get("/api/swipes/deck", headers=legacy).json()]
    assert "Wienerin" in names


def test_radius_validation(client):
    headers = register_user(client, "val.m@example.com")
    assert client.patch("/api/profiles/me", headers=headers, json={"search_radius_km": 1}).status_code == 422
    assert client.patch("/api/profiles/me", headers=headers, json={"search_radius_km": 9999}).status_code == 422

