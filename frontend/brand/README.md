# FLEXR — Marke

Verbindliche Logo-Dateien. **Nicht** nachbauen oder in anderen Programmen
nachsetzen — immer diese Dateien verwenden bzw. per `build_logo.py` neu
erzeugen.

## Wortmarke

`FLEXR` — `FLEX` in Kreideweiß, das **`R` in Signalrot**. Der Akzent liegt auf
dem R (frühere Versionen betonten das X in Orange; das ist überholt).

## Dateien

| Datei | Einsatz |
|---|---|
| `logo-flexr.svg` | **Standard.** Vektor, transparent, für dunkle Hintergründe |
| `logo-flexr-light.svg` | Vektor, transparent, für helle Hintergründe |
| `logo-flexr-badge.svg` | Vektor auf dunklem, abgerundetem Grund — freistehend, z. B. auf Fotos |
| `logo-flexr-512/1024/2048.png` | Raster, transparent, dunkle Hintergründe |
| `logo-flexr-light-1024.png` | Raster, transparent, helle Hintergründe |
| `logo-flexr-badge-1024.png` | Raster-Badge |

SVG bevorzugen — die Buchstaben liegen als Pfade vor, es wird also keine
installierte Schrift benötigt und die Datei skaliert verlustfrei.

## Farben

| Rolle | Hex |
|---|---|
| Wortmarke auf Dunkel | `#F2EFEA` |
| Wortmarke auf Hell | `#141414` |
| Akzent (das `R`) | `#E8412B` |
| Badge-Hintergrund | `#121212` |

Hinweis: Das UI der App nutzt als Akzent weiterhin Orange (`#FF5A1F`,
`--plate`). Logo-Rot und UI-Orange sind bewusst getrennt zu behandeln,
solange die Farbwelt nicht insgesamt umgestellt ist.

## Schutzraum & Mindestgröße

- Rundum mindestens die Höhe eines Versalbuchstabens freilassen.
- Wortmarke nicht unter 80 px Breite einsetzen (darunter das App-Icon nutzen).
- Nicht verzerren, nicht umfärben, Buchstabenabstand nicht verändern.

## Neu erzeugen

```bash
backend/venv/bin/python frontend/brand/build_logo.py
```

Proportionen (Tracking, Badge-Verhältnis) stehen als Konstanten oben im Skript.
Das App-Icon liegt separat unter `frontend/icons/` und wird von
`android/store/gen.py` bzw. dem Bubblewrap-Build verwendet.
