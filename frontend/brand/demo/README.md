# Beispielprofil-Fotos (Demo-Deck)

Sechs KI-generierte Portraits, verwendet als Beispielprofile im Login-Hero
der App (`frontend/app/index.html`, `.hero-demo`) und im
Musterprofile-Abschnitt der Landingpage (`frontend/index.html`).

## Herkunft

Erzeugt mit ChatGPT (Bildgenerierung) am 16.08.2026, vom Nutzer bereitgestellt
und als KI-generiert mit geprüften Rechten bestätigt. Keine echten,
identifizierbaren Personen abgebildet — anders als das ursprüngliche Demo-Deck
(bis 15.08.2026, acht Fotos realer Menschen von images.unsplash.com), das aus
genau diesem Grund entfernt wurde: reale Personen als erfundene FLEXR-Profile
darzustellen ist ein Recht-am-eigenen-Bild-Problem, unabhängig vom
Urheberrecht am Foto selbst.

## Warum trotzdem "Beispielprofil" dranstehen muss

KI-generierte Gesichter bilden keine reale Person ab, könnten aber trotzdem
den Eindruck erwecken, es handle sich um echte, aktive FLEXR-Mitglieder. Das
wäre eine irreführende Angabe im Sinn des Lauterkeitsrechts (UWG), unabhängig
von Bildrechten. Deshalb stehen alle Verwendungsstellen ausdrücklich mit einem
sichtbaren Hinweis ("Beispielprofile · keine echten Nutzer:innen" bzw.
gleichwertig) da — dieser Hinweis darf beim Weiterverwenden nicht entfallen.

## Dateien

Originale (KI-generiert, 1254×1254 px PNG) lagen unter `~/Downloads` auf dem
Arbeitsplatzrechner, nicht Teil dieses Repositories. Hier abgelegt sind nur
die verarbeiteten Fassungen:

| Datei | Zugeordnetes Beispielprofil |
|---|---|
| `demo-lena.jpg` | Lena, 26 |
| `demo-david.jpg` | David, 30 |
| `demo-julia.jpg` | Julia, 25 |
| `demo-tobias.jpg` | Tobias, 28 |
| `demo-nina.jpg` | Nina, 26 |
| `demo-marco.jpg` | Marco, 29 |

Verarbeitung: auf 3:4 zugeschnitten (Kartenformat der echten App,
`.card .photo`), auf 720×960 px skaliert, als JPEG (Qualität 84) exportiert.
Rund 80–115 KB je Datei statt 2,2 MB im Original.

## Selbst gehostet, kein Fremdaufruf

Anders als das alte Deck liegen diese Bilder im eigenen `frontend/`-Ordner und
werden von nginx unter derselben Origin ausgeliefert wie der Rest der Seite.
Kein Drittanbieter bekommt die IP-Adresse von Besuchern zu sehen, keine
Content-Security-Policy-Ausnahme nötig — `img-src 'self'` deckt das bereits
ab.
