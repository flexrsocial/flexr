#!/usr/bin/env python3
"""Erzeugt kleinere WebP-Fassungen der Musterprofile fuer srcset.

Die Hero-Karten der Landingpage zeigen die Fotos nur 200-261 px breit, das
Swipe-Deck hoechstens 380 px. Mit nur der 720er-Datei lud jedes Handy die volle
Groesse; Lighthouse zaehlte am 02.11.2026 rund 230 KB Ueberhang und das
Hero-Foto als LCP-Element (3,2 s mobil).

Quelle ist das JPEG (720x960). Qualitaet 80 mit method=6 ist dieselbe
Einstellung, mit der die vorhandenen 720er-WebPs entstanden sind (byte-gleich
nachgerechnet). Ergebnis: demo-<name>-360.webp und demo-<name>-540.webp neben
dem Original.

    python3 frontend/brand/build_demo_sizes.py
"""

from pathlib import Path

from PIL import Image

DEMO = Path(__file__).resolve().parent / "demo"
BREITEN = (360, 540)


def main() -> None:
    for jpg in sorted(DEMO.glob("demo-*.jpg")):
        bild = Image.open(jpg).convert("RGB")
        for breite in BREITEN:
            hoehe = round(bild.height * breite / bild.width)
            ziel = jpg.with_name(f"{jpg.stem}-{breite}.webp")
            bild.resize((breite, hoehe), Image.LANCZOS).save(
                ziel, "WEBP", quality=80, method=6)
            print(f"{ziel.name}: {ziel.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
