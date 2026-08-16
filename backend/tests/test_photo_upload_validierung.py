"""Was als Profilfoto registriert wird, muss auch wirklich ein Bild sein.

Der Upload laeuft als Presigned PUT direkt in den Objekt-Storage, am Backend
vorbei. Der Client bestimmt dabei den Content-Type mit - aber nur den
*behaupteten*: Die Signatur bindet die Zeichenkette ``image/jpeg``, nicht den
Inhalt. Ohne eine Pruefung nach dem Upload liegt unter dieser Zeichenkette
beliebiger Inhalt in beliebiger Groesse.

``POST /api/profiles/me/photos`` sieht sich das Objekt deshalb an, bevor es
den Datensatz anlegt (``_foto_ist_brauchbar``).

Die uebrige Foto-Suite laeuft gegen einen unerreichbaren Storage
(``testendpunkt.invalid``, siehe backend/.env). Dort faellt die Pruefung
absichtlich durchlaessig aus - andernfalls koennte eine Stoerung beim Storage
den Upload komplett blockieren. Genau deshalb braucht es diese Tests: Sie
setzen die Storage-Antwort selbst und pruefen damit den Pfad, den die anderen
Tests nie erreichen.
"""

import pytest

from tests.conftest import register_user


def _presign(client, headers):
    return client.post(
        "/api/profiles/me/photos/presign",
        headers=headers,
        json={"content_type": "image/jpeg"},
    ).json()


def _register(client, headers, object_key):
    return client.post(
        "/api/profiles/me/photos", headers=headers, json={"object_key": object_key}
    )


def test_zu_grosses_objekt_wird_abgewiesen(client, monkeypatch):
    """Acht Megabyte sind die Grenze; darueber gibt es kein Profilfoto."""
    from app import storage

    monkeypatch.setattr(
        "app.routers.profiles.inspect_uploaded_photo",
        lambda key: {"ok": False, "size": storage.MAX_PHOTO_BYTES + 1, "detected": None},
    )

    headers = register_user(client, "zugross@example.com")
    presign = _presign(client, headers)
    resp = _register(client, headers, presign["object_key"])

    assert resp.status_code == 400
    assert "zu groß" in resp.json()["detail"]
    assert client.get("/api/profiles/me", headers=headers).json()["photos"] == []


def test_kein_bild_wird_abgewiesen(client, monkeypatch):
    """Ein PUT mit Content-Type image/jpeg, in dem gar kein Bild steckt.

    Der Dateianfang wird tatsaechlich gelesen; ``detected`` bleibt dann leer.
    """
    monkeypatch.setattr(
        "app.routers.profiles.inspect_uploaded_photo",
        lambda key: {"ok": False, "size": 1234, "detected": None},
    )

    headers = register_user(client, "keinbild@example.com")
    presign = _presign(client, headers)
    resp = _register(client, headers, presign["object_key"])

    assert resp.status_code == 400
    assert client.get("/api/profiles/me", headers=headers).json()["photos"] == []


def test_echtes_bild_kommt_durch(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.profiles.inspect_uploaded_photo",
        lambda key: {"ok": True, "size": 240_000, "detected": "image/jpeg"},
    )

    headers = register_user(client, "echtesbild@example.com")
    presign = _presign(client, headers)
    resp = _register(client, headers, presign["object_key"])

    assert resp.status_code == 200
    assert len(resp.json()["photos"]) == 1


def test_auch_das_thumbnail_wird_geprueft(client, monkeypatch):
    """Sonst waere der zweite Schluessel das offene Scheunentor."""
    geprueft: list[str] = []

    def urteil(key):
        geprueft.append(key)
        # Vollbild in Ordnung, Thumbnail nicht.
        ok = not key.endswith("-thumb.jpg")
        return {"ok": ok, "size": 1000, "detected": "image/jpeg" if ok else None}

    monkeypatch.setattr("app.routers.profiles.inspect_uploaded_photo", urteil)

    headers = register_user(client, "thumb@example.com")
    user = client.get("/api/profiles/me", headers=headers).json()
    presign = _presign(client, headers)
    resp = client.post(
        "/api/profiles/me/photos",
        headers=headers,
        json={
            "object_key": presign["object_key"],
            "thumb_object_key": f"users/{user['id']}/abc-thumb.jpg",
        },
    )

    assert resp.status_code == 400
    assert len(geprueft) == 2, "Das Thumbnail wurde nicht geprueft"


def test_stoerung_beim_storage_blockiert_den_upload_nicht(client, monkeypatch):
    """Bewusste Entscheidung, hier festgehalten.

    Wenn die Pruefung selbst scheitert - Zeitfehler, Storage gestoert - wird
    durchgelassen und geloggt. Ein Fehler an dieser Stelle wuerde sonst die
    Kernfunktion der App abschalten, und genau das war am 15.08.2026 schon
    einmal der Fall (CSP-Blockade des Uploads).
    """
    def kaputt(key):
        raise RuntimeError("Storage nicht erreichbar")

    monkeypatch.setattr("app.routers.profiles.inspect_uploaded_photo", kaputt)

    headers = register_user(client, "storagestoerung@example.com")
    presign = _presign(client, headers)
    resp = _register(client, headers, presign["object_key"])

    assert resp.status_code == 200
    assert len(resp.json()["photos"]) == 1


@pytest.mark.parametrize(
    "anfang,erwartet",
    [
        (b"\xff\xd8\xff\xe0" + b"\x00" * 12, "image/jpeg"),
        (b"\x89PNG\r\n\x1a\n" + b"\x00" * 8, "image/png"),
        (b"RIFF\x00\x00\x00\x00WEBP", "image/webp"),
        (b"GIF89a" + b"\x00" * 10, None),          # nicht unterstuetzt
        (b"%PDF-1.7" + b"\x00" * 8, None),         # kein Bild
        (b"<?php echo 1; ?>", None),               # ausfuehrbarer Inhalt
    ],
)
def test_dateianfang_entscheidet_nicht_die_endung(anfang, erwartet):
    """Die Endung wird aus dem Content-Type abgeleitet und sagt nichts ueber
    den Inhalt. Massgeblich sind die Magic Bytes."""
    from app.storage import _sniff_image_type

    assert _sniff_image_type(anfang) == erwartet
