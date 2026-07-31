# HANDOFF — native Android-App

Stand: **31.07.2026**, Commit `98265bf` (gepusht, VPS deployt, Arbeitsverzeichnis sauber).
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
| Version | `2.0.1`, versionCode **7** (TWA-Stand war 5) |
| compileSdk / targetSdk / minSdk | 36 / 36 / 26 |
| Signatur | bestehender Upload-Key `android/android.keystore`, SHA-256 `BC:64:AD:3F:…:14:0E:79:80` |

**Offen: der Play-Store-Upload.** Das Bundle liegt unter
`app/build/outputs/bundle/prodRelease/app-prod-release.aab`
(SHA-256 `c0aa5e0f09749ef3c8eb7e981d6ceb9c42f15a075899ecf07720ac0a8f33154f`).

---

## Was vor der Veröffentlichung noch fehlt

1. **Die App lief noch nie auf einem Gerät.** Sie ist gebaut, Unit-Tests sind grün —
   aber es gab weder Emulator noch angeschlossenes Telefon. Vor dem Produktions-Rollout
   gehört ein interner Test-Track oder eine lokale Installation dazu. Kernwege:
   Registrierung inkl. Foto-Upload, Swipe, Chat, Verifizierung.
2. **Datensicherheitserklärung in der Play Console ergänzen:** Standort (grob und
   genau) sowie Kamera. In der TWA liefen diese Berechtigungen über Chrome, die
   native App fordert sie selbst an.
3. **Elf veraltete Backend-Tests** (siehe unten) — blockieren nichts, sollten aber weg.

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

**Bewusste Abweichungen vom Web** (Begründungen in der README-Tabelle): kein
Emoji-Panel (System-Tastatur), keine Browser-Dialoge (Material-3-Dialoge), keine
Marketing-Landingpage, Stripe im Custom Tab, Fused Location Provider statt
`navigator.geolocation`, Android Photo Picker statt File-Input.

**Die Telefonprüfung (SMS-OTP) ist bewusst draußen** — im Web ebenfalls verworfen.
Die Endpunkte `/api/phone/*` existieren im Backend weiter. Ein späterer Einbau
beginnt bei einem neuen `PhoneRepository` gegen diese Endpunkte.

**Das App-Icon ist aus `android/store_icon.png` pixelweise vermessen**: zwei schmale
äußere Scheiben, zwei breite innere, durchgehender Steg. Ein früherer Nachbau mit
sechs Balken und kurzem Mittelsteg war falsch. Das In-App-Symbol
(`core/designsystem/icon/FlexrIcons`) nutzt dieselbe Form dünner gestrichen, weil
die Balkenstärke des Launcher-Icons bei 22 dp zuläuft.

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

**Backend:** `venv/bin/python -m pytest` — **109 grün, 11 rot**. Die 11 Fehlschläge
sind veraltete Tests, kein Produktfehler: `get_deck()` überspringt Profile ohne
freigegebenes Foto (`if not profile.photos: continue`), die Tests legen über
`conftest.register_user()` aber Nutzer ohne Fotos an — das Deck ist damit immer
leer. Die Produktregel kam nach den Tests dazu. Betroffen sind alle Deck-Tests in
`test_location.py` (5), `test_safety.py` (2), `test_admin.py`, `test_messages.py`,
`test_swipes_and_matches.py`, `test_verification.py`.

Der lokale `backend/venv` war beschädigt (in `site-packages` fehlten sämtliche
`.py`-Dateien, übrig waren nur `__pycache__`-Ordner) und wurde am 31.07.2026
komplett aus `requirements-dev.txt` neu aufgesetzt.

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
