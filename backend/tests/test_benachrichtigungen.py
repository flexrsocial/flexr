"""Aktivitaets-Benachrichtigungen: neues Match, wartende Profile, Inaktivitaet.

Geprueft wird jeweils beides - die E-Mail und das App-Zustellfach - sowie die
Schalter, die beide Kanaele einzeln stilllegen.
"""

from datetime import datetime, timedelta

from app.email_jobs import run_activity_notifications
from app.models import PushNotification, User
from tests.conftest import (
    TestingSessionLocal,
    register_user,
    register_user_with_photo,
)

NOW = datetime(2026, 8, 20, 7, 0, 0)  # 09:00 Uhr in Wien (MESZ), ein Donnerstag
# Fuer die woechentliche "offene Likes"-Mail: derselbe Zeitpunkt, aber ein
# Montag (PENDING_LIKES_WEEKDAY) - sonst greift die Wochentagsbedingung nie.
NOW_MONTAG = datetime(2026, 8, 17, 7, 0, 0)


def _user_id(client, headers):
    return client.get("/api/profiles/me", headers=headers).json()["id"]


def _pending(user_id, topic=None):
    db = TestingSessionLocal()
    try:
        query = db.query(PushNotification).filter(PushNotification.user_id == user_id)
        if topic:
            query = query.filter(PushNotification.topic == topic)
        return query.all()
    finally:
        db.close()


def _set_last_active(user_id, moment):
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        user.last_active_at = moment
        db.commit()
    finally:
        db.close()


# --- Neues Match -----------------------------------------------------------

def test_match_benachrichtigt_beide_seiten_per_mail_und_app(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_new_match",
        lambda email, name, match_name, lang="de": mails.append((email, match_name)) or True,
    )

    headers_a = register_user_with_photo(client, "m.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "m.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)

    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": id_a, "action": "like"})

    # Beide Seiten: fuer den zuletzt Swipenden ist das Match genauso neu.
    assert sorted(mails) == [("m.a@example.com", "B"), ("m.b@example.com", "A")]
    assert len(_pending(id_a, "new_match")) == 1
    assert len(_pending(id_b, "new_match")) == 1


def test_erneuter_like_meldet_dasselbe_match_nicht_noch_einmal(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_new_match",
        lambda email, name, match_name, lang="de": mails.append(email) or True,
    )

    headers_a = register_user_with_photo(client, "r.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "r.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)

    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": id_a, "action": "like"})
    # Zweiter Like auf dasselbe Profil: erzeugt kein zweites Match und darf
    # deshalb auch keine zweite Nachricht ausloesen.
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": id_a, "action": "like"})

    assert len(mails) == 2
    assert len(_pending(id_a, "new_match")) == 1


def test_abgeschalteter_kanal_bleibt_stumm(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_new_match",
        lambda email, name, match_name, lang="de": mails.append(email) or True,
    )

    headers_a = register_user_with_photo(client, "s.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "s.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)

    # A schaltet die Match-Mail ab, laesst die App-Benachrichtigung an.
    resp = client.patch(
        "/api/profiles/me/notifications",
        headers=headers_a,
        json={"notify_match_email": False},
    )
    assert resp.status_code == 200
    assert resp.json()["notify_match_email"] is False
    assert resp.json()["notify_match_push"] is True

    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": id_a, "action": "like"})

    assert mails == ["s.b@example.com"]          # nur B bekommt die Mail
    assert len(_pending(id_a, "new_match")) == 1  # A aber weiterhin die App-Meldung


# --- Wartende Profile im Suchradius ---------------------------------------

def test_ab_drei_wartenden_profilen_wird_benachrichtigt(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_queue_waiting",
        lambda email, name, count, lang="de": mails.append((email, count)) or True,
    )
    monkeypatch.setattr(
        "app.notifications.mailer.send_inactivity_reminder",
        lambda email, name, days, lang="de": True,
    )

    headers = register_user_with_photo(client, "q.me@example.com", name="Ich", gender="mann")
    user_id = _user_id(client, headers)
    for i in range(3):
        register_user_with_photo(client, f"q.her{i}@example.com", name=f"P{i}", gender="frau")
    _set_last_active(user_id, NOW - timedelta(hours=1))

    db = TestingSessionLocal()
    try:
        run_activity_notifications(db, NOW)
        # Zweiter Lauf am selben Tag: der Tagesschluessel haelt die Nachricht
        # auf eine pro Tag, sonst kaeme sie bei jedem Joblauf erneut.
        run_activity_notifications(db, NOW + timedelta(hours=2))
    finally:
        db.close()

    assert [m for m in mails if m[0] == "q.me@example.com"] == [("q.me@example.com", 3)]
    assert len(_pending(user_id, "queue_waiting")) == 1


