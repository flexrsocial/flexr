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
| `app-icon-fx-1254.png` | **App-Icon-Vorlage** (FX auf dunkler Kachel) — Quelle für alle Icon-Größen |

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

## App-Icon

Das App-Icon ist **nicht** die Wortmarke, sondern das FX-Zeichen auf dunkler
Kachel (`app-icon-fx-1254.png`). Es hat Verläufe und einen Glow und lässt sich
deshalb nicht als Vektor nachbauen — alle Größen werden aus der Vorlage
gerendert:

```bash
backend/venv/bin/python frontend/brand/build_icons.py
```

Das Skript schreibt in einem Zug:

| Ziel | Inhalt |
|---|---|
| `android-native/…/res/mipmap-*/ic_launcher_foreground.png` | Adaptive-Icon-Vordergrund, freigestellt |
| `android-native/…/res/mipmap-*/ic_launcher_monochrome.png` | Silhouette für Android-13-Themed-Icons |
| `frontend/icons/icon-192.png`, `icon-512.png` | PWA/Favicon, Kachel mit runden Ecken |
| `frontend/icons/icon-maskable-512.png` | randlos, Artwork in der 80-%-Sicherheitszone |
| `frontend/favicon.ico` | 16–256 px in einer Datei |
| `android/store_icon.png`, `android/store/icon-512.png` | Play-Store-Listing (gitignored) |

Nach einem Icon-Wechsel die Cache-Version `?v=` in `index.html`,
`manifest.json` und `sw.js` gemeinsam erhöhen — Chrome hält Favicons in einem
eigenen, sehr langlebigen Cache, der nach URL schlüsselt.
