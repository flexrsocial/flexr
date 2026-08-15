#!/usr/bin/env python3
"""Prueft, ob die Betreiberangaben ueberall zusammenpassen.

Vor dem 15.08.2026 stand der Rechtstraeger an fuenfzehn Stellen im Repository:
in sieben HTML-Seiten, in der Android-App, in der iOS-App und in zwei
Store-Texten. Sie waren auseinandergelaufen, und keine davon nannte einen
zulaessigen Rechtstraeger - "flexr.social Kleinunternehmen" ist keine
Rechtsform, sondern eine erfundene Firmenbezeichnung.

Dieses Skript ist die Bremse dagegen. Es prueft zweierlei:

  1. Keine der alten Bezeichnungen taucht irgendwo wieder auf.
  2. Jede Seite, die den Rechtstraeger nennen muss, nennt ihn richtig.

Quelle der Wahrheit ist shared/betreiber.json. Fuer den Server macht
backend/tests/test_betreiber.py dasselbe.

    python3 tools/check_betreiber.py

Rueckgabewert 0 = alles sauber, 1 = Befunde (Details auf stdout).
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
QUELLE = REPO / "shared" / "betreiber.json"

# Dateien, die den Rechtstraeger nennen muessen. Alles andere wird nur auf die
# verbotenen Altbezeichnungen geprueft.
MUSS_BETREIBER_NENNEN = [
    "frontend/impressum.html",
    "frontend/agb.html",
    "frontend/datenschutz.html",
    "frontend/widerruf.html",
    "frontend/nutzungsrichtlinien.html",
    "frontend/strafverfolgung.html",
    "android-native/app/src/main/java/flexr/social/app/ui/legal/LegalContent.kt",
    "ios/FLEXR/UI/Legal/LegalContent.swift",
]

# Wo ueberhaupt gesucht wird.
SUCHRAEUME = [
    ("frontend", ("*.html", "*.css", "*.js", "*.json", "*.txt", "*.xml")),
    ("android-native/app/src/main", ("*.kt", "*.xml")),
    ("ios/FLEXR", ("*.swift", "*.plist")),
    ("ios/store", ("*.md",)),
    ("android/store", ("*.md",)),
    ("backend/app", ("*.py",)),
]

# Verzeichnisse, die nichts zur Sache tun.
UEBERSPRINGEN = {"node_modules", "venv", ".venv", "__pycache__", "build", ".git", "out"}


def dateien():
    for unter, muster in SUCHRAEUME:
        wurzel = REPO / unter
        if not wurzel.exists():
            continue
        for m in muster:
            for pfad in wurzel.rglob(m):
                if UEBERSPRINGEN & set(pfad.parts):
                    continue
                yield pfad


def main() -> int:
    if not QUELLE.exists():
        print(f"FEHLER: {QUELLE.relative_to(REPO)} fehlt.")
        return 1

    daten = json.loads(QUELLE.read_text(encoding="utf-8"))
    rt = daten["rechtstraeger"]
    verboten = daten["verbotene_altbezeichnungen"]

    befunde: list[str] = []

    # ---- 1. Altbezeichnungen ------------------------------------------------
    for pfad in dateien():
        text = pfad.read_text(encoding="utf-8", errors="replace")
        rel = pfad.relative_to(REPO)
        for begriff in verboten:
            if begriff in text:
                for nr, zeile in enumerate(text.splitlines(), 1):
                    if begriff in zeile:
                        befunde.append(
                            f"{rel}:{nr}  verbotene Altbezeichnung {begriff!r}\n"
                            f"    {zeile.strip()[:110]}"
                        )

    # ---- 2. Pflichtangaben --------------------------------------------------
    for name in MUSS_BETREIBER_NENNEN:
        pfad = REPO / name
        if not pfad.exists():
            befunde.append(f"{name}  Datei fehlt, sollte aber den Betreiber nennen")
            continue
        text = pfad.read_text(encoding="utf-8", errors="replace")
        for feld, wert in (("Name", rt["name"]), ("Strasse", rt["strasse"]),
                           ("Ort", rt["ort"]), ("E-Mail", rt["email"])):
            if wert not in text:
                befunde.append(f"{name}  {feld} fehlt: {wert!r}")

    # ---- 3. Kleinunternehmerregelung nicht als Rechtsform --------------------
    # Sie ist eine umsatzsteuerliche Einstufung. Steht sie neben dem Wort
    # "Rechtsform", ist wieder etwas durcheinandergeraten.
    muster = re.compile(r"Rechtsform[^\n]{0,80}Kleinunternehmer", re.IGNORECASE)
    for pfad in dateien():
        text = pfad.read_text(encoding="utf-8", errors="replace")
        for treffer in muster.finditer(text):
            nr = text[: treffer.start()].count("\n") + 1
            befunde.append(
                f"{pfad.relative_to(REPO)}:{nr}  Kleinunternehmerregelung als "
                f"Rechtsform bezeichnet - sie ist eine Umsatzsteuersache"
            )

    # ---- Ergebnis -----------------------------------------------------------
    if befunde:
        print(f"{len(befunde)} Befund(e):\n")
        for b in befunde:
            print("  " + b)
        print(
            "\nQuelle der Wahrheit ist shared/betreiber.json. Entweder dort "
            "aendern oder die Fundstellen angleichen."
        )
        return 1

    print(f"Betreiberangaben sind einheitlich: {rt['name']}, {rt['rechtsform']}, "
          f"{rt['strasse']}, {rt['plz']} {rt['ort']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
