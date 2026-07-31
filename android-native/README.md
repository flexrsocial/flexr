# FLEXR — native Android-App

Vollständige Neuimplementierung der bisherigen browserbasierten App (TWA über
`android/`) als echte native Android-App: **Kotlin + Jetpack Compose + Material 3**.

Kein WebView, kein HTML, kein CSS, kein JavaScript. Der alte Web-Code wurde
ausschließlich als fachliche Spezifikation gelesen; jede Datei hier ist neu
geschrieben.

Das FastAPI-Backend (`backend/`) bleibt unverändert — die App spricht denselben
REST-Vertrag wie das Web-Frontend.

---

## Schnellstart

```bash
cd android-native && ./gradlew :app:assembleProdDebug
```

Voraussetzungen (liegen user-lokal bereits vor):

```bash
export JAVA_HOME=$HOME/.bubblewrap/jdk/jdk-17.0.11+9
export ANDROID_HOME=$HOME/.bubblewrap/android_sdk
```

Unit-Tests:

```bash
cd android-native && ./gradlew :app:testProdDebugUnitTest
```

### Build-Varianten

| Variante | Backend | Zweck |
|---|---|---|
| `prodDebug` / `prodRelease` | `https://flexr.social/` | Produktion |
| `localDebug` | `http://10.0.2.2:8000/` | lokale Testumgebung im Emulator |

`prodRelease` ist minifiziert (R8) und wird mit dem bestehenden Upload-Key aus
`android/android.keystore` signiert — die Play-Store-App behält dadurch ihre
Identität (`applicationId` bleibt `flexr.social.app`, `versionCode 6` folgt auf
den TWA-Stand 5).

---

## Zielarchitektur

MVVM mit unidirektionalem Datenfluss, Repository-Muster und Hilt als DI.

```
UI (Compose)  ->  ViewModel (StateFlow)  ->  Repository  ->  Retrofit | Room | DataStore
     ^                                            |
     +------------------ Flow --------------------+
```

```
app/src/main/java/flexr/social/app/
├── FlexrApplication.kt          Hilt-Einstieg, Notification-Channels, WorkManager
├── MainActivity.kt              einzige Activity, Splash + edge-to-edge
├── core/
│   ├── common/ServerTime        UTC-Zeitstempel des Backends, Alter, Formate
│   ├── designsystem/            Theme, Typografie, Icons, wiederverwendbare Bausteine
│   ├── media/ImageProcessor     Bildaufbereitung vor dem Upload
│   ├── network/                 Interceptors, Fehlerübersetzung
│   └── browser/                 Custom Tab für Stripe
├── data/
│   ├── remote/                  FlexrApi, OpenPlzApi, DTOs
│   ├── local/                   Room: Matches + Nachrichten
│   ├── session/SessionStore     DataStore: Token, Geräte-ID, Einstellungen
│   └── repository/              10 Repositories, die einzige Datenquelle der VMs
├── domain/model/                Domänenmodelle, frei von Framework-Bezügen
├── notifications/               WorkManager-Abgleich + Systembenachrichtigung
└── ui/                          ein Paket je Bildschirm (Screen + ViewModel)
```

**Room als Single Source of Truth** für Matches und Chats: die Oberfläche liest
ausschließlich aus der Datenbank, das Netz füllt sie nach. Dadurch sind Listen
sofort und offline sichtbar — im Web war jede Ansicht ein Ladebalken.

---

## Migrierte Komponenten

