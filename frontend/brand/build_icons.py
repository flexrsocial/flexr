"""Erzeugt alle Icon-Varianten aus der FX-Vorlage.

Die Vorlage ist ein 1254x1254-RGB-Bild: eine abgerundete dunkle Kachel mit
47 px schwarzem Rand ringsum. Weil das Artwork Verlaeufe und einen Glow hat,
laesst es sich nicht als Vektor nachbauen -> Raster in allen Dichten.
"""
import os
import numpy as np
from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), 'app-icon-fx-1254.png')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

TILE = (47, 47, 1206, 1208)          # Kachel ohne den schwarzen Rand
# Der Kachelhintergrund ist nicht gleichmaessig (Vignette, 15..26). Der obere
# Rand dieses Bereichs wird abgezogen, sonst bleibt beim Freistellen ein
# sichtbarer Geisterrand der Kachel in der Vordergrundebene stehen.
TILE_BG = np.array([27.0, 23.0, 21.0])
# Anteil der Adaptive-Icon-Flaeche (108), den die Kachel einnimmt. 83/108 laesst
# das helle FX auf 64 Einheiten -> 89 % der 72er-Maske, kein Anschnitt.
TILE_ON_CANVAS = 83.0 / 108.0


def load_tile():
    im = Image.open(SRC).convert('RGB').crop(TILE)
    return np.asarray(im).astype(np.float32)


def straight_alpha(rgb):
    """Artwork vom Kachelhintergrund loesen.

    Das Bild ist P = A*C + (1-A)*B ueber dem Hintergrund B. Aus dem hellsten
    Kanal folgt A, daraus laesst sich C zurueckrechnen. Reiner Hintergrund
    wird damit transparent, der Glow behaelt seinen weichen Verlauf.
    """
    maxc = rgb.max(axis=2)
    bg_max = TILE_BG.max()
    a = np.clip((maxc - bg_max) / (255.0 - bg_max), 0.0, 1.0)
    a3 = a[..., None]
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.where(a3 > 1e-4, (rgb - (1.0 - a3) * TILE_BG) / np.maximum(a3, 1e-4), 0.0)
    out = np.dstack([np.clip(c, 0, 255), a * 255.0]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def tile_mask(rgb):
    """Kachel mit abgerundeten Ecken: Alpha direkt aus dem schwarzen Rand."""
    maxc = rgb.max(axis=2)
    a = np.clip(maxc / 10.0, 0.0, 1.0) * 255.0
    out = np.dstack([rgb, a]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def monochrome(rgb):
    """Weisse Silhouette ohne Glow — Android faerbt die Ebene selbst ein."""
    maxc = rgb.max(axis=2)
    a = np.clip((maxc - 150.0) / 45.0, 0.0, 1.0) * 255.0
    white = np.full(rgb.shape, 255.0)
    out = np.dstack([white, a]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def on_canvas(layer, size):
    """Ebene zentriert auf eine quadratische Adaptive-Icon-Flaeche legen."""
    inner = max(1, round(size * TILE_ON_CANVAS))
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    scaled = layer.resize((inner, inner), Image.LANCZOS)
    off = (size - inner) // 2
    canvas.alpha_composite(scaled, (off, off))
    return canvas


def main():
    rgb = load_tile()
    fg = straight_alpha(rgb)
    mono = monochrome(rgb)
    tile = tile_mask(rgb)

    # --- Android: Adaptive-Icon-Ebenen in allen Dichten ---
    densities = {'mdpi': 108, 'hdpi': 162, 'xhdpi': 216, 'xxhdpi': 324, 'xxxhdpi': 432}
    for dpi, size in densities.items():
        d = f'{ROOT}/android-native/app/src/main/res/mipmap-{dpi}'
        os.makedirs(d, exist_ok=True)
        on_canvas(fg, size).save(f'{d}/ic_launcher_foreground.png')
        on_canvas(mono, size).save(f'{d}/ic_launcher_monochrome.png')

    # --- Web: PWA-Icons ---
    icons = f'{ROOT}/frontend/icons'
    tile.resize((192, 192), Image.LANCZOS).save(f'{icons}/icon-192.png')
    tile.resize((512, 512), Image.LANCZOS).save(f'{icons}/icon-512.png')

    # Maskable: randlose Flaeche, Artwork in der 80-%-Sicherheitszone.
    mask512 = Image.new('RGBA', (512, 512), (18, 18, 18, 255))
    mask512.alpha_composite(on_canvas(fg, 512))
    mask512.save(f'{icons}/icon-maskable-512.png')

    # Favicon: mehrere Groessen in einer .ico
    tile.resize((256, 256), Image.LANCZOS).save(
        f'{ROOT}/frontend/favicon.ico',
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    # --- Play-Store-Listing (Upload steht noch aus) ---
    store = Image.new('RGB', (512, 512), (18, 18, 18))
    store.paste(tile.resize((512, 512), Image.LANCZOS), (0, 0),
                tile.resize((512, 512), Image.LANCZOS))
    store.save(f'{ROOT}/android/store_icon.png')
    store.save(f'{ROOT}/android/store/icon-512.png')

    print('fertig')


main()
