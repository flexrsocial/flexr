# FLEXR — native iOS-App

Gegenstück zur nativen Android-App (`android-native/`): **Swift + SwiftUI**,
keine WebView, kein HTML/CSS/JS. Die Android-Fassung wurde ausschließlich als
fachliche Spezifikation gelesen; jede Datei hier ist neu geschrieben.

Das FastAPI-Backend (`backend/`) bleibt unverändert — die App spricht denselben
REST-Vertrag wie Web- und Android-Frontend.

---

## Schnellstart

```bash
open ios/FLEXR.xcodeproj
```

Danach in Xcode das Schema **FLEXR** wählen und starten (⌘R). Vorausgesetzt
werden Xcode 16 und iOS 17 als Mindestversion; externe Pakete gibt es keine, es
ist also kein Auflösen von Abhängigkeiten nötig.

Unit-Tests: ⌘U, oder

```bash
xcodebuild test -project ios/FLEXR.xcodeproj -scheme FLEXR -destination 'platform=iOS Simulator,name=iPhone 16'
```

### Gegen die lokale Testumgebung laufen

Statt eines eigenen Build-Flavors (Android: `local`) genügt ein Startargument:
im Schema unter *Run → Arguments* den bereits angelegten, deaktivierten Eintrag

```
-FlexrAPIBaseURL http://localhost:8000/
```

einschalten. Der Simulator teilt sich das Netzwerk mit dem Mac, ein Sonderhost
wie Androids `10.0.2.2` entfällt. Das Argument wirkt nur in Debug-Builds; für
alles andere gilt die Build-Einstellung `FLEXR_API_BASE_URL`
(`https://flexr.social/`), die über die Info.plist in die App kommt.

| | |
|---|---|
| Bundle-ID | `social.flexr.app` |
| Version | `2.0.6` (`MARKETING_VERSION`), Build 1 |
| Mindestversion | iOS 17.0 |
| Geräte | iPhone und iPad, Hochformat |

---

## Zielarchitektur

MVVM mit unidirektionalem Datenfluss, Repository-Muster und einem
handgeschriebenen Container statt eines DI-Frameworks.

```
SwiftUI-View  ->  @Observable Model  ->  Repository  ->  URLSession | SwiftData | Keychain
     ^                                        |
     +---------------- Zustand ---------------+
```

```
ios/
├── FLEXR.xcodeproj/          Dateisystem-synchronisierte Gruppen (Xcode 16)
├── Config/Info.plist         Berechtigungstexte, Schriften, URL-Schema, BGTask-ID
├── tools/build_icons_ios.py  App-Icon und Splash-Symbol aus der FX-Vorlage
├── FLEXRTests/               Unit-Tests
└── FLEXR/
    ├── FlexrApp.swift            App-Einstieg, AppDelegate, BGTask-Registrierung
    ├── Core/
    │   ├── Common/               ServerTime (UTC-Zeitstempel), Textlängen
    │   ├── DesignSystem/         Farben, Typografie, Formen, Bausteine, Emoji-Panel
    │   ├── Images/               Bildspeicher + Anzeige (Coil-Ersatz)
    │   ├── Media/ImageProcessor  Bildaufbereitung vor dem Upload
    │   ├── Network/              APIClient, Fehlerübersetzung
    │   └── Browser/              SFSafariViewController für Stripe
    ├── Data/
    │   ├── Remote/               FlexrAPI, BackendPlzAPI, DTOs
    │   ├── Local/                SwiftData: Matches + Nachrichten
    │   ├── Session/              Keychain-Token, Geräte-ID, Einstellungen
    │   └── Repository/           11 Repositories, die einzige Datenquelle der Modelle
    ├── Domain/Models.swift       Domänenmodelle, frei von Framework-Bezügen
    ├── DI/AppContainer.swift     Zusammenbau der App an genau einer Stelle
    ├── Notifications/            BGAppRefresh + lokale Benachrichtigung
    └── UI/                       ein Ordner je Bildschirm (View + Model)
```

**SwiftData als Single Source of Truth** für Matches und Chats — dieselbe
Entscheidung wie bei Room auf Android: Die Oberfläche liest ausschließlich aus
dem lokalen Bestand, das Netz füllt ihn nach. Dadurch sind Listen sofort und
offline sichtbar.

---

## Migrierte Komponenten

