"""Setzt Cache-Control UND Content-Type auf alle bereits hochgeladenen Fotos.

Neue Uploads bekommen beide Header seit `set_photo_headers()` automatisch.
Zwei Sorten von Bestandsobjekten brauchen den Nachtrag:

* Objekte von vor der Einfuehrung des Cache-Headers — R2 liefert sie ganz ohne
  Cache-Control aus, Clients fallen auf heuristisches Caching zurueck.
* **Alle** Objekte, die zwischendurch durch die damalige Funktion
  ``set_photo_cache_control`` gelaufen sind: Ihr ``MetadataDirective="REPLACE"``
  hat den Content-Type geloescht (Befund vom 10.09.2026, siehe
  ``app/storage.set_photo_headers``). Genau diese Objekte hat der frühere
  Lauf dieses Skripts uebersprungen, weil er nur auf Cache-Control geschaut hat.

Ausfuehren:

    cd /flexr/backend && venv/bin/python scripts/backfill_photo_headers.py --dry-run
    cd /flexr/backend && venv/bin/python scripts/backfill_photo_headers.py

Idempotent: Objekte, die **beide** Header korrekt tragen, werden uebersprungen.
``--dry-run`` zeigt nur an, was zu tun waere, und fasst nichts an.
"""
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Photo  # noqa: E402
from app.storage import (  # noqa: E402
    PHOTO_CACHE_CONTROL,
    content_type_for_key,
    get_s3_client,
    set_photo_headers,
)


def object_key_from_url(url: str) -> str | None:
    """Die DB speichert die fertige oeffentliche URL, nicht den Schluessel."""
    base = settings.s3_public_base_url.rstrip("/")
    if not url.startswith(base):
        return None
    return urlparse(url[len(base):]).path.lstrip("/") or None


def main() -> int:
    trockenlauf = "--dry-run" in sys.argv
    if trockenlauf:
        print("TROCKENLAUF — es wird nichts geschrieben.\n")

    db = SessionLocal()
    client = get_s3_client()
    gesetzt = uebersprungen = fremd = fehlerhaft = 0
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
                    # Seed-Profile verweisen auf Unsplash statt auf unseren
                    # Bucket. Kein Fehler - dort koennen wir nichts setzen.
                    fremd += 1

        for key in dict.fromkeys(keys):  # Reihenfolge halten, Duplikate raus
            try:
                head = client.head_object(Bucket=settings.s3_bucket_name, Key=key)
            except Exception as exc:  # noqa: BLE001
                print(f"  ! nicht lesbar: {key} ({exc})")
                fehlerhaft += 1
                continue

            fehlt = []
            if head.get("CacheControl") != PHOTO_CACHE_CONTROL:
                fehlt.append("Cache-Control")
            # Ein leerer oder generischer Typ zaehlt als fehlend: R2 liefert
            # nach dem REPLACE-Fehler gar keinen, aeltere Objekte teils
            # "binary/octet-stream" oder "application/octet-stream".
            vorhandener_typ = (head.get("ContentType") or "").split(";")[0].strip()
            if not vorhandener_typ or not vorhandener_typ.startswith("image/"):
                fehlt.append("Content-Type")

            if not fehlt:
                uebersprungen += 1
                continue

            ziel = content_type_for_key(key) or "unveraendert"
            print(f"  {'~' if trockenlauf else '+'} {key}  ({', '.join(fehlt)} -> {ziel})")
            if not trockenlauf:
                # Ohne content_type-Argument: Die Endung des Schluessels ist
                # hier die einzige Quelle - die Magic Bytes zu lesen hiesse,
                # jedes Objekt herunterzuladen.
                set_photo_headers(key)
            gesetzt += 1
    finally:
        db.close()

    verb = "waere zu setzen" if trockenlauf else "gesetzt"
    print(
        f"\n{verb}: {gesetzt} | schon korrekt: {uebersprungen} | "
        f"fremde Herkunft (Seed/Unsplash): {fremd} | Fehler: {fehlerhaft}"
    )
    return 1 if fehlerhaft else 0


if __name__ == "__main__":
    raise SystemExit(main())
