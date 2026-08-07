"""Erzeugt app/data/plz_cities.json aus dem amtlichen PLZ-Verzeichnis.

Quelle: RTR Open Data (https://data.rtr.at/api/v1/tables/plz.json) — das ist
das Postleitzahlenverzeichnis der Österreichischen Post, veröffentlicht unter
CC BY 4.0. Jede adressierbare PLZ hat dort genau EINEN amtlichen Ortsnamen;
genau deshalb wird sie hier verwendet und nicht mehr eine Häufigkeits-Heuristik
über Ortschaftslisten (die z. B. für 4020 „Leonding" statt „Linz" lieferte).

Aufruf (Netzzugang nötig, nur bei Datenaktualisierung):

    python backend/scripts/build_plz_cities.py
"""

import json
import urllib.request
from pathlib import Path

SOURCE_URL = "https://data.rtr.at/api/v1/tables/plz.json"
TARGET = Path(__file__).resolve().parent.parent / "app" / "data" / "plz_cities.json"


def fetch() -> list[dict]:
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "FLEXR/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["data"]


def build(rows: list[dict]) -> dict[str, str]:
    cities: dict[str, str] = {}
    for row in rows:
        # gueltigbis gesetzt = die PLZ wurde aufgelassen; adressierbar = "Nein"
        # sind reine Postfach-/Verwaltungs-PLZ, unter denen niemand wohnt.
        if row.get("gueltigbis") or row.get("adressierbar") != "Ja":
            continue
        plz = str(row["plz"]).zfill(4)
        ort = (row.get("ort") or "").strip()
        if ort:
            cities[plz] = ort
    return dict(sorted(cities.items()))


def main() -> None:
    cities = build(fetch())
    if len(cities) < 2000:
        raise SystemExit(f"Nur {len(cities)} PLZ erhalten — Quelle prüfen, Datei nicht überschrieben.")
    TARGET.write_text(json.dumps(cities, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"{len(cities)} PLZ nach {TARGET} geschrieben.")


if __name__ == "__main__":
    main()
