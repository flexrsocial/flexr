"""Welcher Fortschrittsstrich ist orange? bars.py <png> <y0> <y1> <x0> <x1> <anzahl>"""
import sys
from PIL import Image
p, y0, y1, x0, x1, n = sys.argv[1], *map(int, sys.argv[2:7])
im = Image.open(p).convert('RGB')
seg = (x1 - x0) / n
treffer = []
for i in range(n):
    orange = 0
    for x in range(int(x0 + i * seg + seg * .2), int(x0 + (i + 1) * seg - seg * .2), 3):
        for y in range(y0, y1):
            r, g, b = im.getpixel((x, y))
            if r > 200 and 50 < g < 140 and b < 90:
                orange += 1
    treffer.append(orange)
aktiv = max(range(n), key=lambda i: treffer[i]) if max(treffer) > 0 else None
print('aktiv:', None if aktiv is None else aktiv + 1, 'von', n, treffer)
