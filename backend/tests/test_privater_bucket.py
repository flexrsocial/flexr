"""Verifizierungs-Selfies und Ausweisaufnahmen gehoeren in einen eigenen,
nicht oeffentlichen Bucket (S3_PRIVATE_BUCKET_NAME).

Der Foto-Bucket ist ueber seine r2.dev-Adresse als Ganzes oeffentlich - dort
hatten die Pruefaufnahmen bis zum 22.09.2026 nichts verloren, lagen aber dort.
Geprueft wird, dass neue Aufnahmen im privaten Bucket landen und dass Lesen
und Loeschen auch die Altbestaende im Foto-Bucket noch finden.
"""

from unittest.mock import patch

import pytest

from app import cleanup, storage

UID = "dc2a0cef-1bc5-4b3e-bff2-b42718088396"


class FakeS3:
    def __init__(self, objekte=None):
        # {(bucket, key)}
        self.objekte = set(objekte or [])
        self.presigned = []

    def generate_presigned_url(self, op, Params, ExpiresIn):
        self.presigned.append((op, Params["Bucket"], Params["Key"]))
        return f"https://s3.test/{Params['Bucket']}/{Params['Key']}?sig"

    def head_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objekte:
            raise Exception("404")
        return {"ContentLength": 10}

    def delete_object(self, Bucket, Key):
        self.objekte.discard((Bucket, Key))


@pytest.fixture
def privat(monkeypatch):
    monkeypatch.setattr(storage.settings, "s3_bucket_name", "fotos")
    monkeypatch.setattr(storage.settings, "s3_private_bucket_name", "privat")


def test_neue_aufnahmen_landen_im_privaten_bucket(privat):
    fake = FakeS3()
    with patch.object(storage, "get_s3_client", return_value=fake):
        storage.create_presigned_verification_upload(UID, "image/jpeg")
        storage.create_presigned_document_upload("req-1", "image/jpeg")
        storage.create_presigned_upload(UID, "image/jpeg")
    buckets = [b for _, b, _ in fake.presigned]
    assert buckets == ["privat", "privat", "fotos"]


def test_ansicht_faellt_fuer_altbestand_auf_foto_bucket_zurueck(privat):
    alt = f"users/{UID}/verify/alt.jpg"
    neu = f"users/{UID}/verify/neu.jpg"
    fake = FakeS3({("fotos", alt), ("privat", neu)})
    with patch.object(storage, "get_s3_client", return_value=fake):
        assert "/fotos/" in storage.create_presigned_view_url(alt)
        assert "/privat/" in storage.create_presigned_view_url(neu)


def test_loeschen_raeumt_beide_buckets(privat):
    key = "verification-documents/req-1/a.jpg"
    fake = FakeS3({("fotos", key), ("privat", key)})
    with patch.object(storage, "get_s3_client", return_value=fake):
        assert storage.delete_objects_verified([key]) == []
    assert fake.objekte == set()


def test_konto_loeschen_raeumt_pruefaufnahmen_im_privaten_bucket(privat):
    selfie = f"users/{UID}/verify/s.jpg"
    foto = f"users/{UID}/p.jpg"
    fake = FakeS3({("privat", selfie), ("fotos", foto)})
    with patch.object(cleanup, "get_s3_client", return_value=fake):
        cleanup.delete_storage_objects([selfie, foto])
    assert fake.objekte == set()


def test_ohne_privaten_bucket_bleibt_alles_wie_bisher(monkeypatch):
    monkeypatch.setattr(storage.settings, "s3_bucket_name", "fotos")
    monkeypatch.setattr(storage.settings, "s3_private_bucket_name", "")
    fake = FakeS3()
    with patch.object(storage, "get_s3_client", return_value=fake):
        storage.create_presigned_verification_upload(UID, "image/jpeg")
    assert fake.presigned[0][1] == "fotos"
