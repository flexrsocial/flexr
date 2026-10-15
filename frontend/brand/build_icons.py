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
# Der Kachelhintergrund ist nicht gleichmaessig: eine Vignette laeuft von 15 bis
# etwa 35. Abgezogen wird deshalb deutlich ueber dem Mittelwert - sonst bleibt
# beim Freistellen ein schwach sichtbarer Geisterrand der Kachel in der
# Vordergrundebene stehen. Auf dem Launcher schneidet ihn die Maske weg, auf dem
# Splash-Screen aber nicht zwingend. Was dabei vom aeussersten Glow verloren
# geht, liegt bei ein bis zwei Helligkeitsstufen und ist nicht wahrnehmbar.
TILE_BG = np.array([40.0, 34.0, 31.0])
# Anteil der Adaptive-Icon-Flaeche (108), den die Kachel einnimmt. 83/108 laesst
# das helle FX auf 64 Einheiten -> 89 % der 72er-Maske, kein Anschnitt.
TILE_ON_CANVAS = 83.0 / 108.0

# Der Android-12-Splash zeichnet das Symbol auf 288dp und zeigt davon nur einen
# Kreis von 192dp Durchmesser (ohne eigene Icon-Hintergrundfarbe). Das FX ist
# breiter als hoch; seine halbe Diagonale misst 0.4955 der Kachelbreite und muss
# unter den Kreisradius 192/2/288 = 0.333 passen -> Kachel hoechstens 0.672.
TILE_ON_SPLASH = 0.67


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


def on_canvas(layer, size, anteil=TILE_ON_CANVAS):
    """Ebene zentriert auf eine quadratische Adaptive-Icon-Flaeche legen."""
    inner = max(1, round(size * anteil))
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    scaled = layer.resize((inner, inner), Image.LANCZOS)
    off = (size - inner) // 2
    canvas.alpha_composite(scaled, (off, off))
    return canvas


# --- Kopf der E-Mails (backend/app/mailer.py, MAIL_LOGO_PATH) ---------------
# Liegt unter /icons/ (nur dort liefert nginx aus, /brand/ ist gesperrt) und
# traegt die Version im Namen, weil /icons/ ein Jahr "immutable" gecacht wird.
#
# v2 (15.10.2026): Die Gmail-App unter Android dunkelt Mails mit dem
# Chromium-Dunkelmodus ab. Der haelt jedes Bild, das hoechstens 64 x 64 CSS-px
# gross angezeigt wird, fuer ein Icon und invertiert es, wenn es wenige Farben
# hat - die dunkle FX-Kachel wurde dort weiss. Ist eine Seite groesser,
# bleibt das Bild unangetastet. Darum ist das Bild 80 x 44 px breit: die
# Kachel (44 px) sitzt rechts, links ist es durchsichtig. Optisch aendert
# sich nichts. v1 (quadratisch) bleibt liegen, verschickte Mails laden sie.
MAIL_ICON = f'{ROOT}/frontend/icons/mail-icon-v2.png'
MAIL_ICON_PX = 132          # dreifache Anzeigegroesse (44 px im Mailkopf)
MAIL_BILD_BREITE_PX = 240   # dreifache Bildbreite (80 px im Mailkopf, > 64)
MAIL_KANTE_PX = 10          # Breite der hellen Kante, bezogen auf 512 px
MAIL_KANTE_ALPHA = 0.16     # Deckkraft der Kante (Weiss)


def mail_icon(tile):
    """App-Icon fuer den Kopf der E-Mails.

    Die Kachel hat fast genau die Kartenfarbe der Mails (#17171A) - ohne Kante
    verschwaende sie, und im Kopf schwebte nur das FX. Eine dezente helle Kante
    zeichnet die Kachel nach (wie die Store-Darstellung). Die Ecken bleiben
    transparent und sind ins Bild gerechnet: Outlook kennt kein border-radius.
    """
    from PIL import ImageFilter

    gross = tile.resize((512, 512), Image.LANCZOS)
    # Mit transparentem Rand erodieren: Die Kachel reicht bis an den
    # Bildrand, und dort wiederholt MinFilter die Randpixel - die Kante
    # erschiene sonst nur an den runden Ecken.
    rand = MAIL_KANTE_PX + 2
    gepolstert = Image.new('L', (512 + 2 * rand, 512 + 2 * rand), 0)
    gepolstert.paste(gross.getchannel('A'), (rand, rand))
    alpha = gross.getchannel('A')
    innen = gepolstert.filter(ImageFilter.MinFilter(2 * MAIL_KANTE_PX + 1)).crop(
        (rand, rand, rand + 512, rand + 512))
    ring = np.clip(np.asarray(alpha, np.float32) - np.asarray(innen, np.float32), 0, 255) / 255.0
    rgba = np.asarray(gross, np.float32)
    k = (ring * MAIL_KANTE_ALPHA)[..., None]
    rgba[..., :3] = rgba[..., :3] * (1 - k) + 255.0 * k
    out = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA')
    bild = Image.new('RGBA', (MAIL_BILD_BREITE_PX, MAIL_ICON_PX), (0, 0, 0, 0))
    bild.alpha_composite(out.resize((MAIL_ICON_PX, MAIL_ICON_PX), Image.LANCZOS),
                         (MAIL_BILD_BREITE_PX - MAIL_ICON_PX, 0))
    bild.save(MAIL_ICON, optimize=True)


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

    # --- Android: Splash-Symbol (288dp-Flaeche) ---
    # Ohne diese Dateien zeigt der Start noch die alte Hantel. Kein Vektor,
    # aus demselben Grund wie beim Launcher-Icon.
    for dpi, faktor in {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}.items():
        d = f'{ROOT}/android-native/app/src/main/res/drawable-{dpi}'
        os.makedirs(d, exist_ok=True)
        on_canvas(fg, round(288 * faktor), TILE_ON_SPLASH).save(f'{d}/ic_splash_logo.png')

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

    mail_icon(tile)

    print('fertig')


if __name__ == '__main__':
    import sys

    # Nur das Mail-Icon neu erzeugen, ohne die uebrigen Dateien anzufassen.
    if '--mail' in sys.argv:
        mail_icon(tile_mask(load_tile()))
        print(os.path.basename(MAIL_ICON))
    else:
        main()
