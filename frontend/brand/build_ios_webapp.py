"""Erzeugt Icon und Startbilder fuer die Web-App auf dem iPhone-Home-Bildschirm.

Solange FLEXR nicht im App Store steht, kommt es aufs iPhone als Web-App
("Teilen" -> "Zum Home-Bildschirm"). iOS liest dafuer nicht das Manifest,
sondern eigene Angaben im <head>:

* apple-touch-icon: 180x180, deckend. Transparente Ecken fuellt iOS schwarz
  auf - deshalb das App-Store-Icon der iOS-App als Vorlage und nicht das
  freigestellte icon-192.png.
* apple-touch-startup-image: Ohne sie zeigt iOS beim Start einen weissen
  Bildschirm, bis die Seite gezeichnet ist - bei einer dunklen App ein
  greller Blitz. iOS nimmt ein Bild nur, wenn es exakt die Pixelgroesse des
  Geraets hat, daher eines je Bildschirmgroesse.

    python3 frontend/brand/build_ios_webapp.py

Schreibt nach frontend/icons/ und gibt die <link>-Zeilen fuer den <head> aus.
Nach einer Aenderung die Versionsnummer SPLASH_V hochzaehlen (nginx liefert
/icons/ ein Jahr lang als unveraenderlich aus).
"""
from pathlib import Path

from PIL import Image

HIER = Path(__file__).resolve().parent
ICONS = HIER.parent / "icons"
SPLASH = ICONS / "splash"
IOS_ICON = HIER.parent.parent / "ios" / "FLEXR" / "Assets.xcassets" / "AppIcon.appiconset" / "icon-1024.png"
# Vollflaechig in der App-Hintergrundfarbe (#121212), das FX mittig in der
# sicheren Zone - passt nahtlos auf einen Hintergrund derselben Farbe.
MASKABLE = ICONS / "icon-maskable-512.png"
HINTERGRUND = (18, 18, 18)
SPLASH_V = 1

# (Breite, Hoehe) in CSS-Pixeln, Pixeldichte. Hochformat; die Web-App ist im
# Manifest auf portrait festgelegt.
GERAETE = [
    (440, 956, 3),   # iPhone 16 Pro Max, 17 Pro Max
    (420, 912, 3),   # iPhone Air
    (402, 874, 3),   # iPhone 16 Pro, 17, 17 Pro
    (430, 932, 3),   # iPhone 14 Pro Max, 15 Plus, 15 Pro Max, 16 Plus
    (393, 852, 3),   # iPhone 14 Pro, 15, 15 Pro, 16, 16e
    (428, 926, 3),   # iPhone 12 Pro Max, 13 Pro Max, 14 Plus
    (390, 844, 3),   # iPhone 12, 12 Pro, 13, 13 Pro, 14
    (375, 812, 3),   # iPhone X, XS, 11 Pro, 12 mini, 13 mini
    (414, 896, 3),   # iPhone XS Max, 11 Pro Max
    (414, 896, 2),   # iPhone XR, 11
    (414, 736, 3),   # iPhone 8 Plus
    (375, 667, 2),   # iPhone SE (2./3. Gen.), 8
]


def main() -> None:
    SPLASH.mkdir(parents=True, exist_ok=True)

    icon = Image.open(IOS_ICON).convert("RGB").resize((180, 180), Image.LANCZOS)
    icon.save(ICONS / "apple-touch-icon-180.png", optimize=True)

    zeichen = Image.open(MASKABLE).convert("RGB")
    zeilen = []
    for breite, hoehe, dichte in GERAETE:
        w, h = breite * dichte, hoehe * dichte
        bild = Image.new("RGB", (w, h), HINTERGRUND)
        # Das Zeichen auf rund 45 % der Breite - so gross wie das Icon, das
        # man gerade angetippt hat, nur eben mittig.
        seite = int(w * 0.45)
        logo = zeichen.resize((seite, seite), Image.LANCZOS)
        bild.paste(logo, ((w - seite) // 2, (h - seite) // 2))
        name = f"splash-{w}x{h}.png"
        bild.save(SPLASH / name, optimize=True)
        zeilen.append(
            f'<link rel="apple-touch-startup-image" href="/icons/splash/{name}?v={SPLASH_V}" '
            f'media="(device-width: {breite}px) and (device-height: {hoehe}px) and '
            f'(-webkit-device-pixel-ratio: {dichte}) and (orientation: portrait)">'
        )
    print("\n".join(zeilen))


if __name__ == "__main__":
    main()