| Android (Referenz) | iOS | Anmerkung |
|---|---|---|
| `ui/auth/LoginScreen` | `UI/Auth/LoginView` + `LoginModel` | |
| `ui/auth/RegisterScreen` | `UI/Auth/RegisterView` + `RegisterModel` | Geburtsdatum über `DatePicker` mit 18-Jahres-Grenze |
| `core/media/ImageProcessor` | `Core/Media/ImageProcessor` | ImageIO dreht und skaliert in einem Schritt; 600/1080/256 px wie gehabt |
| `data/repository/PlzRepository` | dito | Gemeinde-Heuristik samt Cache übernommen |
| `ui/components/GymPicker` | `UI/Components/GymPicker` | speichert weiterhin das volle Label |
| `ui/swipe/SwipeCard` | `UI/Swipe/SwipeCard` | Griffpunkt-Rotation, Schwelle und Fling nachgebildet |
| `ui/swipe/MatchOverlay` | `UI/Swipe/MatchOverlay` | |
| `ui/matches/*` | `UI/Matches/*` | plus Zum-Aktualisieren-Ziehen |
| `ui/chat/*` | `UI/Chat/*` | 4-s-Abgleich, optimistisches Senden, Lesebestätigung, Zensur-Hinweis, Chat-Sperre |
| `ui/account/*` | `UI/Account/*` | Profil, Fotos, Radius, Abo, Verifizierung, Löschung |
| `ui/verification/*` | `UI/Verification/*` | AVFoundation statt CameraX, Frontkamera, drei Live-Posen |
| `ui/paywall`, `ui/reports`, `ui/legal` | dito | Rechtstexte als strukturierte Daten, offline |
| `data/session/SessionStore` | dito | Token im Keychain, Rest in UserDefaults |
| Retrofit + 2 Interceptoren | `Core/Network/APIClient` | Header nur auf `/api/`, 401 meldet die Sitzung ab |
| Room + DAOs | `Data/Local/FlexrStore` | SwiftData |
| Coil-ImageLoader | `Core/Images/ImageStore` | eigener Platten-/Speichercache, ignoriert HTTP-Cache-Header |
| Hilt | `DI/AppContainer` | eine Datei statt Modulen — bei dieser Größe übersichtlicher |
| WorkManager | `BGAppRefreshTask` | siehe Abweichungen |

### Bewusste Abweichungen von Android

| Thema | Android | iOS | Grund |
|---|---|---|---|
| Hintergrundabgleich | WorkManager, 15-Minuten-Intervall | `BGAppRefreshTask` | iOS sagt keine Intervalle zu; `earliestBeginDate` ist eine Untergrenze, den Rest entscheidet das System |
| Untere Navigation | `NavigationBar` (Material 3) | eigene Leiste | Hantel-Symbol, Orange-Akzent und Mono-Beschriftung lassen sich in `TabView` nicht abbilden |
| Snackbar | Material-Snackbar | eigenes Toast-Overlay | iOS kennt kein Systemäquivalent |
| Externer Browser | Chrome Custom Tab | `SFSafariViewController` | dieselbe Idee: Zahlungsdaten nie in der App |
| Fotoauswahl | Android Photo Picker | `PhotosPicker` | keine Mediathek-Berechtigung nötig |
| Token-Ablage | DataStore | Keychain | ein Anmeldegeheimnis gehört nicht in die Voreinstellungen |
| Längenprüfung | UTF-16-Einheiten | Unicode-Codepoints | zählt exakt wie Pythons `len()` im Backend |
| Dialoge | Material-3-Dialoge | `alert` / `sheet` | Meldegrund als Blatt, weil ein Alert kein mehrzeiliges Feld trägt |

### Nicht Teil der App

- **Telefonprüfung (SMS-OTP):** verworfen — wie im Web und auf Android. Die
  Endpunkte `/api/phone/*` existieren im Backend weiter, die App spricht sie
  nicht an.
- **Admin-Tool** (`frontend/admin.html`): bleibt Web-Werkzeug für den Betreiber.
- **Marketing-Landingpage:** das Store-Listing übernimmt diese Rolle, die App
  startet direkt beim Login.

---

## Berechtigungen

| Berechtigung | Wofür | Wann erfragt |
|---|---|---|
| Kamera | Verifizierungs-Selfies | beim Start der Verifizierung |
| Mitteilungen | neue Nachrichten | beim Einschalten im Konto |
| Hintergrundaktualisierung | Nachrichtenabgleich | ohne Dialog, systemseitig steuerbar |

Eine Standortberechtigung braucht die App nicht: die Umkreissuche geht
serverseitig von der Adresse des eingetragenen Gyms aus. Die Fotoauswahl braucht
ebenfalls **keine** Berechtigung — `PhotosPicker` liefert nur die ausgewählten
Bilder.

---

## Marke und Assets

Schriften (Oswald, Work Sans, JetBrains Mono) liegen als Variable Fonts unter
`FLEXR/Resources/Fonts/` — dieselben Dateien wie in der Android-App. Die
Gewichtsachse wird über `kCTFontVariationAttribute` gesetzt; ohne das läge jeder
Schnitt auf 400 und die Hierarchie wäre weg.

App-Icon und Splash-Symbol entstehen aus der verbindlichen Vorlage
`frontend/brand/app-icon-fx-1254.png`:

```bash
python3 ios/tools/build_icons_ios.py
```

Das iOS-Icon ist ein **volles Quadrat ohne Alpha**; iOS legt seine Maske selbst
darüber. Die abgerundeten Ecken der Vorlage werden deshalb aus den Nachbarpixeln
aufgefüllt statt schwarz stehen zu lassen — sonst blitzten dunkle Schlitze an
den Kanten durch.

Die Wortmarke folgt `frontend/brand/README.md`: FLEX in Kreideweiß, das **R** in
Signalrot `#E8412B`. Das UI-Orange `#FF5A1F` bleibt davon getrennt.
