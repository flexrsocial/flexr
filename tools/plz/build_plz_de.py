"""Deutsche PLZ in backend/app/data/plz_cities.json und plz_coords.json einpflegen.

Aufruf (Quelldateien liegen bewusst nicht im Repo):

    python3 tools/plz/build_plz_de.py DE.txt nominatim.json

* ``DE.txt``: GeoNames-Postleitzahlen für Deutschland
  (https://download.geonames.org/export/zip/DE.zip, CC BY 4.0).
* ``nominatim.json``: {plz: [lat, lon]} für die PLZ, die GeoNames auf
  denselben Punkt legt (Großstädte), abgefragt bei OpenStreetMap/Nominatim
  (ODbL), höchstens eine Anfrage pro Sekunde.

Großkunden- und Postfach-PLZ (Banken, Behörden, Versandhändler - Ortsname
dort ist der Firmenname, etwa "HUK-Coburg") werden weggelassen: GeoNames
führt bei ihnen keine Genauigkeitsangabe (Spalte 12 leer). Behalten wird
eine PLZ, wenn mindestens ein Eintrag eine Genauigkeit hat, OSM ein
PLZ-Gebiet dafür kennt oder alle ihre Namen echte Ortsnamen sind (sonst
fielen z. B. 14467 Potsdam und 68259 Mannheim heraus); den Ortsnamen liefern nur die Einträge mit
Genauigkeit. Übrig bleiben rund 8.200 - so viele Zustell-PLZ hat Deutschland.

Österreichische (vierstellige) Einträge bleiben unangetastet, alle
fünfstelligen werden neu geschrieben - das Skript ist also wiederholbar.
"""

import collections
import csv
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "backend" / "app" / "data"


def stadtname_aus_kreis(kreis: str) -> str:
    """'Kreisfreie Stadt Dresden' -> 'Dresden', 'Berlin, Stadt' -> 'Berlin'."""
    name = kreis.split(",")[0]
    return re.sub(r"^(Kreisfreie Stadt|Stadtkreis|Landeshauptstadt)\s+", "", name).strip()


def ortsname(eintraege: list[list[str]]) -> str:
    namen = list(dict.fromkeys(r[2] for r in eintraege))
    # "Berlin Friedrichshain" -> "Berlin", wenn die kreisfreie Stadt so heißt
    stadt = stadtname_aus_kreis(eintraege[0][7])
    if stadt and all(n == stadt or n.startswith(stadt + " ") for n in namen):
        return stadt
    # "Hamburg", "Hamburg Altstadt", "Hamburg Klostertor" -> "Hamburg"
    for kandidat in sorted(namen, key=len):
        if all(n == kandidat or n.startswith(kandidat + " ") for n in namen):
            return kandidat
    return namen[0]


def main() -> None:
    geonames, nominatim = Path(sys.argv[1]), Path(sys.argv[2])
    je_plz: dict[str, list[list[str]]] = collections.defaultdict(list)
    with geonames.open(encoding="utf-8") as f:
        for zeile in csv.reader(f, delimiter="\t"):
            if zeile[0] == "DE" and re.fullmatch(r"\d{5}", zeile[1]):
                je_plz[zeile[1]].append(zeile)
    osm = {k: v for k, v in json.loads(nominatim.read_text("utf-8")).items() if v}

    cities_pfad, coords_pfad = DATA / "plz_cities.json", DATA / "plz_coords.json"
    cities = {k: v for k, v in json.loads(cities_pfad.read_text("utf-8")).items() if len(k) == 4}
    coords = {k: v for k, v in json.loads(coords_pfad.read_text("utf-8")).items() if len(k) == 4}

    ortsnamen = {r[2] for v in je_plz.values() for r in v if len(r) > 11 and r[11].strip()}
    weggelassen = 0
    for plz in sorted(je_plz):
        eintraege = je_plz[plz]
        genau = [r for r in eintraege if len(r) > 11 and r[11].strip()]
        if not genau and plz not in osm and not all(r[2] in ortsnamen for r in eintraege):
            weggelassen += 1
            continue
        cities[plz] = ortsname(genau or eintraege)
        if plz in osm:
            lat, lon = osm[plz]
        else:
            lat = sum(float(r[9]) for r in eintraege) / len(eintraege)
            lon = sum(float(r[10]) for r in eintraege) / len(eintraege)
        coords[plz] = [round(lat, 5), round(lon, 5)]

    # Format wie bisher: Ortsnamen eine Zeile je PLZ, Koordinaten kompakt.
    zeilen = ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in cities.items())
    cities_pfad.write_text("{\n" + zeilen + "\n}\n", encoding="utf-8")
    coords_pfad.write_text(json.dumps(coords, separators=(",", ":")), encoding="utf-8")
    print(f"{sum(len(k) == 5 for k in cities)} deutsche PLZ, davon {len(osm)} mit OSM-Koordinate, "
          f"{weggelassen} Großkunden-/Postfach-PLZ weggelassen")


if __name__ == "__main__":
    main()
