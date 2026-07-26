#!/usr/bin/env python3
"""Erzeugt die FLEXR-Wortmarke als Vektor-Master (SVG) und als PNG-Exporte.

    backend/venv/bin/python frontend/brand/build_logo.py

Benoetigt fontTools + Pillow. Beides steckt im Backend-venv, deshalb der Aufruf
ueber dessen Interpreter (das System-Python hier hat kein pip).

Die Buchstaben werden aus der Schrift in echte SVG-Pfade konvertiert - das SVG
ist damit auf jedem System identisch, ohne dass die Schrift installiert sein
muss. Die PNGs entstehen aus derselben Layout-Rechnung, sind also deckungsgleich.

Varianten:
  logo-flexr.svg / .png            Wortmarke, transparent (Standard)
  logo-flexr-badge.svg / .png      Wortmarke auf dunklem, abgerundetem Grund
  logo-flexr-light.svg / .png      Wortmarke fuer helle Hintergruende
"""
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

WORD = "FLEXR"
ACCENT_FROM = 4          # ab diesem Index in Akzentfarbe -> nur das "R"

# --- Markenfarben ----------------------------------------------------------
CHALK = "#F2EFEA"        # FLEX auf dunklem Grund
CHALK_DARK = "#141414"   # FLEX auf hellem Grund
ACCENT = "#E8412B"       # R (Signalrot)
INK = "#121212"          # Badge-Hintergrund

# --- Proportionen (aus der Design-Vorlage abgeleitet) ----------------------
TRACKING = 0.10          # Buchstabenabstand in Versalhoehen
BADGE_W_RATIO = 0.438    # Anteil der Wortmarke an der Badge-Breite
BADGE_ASPECT = 3.01      # Badge-Seitenverhaeltnis (B:H)
BADGE_RADIUS = 0.127     # Eckradius als Anteil der Badge-Hoehe
PAD = 0.30               # seitlicher Rand der transparenten Variante (in Versalhoehen)

CAP = 1000.0             # interne Rechen-Einheit: Versalhoehe = 1000


def layout():
    """Positionen und Pfade aller Buchstaben in Einheiten mit Versalhoehe=CAP."""
    tt = TTFont(FONT_PATH)
    glyphs = tt.getGlyphSet()
    cmap = tt.getBestCmap()
    upem = tt["head"].unitsPerEm
    cap_units = getattr(tt["OS/2"], "sCapHeight", 0) or upem * 0.72
    scale = CAP / cap_units          # Fonteinheiten -> unsere Einheiten

    track = TRACKING * CAP
    items, x = [], 0.0
    for i, ch in enumerate(WORD):
        gname = cmap[ord(ch)]
        pen = SVGPathPen(glyphs)
        glyphs[gname].draw(pen)
        items.append({
            "char": ch,
            "d": pen.getCommands(),
            "x": x,
            "accent": i >= ACCENT_FROM,
        })
        x += tt["hmtx"][gname][0] * scale + track
    total = x - track
    return items, total, scale


ITEMS, WORD_W, SCALE = layout()


def svg_wordmark(fg, accent):
    """Wortmarke als SVG-Fragment (Ursprung links auf der Grundlinie)."""
    out = []
    for it in ITEMS:
        col = accent if it["accent"] else fg
        # Font-Y zeigt nach oben, SVG-Y nach unten -> spiegeln
        out.append(
            f'    <path transform="translate({it["x"]:.1f} 0) '
            f'scale({SCALE:.6f} -{SCALE:.6f})" fill="{col}" d="{it["d"]}"/>'
        )
    return "\n".join(out)


def write_svg(name, fg, accent, badge=False):
    if badge:
        bw = WORD_W / BADGE_W_RATIO
        bh = bw / BADGE_ASPECT
        r = bh * BADGE_RADIUS
        x0 = (bw - WORD_W) / 2
        y0 = (bh + CAP) / 2                      # Grundlinie
        body = (
            f'  <rect width="{bw:.1f}" height="{bh:.1f}" rx="{r:.1f}" fill="{INK}"/>\n'
            f'  <g transform="translate({x0:.1f} {y0:.1f})">\n'
            f'{svg_wordmark(fg, accent)}\n  </g>'
        )
        w, h = bw, bh
    else:
        pad = PAD * CAP
        w, h = WORD_W + 2 * pad, CAP + 2 * pad
        body = (
            f'  <g transform="translate({pad:.1f} {pad + CAP:.1f})">\n'
            f'{svg_wordmark(fg, accent)}\n  </g>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="FLEXR">\n'
        f'{body}\n</svg>\n'
    )
    (HERE / name).write_text(svg, encoding="utf-8")
    return w / h


# --- PNG-Export aus derselben Layout-Rechnung ------------------------------
def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def write_png(name, width, fg, accent, badge=False, transparent=True):
    SS = 4                                    # Supersampling
    if badge:
        bw = WORD_W / BADGE_W_RATIO
        bh = bw / BADGE_ASPECT
    else:
        pad = PAD * CAP
        bw, bh = WORD_W + 2 * pad, CAP + 2 * pad
    px_per_unit = width / bw * SS
    W, H = round(bw * px_per_unit), round(bh * px_per_unit)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0) if transparent else hexrgb(INK) + (255,))
    d = ImageDraw.Draw(img)
    if badge:
        r = bh * BADGE_RADIUS * px_per_unit
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=r, fill=hexrgb(INK) + (255,))

    # Schriftgroesse so, dass die Versalhoehe exakt CAP*px_per_unit ergibt
    probe = ImageFont.truetype(FONT_PATH, 1000)
    cap_px = d.textbbox((0, 0), "H", font=probe)[3] - d.textbbox((0, 0), "H", font=probe)[1]
    size = round(1000 * (CAP * px_per_unit) / cap_px)
    f = ImageFont.truetype(FONT_PATH, size)

    if badge:
        x0 = (bw - WORD_W) / 2 * px_per_unit
        baseline_top = (bh - CAP) / 2 * px_per_unit
    else:
        x0 = PAD * CAP * px_per_unit
        baseline_top = PAD * CAP * px_per_unit

    asc = d.textbbox((0, 0), "H", font=f)[1]
    x = x0
    for it in ITEMS:
        col = hexrgb(accent if it["accent"] else fg) + (255,)
        d.text((x0 + it["x"] * px_per_unit, baseline_top - asc), it["char"], font=f, fill=col)
        x += 1
    img = img.resize((round(W / SS), round(H / SS)), Image.LANCZOS)
    img.save(HERE / name, optimize=True)
    return img.size


if __name__ == "__main__":
    write_svg("logo-flexr.svg", CHALK, ACCENT)
    write_svg("logo-flexr-light.svg", CHALK_DARK, ACCENT)
    write_svg("logo-flexr-badge.svg", CHALK, ACCENT, badge=True)

    for w in (512, 1024, 2048):
        write_png(f"logo-flexr-{w}.png", w, CHALK, ACCENT)
    write_png("logo-flexr-light-1024.png", 1024, CHALK_DARK, ACCENT)
    write_png("logo-flexr-badge-1024.png", 1024, CHALK, ACCENT, badge=True)

    for p in sorted(HERE.glob("logo-*")):
        extra = ""
        if p.suffix == ".png":
            extra = f" {Image.open(p).size}"
        print(f"  {p.name:30}{extra}  {p.stat().st_size / 1024:6.1f} KB")
