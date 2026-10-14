"""Profilbilder im Storage, zu denen kein Foto (mehr) gehoert.

Bis zum 14.10.2026 raeumte die Kontoloeschung nur Bilder ab, die als Foto
gespeichert waren. In der Produktion lagen danach zehn Bilder von fuenf
laengst geloeschten Konten weiter unter ihrer oeffentlichen Adresse.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app import cleanup
from app.config import settings
from app.models import Photo, User
from tests.conftest import TestingSessionLocal, register_user

JETZT = datetime(2026, 10, 14, 12, 0)


class FakeS3:
    def __init__(self, objekte):
        self.objekte = dict(objekte)  # key -> LastModified (aware)
        self.geloescht = []

    def get_paginator(self, _name):
        return self

    def paginate(self, Bucket, Prefix):
        yield {"Contents": [
            {"Key": k, "LastModified": t} for k, t in self.objekte.items() if k.startswith(Prefix)
        ]}

    def delete_object(self, Bucket, Key):
        self.geloescht.append(Key)


def _alt(tage):
    return (JETZT - timedelta(days=tage)).replace(tzinfo=timezone.utc)


@pytest.fixture
def speicher(monkeypatch):
    monkeypatch.setattr(settings, "s3_bucket_name", "fotos")
    monkeypatch.setattr(settings, "s3_public_base_url", "https://cdn.example/fotos")

    def bauen(objekte):
        fake = FakeS3(objekte)
        monkeypatch.setattr(cleanup, "get_s3_client", lambda bucket=None: fake)
        return fake

    return bauen


def _konto_mit_foto(client, email, key):
    register_user(client, email)
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        db.add(Photo(user_id=user.id, url=f"https://cdn.example/fotos/users/{user.id}/{key}", position=0))
        db.commit()
        return user.id
    finally:
        db.close()


def test_verwaiste_bilder_werden_geloescht(client, speicher):
    uid = _konto_mit_foto(client, "verwaist@example.com", "a.jpg")
    fake = speicher({
        f"users/{uid}/a.jpg": _alt(30),            # gespeichertes Foto
        f"users/{uid}/frisch.jpg": _alt(1),        # Upload laeuft womoeglich noch
        f"users/{uid}/liegengelassen.jpg": _alt(8),
        f"users/{uid}/verify/selfie.jpg": _alt(30),  # Sache der Pruefaufnahmen
        "users/geloeschtes-konto/b.jpg": _alt(0),
    })
    db = TestingSessionLocal()
    try:
        assert cleanup.purge_orphan_photo_objects(db, now=JETZT) == 2
    finally:
        db.close()
    assert sorted(fake.geloescht) == sorted(
        [f"users/{uid}/liegengelassen.jpg", "users/geloeschtes-konto/b.jpg"]
    )


def test_notbremse_loescht_nichts(client, speicher):
    fake = speicher({f"users/weg/{i}.jpg": _alt(0) for i in range(cleanup.ORPHAN_PHOTO_MAX_PER_RUN + 1)})
    db = TestingSessionLocal()
    try:
        assert cleanup.purge_orphan_photo_objects(db, now=JETZT) == 0
    finally:
        db.close()
    assert fake.geloescht == []


def test_kontoloeschung_nimmt_den_ganzen_ordner_mit(client, monkeypatch):
    uid = _konto_mit_foto(client, "ordner@example.com", "a.jpg")
    monkeypatch.setattr(cleanup, "list_object_keys", lambda prefix: [f"{prefix}nie-gespeichert.jpg"])
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == uid).one()
        assert f"users/{uid}/nie-gespeichert.jpg" in cleanup.storage_keys_for_user(db, user)
    finally:
        db.close()
