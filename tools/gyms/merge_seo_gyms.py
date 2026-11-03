"""Deutsche Seed-Studios in tools/seo/gyms.json uebernehmen.

gyms.json ist die Datengrundlage der SEO-Seiten und kommt normalerweise per
``build_seo_pages.py --refresh`` von der Live-API. Bis die deutschen Studios
auf dem Server sind, liefert die API sie nicht - dieses Skript traegt sie aus
backend/app/data/gyms_seed_de.json nach (Form wie die API-Antwort, id per
uuid5 stabil). Oesterreichische Eintraege bleiben, wie sie sind.
"""

import json
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEO = REPO / "tools" / "seo" / "gyms.json"


def main() -> None:
    bestand = [g for g in json.loads(SEO.read_text("utf-8")) if len(g["plz"]) == 4]
    de = json.loads((REPO / "backend" / "app" / "data" / "gyms_seed_de.json").read_text("utf-8"))
    for g in de:
        adresse = f'{g["street"]} {g["house_number"]}'.strip()
        bestand.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f'flexr-gym:{g["name"]}|{g["plz"]}|{g["street"]}')),
            **g,
            "label": f'{g["name"]} — {adresse}, {g["plz"]} {g["city"]}',
        })
    bestand.sort(key=lambda g: (g["plz"], g["name"].lower()))
    SEO.write_text(json.dumps(bestand, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(bestand)} Studios in gyms.json, davon {len(de)} deutsch")


if __name__ == "__main__":
    main()
