from tests.conftest import register_user, register_user_with_photo


def make_pair(client):
    # Freigegebenes Foto auf beiden Seiten: das Deck zeigt nur Profile mit Foto.
    headers_a = register_user_with_photo(
        client, "safety.a@example.com", name="A", gender="mann"
    )
    headers_b = register_user_with_photo(
        client, "safety.b@example.com", name="B", gender="frau"
    )
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    user_b = client.get("/api/profiles/me", headers=headers_b).json()
    return (headers_a, user_a), (headers_b, user_b)


def test_report_user(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    resp = client.post(
        "/api/reports",
        headers=headers_a,
        json={"reported_user_id": user_b["id"], "reason": "Unangemessenes Verhalten"},
    )
    assert resp.status_code == 201


def test_cannot_report_self(client):
    headers_a = register_user(client, "reportself@example.com")
    user_a = client.get("/api/profiles/me", headers=headers_a).json()
    resp = client.post(
        "/api/reports",
        headers=headers_a,
        json={"reported_user_id": user_a["id"], "reason": "Test"},
    )
    assert resp.status_code == 400


def test_block_removes_user_from_deck(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)

    deck_before = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["id"] == user_b["id"] for p in deck_before)

    block_resp = client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})
    assert block_resp.status_code == 201

    deck_after = client.get("/api/swipes/deck", headers=headers_a).json()
    assert not any(p["id"] == user_b["id"] for p in deck_after)

    # Blockierung wirkt in beide Richtungen
    deck_of_b = client.get("/api/swipes/deck", headers=headers_b).json()
    assert not any(p["id"] == user_a["id"] for p in deck_of_b)


def test_unblock_restores_visibility(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})

    unblock_resp = client.delete(f"/api/blocks/{user_b['id']}", headers=headers_a)
    assert unblock_resp.status_code == 200

    deck_after = client.get("/api/swipes/deck", headers=headers_a).json()
    assert any(p["id"] == user_b["id"] for p in deck_after)


def test_list_blocks(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})
    resp = client.get("/api/blocks", headers=headers_a)
    assert resp.status_code == 200
    assert user_b["id"] in resp.json()


def test_list_blocks_bleibt_ohne_detail_eine_reine_id_liste(client):
    """Android und iOS deklarieren List<String> - die Standardform darf sich
    nicht ändern, solange dort niemand nachgezogen hat."""
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})

    rows = client.get("/api/blocks", headers=headers_a).json()
    assert rows == [user_b["id"]]
    assert all(isinstance(row, str) for row in rows)


def test_list_blocks_mit_detail_zeigt_name_alter_und_foto(client):
    """Für die Verwaltungsliste im Konto: ohne Name und Bild lässt sich nicht
    erkennen, wen man da eigentlich blockiert hat."""
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})

    resp = client.get("/api/blocks?detail=true", headers=headers_a)
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    eintrag = rows[0]
    assert eintrag["user_id"] == user_b["id"]
    assert eintrag["name"] == "B"
    assert eintrag["age"] == user_b["age"]
    assert eintrag["photo_url"]
    assert eintrag["blocked_at"]
    # Nichts darüber hinaus: wer blockiert ist, dessen Profil bleibt zu.
    assert "bio" not in eintrag and "gym" not in eintrag


def test_detail_liste_zeigt_keine_ungeprueften_fotos(client):
    """Gleiche Regel wie im Deck: nur freigegebene Fotos werden ausgeliefert."""
    from app.models import Photo, PhotoStatus

    from tests.conftest import TestingSessionLocal

    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    with TestingSessionLocal() as db:
        for foto in db.query(Photo).filter(Photo.user_id == user_b["id"]).all():
            foto.status = PhotoStatus.pending
        db.commit()

    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})
    eintrag = client.get("/api/blocks?detail=true", headers=headers_a).json()[0]
    assert eintrag["photo_url"] is None
    assert eintrag["name"] == "B"


def test_detail_liste_zeigt_nur_eigene_blockierungen(client):
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})

    # B hat selbst niemanden blockiert und darf As Liste nicht sehen
    assert client.get("/api/blocks?detail=true", headers=headers_b).json() == []


def test_aufheben_holt_match_und_chatverlauf_zurueck(client):
    """Blockieren blendet ein Match nur aus, es loest es nicht auf - genau so
    steht es auch im Hinweistext der Weboberflaeche."""
    (headers_a, user_a), (headers_b, user_b) = make_pair(client)
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": user_b["id"], "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": user_a["id"], "action": "like"})
    match_id = client.get("/api/matches", headers=headers_a).json()[0]["match_id"]
    client.post(
        f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": "Vor dem Blockieren"}
    )

    client.post("/api/blocks", headers=headers_a, json={"user_id": user_b["id"]})
    assert client.get("/api/matches", headers=headers_a).json() == []
    assert client.get(f"/api/matches/{match_id}/messages", headers=headers_a).status_code == 403

    client.delete(f"/api/blocks/{user_b['id']}", headers=headers_a)
    assert len(client.get("/api/matches", headers=headers_a).json()) == 1
    nachrichten = client.get(f"/api/matches/{match_id}/messages", headers=headers_a).json()
    assert [m["content"] for m in nachrichten] == ["Vor dem Blockieren"]
