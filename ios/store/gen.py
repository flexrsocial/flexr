#!/usr/bin/env python3
"""FLEXR App-Store-Screenshots in den von Apple verlangten Groessen.

Zeichenroutinen, Palette und Schriften kommen aus android/store/gen.py — es ist
dieselbe Marke und derselbe Bildaufbau, nur die Leinwandgroessen unterscheiden
sich. Der Play-Store-Generator wird dabei nicht mit ausgefuehrt; sein
Generierungsteil steht hinter `if __name__ == "__main__"`.

    python3 ios/store/gen.py

Fuer TestFlight sind Screenshots nicht noetig — die verlangt erst die
Einreichung zur Veroeffentlichung.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ANDROID_STORE = os.path.join(ROOT, "android", "store")

# android/store/ steht bewusst nicht unter Versionsverwaltung (siehe
# .gitignore: "Play-Store-Marketing-Assets - generiert, nicht versioniert").
# In einem frischen Klon fehlen deshalb sowohl gen.py als auch die Schriften.
if not os.path.isfile(os.path.join(ANDROID_STORE, "gen.py")):
    sys.exit(
        "android/store/gen.py fehlt.\n"
        "Dieser Ordner ist gitignoriert; die Zeichenroutinen und die Schriften\n"
        "liegen nur lokal vor. Ohne sie lassen sich keine Store-Grafiken\n"
        "erzeugen — fuer TestFlight werden sie aber auch nicht gebraucht."
    )

sys.path.insert(0, ANDROID_STORE)
import gen  # noqa: E402  (Pfad muss vorher stehen)

# Ausgabe in den iOS-Ordner umlenken; die Schriften bleiben, wo sie liegen.
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
gen.OUT = OUT

# App Store Connect, Stand 2026. 6,9" ist Pflicht; 6,5" nimmt Apple weiterhin
# an und deckt aeltere Geraeteklassen ab. iPad 13" ist Pflicht, weil die App
# auf dem iPad laeuft (TARGETED_DEVICE_FAMILY = "1,2").
IPHONE_69 = (1320, 2868)
IPHONE_65 = (1242, 2688)
IPAD_13 = (2064, 2752)


def main():
    for i, (eyebrow, line1, line2, accent, kind) in enumerate(gen.PANELS, 1):
        gen.store_panel(*IPHONE_69, eyebrow, line1, line2, accent, kind,
                        f"iphone-69-{i}.png")
        gen.store_panel(*IPHONE_65, eyebrow, line1, line2, accent, kind,
                        f"iphone-65-{i}.png")

    # iPad: die beiden aussagekraeftigsten Panels reichen, mehr will Apple nicht.
    for i, idx in enumerate([0, 2], 1):
        eyebrow, line1, line2, accent, kind = gen.PANELS[idx]
        gen.store_panel(*IPAD_13, eyebrow, line1, line2, accent, kind,
                        f"ipad-13-{i}.png")

    print("FERTIG —", OUT)


if __name__ == "__main__":
    main()
