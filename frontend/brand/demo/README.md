# Beispielprofil-Fotos (Demo-Deck)

28 KI-generierte Portraits. 22 davon werden als Beispielprofile im Login-Hero
der App (`frontend/app/index.html`, `.hero-demo`) und 23 im
Musterprofile-Abschnitt der Landingpage (`frontend/index.html`) verwendet.
Von den am 19.08.2026 hinzugekommenen 20 Motiven sind 19 in beiden Decks
eingebunden: zehn Frauen und neun Männer. Samuel wurde am 19.08.2026 auf
Nutzerwunsch aus beiden Decks entfernt; die Quelldatei bleibt erhalten.

## Herkunft

Der erste Satz wurde am 16.08.2026 mit ChatGPT (Bildgenerierung) erzeugt und
vom Nutzer bereitgestellt. Weitere 20 Bilder wurden am 19.08.2026 mit dem in
Codex eingebauten ImageGen erzeugt. Keine echten, identifizierbaren Personen
abgebildet — anders als das ursprüngliche Demo-Deck
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

Originale (KI-generiert, 1254×1254 px PNG) lagen auf dem Arbeitsplatzrechner
(zunächst `~/Downloads`, zweiter Satz unter `~/MEGA/FLEXR/Grafiken`), nicht
Teil dieses Repositories. Hier abgelegt sind nur die verarbeiteten Fassungen:

| Datei | Zugeordnetes Beispielprofil | Verwendet in |
|---|---|---|
| `demo-lena.jpg` | Lena, 26 | Landingpage, App-Login-Hero |
| `demo-tobias.jpg` | Tobias, 28 | Landingpage, App-Login-Hero |
| `demo-sophie.jpg` | Sophie, 27 | Landingpage |
| `demo-jonas.jpg` | Jonas, 25 | Landingpage |
| `demo-julia.jpg` | Julia, 25 | App-Login-Hero |
| `demo-david.jpg` | — | nicht mehr eingebunden (16.08.2026 von der Landingpage entfernt, Datei bleibt liegen) |
| `demo-nina.jpg` | — | nicht mehr eingebunden (16.08.2026 von der Landingpage entfernt, Datei bleibt liegen) |
| `demo-marco.jpg` | — | nicht mehr eingebunden (16.08.2026 von der Landingpage entfernt, Datei bleibt liegen) |
| `demo-anna-v2.jpg` | Anna, 26 | Landingpage, App-Login-Hero |
| `demo-miriam-v2.jpg` | Miriam, 28 | Landingpage, App-Login-Hero |
| `demo-emi-v2.jpg` | Emi, 29 | Landingpage, App-Login-Hero |
| `demo-zeynep-v2.jpg` | Zeynep, 27 | Landingpage, App-Login-Hero |
| `demo-laura-v2.jpg` | Laura, 30 | Landingpage, App-Login-Hero |
| `demo-amara-v2.jpg` | Amara, 30 | Landingpage, App-Login-Hero |
| `demo-maya-v2.jpg` | Maya, 26 | Landingpage, App-Login-Hero |
| `demo-priya-v2.jpg` | Priya, 31 | Landingpage, App-Login-Hero |
| `demo-katharina-v2.jpg` | Katharina, 32 | Landingpage, App-Login-Hero |
| `demo-sofia-v2.jpg` | Sofia, 28 | Landingpage, App-Login-Hero |
| `demo-lukas-v2.jpg` | Lukas, 28 | Landingpage, App-Login-Hero |
| `demo-marco-v2.jpg` | Marco, 27 | Landingpage, App-Login-Hero |
| `demo-elias-v2.jpg` | Elias, 30 | Landingpage, App-Login-Hero |
| `demo-kenji-v2.jpg` | Kenji, 25 | Landingpage, App-Login-Hero |
| `demo-cem-v2.jpg` | Cem, 29 | Landingpage, App-Login-Hero |
| `demo-felix-v2.jpg` | Felix, 32 | Landingpage, App-Login-Hero |
| `demo-mateo-v2.jpg` | Mateo, 26 | Landingpage, App-Login-Hero |
| `demo-arjun-v2.jpg` | Arjun, 31 | Landingpage, App-Login-Hero |
| `demo-noah-v2.jpg` | Noah, 27 | Landingpage, App-Login-Hero |
| `demo-samuel-v2.jpg` | Samuel, 33 | nicht mehr eingebunden (19.08.2026 auf Nutzerwunsch entfernt) |

Der Hinweistext "Beispielprofile · keine echten Nutzer:innen" wurde am
16.08.2026 auf ausdrücklichen Wunsch von beiden Einbindungsstellen entfernt.
Die Begründung dafür (Abschnitt oben) gilt inhaltlich unverändert — nur die
sichtbare Kennzeichnung ist weg.

Verarbeitung: auf 3:4 zugeschnitten (Kartenformat der echten App,
`.card .photo`), auf 720×960 px skaliert, als JPEG (Qualität 84) exportiert.
Je nach Motiv rund 55–125 KB je Datei statt mehrerer Megabyte im Original.

## Prompt-Set vom 19.08.2026

Gemeinsame Basis aller 20 ImageGen-Prompts: fotorealistisch-natürliche,
hochwertige Fitness-Lifestyle-Fotografie im vertikalen 3:4-Format; klar
erwachsene, sympathische Personen; realistische Haut und Anatomie; moderne,
unbedruckte Performance-Kleidung; keine Marken, Schrift, Wasserzeichen,
Prominenten oder weiteren Personen. Die Szenenvarianten waren Squat Rack,
Dumbbell Shoulder Press, Cable Row, Sled Push, Laufband, Boxsack,
Calisthenics, Deadlift, Cycling, Battle Ropes, Pull-up Rig, Incline Dumbbell,
Indoor Rower, Outdoor Dips, SkiErg und ein professioneller Men's-Physique-
Bühnenauftritt. Die Kleidung ist bewusst markenfrei statt als Gymshark-
Produktdarstellung ausgeführt.

## Selbst gehostet, kein Fremdaufruf

Anders als das alte Deck liegen diese Bilder im eigenen `frontend/`-Ordner und
werden von nginx unter derselben Origin ausgeliefert wie der Rest der Seite.
Kein Drittanbieter bekommt die IP-Adresse von Besuchern zu sehen, keine
Content-Security-Policy-Ausnahme nötig — `img-src 'self'` deckt das bereits
ab.
