"""Erzeugt die iOS-Icon-Assets aus der FX-Vorlage.

Gegenstueck zu frontend/brand/build_icons.py, aber mit den Regeln von iOS:

* Das App-Icon ist ein **volles Quadrat ohne Alpha** (1024x1024). iOS legt die
  Squircle-Maske selbst darueber — ein Icon mit eigenen runden Ecken bekaeme
  dunkle Schlitze an den Kanten. Die abgerundeten Ecken der Vorlage werden
  deshalb aus den Nachbarpixeln aufgefuellt statt schwarz stehen zu lassen.
* Das Splash-Symbol ist freigestellt (RGBA) und wird auf der Startbildschirm-
  Flaeche zentriert. iOS skaliert es nicht wie Android auf eine feste
  Kreisflaeche, deshalb entfaellt der TILE_ON_SPLASH-Faktor.

Aufruf:  python3 ios/tools/build_icons_ios.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'frontend', 'brand', 'app-icon-fx-1254.png')
ASSETS = os.path.join(ROOT, 'ios', 'FLEXR', 'Assets.xcassets')

TILE = (47, 47, 1206, 1208)          # Kachel ohne den schwarzen Rand
TILE_BG = np.array([40.0, 34.0, 31.0])
ICON_PX = 1024
SPLASH_PX = 512


def load_tile():
    im = Image.open(SRC).convert('RGB').crop(TILE)
    return np.asarray(im).astype(np.float32)


def straight_alpha(rgb):
    """Artwork vom Kachelhintergrund loesen (identisch zur Android-Fassung)."""
    maxc = rgb.max(axis=2)
    bg_max = TILE_BG.max()
    a = np.clip((maxc - bg_max) / (255.0 - bg_max), 0.0, 1.0)
    a3 = a[..., None]
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.where(a3 > 1e-4, (rgb - (1.0 - a3) * TILE_BG) / np.maximum(a3, 1e-4), 0.0)
    return Image.fromarray(np.dstack([np.clip(c, 0, 255), a * 255.0]).astype(np.uint8), 'RGBA')


def fill_rounded_corners(rgb):
    """Die runden Ecken der Vorlage aus den Nachbarpixeln auffuellen.

    Innerhalb der Kachel ist alles heller als der schwarze Rand; die Ecken
    lassen sich deshalb ueber die Helligkeit erkennen. Sie werden schrittweise
    von innen nach aussen mit dem Mittel der bereits gefuellten Nachbarn
    ueberschrieben — die Kachel hat dort ohnehin nur ihre dunkle Vignette,
    der Uebergang ist nicht wahrnehmbar.
    """
    inside = rgb.max(axis=2) > 10.0
    out = rgb.copy()
    out[~inside] = 0.0
    known = inside.astype(np.float32)

    while not known.all():
        padded_v = np.pad(out, ((1, 1), (1, 1), (0, 0)))
        padded_k = np.pad(known, ((1, 1), (1, 1)))
        neighbour_sum = (
            padded_v[:-2, 1:-1] + padded_v[2:, 1:-1] +
            padded_v[1:-1, :-2] + padded_v[1:-1, 2:]
        )
        neighbour_count = (
            padded_k[:-2, 1:-1] + padded_k[2:, 1:-1] +
            padded_k[1:-1, :-2] + padded_k[1:-1, 2:]
        )
        fillable = (known == 0) & (neighbour_count > 0)
        if not fillable.any():
            break
        out[fillable] = neighbour_sum[fillable] / neighbour_count[fillable][..., None]
        known[fillable] = 1.0

    return np.clip(out, 0, 255)


def save(image, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)
    print('  ', os.path.relpath(path, ROOT))


def main():
    rgb = load_tile()

    print('App-Icon (1024, ohne Alpha):')
    icon = Image.fromarray(fill_rounded_corners(rgb).astype(np.uint8), 'RGB')
    icon = icon.resize((ICON_PX, ICON_PX), Image.LANCZOS)
    save(icon, os.path.join(ASSETS, 'AppIcon.appiconset', 'icon-1024.png'))

    print('Splash-Symbol (freigestellt):')
    splash = straight_alpha(rgb).resize((SPLASH_PX, SPLASH_PX), Image.LANCZOS)
    save(splash, os.path.join(ASSETS, 'SplashLogo.imageset', 'splash-logo.png'))


if __name__ == '__main__':
    main()
