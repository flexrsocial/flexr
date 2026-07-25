"""Geo-Helfer für die Umkreissuche.

PLZ-Koordinaten in app/data/plz_coords.json stammen überwiegend aus dem
GeoNames-Postleitzahlen-Datensatz für Österreich
(https://download.geonames.org/export/zip/, Lizenz CC BY 4.0), aggregiert als
Mittelwert je PLZ.

GeoNames verortet allerdings alle Bezirks-PLZ der Großstädte am Stadtzentrum
(z. B. alle Wiener PLZ 1010-1230 auf denselben Punkt), wodurch die
Intra-Stadt-Distanz 0 km wäre. Für diese 116 kollidierenden PLZ wurden die
Koordinaten daher aus den PLZ-Gebietszentren von OpenStreetMap
(Nominatim, © OpenStreetMap-Mitwirkende, Lizenz ODbL) übernommen.
"""

import json
import math
from pathlib import Path
from typing import Optional

_DATA_FILE = Path(__file__).parent / "data" / "plz_coords.json"

with open(_DATA_FILE, encoding="utf-8") as f:
    _PLZ_COORDS: dict[str, list[float]] = json.load(f)


def coords_for_plz(plz: str) -> Optional[tuple[float, float]]:
    """Liefert (lat, lon) für eine österreichische PLZ oder None."""
    entry = _PLZ_COORDS.get(plz)
    return (entry[0], entry[1]) if entry else None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Großkreis-Distanz zwischen zwei Punkten in Kilometern."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
