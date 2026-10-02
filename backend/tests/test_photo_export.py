"""Foto-Export fuers Backup (app.photo_export).

Wichtigster Punkt: Pruefaufnahmen (Selfies, Ausweise) duerfen NIE im Backup
landen - auch nicht die Altbestaende, die noch im Foto-Bucket liegen.
"""

from unittest.mock import patch

from app import photo_export

UID = "dc2a0cef-1bc5-4b3e-bff2-b42718088396"


class FakePaginator:
    def __init__(self, pages):
        self.pages = pages

    def paginate(self, Bucket):
        return iter(self.pages)


class FakeS3:
    def __init__(self, pages):
        self.pages = pages
        self.downloads = []

    def get_paginator(self, name):
        assert name == "list_objects_v2"
        return FakePaginator(self.pages)

    def download_file(self, bucket, key, dest):
        self.downloads.append((bucket, key))
        with open(dest, "wb") as fh:
            fh.write(b"x" * 3)


def _obj(key, size=3):
    return {"Key": key, "Size": size}


def test_exportiert_fotos_aber_keine_pruefaufnahmen(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_export.settings, "s3_bucket_name", "fotos")
    fake = FakeS3([
        {"Contents": [
            _obj(f"users/{UID}/a.jpg"),
            _obj(f"users/{UID}/verify/selfie.jpg"),
        ]},
        {"Contents": [
            _obj("verification-documents/req-1/ausweis.jpg"),
            _obj(f"users/{UID}/thumbs/b.jpg"),
            _obj("ordner/"),
        ]},
    ])
    with patch.object(photo_export, "get_s3_client", return_value=fake):
        files, total, skipped = photo_export.export_photos(tmp_path)

    assert (files, total, skipped) == (2, 6, 2)
    assert [k for _, k in fake.downloads] == [f"users/{UID}/a.jpg", f"users/{UID}/thumbs/b.jpg"]
    assert (tmp_path / "users" / UID / "a.jpg").exists()
    assert not any("verify" in str(p) or "verification" in str(p) for p in tmp_path.rglob("*"))


def test_schluessel_ausserhalb_des_ziels_werden_uebersprungen(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_export.settings, "s3_bucket_name", "fotos")
    fake = FakeS3([{"Contents": [_obj("../boese.jpg"), _obj("/abs.jpg"), _obj("a//b.jpg")]}])
    with patch.object(photo_export, "get_s3_client", return_value=fake):
        assert photo_export.export_photos(tmp_path / "ziel") == (0, 0, 3)
    assert fake.downloads == []


def test_leerer_bucket(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_export.settings, "s3_bucket_name", "fotos")
    with patch.object(photo_export, "get_s3_client", return_value=FakeS3([{}])):
        assert photo_export.export_photos(tmp_path) == (0, 0, 0)
