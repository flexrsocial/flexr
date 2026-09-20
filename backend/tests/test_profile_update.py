from datetime import datetime, timedelta

from tests.conftest import GYM_GRAZ, GYM_WIEN, GYM_WIEN_2, TestingSessionLocal, register_user


def test_update_gym_and_bio(client):
    headers = register_user(client, "update@example.com")
    resp = client.patch(
        "/api/profiles/me",
        headers=headers,
        json={"gym": "Clever Fit", "bio": "Neue Bio 🏋️💪🔥"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["gym"] == "Clever Fit"
    assert body["bio"] == "Neue Bio 🏋️💪🔥"  # Emojis müssen erhalten bleiben


def test_update_gym_stores_full_label_with_address(client):
    """Bugfix: Beim Speichern muss der volle Anzeigename mit Adresse erhalten
    bleiben, nicht nur der Ketten-Name (z. B. mehrere 'McFit'-Standorte)."""
    headers = register_user(client, "gymlabel@example.com")
    label = "Testgym mit Adresse — Teststraße 12, 1010 Wien"
    resp = client.patch("/api/profiles/me", headers=headers, json={"gym": label})
    assert resp.status_code == 200, resp.text
    assert resp.json()["gym"] == label
    # und bleibt beim erneuten Laden erhalten
    assert client.get("/api/profiles/me", headers=headers).json()["gym"] == label


def test_update_gym_wrong_label_rejected(client):
    headers = register_user(client, "gymlabelbad@example.com")
    resp = client.patch(
        "/api/profiles/me", headers=headers,
        json={"gym": "Testgym mit Adresse — Falschgasse 9, 9999 Nirgendwo"},
    )
    assert resp.status_code == 400


def test_update_plz_and_city_together(client):
    headers = register_user(client, "move@example.com")
    resp = client.patch(
        "/api/profiles/me",
        headers=headers,
        json={"plz": "8010", "city": "Graz"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["plz"] == "8010"
    assert body["city"] == "Graz"


def test_update_plz_without_city_rejected(client):
    headers = register_user(client, "moveonly@example.com")
    resp = client.patch("/api/profiles/me", headers=headers, json={"plz": "8010"})
    assert resp.status_code == 400


def test_update_invalid_gym_rejected(client):
    headers = register_user(client, "fakegym@example.com")
    resp = client.patch(
        "/api/profiles/me", headers=headers, json={"gym": "Garagen-Gym 3000"}
    )
    assert resp.status_code == 400


def test_update_invalid_plz_rejected(client):
    headers = register_user(client, "badplz@example.com")
    resp = client.patch(
        "/api/profiles/me", headers=headers, json={"plz": "12", "city": "Wien"}
    )
    assert resp.status_code == 422


def test_empty_bio_clears_bio(client):
    headers = register_user(client, "clearbio@example.com", bio="Alte Bio")
    resp = client.patch("/api/profiles/me", headers=headers, json={"bio": ""})
    assert resp.status_code == 200
    assert resp.json()["bio"] is None


def test_untouched_fields_stay(client):
    headers = register_user(client, "stay@example.com")
    before = client.get("/api/profiles/me", headers=headers).json()
    resp = client.patch("/api/profiles/me", headers=headers, json={"bio": "Nur die Bio neu"})
    after = resp.json()
    assert after["bio"] == "Nur die Bio neu"
    assert after["gym"] == before["gym"]
    assert after["city"] == before["city"]
    assert after["plz"] == before["plz"]


# ---------------------------------------------------------------------------
# Karenz zwischen zwei Gym-Wechseln (Umgehungsschutz fuer den per Gym-Adresse
# berechneten FLEXR-Premium-Suchumkreis, siehe models.GYM_CHANGE_COOLDOWN_DAYS)
# ---------------------------------------------------------------------------

def _set_gym_changed_at(user_id, when):
    from app.models import User

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.gym_changed_at = when
        db.commit()
    finally:
        db.close()


def test_gym_change_cooldown_blocks_second_change_within_three_months(client):
    """Ohne Karenz liesse sich der Suchumkreis von FLEXR Premium umgehen,
    indem das Gym (der Mittelpunkt der Umkreissuche) beliebig oft gewechselt
    wird."""
    headers = register_user(client, "gymkarenz@example.com", gym=GYM_WIEN)
    first = client.patch("/api/profiles/me", headers=headers, json={"gym": GYM_WIEN_2})
    assert first.status_code == 200, first.text

    second = client.patch("/api/profiles/me", headers=headers, json={"gym": GYM_GRAZ})
    assert second.status_code == 400
    assert "drei Monate" in second.json()["detail"]

    # Das eingetragene Gym bleibt beim zurueckgewiesenen Versuch unveraendert
    assert client.get("/api/profiles/me", headers=headers).json()["gym"] == GYM_WIEN_2


def test_gym_change_cooldown_allows_change_after_three_months(client):
    headers = register_user(client, "gymkarenzok@example.com", gym=GYM_WIEN)
    assert client.patch(
        "/api/profiles/me", headers=headers, json={"gym": GYM_WIEN_2}
    ).status_code == 200

    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    _set_gym_changed_at(user_id, datetime.utcnow() - timedelta(days=91))

    resp = client.patch("/api/profiles/me", headers=headers, json={"gym": GYM_GRAZ})
    assert resp.status_code == 200, resp.text
    assert resp.json()["gym"] == GYM_GRAZ


def test_gym_change_cooldown_ignores_patch_with_unchanged_value(client):
    """Ein Patch mit dem bereits eingetragenen Gym ist kein Wechsel und darf
    die Karenz nicht auslösen - sonst würde jedes erneute Speichern des
    unveränderten Profils die Sperre neu starten."""
    headers = register_user(client, "gymgleich@example.com", gym=GYM_WIEN)
    assert client.patch(
        "/api/profiles/me", headers=headers, json={"gym": GYM_WIEN}
    ).status_code == 200
    assert client.patch(
        "/api/profiles/me", headers=headers, json={"gym": GYM_WIEN_2}
    ).status_code == 200


def test_gym_change_locked_until_reported_in_profile(client):
    """Web/Android/iOS zeigen die Karenz an und sperren das Feld - dafuer
    muss die eigene Profilansicht das Sperrdatum mitliefern."""
    headers = register_user(client, "gymlocked@example.com", gym=GYM_WIEN)
    before = client.get("/api/profiles/me", headers=headers).json()
    assert before["gym_change_locked_until"] is None

    assert client.patch(
        "/api/profiles/me", headers=headers, json={"gym": GYM_WIEN_2}
    ).status_code == 200

    after = client.get("/api/profiles/me", headers=headers).json()
    assert after["gym_change_locked_until"] is not None
