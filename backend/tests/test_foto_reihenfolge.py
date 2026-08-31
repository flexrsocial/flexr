"""Fotos umsortieren (Drag & Drop im Profil).

Position 0 ist das Hauptfoto - Swipe-Karte, Avatar und Chat-Kopf haengen daran.
Entsprechend streng ist der Endpunkt bei unvollstaendigen oder fremden Listen.
"""

from tests.conftest import add_approved_photo, register_user


def _drei_fotos(client, headers):
    return [
        add_approved_photo(client, headers, url=f"https://cdn.example.test/{i}.jpg")
        for i in range(3)
    ]


def test_reihenfolge_wird_uebernommen(client):
    headers = register_user(client, "sort@example.com")
    a, b, c = _drei_fotos(client, headers)

    resp = client.put(
        "/api/profiles/me/photos/order", headers=headers, json={"photo_ids": [c, a, b]}
    )
    assert resp.status_code == 200, resp.text
    assert [p["id"] for p in resp.json()["photos"]] == [c, a, b]

    # Auch beim naechsten Abruf - die Positionen sind gespeichert, nicht nur
    # in der Antwort umsortiert.
    erneut = client.get("/api/profiles/me", headers=headers).json()
    assert [p["id"] for p in erneut["photos"]] == [c, a, b]


def test_unvollstaendige_liste_wird_abgelehnt(client):
    headers = register_user(client, "teil@example.com")
    a, b, c = _drei_fotos(client, headers)

    # Ohne c bliebe offen, welche Position dieses Foto bekommt.
    resp = client.put(
        "/api/profiles/me/photos/order", headers=headers, json={"photo_ids": [b, a]}
    )
    assert resp.status_code == 400
    assert [p["id"] for p in client.get("/api/profiles/me", headers=headers).json()["photos"]] == [a, b, c]


def test_fremdes_foto_in_der_liste_wird_abgelehnt(client):
    headers = register_user(client, "eigen@example.com")
    fremd_headers = register_user(client, "fremd@example.com")
    a, b, c = _drei_fotos(client, headers)
    fremd = add_approved_photo(client, fremd_headers)

    resp = client.put(
        "/api/profiles/me/photos/order",
        headers=headers,
        json={"photo_ids": [a, b, fremd]},
    )
    assert resp.status_code == 400
    # Das fremde Foto bleibt beim fremden Konto.
    fremd_profil = client.get("/api/profiles/me", headers=fremd_headers).json()
    assert [p["id"] for p in fremd_profil["photos"]] == [fremd]


def test_doppelte_id_wird_abgelehnt(client):
    headers = register_user(client, "doppelt@example.com")
    a, b, c = _drei_fotos(client, headers)

    resp = client.put(
        "/api/profiles/me/photos/order", headers=headers, json={"photo_ids": [a, a, b]}
    )
    assert resp.status_code == 400


def test_hauptfoto_wechselt_mit_der_reihenfolge(client):
    """Das erste Foto ist das, was andere zuerst sehen."""
    headers = register_user(client, "haupt@example.com")
    a, b, c = _drei_fotos(client, headers)

    client.put(
        "/api/profiles/me/photos/order", headers=headers, json={"photo_ids": [b, c, a]}
    )
    profil = client.get("/api/profiles/me", headers=headers).json()
    assert profil["photos"][0]["id"] == b
