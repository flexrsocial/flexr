"""Komplette Nutzerreise einer deutschen Nutzerin (seit 03.11.2026).

Von der PLZ-Eingabe über Gym-Suche, Registrierung, Deck, Match und Chat bis
zu Umzug, Kündigung, Rücktritt und Kontolöschung - jeweils mit deutscher PLZ
und deutschen Studios. Was der echte Ablauf über Objekt-Storage und Mail
erledigt (Fotos, Prüfung, Bestätigungslink), setzen die Helfer aus
conftest direkt in die Test-DB, wie in allen anderen Tests.
"""

import pytest

from app.models import Gym, GymStatus, User
from tests.conftest import (
    GYM_WIEN,
    TestingSessionLocal,
    add_required_photos,
    create_admin,
    register_raw,
    register_user,
    register_user_with_photo,
)

GYM_MUENCHEN = "McFit — Landsberger Straße 163, 80687 München"
GYM_MUENCHEN_2 = "Fitness First — Sendlinger Straße 7, 80331 München"
GYM_BERLIN = "McFit — Leipziger Straße 46, 10117 Berlin"
GYM_FREILASSING = "Studio Grenzland — Hauptstraße 1, 83395 Freilassing"
GYM_SALZBURG = "Salzburg Fit — Linzer Gasse 2, 5020 Salzburg"


@pytest.fixture(autouse=True)
def deutsche_gyms():
    db = TestingSessionLocal()
    try:
        for label in (GYM_MUENCHEN, GYM_MUENCHEN_2, GYM_BERLIN, GYM_FREILASSING, GYM_SALZBURG):
            name, rest = label.split(" — ")
            strasse_nr, ort = rest.split(", ")
            strasse, nr = strasse_nr.rsplit(" ", 1)
            plz, stadt = ort.split(" ", 1)
            db.add(Gym(name=name, street=strasse, house_number=nr, plz=plz, city=stadt,
                       status=GymStatus.approved))
        db.commit()
    finally:
        db.close()


def _id(client, headers):
    return client.get("/api/profiles/me", headers=headers).json()["id"]


def test_plz_und_gymsuche_vor_der_registrierung(client):
    assert client.get("/api/geo/plz/80331").json()["city"] == "München"
    # Nahe Studios zuerst: Die Münchner McFit-Filiale vor der Berliner
    treffer = client.get("/api/gyms?q=McFit&near=80331").json()
    labels = [g["label"] for g in treffer]
    assert labels.index(GYM_MUENCHEN) < labels.index(GYM_BERLIN)


def test_registrierung_mit_deutscher_plz_und_falscher_plz(client):
    resp = client.post("/api/auth/register", json={
        "email": "falsch@example.com", "password": "supersecret123", "name": "X",
        "birthdate": "1996-04-12", "plz": "123", "city": "x", "gender": "frau",
        "gym": GYM_MUENCHEN, "consent_sensitive_data": True,
    })
    assert resp.status_code == 422

    headers = register_raw(client, "lena@example.com", name="Lena", gender="frau",
                           plz="80331", city="egal", gym=GYM_MUENCHEN)
    me = client.get("/api/profiles/me", headers=headers).json()
    assert (me["plz"], me["city"], me["gym"]) == ("80331", "München", GYM_MUENCHEN)


def test_deck_match_und_chat_in_muenchen(client):
    lena = register_user_with_photo(client, "lena@example.com", name="Lena", gender="frau",
                                    plz="80331", city="München", gym=GYM_MUENCHEN)
    register_user_with_photo(client, "max@example.com", name="Max", gender="mann",
                             plz="80333", city="München", gym=GYM_MUENCHEN_2)
    register_user_with_photo(client, "ben@example.com", name="Ben", gender="mann",
                             plz="10115", city="Berlin", gym=GYM_BERLIN)

    deck = client.get("/api/swipes/deck", headers=lena).json()
    namen = {p["name"]: p for p in deck}
    assert "Max" in namen and "Ben" not in namen
    assert namen["Max"]["distance_km"] <= 5

    max_headers = client.post("/api/auth/login", json={
        "email": "max@example.com", "password": "supersecret123"}).json()
    max_headers = {"Authorization": f"Bearer {max_headers['access_token']}"}
    max_id = namen["Max"]["id"]
    client.post("/api/swipes", headers=lena, json={"to_user_id": max_id, "action": "like"})
    antwort = client.post("/api/swipes", headers=max_headers,
                          json={"to_user_id": _id(client, lena), "action": "like"})
    assert antwort.json()["matched"] is True

    match_id = client.get("/api/matches", headers=lena).json()[0]["match_id"]
    gesendet = client.post(f"/api/matches/{match_id}/messages", headers=lena,
                           json={"content": "Servus aus München! Training morgen?"})
    assert gesendet.status_code == 201, gesendet.text


