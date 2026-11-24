# FLEXR · DESIGN.md

Eine Vorgabe für alle vier Oberflächen: **flexr.social** (Landingpage, Städte- und
Ratgeberseiten), **Web-App `/app`**, **Android** (`android-native`, Compose) und
**iOS** (`ios/FLEXR`, SwiftUI). Wer etwas Neues baut oder umbaut, hält sich daran.
Eine Abweichung ist erlaubt, wenn sie begründet und hier nachgetragen wird.

Stand: 24.11.2026. Entstanden aus zwei Design-Runden gegen den KI-Look
(Landingpage, Web-App, Apps) und einer Sichtung von 10 Referenzseiten.

---

## 1. Referenzen: was bei anderen funktioniert

Gesichtet am 24.11.2026, jeweils Startseite, Desktop und Handy. Dating-Apps
(Hinge, Bumble, Feeld) ließen sich im Prüf-Browser nicht öffnen und fehlen
deshalb. Bei mehreren Seiten verdeckte ein Cookie-Banner Teile der Seite.
Die Beobachtungen gelten für das, was sichtbar war.

| Seite | Was wirkt | Was wir übernehmen |
|---|---|---|
| **Strava** | Bildschirmfüllendes, unscharfes Bewegungsfoto als Hero, ein Satz, ein orangefarbener Button. Darunter viel Weißraum und Text zentriert. Orange nur für den Button und das Logo. | Orange sparsam: für die eine Hauptaktion pro Ansicht, nicht als Dekoration. |
| **Whoop** | Großes Produktfoto, große Sans-Überschrift, nur Schwarz und Weiß. **Gegenbeispiel:** Preise als gleichförmige Karten mit Haken. | Ruhe durch wenige Farben. Keine Preiskarten mit Haken. |
| **Gymshark** | Eigene schmale Display-Schrift in Großbuchstaben, eine vollflächige Farbfläche (Blau) für die Kampagne. | Schmale Großbuchstaben-Schrift (bei uns Oswald) plus vollflächige Markenfarbe als Plakat. |
| **Equinox** | Schwarzer Grund, randlose Bilder, kleines weit gesperrtes Logo. Wirkt wie ein Magazin. | Dunkler Grund, Bilder randlos, Typografie zurückhaltend und groß. |
| **Hevy** | Inter, ein farbiges Wort in der Überschrift, weiße Seite. **Gegenbeispiel:** genau der austauschbare Look. | Kein Inter, kein einzelnes Farbwort als Stilmittel ohne Grund. |
| **Les Mills** | Riesige Großbuchstaben direkt auf dem Trainingsfoto, schwarzer Grund, neongrüner Button. | Großbuchstaben auf Foto, Neon nur als Akzent. |
| **PureGym** | Poppins und Inter, Standard-Karten. **Gegenbeispiel:** wirkt wie eine Vorlage. | Nicht so. |
| **McFIT** | Vollflächige Signalfarbe (Gelb) mit großen Zahlen (Countdown), fette Montserrat. | Große Zahlen als Bild (unser „0 €“-Plakat, Kontur-Ziffern 01–03). |
| **John Reed** | Vollflächiges Pink, Großbuchstaben, laute Kampagnenenergie. | Eine laute Fläche pro Seite reicht. |
| **Nike** | Foto zuerst, schmale Futura in Großbuchstaben mittig auf dem Bild, kleiner Pillen-Button. | Das Foto trägt die Marke. Darauf nur die Überschrift und eine Aktion. |

**Was die guten gemeinsam haben:**
1. **Echte Trainingsfotos tragen die Marke.** Bei FLEXR offen: Fotos von Studios,
   Hanteln und Kreide ohne Gesichter, geliefert vom Betreiber (Punkt B,
   später). Bis dahin sind die KI-Beispielprofile die einzigen Bilder. Sie
   bleiben als solche gekennzeichnet.
2. **Eine eigene, schmale Display-Schrift in Großbuchstaben** und eine
   unauffällige Textschrift.
3. **Eine Markenfarbe, vollflächig statt als Verlauf**, sparsam eingesetzt.
4. **Große Zahlen als Gestaltungselement** statt Symbol-Kärtchen.

**Woran man die austauschbaren erkennt:** Inter oder Poppins, ein farbiges Wort
in der Überschrift, Karten mit Haken, Verläufe, Weichzeichner-Glas.