| Web (Referenz) | Nativ | Anmerkung |
|---|---|---|
| `index.html` Login-Screen | `ui/auth/LoginScreen` + `LoginViewModel` | |
| Onboarding-Formular | `ui/auth/RegisterScreen` + `RegisterViewModel` | Geburtsdatum über den nativen Kalenderdialog mit 18-Jahres-Grenze |
| `preparePhoto()` (Canvas) | `core/media/ImageProcessor` | 600 px Mindestmaß, 1080 px Vollbild, 256 px Thumbnail, EXIF-Drehung |
| PLZ-Lookup (OpenPLZ) | `data/repository/PlzRepository` | Gemeinde-Heuristik übernommen, mit Cache |
| Gym-Suchfeld + Vorschlag | `ui/components/GymPicker` | speichert weiterhin das volle Label `Name — Straße 1, 1100 Wien` |
| Swipe-Deck + Drag-Physik | `ui/swipe/SwipeCard` | Griffpunkt-Rotation, Schwellenwert und Fling-Verhalten 1:1 nachgebildet |
| `showMatchOverlay()` | `ui/swipe/MatchOverlay` | |
| Matches-/Chats-Listen | `ui/matches/*` | plus Pull-to-Refresh |
| Chat inkl. 4-s-Polling | `ui/chat/*` | optimistisches Senden, Lesebestätigung, Zensur-Hinweis, Chat-Sperre |
| Match-Profil | `ui/matches/MatchProfileScreen` | |
| Konto-Screen | `ui/account/*` | Profil, Fotos, Radius, Abo, Verifizierung, Löschung |
| Foto-Verifizierung (getUserMedia) | `ui/verification/*` | CameraX, Frontkamera, drei Live-Posen |
| Paywall | `ui/paywall/PaywallScreen` | |
| `impressum/agb/datenschutz/faq.html` | `ui/legal/LegalContent` | als strukturierte Compose-Daten, offline verfügbar |
| `localStorage` (Token, Geräte-ID) | `data/session/SessionStore` | DataStore, vom Cloud-Backup ausgenommen |
| `api()`-Fetch-Wrapper | `core/network/` + Retrofit | inkl. Übersetzung der FastAPI-`detail`-Formate |
| Service Worker | entfällt | ersetzt durch Room-Cache und WorkManager |

### Bewusste Abweichungen

| Thema | Web | Nativ | Grund |
|---|---|---|---|
| Emoji-Auswahl in Bio/Chat | eigenes Emoji-Panel | System-Tastatur | Android liefert die Emoji-Auswahl mit; ein Nachbau wäre ein Web-Relikt |
| `prompt()` / `confirm()` | Browser-Dialoge | Material-3-Dialoge | u. a. Meldegrund mit Längenprüfung (3–500 Zeichen wie im Backend) |
| Landingpage mit Demo-Deck | Marketing-Hero | entfällt | Store-Listing übernimmt diese Rolle; die App startet direkt beim Login |
| Ungelesen-Zähler | Polling nur bei offener Seite | WorkManager + Systembenachrichtigung | Nachrichten erreichen den Nutzer auch bei geschlossener App |
| Stripe-Checkout | `location.href` | Chrome Custom Tab | Zahlungsdaten werden nie in der App eingegeben |
| Standort | `navigator.geolocation` | Fused Location Provider | echte Laufzeitberechtigung, grob/fein, Zeitlimit |
| Foto-Auswahl | `<input type=file>` | Android Photo Picker | keine Speicher-Berechtigung nötig |

### Nicht Teil der App

- **Telefonprüfung (SMS-OTP):** verworfen — wie schon in der Web-Version. Die
  Endpunkte `/api/phone/*` existieren im Backend weiter, die App spricht sie
  nicht an. Ein späterer Einbau beginnt bei einem neuen `PhoneRepository` gegen
  diese Endpunkte.
- **Admin-Tool** (`frontend/admin.html`): bleibt Web-Werkzeug für den Betreiber
  und ist nicht Teil der Nutzer-App.

---

## Berechtigungen

| Berechtigung | Wofür | Wann erfragt |
|---|---|---|
| `INTERNET` | REST-API, Foto-Upload | — |
| `ACCESS_COARSE/FINE_LOCATION` | Umkreissuche | beim ersten Öffnen des Decks |
| `CAMERA` | Verifizierungs-Selfies | beim Start der Verifizierung |
| `POST_NOTIFICATIONS` | neue Nachrichten | beim Einschalten im Konto |

Ohne Standortfreigabe wird eine gespeicherte GPS-Position gelöscht; serverseitig
greift dann die Koordinate der Postleitzahl.
