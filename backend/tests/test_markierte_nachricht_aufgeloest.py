"""Automatisch markierte Nachrichten überstehen das Auflösen des Matches.

Bis zum 14.10.2026 gingen sie mit dem Chat verloren: Wer einen Scam-Link
schickte und gleich danach auflöste - oder die Empfängerin, die die Person
los sein wollte -, nahm das Beweisstück mit, bevor die Moderation es gesehen
hatte. Jetzt bleiben sie ohne Chat stehen, bis sie geprüft sind, höchstens
FLAGGED_MESSAGE_UNMATCHED_DAYS nach dem Senden.
"""

from datetime import timedelta

from app import cleanup, premium, retention
from app.models import Message, User
from app.timeutil import utcnow
from tests.conftest import TestingSessionLocal, create_admin, register_user_with_photo
from tests.test_messages import make_match

SCAM = "Schick mir Geld per Western Union, dann besuch ich dich."


def _nachrichten():
    db = TestingSessionLocal()
    try:
        return [(m.content, m.match_id, m.is_flagged) for m in db.query(Message).all()]
    finally:
        db.close()


def _aufgeloest_mit_scam(client, aufloesen_durch="b"):
    match_id, (headers_a, user_a), (headers_b, user_b) = make_match(client)
    client.post(f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": "Hey!"})
    client.post(f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": SCAM})
    client.post(f"/api/matches/{match_id}/messages", headers=headers_b, json={"content": "Nein danke."})
    headers = headers_b if aufloesen_durch == "b" else headers_a
    assert client.delete(f"/api/matches/{match_id}", headers=headers).status_code == 200
    return match_id, (headers_a, user_a), (headers_b, user_b)


def test_markierte_nachricht_bleibt_ohne_chat_stehen(client):
    match_id, (headers_a, _), (headers_b, _) = _aufgeloest_mit_scam(client)

    # Nur die markierte bleibt, losgelöst vom Chat.
    assert _nachrichten() == [(SCAM, None, True)]
    # Für beide Seiten ist der Chat weg.
    assert client.get("/api/matches", headers=headers_a).json() == []
    assert client.get("/api/matches", headers=headers_b).json() == []
    assert client.get(f"/api/matches/{match_id}/messages", headers=headers_a).status_code == 404

    admin_headers, _ = create_admin(client)
    markiert = client.get("/api/admin/flagged-messages", headers=admin_headers).json()
    assert len(markiert) == 1
    assert markiert[0]["content"] == SCAM
    assert markiert[0]["chat_dissolved"] is True
    stats = client.get("/api/admin/stats", headers=admin_headers).json()
    assert stats["flagged_messages"] == 1


def test_auch_wenn_der_absender_aufloest(client):
    _aufgeloest_mit_scam(client, aufloesen_durch="a")
    assert _nachrichten() == [(SCAM, None, True)]


def test_ok_im_adminportal_loescht_die_abgeloeste_nachricht(client):
    _aufgeloest_mit_scam(client)
    admin_headers, _ = create_admin(client)
    nachricht = client.get("/api/admin/flagged-messages", headers=admin_headers).json()[0]

    resp = client.post(
        f"/api/admin/flagged-messages/{nachricht['id']}/clear", headers=admin_headers
    )

    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
    assert _nachrichten() == []


def test_ok_bei_bestehendem_chat_hebt_nur_die_markierung_auf(client):
    match_id, (headers_a, _), _ = make_match(client)
    client.post(f"/api/matches/{match_id}/messages", headers=headers_a, json={"content": SCAM})
    admin_headers, _ = create_admin(client)
    nachricht = client.get("/api/admin/flagged-messages", headers=admin_headers).json()[0]
    assert nachricht["chat_dissolved"] is False

    resp = client.post(
        f"/api/admin/flagged-messages/{nachricht['id']}/clear", headers=admin_headers
    )

    assert resp.json()["deleted"] is False
    assert _nachrichten() == [(SCAM, match_id, False)]


def _zweites_match(client):
    """Ein weiteres Paar - make_match legt immer dieselben Adressen an."""
    headers_c = register_user_with_photo(client, "zweit.c@example.com", name="C", gender="mann")
    headers_d = register_user_with_photo(client, "zweit.d@example.com", name="D", gender="frau")
    id_c = client.get("/api/profiles/me", headers=headers_c).json()["id"]
    id_d = client.get("/api/profiles/me", headers=headers_d).json()["id"]
    client.post("/api/swipes", headers=headers_c, json={"to_user_id": id_d, "action": "like"})
    client.post("/api/swipes", headers=headers_d, json={"to_user_id": id_c, "action": "like"})
    return client.get("/api/matches", headers=headers_c).json()[0]["match_id"], headers_c


def test_ungepruefte_abgeloeste_nachricht_verschwindet_nach_der_frist(client):
    _aufgeloest_mit_scam(client)
    match_id, headers_c = _zweites_match(client)
    client.post(f"/api/matches/{match_id}/messages", headers=headers_c, json={"content": SCAM})

    frist = timedelta(days=retention.FLAGGED_MESSAGE_UNMATCHED_DAYS)
    db = TestingSessionLocal()
    try:
        # Eine abgelöste, die älter ist als die Frist ...
        alt = db.query(Message).filter(Message.match_id.is_(None)).one()
        alt.created_at = utcnow() - frist - timedelta(hours=1)
        # ... und eine alte, markierte im noch bestehenden Chat: die bleibt.
        im_chat = db.query(Message).filter(Message.match_id == match_id).one()
        im_chat.created_at = utcnow() - frist - timedelta(days=10)
        db.commit()

        assert cleanup.purge_unmatched_flagged_messages(db) == 1
        assert [(m.match_id, m.content) for m in db.query(Message)] == [(match_id, SCAM)]
    finally:
        db.close()


def test_junge_abgeloeste_nachricht_bleibt_bis_zur_frist(client):
    _aufgeloest_mit_scam(client)
    db = TestingSessionLocal()
    try:
        assert cleanup.purge_unmatched_flagged_messages(db) == 0
    finally:
        db.close()
    assert len(_nachrichten()) == 1


def test_abgeloeste_nachricht_belegt_keinen_chat_platz(client):
    _, (_, user_a), _ = _aufgeloest_mit_scam(client)
    db = TestingSessionLocal()
    try:
        absender = db.query(User).filter(User.id == user_a["id"]).one()
        assert premium.open_chats_used(db, absender) == 0
    finally:
        db.close()