---

## 2. Verboten (KI-Look)

- Kein **Inter**, kein **Poppins**, keine Mono-Schrift als Stilmittel.
- Keine **Verläufe** auf Flächen, Buttons oder Karten (auch keine „fast
  unsichtbaren“ von #202020 nach #191919). Erlaubt sind nur dunkle Schleier
  über Fotos, damit Schrift lesbar bleibt, und der Füllstand eines Reglers.
- Kein **Leuchten**: keine farbigen box-shadows, kein Lichtschein hinter
  Elementen, kein Glühen bei Hover.
- Keine **Serifen-Überschrift mit einem kursiven Wort**.
- Keine **vier Statistik-Karten in einer Reihe**, keine Raster aus gleich
  aussehenden Karten (dunkler Kasten, oranger Strich, Titel, grauer Text).
- Keine **Preiskarten mit Haken** und keinem „Empfohlen“-Schild.
- Keine **Eyebrow-Zeilen** (kleine orange Großbuchstaben-Zeile über der
  Überschrift), keine Slogans wie „Match. Train. Repeat.“, kein „Bereit?“.
- Keine **Zierbalken**: kein oranger Strich unter dem Logo, kein Balken vor
  Abschnittstiteln.
- Kein **Glas** (backdrop-filter als Deko), keine radialen Lichtflecken im
  Hintergrund.

Faustregel: Sieht ein Abschnitt aus wie auf jeder anderen KI-Seite, wird er neu
gedacht, nicht nachpoliert.

---

## 3. Farben

Gleiche Werte auf allen Plattformen. Quellen: Web `:root` in
`frontend/index.html` und `frontend/app/index.html`, Android
`core/designsystem/theme/Color.kt`, iOS `Core/DesignSystem/Theme/FlexrColor.swift`.

| Token | Wert | Verwendung |
|---|---|---|
| `ink` | `#121212` | Seitengrund |
| `surface` | `#1C1C1C` | Karten, Listenzeilen, Eingabefelder (flach!) |
| `surface-2` / `surface-3` | `#242424` / `#2C2C2C` | Kleine runde Knöpfe, Hover-Grund |
| `steel` | `#3A3A3A` | Rahmen von Sekundär-Buttons, Tabellen-Kopflinie |
| `hairline` | `rgba(255,255,255,.07)` | Trennlinien, Kartenrand |
| `chalk` | `#EDE9E2` | Haupttext |
| `chalk-dim` | `#A8A49B` | Nebentext |
| `plate` | `#FF5A1F` | **Die** Markenfarbe: Hauptaktion, Plakatflächen, Premium |
| `plate-bright` | `#FF7A45` | Hover der Hauptaktion |
| `plate-ink` | `#191008` (Web-Plakat: `#140700`) | Schrift auf Orange |
| `lime` | `#C7FF4A` | Hinweise „derzeit gratis“, Like-Stempel, Fokus-Rand |
| `danger` | `#E34848` | Fehler, Löschen |

Regeln:
- **Orange flach.** Pro Ansicht eine orange Hauptaktion. Große orange Flächen
  nur als Plakat (Preis-„0 €“, Premium-Spaltenkopf).
- **Schrift auf Orange ist dunkel** (`plate-ink`), nie weiß.
- `lime` nie als Flächenfarbe für Buttons im Inhalt (nur Skip-Link, Stempel).

---

## 4. Schrift

| Rolle | Schrift | Regeln |
|---|---|---|
| Display / Überschriften | **Oswald** 500–700, Großbuchstaben, Sperrung .02em | H1 Landing `clamp(…)`, H2 `clamp(23px,4vw,31px)` |
| Text | **Work Sans** 400–700 | Fließtext 15–17 px, Zeilenhöhe 1.6 |
| Zahlen als Bild | Oswald 700 | Kontur-Ziffern 01–03, „0 €“ bis 200 px |

- **Mindestgröße 12 px / 12 sp / 12 pt** für jeden lesbaren Text. Ausnahmen nur
  Zähler-Badges (Navigation, ungelesen) und Trennlinien-Text.
- Großbuchstaben nur für Oswald-Überschriften, Buttons und kurze Labels.
  Kein Großbuchstaben-Fließtext.
- Dateien: `frontend/fonts/oswald.woff2`, `work-sans.woff2`. Android und iOS
  haben dieselben Schnitte eingebettet.

---

## 5. Abstände, Radien, Linien

- Raster in 4er-Schritten. Abschnitte auf der Landingpage `padding:44px 0`,
  dazwischen eine `hairline`.
- Inhaltsbreite Landing max. 880 px, Web-App max. 430 px.
- Radien: Buttons **12**, Eingabefelder und Listenzeilen **14**, Swipe-Karte
  **20**, Plakatflächen und Tabellenrahmen **4** (bewusst eckig, Plakat-Anmutung).
- Struktur kommt über **Linien und Weißraum**, nicht über Kästen. Listen mit
  Trennlinien statt Karten-Stapel, Tabellen statt Karten mit Haken.

---

## 6. Bausteine

- **Button primär:** Oswald 16 px, Großbuchstaben, Sperrung .06em, `plate` flach,
  Schrift dunkel, Radius 12, Höhe ≥ 48. Hover nur heller (`plate-bright`).
- **Button sekundär (ghost):** transparent, Rand `steel`, Schrift `chalk`.
- **Plakat:** vollflächig `plate`, dunkle Schrift, riesige Zahl links, Text und
  dunkler Button rechts. Am Handy untereinander. Einmal pro Seite.
- **Vergleichstabelle (Preis):** Zeilen mit `hairline`, Werte statt Haken.
  Hervorgehobene Spalte: oranger Kopf als Plakat-Stück und 3 px orange Linie
  links, **kein Rahmen um die Spalte**. Aktion darunter mit Abstand, so breit
  wie die Spalte.
- **Schrittfolge:** große Oswald-Kontur-Ziffern 01/02/03, kurzer Titel, eine Zeile Text.
- **Checkliste Sicherheit:** großer Satz als Zitat, darunter Punkte mit eigenem
  Linien-Symbol, keine Karten.
- **Listenzeile (Matches, Chats, Konto):** `surface` flach, Rand `hairline`,
  Radius 14, Pfeil rechts.
- **Abschnittstitel im Konto:** Großbuchstaben, Linie darunter, ohne Balken davor.

---

## 7. Bedienung und Feinschliff

- **Tippflächen ≥ 44 px (Web, iOS pt) bzw. 48 dp (Android).** Kleine Symbole
  bekommen eine unsichtbare größere Fläche. Fließtext-Links sind ausgenommen.
- **Hover nur mit echter Maus:** Web-Regeln mit `:hover` stehen in
  `@media (hover:hover)`, damit am Handy nach dem Antippen nichts orange
  „hängen“ bleibt. Hover = Farbe heller oder 1–2 px anheben, nie Leuchten.
- **Texte je Gerät:** Am Handy keine Hinweise auf Maus oder Pfeiltasten
  (Landing: `.hint-touch` / `.hint-mouse`).
- **Animation:** kurz (150–300 ms), `ease`. Einblenden mit 6 px Versatz.
  Federnde Effekte nur beim Match-Moment.
- **Jede Seite bei 375 px prüfen** (auch 320 px für Überschriften): nichts ragt
  über den Rand, Abstände gleichmäßig, Buttons nicht gequetscht.

---

## 8. Sprache und Inhalt

- Du-Form, kurz, konkret, ehrlich. Keine Versprechen, die FLEXR nicht halten
  kann („mehr Matches“).
- Gleiche Aussagen überall gleich formulieren: Landing, `/app`, Apps und Store
  verwenden dieselben Kernsätze (z. B. „Dauerhaft gratis nutzbar — nichts wird
  abgebucht, Premium ist freiwillig“).
- Fakten (Preis 10 €/Monat, 20 Likes/Tag, 3 Unterhaltungen, 50 km bzw. derzeit
  1.100 km) stehen in Landing-Preis, FAQ und Premium-Screen gleich.

---

## 9. Ablauf bei Design-Änderungen

1. Prüfen gegen Abschnitt 2 (Verboten) und diese Datei.
2. Größere Umbauten: **3 deutlich verschiedene Entwürfe** auf einer lokalen
   Testseite (`frontend/_entwuerfe-*.html`, nicht live), jeder nach einer
   anderen Referenz. Erst nach Auswahl bauen.
3. Polish-Pass bei 375 px, Hover und Tippflächen.
4. Alle vier Plattformen nachziehen und hier eintragen, was neu ist.
