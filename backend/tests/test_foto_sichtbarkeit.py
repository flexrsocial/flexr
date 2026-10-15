"""Fotos und Sichtbarkeit in der Suche (Bugfix-Runde 14.10.2026).

Anlass: Ein Konto mit drei freigegebenen Fotos bekam beim Klick aufs ✕
"Mindestens 3 Fotos sind erforderlich" - richtig nach der Regel, aber die
Oberflaeche sah dem ✕ nicht an, dass es gesperrt war. Dazu kam: Wer nach der
Freischaltung noch auf die Fotofreigabe wartete oder eine Ablehnung bekam,
erfuhr nur aus einer kleinen Zeile unter dem Fotoraster, dass ihn niemand
sieht. Der Server liefert dafuer jetzt ``photo_visibility``.
"""

from app.models import Photo, PhotoStatus
from tests.conftest import (
    TestingSessionLocal,
    add_approved_photo,
    create_admin,
    register_user,
)


def _foto(client, headers, status):
    """Foto mit vorgegebenem Status direkt in die Test-DB (kein Objektspeicher)."""
    foto_id = add_approved_photo(client, headers)
    with TestingSessionLocal() as db:
        foto = db.query(Photo).filter(Photo.id == foto_id).one()
        foto.status = status
        db.commit()
    return foto_id


def _me(client, headers):
    return client.get("/api/profiles/me", headers=headers).json()


def test_ohne_fotos_none(client):
    h = register_user(client, "sicht.none@example.com")
    assert _me(client, h)["photo_visibility"] == "none"


def test_genug_gueltige_aber_nicht_alle_frei_pending(client):
    """Drei gueltige, davon erst zwei freigegeben: wartet auf die Pruefung."""
    h = register_user(client, "sicht.pending@example.com")
    _foto(client, h, PhotoStatus.approved)
    _foto(client, h, PhotoStatus.approved)
    _foto(client, h, PhotoStatus.pending)
    _foto(client, h, PhotoStatus.rejected)
    assert _me(client, h)["photo_visibility"] == "pending"


def test_zu_wenige_gueltige_nach_ablehnung_rejected(client):
    """Zwei freigegebene plus ein abgelehntes: Ersatz noetig."""
    h = register_user(client, "sicht.rejected@example.com")
    _foto(client, h, PhotoStatus.approved)
    _foto(client, h, PhotoStatus.approved)
    _foto(client, h, PhotoStatus.rejected)
    assert _me(client, h)["photo_visibility"] == "rejected"


def test_zu_wenige_hochgeladen_none(client):
    """Zwei Fotos, keines abgelehnt (Bestandskonto): zu wenige."""
    h = register_user(client, "sicht.zuwenig@example.com")
    _foto(client, h, PhotoStatus.approved)
    _foto(client, h, PhotoStatus.pending)
    assert _me(client, h)["photo_visibility"] == "none"


def test_erst_drei_freigegebene_sind_visible(client):
    """Wie das Deck (swipes.genug_fotos_condition): MIN_PHOTOS freigegebene.
    Bis zum 15.10.2026 genuegte eines."""
    h = register_user(client, "sicht.visible@example.com")
    _foto(client, h, PhotoStatus.approved)
    _foto(client, h, PhotoStatus.approved)
    offen = _foto(client, h, PhotoStatus.pending)
    assert _me(client, h)["photo_visibility"] == "pending"
    with TestingSessionLocal() as db:
        db.query(Photo).filter(Photo.id == offen).one().status = PhotoStatus.approved
        db.commit()
    assert _me(client, h)["photo_visibility"] == "visible"


def test_sichtbarkeit_steht_auch_in_den_foto_antworten(client):
    """Die Clients zeichnen den Hinweis aus der Antwort von Loeschen und
    Sortieren neu, ohne /me ein zweites Mal zu holen."""
    h = register_user(client, "sicht.antwort@example.com")
    ids = [_foto(client, h, PhotoStatus.approved) for _ in range(4)]
    geloescht = client.delete(f"/api/profiles/me/photos/{ids[0]}", headers=h)
    assert geloescht.status_code == 200
    assert geloescht.json()["photo_visibility"] == "visible"
    sortiert = client.put(
        "/api/profiles/me/photos/order", headers=h, json={"photo_ids": list(reversed(ids[1:]))}
    )
    assert sortiert.json()["photo_visibility"] == "visible"


def test_genau_drei_gueltige_sind_gesperrt_abgelehnte_nicht(client):
    """Der gemeldete Fall: vorher ein Foto abgelehnt, dann ein neues
    hochgeladen und freigegeben. Drei gueltige + ein abgelehntes -> nur das
    abgelehnte darf weg; danach drei gueltige, keines darf weg."""
    h = register_user(client, "sicht.drei@example.com")
    gueltige = [_foto(client, h, PhotoStatus.approved) for _ in range(2)]
    abgelehnt = _foto(client, h, PhotoStatus.rejected)
    gueltige.append(_foto(client, h, PhotoStatus.approved))

    me = _me(client, h)
    loeschbar = {p["id"]: p["deletable"] for p in me["photos"]}
    assert loeschbar[abgelehnt] is True
    assert all(loeschbar[i] is False for i in gueltige)

    # Ein gesperrtes laesst der Server auch nicht weg - mit dem Hinweis, wie
    # es weitergeht.
    resp = client.delete(f"/api/profiles/me/photos/{gueltige[0]}", headers=h)
    assert resp.status_code == 400
    assert "Lade zuerst ein neues Foto hoch" in resp.json()["detail"]

    assert client.delete(f"/api/profiles/me/photos/{abgelehnt}", headers=h).status_code == 200
    me = _me(client, h)
    assert len(me["photos"]) == 3
    assert all(p["deletable"] is False for p in me["photos"])

    # Austauschen: erst ein viertes, dann darf eines der alten weg.
    neu = _foto(client, h, PhotoStatus.pending)
    me = _me(client, h)
    assert all(p["deletable"] is True for p in me["photos"])
    resp = client.delete(f"/api/profiles/me/photos/{gueltige[0]}", headers=h)
    assert resp.status_code == 200
    assert {p["id"] for p in resp.json()["photos"]} == {gueltige[1], gueltige[2], neu}


