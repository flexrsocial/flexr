"""Kopiert die Profilfotos aus dem Objektspeicher in ein lokales Verzeichnis,
damit `scripts/backup.sh` sie mit restic sichern kann.

Ausfuehren (macht backup.sh automatisch):

    cd /flexr/backend && venv/bin/python -m app.photo_export /pfad/zum/ziel

Gesichert wird NUR der Foto-Bucket. Verifizierungs-Selfies und
Ausweisaufnahmen bleiben bewusst draussen - auch Altbestaende, die noch im
Foto-Bucket liegen: Laut Datenschutzerklaerung werden sie unmittelbar nach der
Pruefentscheidung geloescht, eine Kopie mit monatelanger Aufbewahrung im
Backup wuerde diese Zusage brechen. Geht eine Pruefaufnahme verloren, kann die
Person neu verifizieren.

Laedt bei jedem Lauf alles neu herunter. Das Ziel ist das Arbeitsverzeichnis
von backup.sh, das nach jedem Lauf geloescht wird; restic speichert dabei nur,
was sich gegenueber dem letzten Snapshot geaendert hat.
"""

import sys
from pathlib import Path

from .config import settings
from .storage import get_s3_client, is_verification_key


def _safe_relative_path(key: str) -> Path | None:
    """Objektschluessel als relativer Pfad - oder None, wenn er aus dem
    Zielverzeichnis herausfuehren wuerde (`..`, absolute Pfade)."""
    parts = key.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return None
    return Path(*parts)


def export_photos(target: Path) -> tuple[int, int, int]:
    """Laedt alle Fotos nach `target`. Liefert (Dateien, Bytes, uebersprungen)."""
    bucket = settings.s3_bucket_name
    if not bucket:
        raise RuntimeError("S3_BUCKET_NAME ist nicht gesetzt")

    client = get_s3_client(bucket)
    files = total_bytes = skipped = 0
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            rel = _safe_relative_path(key)
            if is_verification_key(key) or rel is None:
                skipped += 1
                continue
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            client.download_file(bucket, key, str(dest))
            files += 1
            total_bytes += obj.get("Size", 0)
    return files, total_bytes, skipped


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Aufruf: python -m app.photo_export <zielverzeichnis>", file=sys.stderr)
        return 2
    target = Path(argv[1])
    target.mkdir(parents=True, exist_ok=True)
    files, total_bytes, skipped = export_photos(target)
    print(f"{files} Fotos, {total_bytes} Bytes, {skipped} uebersprungen (Pruefaufnahmen/ungueltige Schluessel)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