def test_unter_der_schwelle_keine_nachricht(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_queue_waiting",
        lambda email, name, count, lang="de": mails.append(email) or True,
    )
    monkeypatch.setattr(
        "app.notifications.mailer.send_inactivity_reminder",
        lambda email, name, days, lang="de": True,
    )

    headers = register_user_with_photo(client, "u.me@example.com", name="Ich", gender="mann")
    user_id = _user_id(client, headers)
    # Nur zwei wartende Profile - die Schwelle liegt bei drei.
    for i in range(2):
        register_user_with_photo(client, f"u.her{i}@example.com", name=f"P{i}", gender="frau")
    _set_last_active(user_id, NOW - timedelta(hours=1))

    db = TestingSessionLocal()
    try:
        run_activity_notifications(db, NOW)
    finally:
        db.close()

    assert "u.me@example.com" not in mails
    assert _pending(user_id, "queue_waiting") == []


# --- Inaktivitaet ----------------------------------------------------------

def test_erinnerung_nach_sieben_tagen_ohne_nutzung(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_inactivity_reminder",
        lambda email, name, days, lang="de": mails.append((email, days)) or True,
    )
    monkeypatch.setattr(
        "app.notifications.mailer.send_queue_waiting",
        lambda email, name, count, lang="de": True,
    )

    headers = register_user(client, "i.alt@example.com", name="Alt")
    aktiv_headers = register_user(client, "i.neu@example.com", name="Neu")
    alt_id = _user_id(client, headers)
    neu_id = _user_id(client, aktiv_headers)
    _set_last_active(alt_id, NOW - timedelta(days=8))
    _set_last_active(neu_id, NOW - timedelta(days=2))

    db = TestingSessionLocal()
    try:
        run_activity_notifications(db, NOW)
    finally:
        db.close()

    assert mails == [("i.alt@example.com", 8)]
    assert len(_pending(alt_id, "inactivity")) == 1
    assert _pending(neu_id, "inactivity") == []


def test_hintergrundabruf_zaehlt_nicht_als_nutzung(client):
    """Der Poller der Apps darf die Inaktivitaets-Uhr nicht zuruecksetzen."""
    headers = register_user(client, "bg@example.com", name="BG")
    user_id = _user_id(client, headers)
    _set_last_active(user_id, NOW - timedelta(days=8))

    # Hintergrundabgleich der App - markiert durch den Header.
    client.get(
        "/api/notifications/pending",
        headers={**headers, "X-Flexr-Background": "1"},
    )
    db = TestingSessionLocal()
    try:
        unveraendert = db.query(User).filter(User.id == user_id).one().last_active_at
    finally:
        db.close()
    assert unveraendert == NOW - timedelta(days=8)

    # Derselbe Abruf ohne den Header ist Vordergrund-Nutzung.
    client.get("/api/notifications/pending", headers=headers)
    db = TestingSessionLocal()
    try:
        aktualisiert = db.query(User).filter(User.id == user_id).one().last_active_at
    finally:
        db.close()
    assert aktualisiert > NOW


# --- Zustellfach der Apps --------------------------------------------------

def test_zustellfach_liefert_und_quittiert(client, monkeypatch):
    monkeypatch.setattr(
        "app.notifications.mailer.send_new_match",
        lambda email, name, match_name, lang="de": True,
    )

    headers_a = register_user_with_photo(client, "z.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "z.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": id_a, "action": "like"})

    offen = client.get("/api/notifications/pending", headers=headers_a).json()
    assert len(offen) == 1
    assert offen[0]["topic"] == "new_match"
    assert offen[0]["target"] == "matches"

    quittiert = client.post(
        "/api/notifications/delivered",
        headers=headers_a,
        json={"ids": [offen[0]["id"]]},
    )
    assert quittiert.json() == {"delivered": 1}
    # Nach der Quittung bleibt das Fach leer - sonst meldete die App dasselbe
    # Match bei jedem Durchlauf erneut.
    assert client.get("/api/notifications/pending", headers=headers_a).json() == []


# --- Offene Likes ohne Match -----------------------------------------------

def test_offener_like_wird_woechentlich_gemeldet(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_pending_likes",
        lambda email, name, count, lang="de": mails.append((email, count)) or True,
    )

    headers_a = register_user_with_photo(client, "p.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "p.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)
    # A liked B - B hat noch gar nicht reagiert, also offen.
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})

    db = TestingSessionLocal()
    try:
        run_activity_notifications(db, NOW_MONTAG)
        # Zweiter Lauf in derselben Woche: der Wochenschluessel haelt die
        # Nachricht auf eine pro Woche.
        run_activity_notifications(db, NOW_MONTAG + timedelta(hours=2))
    finally:
        db.close()

    assert mails == [("p.b@example.com", 1)]
    assert len(_pending(id_b, "pending_likes")) == 1
    assert _pending(id_a, "pending_likes") == []


