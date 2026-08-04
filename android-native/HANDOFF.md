# HANDOFF — native Android-App

Stand: **03.08.2026**, Commit `4cf43dd` (gepusht, VPS deployt, Arbeitsverzeichnis sauber).
Für Aufbau, Build-Befehle und die Migrationstabelle siehe [README.md](README.md) —
hier steht nur, was daraus *nicht* hervorgeht.

---

## Wo das Projekt steht

Die browserbasierte Android-App (TWA in `android/`) wurde vollständig durch eine
native App in `android-native/` ersetzt: 73 Kotlin-Dateien, ~10.800 Zeilen,
Kotlin + Jetpack Compose + Material 3, MVVM + Repository, Hilt, Room, Retrofit,
CameraX, WorkManager. Kein WebView, kein HTML/CSS/JS. Das FastAPI-Backend blieb
unverändert — die App spricht denselben REST-Vertrag wie das Web-Frontend.

| | |
|---|---|
| applicationId | `flexr.social.app` (unverändert, Play-Store-Kontinuität) |
| Version | `2.0.9`, versionCode **15** (TWA-Stand war 5) |
| compileSdk / targetSdk / minSdk | 36 / 36 / 26 |
| Signatur | bestehender Upload-Key `android/android.keystore`, SHA-256 `BC:64:AD:3F:…:14:0E:79:80` |

**Offen: der Play-Store-Upload.** Das signierte Bundle für `2.0.9` liegt unter
`app/build/outputs/bundle/prodRelease/app-prod-release.aab` (Stand 04.08.2026,
Signatur `META-INF/FLEXR.RSA`), neu zu bauen mit
`./gradlew :app:bundleProdRelease` (siehe Build-Umgebung unten). Die nie
hochgeladene `2.0.8` ist damit übersprungen.

**Neu in 2.0.9.** Das Swipe-Deck folgt einer Änderung des Suchumkreises sofort.
Bis `2.0.8` las der Swipe-Bildschirm Radius und Gym nur einmal beim Erzeugen des
ViewModels; da ihn die untere Navigation am Leben hält (`saveState`/
`restoreState`), blieb dieser Stand bis zum Neustart der App stehen.

**Neu in 2.0.7/2.0.8 — die Standortberechtigung ist weg.** Die Umkreissuche geht seit
dieser Fassung von der Adresse des eingetragenen Gyms aus, nicht mehr von der
Geräteposition. Entfallen sind damit `ACCESS_COARSE_LOCATION`,
`ACCESS_FINE_LOCATION`, das Feature-Flag `android.hardware.location.gps`, die
Abhängigkeit `play-services-location` und `LocationRepository`. Für die
**Datensicherheitserklärung in der Play Console** heißt das: der Abschnitt
Standort entfällt ersatzlos — das ist beim Upload mit anzupassen, sonst weicht
die Angabe vom tatsächlichen Verhalten ab.

---

## Was vor der Veröffentlichung noch fehlt

1. **Die App lief noch nie auf einem Gerät.** Sie ist gebaut, Unit-Tests sind grün —
   aber es gab weder Emulator noch angeschlossenes Telefon. Vor dem Produktions-Rollout
   gehört ein interner Test-Track oder eine lokale Installation dazu. Kernwege:
   Registrierung inkl. Foto-Upload, Swipe, Chat, Verifizierung.
   Auf dieser Maschine ist das nicht nachholbar: Das Bubblewrap-SDK enthält weder
   `emulator` noch System-Images, und `adb devices` bleibt leer.
2. **Datensicherheitserklärung in der Play Console ergänzen:** Standort (grob und
   genau) sowie Kamera. In der TWA liefen diese Berechtigungen über Chrome, die
   native App fordert sie selbst an.

---

## Nicht offensichtliche Entscheidungen

**Room ist Single Source of Truth für Matches und Chats.** Die Oberfläche liest
ausschließlich aus der Datenbank, das Netz füllt sie nach. Wer Listen "direkt vom
Server" rendern will, bricht die Offline-Fähigkeit.

**Zeitstempel des Backends sind naives UTC.** `datetime.utcnow()` liefert keinen
Offset. `core/common/ServerTime` interpretiert fehlende Offsets deshalb explizit
als UTC — sonst wäre z. B. eine stundengenaue Chat-Sperre um den lokalen Offset
verschoben. Dieselbe Falle steckt serverseitig in `stripe_client.py`.

**Das Gym wird als volles Label gespeichert** (`Name — Straße 1, 1100 Wien`).
Nur das erkennt `gyms.gym_exists_for_profile()` als gültig; der bloße Name gilt
ausschließlich für Bestandsprofile.

**Der `AuthHeaderInterceptor` hängt Header nur an `/api/`-Pfade.** Ein
Authorization-Header auf einer Presigned-S3-URL würde die Signatur ungültig machen.

**Bewusste Abweichungen vom Web** (Begründungen in der README-Tabelle): keine
Browser-Dialoge (Material-3-Dialoge), keine Marketing-Landingpage, Stripe im
Custom Tab, Fused Location Provider statt `navigator.geolocation`, Android Photo
Picker statt File-Input.

