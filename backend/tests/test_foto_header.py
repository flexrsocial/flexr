"""Regressionstest: set_photo_headers darf den Content-Type nie verlieren."""
from unittest.mock import MagicMock, patch

from app import storage


def _copy_params(erkannt=None, key="users/u/p.jpg", head_type=None):
    client = MagicMock()
    client.head_object.return_value = {"ContentType": head_type} if head_type else {}
    with patch.object(storage, "get_s3_client", return_value=client):
        storage.set_photo_headers(key, erkannt)
    return client.copy_object.call_args.kwargs


def test_erkannter_typ_gewinnt():
    p = _copy_params(erkannt="image/png")
    assert p["ContentType"] == "image/png"
    assert p["CacheControl"] == storage.PHOTO_CACHE_CONTROL


def test_ohne_befund_zaehlt_die_endung():
    assert _copy_params(key="users/u/p.webp")["ContentType"] == "image/webp"


def test_unbekannte_endung_bewahrt_den_vorhandenen_typ():
    p = _copy_params(key="users/u/p.bin", head_type="image/jpeg")
    assert p["ContentType"] == "image/jpeg"


def test_replace_ohne_content_type_kommt_nicht_mehr_vor():
    """Der eigentliche Fehler vom 10.09.2026."""
    p = _copy_params()
    assert p["MetadataDirective"] == "REPLACE"
    assert "ContentType" in p, "REPLACE ohne ContentType loescht den Header"