def test_erwiderter_like_zaehlt_nicht_als_offen(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_pending_likes",
        lambda email, name, count, lang="de": mails.append(email) or True,
    )
    monkeypatch.setattr(
        "app.notifications.mailer.send_new_match",
        lambda email, name, match_name, lang="de": True,
    )

    headers_a = register_user_with_photo(client, "e.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "e.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)
    # Beide Seiten liken sich - daraus wird ein Match, kein offener Like.
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": id_a, "action": "like"})

    db = TestingSessionLocal()
    try:
        run_activity_notifications(db, NOW_MONTAG)
    finally:
        db.close()

    assert mails == []


def test_bereits_gepasstes_profil_zaehlt_nicht_als_offen(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_pending_likes",
        lambda email, name, count, lang="de": mails.append(email) or True,
    )

    headers_a = register_user_with_photo(client, "g.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "g.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})
    # B hat A schon bewertet (Absage) - keine offene Entscheidung mehr.
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": id_a, "action": "pass"})

    db = TestingSessionLocal()
    try:
        run_activity_notifications(db, NOW_MONTAG)
    finally:
        db.close()

    assert mails == []


def test_pending_likes_laeuft_nur_montags(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_pending_likes",
        lambda email, name, count, lang="de": mails.append(email) or True,
    )
    monkeypatch.setattr(
        "app.notifications.mailer.send_queue_waiting", lambda email, name, count, lang="de": True,
    )
    monkeypatch.setattr(
        "app.notifications.mailer.send_inactivity_reminder", lambda email, name, days, lang="de": True,
    )

    headers_a = register_user_with_photo(client, "d.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "d.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})
    _set_last_active(id_b, NOW - timedelta(hours=1))

    db = TestingSessionLocal()
    try:
        # NOW ist ein Donnerstag - die Wochentagsbedingung greift nicht.
        run_activity_notifications(db, NOW)
    finally:
        db.close()

    assert mails == []
    assert _pending(id_b, "pending_likes") == []


def test_abgeschalteter_kanal_pending_likes_bleibt_stumm(client, monkeypatch):
    mails = []
    monkeypatch.setattr(
        "app.notifications.mailer.send_pending_likes",
        lambda email, name, count, lang="de": mails.append(email) or True,
    )

    headers_a = register_user_with_photo(client, "x.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "x.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)

    resp = client.patch(
        "/api/profiles/me/notifications",
        headers=headers_b,
        json={"notify_pending_likes_email": False},
    )
    assert resp.status_code == 200
    assert resp.json()["notify_pending_likes_email"] is False
    assert resp.json()["notify_pending_likes_push"] is True

    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})

    db = TestingSessionLocal()
    try:
        run_activity_notifications(db, NOW_MONTAG)
    finally:
        db.close()

    assert mails == []
    # Die App-Benachrichtigung bleibt an und landet weiterhin im Zustellfach.
    assert len(_pending(id_b, "pending_likes")) == 1


def test_fremde_benachrichtigung_laesst_sich_nicht_quittieren(client, monkeypatch):
    monkeypatch.setattr(
        "app.notifications.mailer.send_new_match",
        lambda email, name, match_name, lang="de": True,
    )

    headers_a = register_user_with_photo(client, "f.a@example.com", name="A", gender="mann")
    headers_b = register_user_with_photo(client, "f.b@example.com", name="B", gender="frau")
    id_a, id_b = _user_id(client, headers_a), _user_id(client, headers_b)
    client.post("/api/swipes", headers=headers_a, json={"to_user_id": id_b, "action": "like"})
    client.post("/api/swipes", headers=headers_b, json={"to_user_id": id_a, "action": "like"})

    fremde_id = client.get("/api/notifications/pending", headers=headers_a).json()[0]["id"]
    resp = client.post(
        "/api/notifications/delivered", headers=headers_b, json={"ids": [fremde_id]}
    )
    assert resp.json() == {"delivered": 0}
    assert len(client.get("/api/notifications/pending", headers=headers_a).json()) == 1