**Das Emoji-Panel ist seit 03.08.2026 auch nativ da** — vorher galt die
Systemtastatur als ausreichend. Katalog und Einfügelogik liegen in
`core/designsystem/component/EmojiPicker.kt` und spiegeln `initEmojiPicker` im
Web-Frontend: dieselbe Liste, Einfügen an der Cursorposition, Auswahl wird
ersetzt, Längenlimit gilt. `FlexrTextField` schaltet es über `emojiPicker = true`
frei (Bio in Konto und Registrierung), der Chat baut es in seine Eingabezeile
ein. Weil die Cursorposition gebraucht wird, hält das Feld intern einen
`TextFieldValue` und gibt nach außen weiterhin nur den Text.

**Die Telefonprüfung (SMS-OTP) ist bewusst draußen** — im Web ebenfalls verworfen.
Die Endpunkte `/api/phone/*` existieren im Backend weiter. Ein späterer Einbau
beginnt bei einem neuen `PhoneRepository` gegen diese Endpunkte.

**Das App-Icon ist seit 31.07.2026 das FX-Zeichen, kein Vektor mehr.** Vorlage ist
`frontend/brand/app-icon-fx-1254.png`; wegen Verläufen und Glow lässt es sich nicht
als `<vector>` nachbauen. Alle Größen — Android-Mipmaps, Splash-Symbol, PWA-Icons,
Favicon, Play-Store-Kachel — erzeugt `frontend/brand/build_icons.py` in einem Lauf,
Details in `frontend/brand/README.md`. Die Hantel-Vektoren
`ic_launcher_foreground.xml`, `ic_launcher_monochrome.xml` und `ic_splash_logo.xml`
sind entfallen. Nur das In-App-Symbol (`core/designsystem/icon/FlexrIcons`) zeigt
noch die Hantel.

**Das Splash-Symbol ist kleiner skaliert als das Launcher-Icon.** Der
Android-12-Splash zeigt von der 288dp-Fläche nur einen Kreis von 192dp
Durchmesser. Das FX ist breiter als hoch; maßgeblich ist deshalb seine halbe
Diagonale, nicht die Breite — daher `TILE_ON_SPLASH = 0.67` gegen
`TILE_ON_CANVAS = 0.769` beim Launcher.

**Coil bekommt in `FlexrApplication` einen eigenen ImageLoader mit
`respectCacheHeaders(false)`.** Ohne den richtet sich Coil nach den
HTTP-Cache-Headern; R2 lieferte lange gar keine, wodurch praktisch jede Anzeige
eines Fotos ein Netz-Roundtrip war. Die Objektschlüssel sind UUIDs und werden nie
überschrieben — ein geladenes Bild bleibt gültig. Serverseitig setzt
`storage.set_photo_cache_control()` den Header zusätzlich.

**Die Wortmarke folgt `frontend/brand/README.md`:** FLEX in Kreideweiß, das **R** in
Signalrot `#E8412B`. Das orange X im HTML-Header der Web-App ist laut Markendokument
überholt.

---

## Backend-Änderung in diesem Zug (bereits live)

`stripe_client.py` übergab beim Checkout `trial_period_days=30` und kündigte damit
einen **neuen** 30-Tage-Zeitraum ab Zahlung an — die Gratiszeit verdoppelte sich
faktisch. Jetzt geht das feststehende `trial_ends_at` des Kontos als `trial_end`
an Stripe: nur der Rest ist gratis, danach beginnt das Abo sofort.

Randfälle: Probemonat abgelaufen → kein Trial. Weniger als 48 h Rest → ebenfalls
kein Trial, weil Stripe `trial_end` erst ab 48 h Vorlauf akzeptiert.
Abgedeckt von `backend/tests/test_billing_trial.py` (5 Tests, grün).

Wirkt für App **und** Web-Version gleichermaßen.

---

## Zustand der Test-Suites

**Android:** `./gradlew :app:testProdDebugUnitTest` — grün.

**Backend:** `venv/bin/python -m pytest` — **120 grün**. Die elf zuvor roten
Deck-Tests hat `2f76147` an die Foto-Pflicht angepasst: `get_deck()` überspringt
Profile ohne freigegebenes Foto (`if not profile.photos: continue`), die Tests
legten über `conftest.register_user()` aber Nutzer ohne Fotos an — das Deck war
damit immer leer.

**Der lokale `backend/venv` löst sich wiederholt auf.** Am 31.07.2026 fehlten in
`site-packages` sämtliche `.py`-Dateien, am 03.08.2026 enthielt der Baum überhaupt
keine Datei mehr, nur noch leere Verzeichnisse. Ursache ungeklärt; der venv liegt
nicht im Git. Wiederherstellen kostet eine Minute:

```bash
cd backend && rm -rf venv && python3 -m venv venv && venv/bin/pip install -r requirements-dev.txt
```

---

## Build-Umgebung

Die Toolchain stammt aus dem alten Bubblewrap-Setup und wird weiterverwendet:

```bash
export JAVA_HOME=$HOME/.bubblewrap/jdk/jdk-17.0.11+9
export ANDROID_HOME=$HOME/.bubblewrap/android_sdk
cd android-native && ./gradlew :app:bundleProdRelease
```

Der Release-Build liest das Keystore-Passwort aus `android/KEYSTORE-CREDENTIALS.txt`
(gitignored) oder aus `-Pflexr.keystorePassword`. Ohne die Datei entfällt die
Signatur-Konfiguration stillschweigend — dann entsteht ein unsigniertes Artefakt.

`android/` (TWA, Bubblewrap, `build.sh`) ist abgelöst und sollte nicht mehr gebaut
werden. `frontend/.well-known/assetlinks.json` wird für die native App nicht mehr
gebraucht.