def test_englische_meldung_beim_gesperrten_loeschen(client):
    h = register_user(client, "sicht.en@example.com")
    ids = [_foto(client, h, PhotoStatus.approved) for _ in range(3)]
    resp = client.delete(
        f"/api/profiles/me/photos/{ids[0]}", headers={**h, "Accept-Language": "en"}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == (
        "At least 3 photos are required. Upload a new photo first, then you can delete this one."
    )


def test_ablehnung_schiebt_das_foto_ans_ende(client):
    """Ein abgelehntes Hauptfoto stand sonst weiter auf Platz 1 - im Raster
    ein leerer Platz mit der Nummer des Hauptfotos."""
    h = register_user(client, "sicht.ende@example.com")
    a, b, c = (_foto(client, h, PhotoStatus.approved) for _ in range(3))
    admin_headers, _ = create_admin(client, email="admin.ende@example.com")

    resp = client.post(
        f"/api/admin/photos/{a}/reject", headers=admin_headers, json={"reason": "no_person"}
    )
    assert resp.status_code == 200
    fotos = _me(client, h)["photos"]
    assert [p["id"] for p in fotos] == [b, c, a]
    assert [p["position"] for p in fotos] == [0, 1, 2]
    assert fotos[-1]["status"] == "rejected"


def test_abgelehntes_foto_bekommt_keine_freigabe_mehr(client):
    h = register_user(client, "sicht.keinefreigabe@example.com")
    foto_id = _foto(client, h, PhotoStatus.approved)
    admin_headers, _ = create_admin(client, email="admin.keinefreigabe@example.com")
    client.post(f"/api/admin/photos/{foto_id}/reject", headers=admin_headers)

    resp = client.post(f"/api/admin/photos/{foto_id}/approve", headers=admin_headers)
    assert resp.status_code == 409
    assert _me(client, h)["photo_visibility"] == "rejected"


def test_admin_tool_bietet_freigabe_nur_fuer_offene_fotos_an():
    """Der Knopf "Freigeben" stand auch an abgelehnten Fotos."""
    from pathlib import Path

    admin_js = (Path(__file__).resolve().parents[2] / "frontend" / "admin.js").read_text(encoding="utf-8")
    assert "p.status === 'pending' ? `<button class=\"btn small\" data-action=\"approve\">" in admin_js
    assert "p.status !== 'approved' ? `<button class=\"btn small\" data-action=\"approve\">" not in admin_js


def test_ablehnungsmail_sagt_wenn_weniger_als_drei_freigegeben_bleiben(client, monkeypatch):
    from app import mailer

    aufrufe = []
    monkeypatch.setattr(
        mailer, "send_photo_rejected", lambda *a, **kw: aufrufe.append(kw) or True
    )
    admin_headers, _ = create_admin(client, email="admin.mailhinweis@example.com")

    h = register_user(client, "sicht.mail@example.com")
    fotos = [_foto(client, h, PhotoStatus.approved) for _ in range(4)]

    # Drei freigegebene bleiben: kein Hinweis.
    client.post(f"/api/admin/photos/{fotos[0]}/reject", headers=admin_headers)
    assert aufrufe[-1]["hidden"] is False
    # Jetzt nur noch zwei: Hinweis.
    client.post(f"/api/admin/photos/{fotos[1]}/reject", headers=admin_headers)
    assert aufrufe[-1]["hidden"] is True


def test_eingehende_likes_und_erinnerung_nur_mit_genug_fotos(client):
    """Deck, "Wer dich geliket hat" und die Like-Erinnerung nutzen dieselbe
    Schwelle (swipes.genug_fotos_condition). Vorher kannte die Liste gar
    keine Fotobedingung - ein Liker ohne freigegebenes Foto erschien mit
    leerem Bild, und die Mail zaehlte ihn mit."""
    from app.email_jobs import _pending_likes_count
    from app.models import User
    from tests.conftest import add_required_photos

    ziel_h = register_user(client, "sicht.ziel@example.com", gender="frau")
    ziel_id = _me(client, ziel_h)["id"]
    genug = register_user(client, "sicht.genug@example.com", gender="mann")
    add_required_photos(client, genug)
    zu_wenig = register_user(client, "sicht.zuwenig.liker@example.com", gender="mann")
    _foto(client, zu_wenig, PhotoStatus.approved)

    for h in (genug, zu_wenig):
        resp = client.post("/api/swipes", headers=h, json={"to_user_id": ziel_id, "action": "like"})
        assert resp.status_code == 200, resp.text

    eingang = client.get("/api/swipes/incoming", headers=ziel_h).json()
    assert eingang["count"] == 1
    with TestingSessionLocal() as db:
        ziel = db.query(User).filter(User.id == ziel_id).one()
        assert _pending_likes_count(db, ziel) == 1
