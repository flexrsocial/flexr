"""Geo-Helfer für die Umkreissuche.

FLEXR deckt Österreich und Deutschland ab. Österreichische PLZ haben vier,
deutsche fünf Stellen - die beiden Räume überschneiden sich also nicht, und
das Land ergibt sich eindeutig aus der Länge (``country_for_plz``). Beide
Länder liegen deshalb in denselben zwei Tabellen.

Österreich: PLZ-Koordinaten in app/data/plz_coords.json stammen überwiegend aus dem
GeoNames-Postleitzahlen-Datensatz für Österreich
(https://download.geonames.org/export/zip/, Lizenz CC BY 4.0), aggregiert als
Mittelwert je PLZ.

GeoNames verortet allerdings alle Bezirks-PLZ der Großstädte am Stadtzentrum
(z. B. alle Wiener PLZ 1010-1230 auf denselben Punkt), wodurch die
Intra-Stadt-Distanz 0 km wäre. Für diese 116 kollidierenden PLZ wurden die
Koordinaten daher aus den PLZ-Gebietszentren von OpenStreetMap
(Nominatim, © OpenStreetMap-Mitwirkende, Lizenz ODbL) übernommen.

Die Ortsnamen in app/data/plz_cities.json stammen aus dem amtlichen
Postleitzahlenverzeichnis der Österreichischen Post, bezogen über RTR Open Data
(https://data.rtr.at, Lizenz CC BY 4.0). Erzeugt von scripts/build_plz_cities.py.

Deutschland: Koordinaten und Ortsnamen aus dem GeoNames-Datensatz für
Deutschland (CC BY 4.0), Koordinate als Mittelwert je PLZ. Wie in Österreich
legt GeoNames die PLZ der Großstädte teils auf denselben Punkt; für diese PLZ
stammen die Koordinaten aus den PLZ-Gebietszentren von OpenStreetMap
(Nominatim, ODbL). Ortsname bei mehreren Orten je PLZ: der gemeinsame
Stadtname ("Hamburg" statt "Hamburg Altstadt"), sonst der erste Eintrag.
Erzeugt von tools/plz/build_plz_de.py.
"""

import json
import math
from pathlib import Path
from typing import Optional

# Vier Ziffern = Österreich, fünf = Deutschland. Eine Stelle für Schemas und
# Router, damit die Prüfung nicht wieder an zehn Orten auseinanderläuft.
PLZ_PATTERN = r"^\d{4,5}$"

_DATA_DIR = Path(__file__).parent / "data"

with open(_DATA_DIR / "plz_coords.json", encoding="utf-8") as f:
    _PLZ_COORDS: dict[str, list[float]] = json.load(f)

with open(_DATA_DIR / "plz_cities.json", encoding="utf-8") as f:
    _PLZ_CITIES: dict[str, str] = json.load(f)


def coords_for_plz(plz: str) -> Optional[tuple[float, float]]:
    """Liefert (lat, lon) für eine österreichische oder deutsche PLZ oder None."""
    entry = _PLZ_COORDS.get(plz)
    return (entry[0], entry[1]) if entry else None


def city_for_plz(plz: str) -> Optional[str]:
    """Liefert den Ortsnamen zu einer österreichischen oder deutschen PLZ oder None."""
    return _PLZ_CITIES.get((plz or "").strip())


def country_for_plz(plz: Optional[str]) -> Optional[str]:
    """Ländercode (ISO 3166-1) einer PLZ: "AT" bei vier, "DE" bei fünf Ziffern."""
    value = (plz or "").strip()
    if not value.isdigit():
        return None
    return {4: "AT", 5: "DE"}.get(len(value))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Großkreis-Distanz zwischen zwei Punkten in Kilometern."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