def test_ueber_die_grenze_salzburg_freilassing(client):
    """FLEXR rechnet mit Entfernungen zwischen Studios, nicht mit Grenzen."""
    anna = register_user_with_photo(client, "anna@example.com", name="Anna", gender="frau",
                                    plz="83395", city="Freilassing", gym=GYM_FREILASSING)
    register_user_with_photo(client, "lukas@example.com", name="Lukas", gender="mann",
                             plz="5020", city="Salzburg", gym=GYM_SALZBURG)
    deck = client.get("/api/swipes/deck", headers=anna).json()
    lukas = next(p for p in deck if p["name"] == "Lukas")
    assert lukas["distance_km"] < 15


def test_umzug_nach_berlin_wechselt_das_deck(client):
    lena = register_user_with_photo(client, "lena@example.com", name="Lena", gender="frau",
                                    plz="80331", city="München", gym=GYM_MUENCHEN)
    register_user_with_photo(client, "ben@example.com", name="Ben", gender="mann",
                             plz="10115", city="Berlin", gym=GYM_BERLIN)
    assert "Ben" not in [p["name"] for p in client.get("/api/swipes/deck", headers=lena).json()]

    resp = client.patch("/api/profiles/me", headers=lena,
                        json={"plz": "10117", "city": "x", "gym": GYM_BERLIN})
    assert resp.status_code == 200, resp.text
    assert resp.json()["city"] == "Berlin"
    assert "Ben" in [p["name"] for p in client.get("/api/swipes/deck", headers=lena).json()]


def test_zugriffsstatistik_zaehlt_deutschland(client):
    admin_headers, _ = create_admin(client, email="admin.de@example.com")
    lena = register_user(client, "lena@example.com", plz="80331", city="München", gym=GYM_MUENCHEN)
    client.get("/api/profiles/me", headers=lena)
    laender = client.get("/api/admin/access-stats?days=7", headers=admin_headers).json()["countries"]
    assert any(c["country"] == "DE" for c in laender)


def test_checkout_verlangt_erklaerung_zum_sofortigen_beginn(client):
    lena = register_user(client, "lena@example.com", plz="80331", city="München", gym=GYM_MUENCHEN)
    assert client.post("/api/billing/checkout", headers=lena, json={}).status_code == 422


def test_kuendigung_und_ruecktritt_ohne_anmeldung(client, monkeypatch):
    from app import telegram
    monkeypatch.setattr(telegram, "notify_admin_task", lambda text: True)
    register_user(client, "lena@example.com", plz="80331", city="München", gym=GYM_MUENCHEN)

    kuendigung = client.post("/api/cancellation", json={
        "name": "Lena", "email": "lena@example.com", "confirmed": True})
    assert kuendigung.status_code == 201
    ruecktritt = client.post("/api/withdrawal", json={
        "name": "Lena", "email": "lena@example.com", "confirmed": True})
    assert ruecktritt.status_code == 201


def test_konto_loeschen(client):
    lena = register_user(client, "lena@example.com", plz="80331", city="München", gym=GYM_MUENCHEN)
    resp = client.request("DELETE", "/api/profiles/me", headers=lena,
                          json={"password": "supersecret123"})
    assert resp.status_code == 200


def test_oesterreicher_unveraendert(client):
    wien = register_user(client, "wien@example.com", plz="1010", city="Wien", gym=GYM_WIEN)
    assert client.get("/api/profiles/me", headers=wien).json()["city"] == "Wien"
