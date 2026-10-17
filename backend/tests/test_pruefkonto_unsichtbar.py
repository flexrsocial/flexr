"""Prüfkonto für Google und Apple ist für andere unsichtbar (17.10.2026).

Anlass: Mit dem Produktionsstart in Google Play wischen echte Nutzer durch
dieselben Decks wie das Prüfkonto appreview@flexr.social. Sie sollen weder auf
ein Konto wischen, hinter dem Prüfer sitzen, noch deren Likes als Interesse
gemeldet bekommen. Das Prüfkonto selbst muss die App dagegen vollständig
bedienen können - Deck, Like, Match.
"""

from app.email_jobs import _pending_likes_count
from app.models import Swipe, User
from tests.conftest import TestingSessionLocal, register_user_with_photo


def _id(client, headers) -> str:
    return client.get("/api/profiles/me", headers=headers).json()["id"]


def _deck_ids(client, headers) -> list[str]:
    resp = client.get("/api/swipes/deck", headers=headers)
    assert resp.status_code == 200, resp.text
    return [p["id"] for p in resp.json()]


def _unsichtbar(user_id: str) -> None:
    with TestingSessionLocal() as db:
        db.query(User).filter(User.id == user_id).one().hidden_from_others = True
        db.commit()


def _pruefkonto_und_nutzer(client):
    pruefer = register_user_with_photo(
        client, "appreview@example.com", name="Prüferin", gender="frau", interest="mann"
    )
    nutzer = register_user_with_photo(client, "echt@example.com", name="Echter Nutzer")
    pruefer_id, nutzer_id = _id(client, pruefer), _id(client, nutzer)
    return pruefer, nutzer, pruefer_id, nutzer_id


def test_ohne_markierung_sehen_sich_beide(client):
    """Gegenprobe: Die beiden Konten passen zueinander und stehen im selben Gym."""
    pruefer, nutzer, pruefer_id, nutzer_id = _pruefkonto_und_nutzer(client)
    assert pruefer_id in _deck_ids(client, nutzer)
    assert nutzer_id in _deck_ids(client, pruefer)


def test_pruefkonto_fehlt_im_fremden_deck_sieht_aber_selbst_eines(client):
    pruefer, nutzer, pruefer_id, nutzer_id = _pruefkonto_und_nutzer(client)
    _unsichtbar(pruefer_id)

    assert pruefer_id not in _deck_ids(client, nutzer)
    assert nutzer_id in _deck_ids(client, pruefer)


def test_like_des_pruefkontos_wird_nirgends_gemeldet(client):
    pruefer, nutzer, pruefer_id, nutzer_id = _pruefkonto_und_nutzer(client)
    _unsichtbar(pruefer_id)

    resp = client.post(
        "/api/swipes", json={"to_user_id": nutzer_id, "action": "like"}, headers=pruefer
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["matched"] is False

    # Weder vorn im Deck (Liker-Vorrang) noch unter "Wer dich geliket hat"
    # noch in der Like-Erinnerung.
    assert pruefer_id not in _deck_ids(client, nutzer)
    incoming = client.get("/api/swipes/incoming", headers=nutzer).json()
    assert incoming["count"] == 0
    assert incoming["profiles"] == []
    with TestingSessionLocal() as db:
        nutzer_row = db.query(User).filter(User.id == nutzer_id).one()
        assert _pending_likes_count(db, nutzer_row) == 0


def test_kein_like_auf_das_pruefkonto(client):
    """Auch per handgebautem Request nicht - sonst entstuende ueber einen
    Gegen-Like des Pruefers ein Match mit einem echten Nutzer."""
    pruefer, nutzer, pruefer_id, nutzer_id = _pruefkonto_und_nutzer(client)
    _unsichtbar(pruefer_id)

    resp = client.post(
        "/api/swipes", json={"to_user_id": pruefer_id, "action": "like"}, headers=nutzer
    )
    assert resp.status_code == 404


def test_pruefkonto_kann_weiter_matchen(client):
    """Der Ablauf, den die Pruefer testen: Like auf ein Profil, das sie schon
    geliked hat (Testprofile in der Produktion), ergibt ein Match."""
    pruefer, nutzer, pruefer_id, nutzer_id = _pruefkonto_und_nutzer(client)
    _unsichtbar(pruefer_id)
    with TestingSessionLocal() as db:
        db.add(Swipe(from_user_id=nutzer_id, to_user_id=pruefer_id, action="like"))
        db.commit()

    resp = client.post(
        "/api/swipes", json={"to_user_id": nutzer_id, "action": "like"}, headers=pruefer
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["matched"] is True
    matches = client.get("/api/matches", headers=pruefer).json()
    assert len(matches) == 1
