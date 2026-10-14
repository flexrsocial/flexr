"""Der S3-Client: einmal je Zugangsdaten angelegt und mit festen Zeitgrenzen.

Bis zum 14.10.2026 entstand bei jedem Storage-Aufruf ein neuer Client mit den
botocore-Vorgaben (60 s je Lesevorgang, bis zu fuenf Versuche) - ein haengendes
R2 hielt eine Anfrage dann laenger fest, als nginx wartet.
"""

from app import storage


def _zugangsdaten(monkeypatch):
    monkeypatch.setattr(storage.settings, "s3_endpoint_url", "https://s3.test")
    monkeypatch.setattr(storage.settings, "s3_access_key_id", "foto-id")
    monkeypatch.setattr(storage.settings, "s3_secret_access_key", "foto-secret")
    monkeypatch.setattr(storage.settings, "s3_private_bucket_name", "privat")
    monkeypatch.setattr(storage.settings, "s3_private_access_key_id", "privat-id")
    monkeypatch.setattr(storage.settings, "s3_private_secret_access_key", "privat-secret")


def test_client_wird_wiederverwendet(monkeypatch):
    _zugangsdaten(monkeypatch)
    assert storage.get_s3_client() is storage.get_s3_client("fotos")
    assert storage.get_s3_client("privat") is storage.get_s3_client("privat")
    assert storage.get_s3_client("privat") is not storage.get_s3_client()


def test_neue_zugangsdaten_ergeben_neuen_client(monkeypatch):
    _zugangsdaten(monkeypatch)
    alt = storage.get_s3_client()
    monkeypatch.setattr(storage.settings, "s3_secret_access_key", "rotiert")
    assert storage.get_s3_client() is not alt


def test_zeitgrenzen_gesetzt(monkeypatch):
    _zugangsdaten(monkeypatch)
    config = storage.get_s3_client().meta.config
    assert config.connect_timeout == 5
    assert config.read_timeout == 10
    assert config.retries["total_max_attempts"] == 2
