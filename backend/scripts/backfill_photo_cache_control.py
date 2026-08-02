"""Setzt Cache-Control auf alle bereits hochgeladenen Foto-Objekte.

Neue Uploads bekommen den Header seit `set_photo_cache_control()` automatisch.
Bestandsobjekte wurden ohne hochgeladen — R2 liefert sie deshalb ganz ohne
Cache-Control aus, und Clients fallen auf heuristisches Caching zurück.

Einmalig ausfuehren:

    cd /flexr/backend && venv/bin/python scripts/backfill_photo_cache_control.py

Idempotent: Objekte, die den Header schon tragen, werden uebersprungen.
"""
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Photo  # noqa: E402
from app.storage import PHOTO_CACHE_CONTROL, get_s3_client, set_photo_cache_control  # noqa: E402


def object_key_from_url(url: str) -> str | None:
    """Die DB speichert die fertige oeffentliche URL, nicht den Schluessel."""
    base = settings.s3_public_base_url.rstrip("/")
    if not url.startswith(base):
        return None
    return urlparse(url[len(base):]).path.lstrip("/") or None


def main() -> int:
    db = SessionLocal()
    client = get_s3_client()
    gesetzt = uebersprungen = fehlerhaft = 0
    try:
        keys: list[str] = []
        for photo in db.query(Photo).all():
            for url in (photo.url, photo.thumb_url):
                if not url:
                    continue
                key = object_key_from_url(url)
                if key:
                    keys.append(key)
                else:
                    print(f"  ! URL passt nicht zur Basis-URL: {url}")
                    fehlerhaft += 1

        for key in dict.fromkeys(keys):  # Reihenfolge halten, Duplikate raus
            try:
                head = client.head_object(Bucket=settings.s3_bucket_name, Key=key)
            except Exception as exc:  # noqa: BLE001
                print(f"  ! nicht lesbar: {key} ({exc})")
                fehlerhaft += 1
                continue

            if head.get("CacheControl") == PHOTO_CACHE_CONTROL:
                uebersprungen += 1
                continue

            set_photo_cache_control(key)
            gesetzt += 1
            print(f"  + {key}")
    finally:
        db.close()

    print(f"\ngesetzt: {gesetzt} | schon korrekt: {uebersprungen} | Fehler: {fehlerhaft}")
    return 1 if fehlerhaft else 0


if __name__ == "__main__":
    raise SystemExit(main())
