"""PLZ-Ortslookup: der Ort kommt jetzt aus dem Backend, nicht mehr aus einem
Fremddienst im Client (siehe app/routers/geo.py)."""

from app.geo import coords_for_plz
from tests.conftest import register_user


def test_lookup_returns_official_city(client):
    resp = client.get("/api/geo/plz/1010")
    assert resp.status_code == 200
    assert resp.json() == {"plz": "1010", "city": "Wien"}


def test_lookup_picks_the_city_not_a_neighbouring_municipality(client):
    """Die alte Häufigkeits-Heuristik über Ortschaftslisten lieferte für diese
    PLZ die Umlandgemeinde statt der Stadt (4020 -> „Leonding", 8010 ->
    „Eggersdorf bei Graz")."""
    for plz, city in [("4020", "Linz"), ("8010", "Graz"),
                      ("9020", "Klagenfurt am Wörthersee"), ("2700", "Wiener Neustadt")]:
        assert client.get(f"/api/geo/plz/{plz}").json()["city"] == city


def test_lookup_is_public(client):
    # Wird schon vor der Registrierung gebraucht - darf keinen Token verlangen.
    assert client.get("/api/geo/plz/8010").status_code == 200


def test_unknown_plz_returns_404(client):
    resp = client.get("/api/geo/plz/9999")
    assert resp.status_code == 404
    assert "nicht gefunden" in resp.json()["detail"]


def test_malformed_plz_is_rejected(client):
    assert client.get("/api/geo/plz/12").status_code == 422
    assert client.get("/api/geo/plz/abcd").status_code == 422


def test_every_known_plz_also_has_coordinates():
    """Sonst käme ein Nutzer durch die Registrierung, fiele aber aus dem Deck."""
    from app.geo import _PLZ_CITIES

    ohne_koordinaten = [plz for plz in _PLZ_CITIES if coords_for_plz(plz) is None]
    assert ohne_koordinaten == []


def test_register_stores_the_official_city(client):
    """Der Client kann den Ort nicht frei wählen - die PLZ bestimmt ihn."""
    headers = register_user(client, "ortsname@example.com", plz="8010",
                            city="Eggersdorf bei Graz")
    assert client.get("/api/profiles/me", headers=headers).json()["city"] == "Graz"


def test_profile_update_stores_the_official_city(client):
    headers = register_user(client, "ortswechsel@example.com")
    resp = client.patch(
        "/api/profiles/me",
        json={"plz": "4020", "city": "Leonding"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Linz"
