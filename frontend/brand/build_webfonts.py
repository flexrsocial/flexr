"""Erzeugt die selbst gehosteten Webfonts unter frontend/fonts/.

Warum überhaupt: Bis zum 15.08.2026 holten index.html und admin.html ihre
Schriften von fonts.googleapis.com. Damit ging bei jedem Seitenaufruf die
IP-Adresse des Besuchers an Google in die USA — ein Empfänger, der in der
Datenschutzerklärung nirgends stand und für den es keine Rechtsgrundlage gab.
Selbst ausliefern beendet den Transfer, statt ihn zu dokumentieren.

Die Quelldateien liegen bereits im Repo (android/store/fonts/, variable TTFs).
Hier werden sie auf den tatsächlich gebrauchten Zeichenvorrat verkleinert und
nach WOFF2 gepackt — aus rund 700 kB TTF werden so wenige Dutzend kB.

Aufruf (einmalig, Ergebnis ist eingecheckt):

    backend/venv/bin/python frontend/brand/build_webfonts.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "android" / "store" / "fonts"
OUT = ROOT / "frontend" / "fonts"

# Deutsch/Österreich plus die Sonderzeichen, die in den Texten wirklich
# vorkommen (Gedankenstrich, typografische Anführungszeichen, Euro, ×).
UNICODES = (
    "U+0020-007E,"      # ASCII
    "U+00A0-00FF,"      # Latin-1 Supplement (Umlaute, ß, ©, °, ×)
    "U+0100-0131,"      # Latin Extended-A (Teil)
    "U+2013-2014,"      # – —
    "U+2018-201E,"      # ‘ ’ „ “ ”
    "U+2022,"           # •
    "U+2026,"           # …
    "U+2030,"
    "U+2039-203A,"
    "U+2044,"
    "U+2052,"
    "U+20AC,"           # €
    "U+2122,"           # ™
    "U+2212"            # −
)

# Quelldatei -> Zieldatei. Alle drei sind variable Fonts; die Gewichtsachse
# bleibt vollständig erhalten, damit CSS weiter frei zwischen 400 und 700
# wählen kann.
FONTS = [
    ("Oswald.ttf", "oswald"),
    ("WorkSans.ttf", "work-sans"),
    ("JetBrainsMono.ttf", "jetbrains-mono"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, slug in FONTS:
        src = SRC / filename
        if not src.exists():
            print(f"FEHLT: {src}", file=sys.stderr)
            return 1
        dest = OUT / f"{slug}.woff2"
        cmd = [
            sys.executable, "-m", "fontTools.subset", str(src),
            f"--unicodes={UNICODES}",
            "--flavor=woff2",
            "--layout-features=kern,liga,calt",
            f"--output-file={dest}",
        ]
        subprocess.run(cmd, check=True)
        print(f"{dest.relative_to(ROOT)}  {dest.stat().st_size // 1024} kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
