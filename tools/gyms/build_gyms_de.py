"""Deutsche Fitnessstudios aus OpenStreetMap nach backend/app/data/gyms_seed_de.json.

Aufruf (die Rohdaten liegen bewusst nicht im Repo):

    python3 tools/gyms/build_gyms_de.py staedte.json

``staedte.json`` ist {Stadt: [Overpass-Elemente]} - je Großstadt die
Ergebnisse von ``nwr["leisure"="fitness_centre"]["name"](Rahmen der Stadt)``
mit ``out tags center``. Daten © OpenStreetMap-Mitwirkende, ODbL 1.0.

Übernommen wird nur, was sich als Studio mit Adresse auswählen lässt:
Name, Straße und eine deutsche PLZ, die es in plz_cities.json gibt. Der Ort
kommt - wie bei Nutzer-Vorschlägen - aus der PLZ, nicht aus addr:city, damit
die Schreibweise überall gleich ist. Dadurch fallen auch Treffer weg, die der
Rahmen einer grenznahen Stadt im Ausland erwischt (Konstanz -> Schweiz):
Deren PLZ haben vier Stellen. Private Anlagen (access=private, z. B.
Hotel- oder Firmen-Gyms) bleiben draußen.

Doppelte Einträge (dieselbe Anlage als Knoten und als Fläche, oder in den
Rahmen zweier Nachbarstädte) werden über Name, PLZ und Straße erkannt.
"""

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "backend" / "app" / "data"


def sauber(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def main() -> None:
    roh = json.loads(Path(sys.argv[1]).read_text("utf-8"))
    orte = json.loads((DATA / "plz_cities.json").read_text("utf-8"))

    gesehen: dict[tuple[str, str, str], dict] = {}
    verworfen = {"ohne Adresse": 0, "PLZ unbekannt": 0, "privat": 0}
    for elemente in roh.values():
        for element in elemente:
            tags = element.get("tags", {})
            name = sauber(tags.get("name", ""))
            strasse = sauber(tags.get("addr:street", ""))
            plz = sauber(tags.get("addr:postcode", ""))
            if tags.get("access") in ("private", "no", "customers_only_private"):
                verworfen["privat"] += 1
                continue
            if not name or not strasse or not plz:
                verworfen["ohne Adresse"] += 1
                continue
            if not re.fullmatch(r"\d{5}", plz) or plz not in orte:
                verworfen["PLZ unbekannt"] += 1
                continue
            gym = {
                "name": name[:120],
                "street": strasse[:120],
                "house_number": sauber(tags.get("addr:housenumber", ""))[:20],
                "plz": plz,
                "city": orte[plz],
            }
            schluessel = (name.lower(), plz, strasse.lower())
            # Bei Dubletten gewinnt der Eintrag mit Hausnummer.
            if schluessel not in gesehen or (gym["house_number"] and not gesehen[schluessel]["house_number"]):
                gesehen[schluessel] = gym

    gyms = sorted(gesehen.values(), key=lambda g: (g["plz"], g["name"].lower()))
    ziel = DATA / "gyms_seed_de.json"
    ziel.write_text(json.dumps(gyms, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"{len(gyms)} Studios nach {ziel.name}, verworfen: {verworfen}")


if __name__ == "__main__":
    main()
