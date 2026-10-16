# HANDOFF — native Android-App

Stand: **16.10.2026**, Version 2.7.35 / versionCode 147. Der jüngste
Abschnitt steht oben, ältere folgen darunter. Fassungen zwischen dem
16.09. und dem 04.10. sowie 2.7.29 bis 2.7.34 sind nur im Kommentar am
`versionCode` in `app/build.gradle.kts` und in der Haupt-`HANDOFF.md`
beschrieben.
Für Aufbau, Build-Befehle und die Migrationstabelle siehe [README.md](README.md) —
hier steht nur, was daraus *nicht* hervorgeht.

---

## Play-Console-Hinweise: Edge-to-Edge und große Displays, 16.10.2026 (2.7.35)

**2.7.35 statt 2.7.34 hochladen** (enthält 2.7.34). Anlass: die Hinweise
„Für deinen nächsten Release“ der Play Console zu 2.7.34 und der
Richtlinienstatus „App muss auf API-Level 36 ausgerichtet sein“.

* **API 36:** Die native App zielt seit der ersten Fassung auf API 36. Die
  Meldung kommt von der alten TWA 1.0.4 (versionCode 5, API 35) in Produktion
  und erledigt sich mit der ersten nativen Produktionsversion.
* **Randlose Anzeige / eingestellte APIs:** Der Release-Dex von 2.7.34 zeigte
  (dexdump plus R8-Mapping), dass `Window.setStatusBarColor`,
  `setNavigationBarColor` und der Cutout-Modus `SHORT_EDGES` nur aus
  `enableEdgeToEdge()` von androidx.activity kamen (`EdgeToEdgeApi26/28/29/30`).
  Ein Update hilft nicht, 1.13.0 enthält sie auch noch. Jetzt
  `MainActivity.drawBehindSystemBars()`: `setDecorFitsSystemWindows(false)`,
  kein Kontrastschleier, helle Symbole. Durchsichtig sind die Leisten bis
  Android 14 über das Theme. Im Dex von 2.7.35 sind die drei Aufrufe weg;
  `setDecorFitsSystemWindows` bleibt (nicht eingestellt, nutzt auch Compose
  für jeden Dialog, `DialogWrapper`).
* **Ausrichtung:** `screenOrientation="portrait"` ist aus dem Manifest
  entfernt. `MainActivity.lockPortraitOnPhones()` setzt das Hochformat zur
  Laufzeit nur bei kleinster Breite unter 600 dp. Ändert sich die kleinste
  Breite (Foldable auf-/zuklappen), baut Android die Activity neu auf
  (`smallestScreenSize` fehlt bewusst in `configChanges`).
* **Tablets:** `AppFrame` in `FlexrApp.kt` hält die Oberfläche in höchstens
  600 dp Breite mittig, der Hintergrund läuft über die ganze Fläche, dazu
  der seitliche Rand der Kamera-Aussparung (ab Android 15 auch im Querformat
  im Fenster). Unter 600 dp ändert sich nichts.

Geprüft im Emulator (API 35, lokales Backend gegen eine SQLite-Kopie):
Handy bleibt bei gedrehtem Gerät im Hochformat, Optik unverändert
(Statusleiste, Gestenleiste, 3-Tasten-Navigation). Tablet (`wm size
1600x2560`, `wm density 320`, sw 800 dp) hoch und quer: Login, Verifizierungs-
Gate, Deck mit Karte, Matches, Chats, Chat mit Tastatur, Konto mit Tastatur.
Entwürfe (Bio, Chat) überstehen das Drehen und den Wechsel Tablet → Handy.
Die 3-Tasten-Symbole sind im Emulator dunkelgrau auf dunklem Grund, im
alten Stand mit `enableEdgeToEdge()` genauso (A/B-Build, gleiche Pixelwerte),
also keine Folge dieser Änderung. Android 8 bis 14 nicht im Emulator geprüft
(nur das API-35-Image vorhanden).

* 77 Unit-Tests grün, Lint 0 Fehler (122 Warnungen, keine in den geänderten
  Dateien).

| 2.7.35 / 147 | SHA-256 | Größe |
|---|---|---|
| AAB (Play Console) | `18dfa18b4902b09ac24f6c7f3dfbbb0d35cc19060f45578d452ec50ab7fc6a3f` | 8.605.303 Bytes |
| APK (Testgerät) | `5c892bf4f7f87b56091bd3a890923af696ca14fab02069ce475e70e0c38bd4ed` | 4.459.278 Bytes |

aapt2: 147 / 2.7.35, targetSdk 36, keine Ausrichtungs- oder Größensperre im
Manifest; Signer SHA-256 `BC:64:AD…79:80` (Upload-Key) für AAB und APK
geprüft. Liegt in `release-2.7.35/` (gitignored), dort auch
`tablet-uebersicht-2.7.35.png`.

---

## Datenschutz-Kurzfassung Fassung 2026-10-14, 14.10.2026 (2.7.28)

**2.7.28 statt 2.7.27 hochladen** (enthält 2.7.27). Die Datenschutzerklärung
hat eine neue Fassung 2026-10-14: Eine automatisch markierte Nachricht bleibt
nach dem Auflösen des Matches bis zur Prüfung stehen, höchstens 30 Tage nach
dem Senden (Haupt-`HANDOFF.md`, Sitzung 14.10.2026 (11)/(12)).

* `LegalContent.kt`: „Stand: 14. Oktober 2026“, neuer Punkt unter
  „5. Speicherdauer“. Sonst keine Änderung.
* Play Console: keine neue Datenart, nur Speicherdauer (`PLAY-CONSOLE.md`).
* 63 Unit-Tests grün, Lint 0 Fehler (109 Warnungen, wie bisher).

| 2.7.28 / 140 | SHA-256 | Größe |
|---|---|---|
| AAB (Play Console) | `1ad509c8fd8223dad03928987b344bb0542648223fca9e337ef0b4bd25e50693` | 8.537.117 Bytes |
| APK (Testgerät) | `b26847e6eaac4df1b2d57876a5ed18932e914475cd5350ec23badde2b9818a6a` | 4.421.198 Bytes |

aapt2: 140 / 2.7.28, targetSdk 36; Signer SHA-256 `BC:64:AD…79:80`
(Upload-Key) für AAB und APK geprüft. Liegt in `release-2.7.28/` (gitignored).

---

## Ausweis-Einreichung übersteht eine verlorene Antwort, 14.10.2026 (2.7.27)

**2.7.27 statt 2.7.26 hochladen.** Bugfix-Runde 5 (Haupt-`HANDOFF.md`,
Sitzung 14.10.2026 (10)): Am 13.10. kam beim Einreichen eines Ausweises (Web)
ein 504, der Server hatte aber eingereicht. Jeder weitere Versuch scheiterte
schon beim Presign („Für diesen Schritt läuft keine offene Verifizierung.“).
Auf dem Handy reicht dafür ein Funkloch im falschen Moment.

* `VerificationRepository.submitDocument` fragt bei jedem Fehler (Upload,
  Presign, Einreichen) `GET /verification/status` nach; steht dort
  `submitted`, gilt die Einreichung als gelungen, sonst kommt der
  ursprüngliche Fehler. `CancellationException` geht unverändert durch.
* Drei neue Tests in `VerificationRepositoryTest` (verlorene Antwort,
  zweiter Versuch nach Einreichung, echter Fehler bleibt Fehler); 63
  Unit-Tests grün, Lint 0 Fehler (109 Warnungen, wie bisher). Gerätetest
  steht aus.

| 2.7.27 / 139 | SHA-256 | Größe |
|---|---|---|
| AAB (Play Console) | `501b6bdb6adf08591dc3b5480ce96c16082626006b815c70da09a0af7fc081ea` | 8.537.013 Bytes |
| APK (Testgerät) | `f6407d8da551833b8443be1bab32b70e7eb713c3a7448b2601c88bfc537e141a` | 4.421.202 Bytes |

aapt2: 139 / 2.7.27, targetSdk 36; Signer SHA-256 `BC:64:AD…79:80`
(Upload-Key) für AAB und APK geprüft. Liegt in `release-2.7.27/` (gitignored).

---

## Abgelehnte Fotos zählen nicht zur Pflichtzahl, 14.10.2026 (2.7.26)

**2.7.26 statt 2.7.25 hochladen.** Der Server verlangt für
`/verification/start` seit `d0a2c4e` drei **gültige** Fotos (abgelehnte zählen
nicht mehr). Der Prüfbildschirm bis 2.7.25 zählte alle Fotos, bot dann keinen
Ersatz-Upload an und lief beim Start in den 400 - mit 2.7.26 nicht mehr.

* `VerificationGateUiState.photoCount` zählt nur Fotos mit Status ≠ REJECTED,
  neu `hasRejectedPhoto`. `MissingPhotoContent` zeigt dann
  `vgate_photo_body2_rejected` („Ein Foto wurde von der Moderation abgelehnt
  …“) statt „Beim Anlegen deines Profils hat der Upload nicht geklappt“.
* Neuer Test `abgelehntes Foto zaehlt nicht und wird benannt`; 60 Unit-Tests
  grün, Lint 0 Fehler (109 Warnungen, wie bisher). Gerätetest steht aus.

| 2.7.26 / 138 | SHA-256 | Größe |
|---|---|---|
| AAB (Play Console) | `ba674d70e08ab16d4e1af21a2f083290d987731f1f0a06b2d2240558ce1e467b` | 8.536.811 Bytes |
| APK (Testgerät) | `51c9358eb28b5d7e18f8d9f08773cb9bd9f7b50ffdf5b374333cd2cca967b8f3` | 4.421.198 Bytes |

aapt2: 138 / 2.7.26, targetSdk 36; Signer SHA-256 `BC:64:AD…79:80`
(Upload-Key) für AAB und APK geprüft. Liegt in `release-2.7.26/` (gitignored).

---

## Löschdialog nennt das Abo, 14.10.2026 (2.7.25)

**2.7.25 statt 2.7.24 hochladen.** Bugfix-Runde 3 (Haupt-`HANDOFF.md`,
Sitzung 14.10.2026 (7)): Eine Kontolöschung beendete ein laufendes Abo nicht.
Ein Stripe-Abo beendet der Server seither selbst zum Periodenende, ein
Play-/App-Store-Abo kann er nicht kündigen.

* `DeleteAccountDialog` bekommt `aboHinweis` (Standard `null`, der Aufruf aus
  dem Verifizierungs-Gate bleibt unverändert). `AccountScreen` setzt ihn bei
  laufendem Premium: `delete_sub_stripe` mit Stripe-Abo („endet damit zum Ende
  des bezahlten Zeitraums“), sonst `delete_sub_store` („Die Löschung beendet es
  nicht – kündige es bitte dort“). Halbfett unter dem Erklärtext, DE/EN.
* 59 Unit-Tests grün, Lint 0 Fehler (109 Warnungen, wie bisher). Gerätetest
  steht weiter aus.

| 2.7.25 / 137 | SHA-256 | Größe |
|---|---|---|
| AAB (Play Console) | `4f5127a83010836ea23d2ee9a23180d2e42e7acbf891b762360c74fe05b16688` | 8.536.989 Bytes |
| APK (Testgerät) | `b278a49dae617ade48a4df7a259854a23a7b58bc1587902465d1d6ede5fb0875` | 4.420.814 Bytes |

aapt2: 137 / 2.7.25, targetSdk 36; Signer SHA-256 `BC:64:AD…79:80`
(Upload-Key) für AAB und APK geprüft. Liegt in `release-2.7.25/` (gitignored).

---

## Prüfrunde, 13.10.2026 (2.7.24)

Reine Textkorrekturen, kein Verhalten geändert. **2.7.24 statt 2.7.23 hochladen.**

* Der Knopf im Konto heißt jetzt **„Abo verwalten / kündigen“** (EN „Manage /
  cancel subscription“). AGB 9 a, FAQ und Rücktrittsseite nennen ihn seit
  jeher so („Der Knopf ‚Abo verwalten / kündigen‘ in der App führt dich direkt
  dorthin“), in der App hieß er nur „Abo verwalten“. Die Web-App zieht mit.
* `verify_privacy_note`: Das Selfie wird mit Profilfotos **und Ausweis**
  verglichen (stand „nur mit deinen Profilfotos“, EN „with your profile photos
  only“).
* Gedankenstriche statt Bindestrich in `register_err_consent` und
  `startup_offline_text`; deutsche Anführungszeichen „…“ in der
  AGB-/Richtlinien-Kurzfassung (`LegalContent.kt`, vorher „…\").
* 59 Unit-Tests grün, Lint 0 Fehler (109 Warnungen). Gerätetest steht weiter aus.

| 2.7.24 / 136 | SHA-256 | Größe |
|---|---|---|
| AAB (Play Console) | `061a5510bdbd16bd0f179aed841f45dfa47b7a77215e1a9c77b6ded10d47d2d2` | 8.535.946 Bytes |
| APK (Testgerät) | `1a1099a1e60be5f95e09243d0a4edc53e9c0a33eecc4c310d44a3a40eaa0e9c8` | 4.420.114 Bytes |

aapt2: 136 / 2.7.24, targetSdk 36; Signer SHA-256 `BC:64:AD…79:80`
(Upload-Key) für AAB und APK geprüft. Liegt in `release-2.7.24/` (gitignored).

---

## Suchumkreis bis 580 km und Startboost, 13.10.2026 (2.7.23)

Zieht nach, was Web und Backend am selben Tag bekamen (Haupt-`HANDOFF.md`,
Sitzungen 13.10.2026): Der Server erlaubt bis 580 km statt 250, und bis
31.12.2026 hat jedes Konto den vollen Umkreis, auch ohne Premium.

* `AccountViewModel.MAX_RADIUS_KM = 580`. Der Regler läuft **quadratisch**
  (`radiusAusStellung`/`stellungAusRadius` im `companion`, km = 2 + (max−2)·p²,
  dieselbe Skala wie Web und iOS). Linear lägen 50 km bei 8 % der Schiene. Der
  Zustand bleibt in km, nur der `Slider` läuft in 0..1. Die Ansage für
  Screenreader kommt per `stateDescription` in km. Der Regler endet wie bisher
  bei `maxSelectableRadiusKm` (nach dem Boost ohne Premium: 50).
* Startboost: `radius_boost_last_day` → `MembershipStatusDto.radiusBoostLastDay`
  → `Membership.radiusBoostLastDay` (`LocalDate?`, Standard `null`) →
  `AccountUiState.radiusBoostLastDay`. Steht ein Datum, zeigt `AccountScreen`
  unter dem Regler den limettengrünen Hinweis (`account_radius_boost`), und die
  Paywall zeigt „Voller Suchumkreis bis 580 km – bis 31.12.2026 für alle frei“
  (`premium_feature_radius_boost`). Ab Neujahr liefert der Server `null`, beides
  entfällt von selbst.
* Texte: `premium_feature_radius` jetzt 580 km. AGB-Kurzfassung
  (`LegalContent.agb`): Premium bis 580 km und die Startaktion (AGB-Fassung
  2026-10-13, Punkt 7 e).
* Tests: neu `ui/account/RadiusSkalaTest` (Enden, Anteil bei 20/50 km, jeder
  Wert 2..580 und 2..50 übersteht den Weg über die Stellung, Kappen). 59 Tests
  grün, Lint 0 Fehler (109 Warnungen).
* **Build auf diesem Rechner geht doch:** JDK 17 und Android-SDK liegen unter
  `~/.bubblewrap/` (`jdk/jdk-17.0.11+9`, `android_sdk` mit `android-36`).
  `local.properties` → `sdk.dir=/home/blktomcat/.bubblewrap/android_sdk`
  (zeigte auf `/home/blacktomcat88/…`). Aufruf:
  `JAVA_HOME=~/.bubblewrap/jdk/jdk-17.0.11+9 ./gradlew --no-daemon
  :app:bundleProdRelease :app:assembleProdRelease`. Der Keystore wird aus
  `../android/` gelesen.

| 2.7.23 / 135 | SHA-256 | Größe |
|---|---|---|
| AAB (Play Console) | `3676e235ac8d93046ea6f3d2d12c46fb1ae5ab8f00352ac6cf9c43b1b5e6669e` | 8.535.850 Bytes |
| APK (Testgerät) | `089fcf505f9a5030668e403e09f03d75837562640afeab5a78e76e82d87de1df` | 4.420.054 Bytes |

aapt2: 135 / 2.7.23, targetSdk 36; Signer SHA-256 `BC:64:AD…79:80`
(Upload-Key), für AAB und APK geprüft. Liegt in `release-2.7.23/`
(gitignored). **2.7.23 statt 2.7.22 hochladen.** Am Gerät noch nicht
geprüft, hier gibt es keinen Emulator.

---

## Durchsicht vor der Veröffentlichung, 04.10.2026 (2.7.22)

Die Play-Store-Veröffentlichung ist für Mitte Oktober 2026 geplant. Geprüft:

* **Play-Anforderungen erfüllt:** Ziel-SDK 36, Play Billing 8, alle 16 nativen
  Bibliotheken im Bundle mit 16-KB-Seitenausrichtung (ELF-`p_align` 16384,
  gemessen an 2.7.21), Edge-to-Edge, vorausschauende Zurück-Geste.
  `assetlinks.json` führt Play-Signing- und Upload-Key.
* **Gleichstand mit dem Web:** Der Freischaltungs-Schirm lädt bei jeder Rückkehr
  in die App neu (`LifecycleEventEffect(ON_RESUME)`), der Mail-Link öffnet die
  App als App Link. Die Lücken, die die Web-App vom iPhone-Home-Bildschirm am
  04.10. hatte, gibt es hier nicht. Play-Käufe werden bestätigt (Server, mit
  Rückfall in der App), ausstehende Zahlungen abgewartet, frühere Käufe
  automatisch wiederhergestellt.
* **Nachgezogen:** Die Datenschutz-Kurzfassung (`LegalContent.datenschutz`)
  hinkte der Web-Fassung hinterher — die verschlüsselten Sicherungskopien
  (Fassung 2026-10-02) und Google Play als Empfänger bei Käufen in der App
  (Web seit 21.09.) fehlten. Ergänzt, dazu ein Vorspann mit Stand und dem
  Hinweis, dass der vollständige Text auf flexr.social maßgeblich ist (wie bei
  Nutzungs- und Strafverfolgungsrichtlinien).
* **`PLAY-CONSOLE.md` neu gefasst:** stand auf 2.4.1 und behauptete u. a., es
  gebe keinen Push-Dienst. Abschnitt 0 sammelt, was seither in der Console
  anzugeben ist (FCM-Token, Kaufverlauf, Geräte-ID, sexuelle Orientierung,
  Prüfzugang mit freigeschaltetem Testkonto, Web-Adresse zur Kontolöschung).
* `local.properties` zeigte wieder auf `/home/blktomcat/…` — korrigiert
  (Datei ist nicht im Git).

---

## FLEXR Premium: die drei Zusatzfunktionen, 16.09.2026

Backend und Web-App haben sie seit dem 10.09.2026, die nativen Clients hatten
bis jetzt nur den Werbetext auf der Paywall. Nachgezogen sind alle drei:

1. **Premium-Abzeichen** — ein gefüllter Stern in Plate-Orange neben dem Namen,
   in Swipe-Karte, Match-/Chatliste, Chat-Kopfzeile und Kontobereich.
   `PremiumBadge` steht bewusst **ohne** runden Grund neben dem blauen
   Verifiziert-Haken: zwei gleich gebaute Plaketten nebeneinander liest niemand
   auseinander (im Web dieselbe Unterscheidung, `.premium-badge` trägt nur
   `color`).
2. **Letzten Swipe zurücknehmen** — kleiner runder Knopf links neben „Nope",
   `POST /api/swipes/rewind`. Er erscheint **nur mit Premium**; ohne Abo steht
   dort nichts statt eines gesperrten Knopfes. Die Knopfreihe ist der
   meistbenutzte Ort der App, ein dauerhaft totes Element daneben wäre eine
   tägliche Belästigung.
3. **„Wer dich geliket hat"** — Karte über der Matchliste (Zahl im Kreis) und
   ein eigener Bildschirm dahinter (`Routes.INCOMING`, `ui/incoming/`). Ohne
   Premium liefert der Server die **Anzahl ohne Profile**; die Ansicht zeigt
   dann „3 Leute warten auf dich" plus den Hinweis, dass dieselben Leute
   ohnehin im Deck auftauchen — kein Fehlerbildschirm. Ohne offene Likes bleibt
   die Karte ganz weg, eine „0" wäre eine Enttäuschung ohne Anlass.

**Room-Schema 2 → 3**: `MatchEntity.isPremium` ist dazugekommen, damit das
Abzeichen auch in der offline gespiegelten Match-/Chatliste steht. Keine
Migration nötig — die Tabelle ist reiner Cache
(`fallbackToDestructiveMigration(dropAllTables = true)` in `DatabaseModule`).

**Das Restkontingent zieht jetzt nach.** `SwipeResultDto` und `RewindResultDto`
liefern `likes_remaining` mit; `BillingRepository.updateLikesRemaining()`
schreibt es in den zwischengespeicherten `Membership`, und `MainViewModel`
beobachtet diesen Fluss. Vorher zeigte die Pille im Kopf den Stand vom
App-Start, bis sich jemand neu anmeldete — ein zweiter `/api/billing/status`
nach jedem Like wäre die teure Alternative gewesen.

**Alles hängt weiterhin an `PREMIUM_ENABLED` am Server.** Solange der Schalter
aus ist, ist `is_premium` für jeden falsch: kein Abzeichen, kein
Zurücknehmen-Knopf, und die Karte zeigt den gesperrten Text. Es gibt in der App
keinen zweiten Ort, an dem sich das entscheidet.

**Geprüft:** `:app:compileProdReleaseKotlin` und
`:app:testProdReleaseUnitTest` grün, **49 Tests, 0 Fehler** — zwei davon neu
für das Zurücknehmen (Deck wird neu geladen; ein abgelehntes Zurücknehmen
lässt das Deck stehen). Auf einem Gerät ausprobiert ist noch nichts.

**Noch nicht nachgezogen:** der Like-Zähler unter dem Deck, den die Web-App
dort führt. Auf Android steht die Restzahl bereits in der Statuspille im Kopf
(`status_likes_left`) — ein zweiter Zähler wenige Zentimeter darunter wäre
Dopplung, keine Parität. Wenn er doch gewünscht ist, gehört er als Zeile unter
die Knopfreihe, samt „Unbegrenzt liken"-Knopf wie im Web.

## Wo das Projekt steht

Die browserbasierte Android-App (TWA in `android/`) wurde vollständig durch eine
native App in `android-native/` ersetzt: 73 Kotlin-Dateien, ~10.800 Zeilen,
Kotlin + Jetpack Compose + Material 3, MVVM + Repository, Hilt, Room, Retrofit,
CameraX, WorkManager. Kein WebView, kein HTML/CSS/JS. Das FastAPI-Backend blieb
unverändert — die App spricht denselben REST-Vertrag wie das Web-Frontend.

| | |
|---|---|
| applicationId | `flexr.social.app` (unverändert, Play-Store-Kontinuität) |
| Version | **`2.7.18`, versionCode 130** (Stand 22.09.2026, gebaut und in `release-2.7.18/`; Upload in die Play Console durch den Nutzer) |
| compileSdk / targetSdk / minSdk | 36 / 36 / 26 |
| Signatur | bestehender Upload-Key `android/android.keystore`, SHA-256 `BC:64:AD:3F:…:14:0E:79:80` |

**Offen: der Play-Store-Upload.** Das signierte Bundle entsteht unter
`app/build/outputs/bundle/prodRelease/app-prod-release.aab`, zu bauen mit
`./gradlew :app:bundleProdRelease` (siehe Build-Umgebung unten). Ohne
`android/KEYSTORE-CREDENTIALS.txt` entfällt die Signatur stillschweigend — das
Ergebnis ist dann nicht hochladbar, also nach dem Build gegenprüfen:
`unzip -l app-prod-release.aab | grep META-INF` muss `FLEXR.RSA` zeigen.

**Neu in 2.2.8 — der Wartebildschirm war eine Sackgasse.** Wer während der
Prüfung freigeschaltet wurde, drückte „Status aktualisieren" und bekam nichts:
keine Meldung, keinen Wechsel in die App. `refresh()` lud das Profil und baute
darauf, dass die App dem Sitzungszustand folgt — `MainViewModel` beobachtet aber
nur `isLoggedIn`, nie das Profil. Die Freischaltung steht ohnehin in der
Statusantwort selbst (`account_activated`); sie landet jetzt als
`VerificationGateUiState.isActivated` im UI-Zustand, und der Bildschirm stößt
daraufhin `loadSession()` an. Weil der Verifizierungsgraph nur über einen neu
geladenen Sitzungszustand verlassen wird, ist das der einzige Weg heraus — der
sichtbare „Weiter zu FLEXR"-Knopf ist der Ausweg, falls das Nachladen an einem
Netzfehler scheitert. Regressionstest: `VerificationGateViewModelTest`.

**Ebenfalls in 2.2.8 — der gesperrte Knopf war unsichtbar.** `FlexrButton` legte
im gesperrten Zustand `alpha 0.4` über den orangen Verlauf; auf `#121212`
verschwand er dabei praktisch vollständig. Gemeldet wurde das zuerst bei der
Registrierung, dann beim Login. Statt zu verblassen wechselt der Knopf jetzt die
Farbe: deckende Stahlfläche, 1 dp Rand, `chalkDim` als Schrift. Der Ladezustand
bleibt davon unberührt und sieht weiter nach Aktion aus. Der Login-Knopf ist
zusätzlich immer tippbar (`canSubmit` ist entfallen) — ein gesperrter Knopf sagt
nicht, was fehlt, `login()` nennt den Grund beim Tippen. Das entspricht dem
Verhalten der Registrierung.

**Neu in 2.2.0 — die Alters- und Identitätsprüfung.** Ein neu registriertes Konto
ist angelegt, aber nicht nutzbar, bis ein Mensch Profilfoto, Verifizierungs-Selfie
und einen amtlichen Lichtbildausweis verglichen und das Geburtsdatum abgeglichen
hat. Die App bildet den Ablauf vollständig ab:

* `AppState.NeedsVerification` ist ein eigener Navigationsgraph — ohne
  Freischaltung existiert die untere Navigation gar nicht, statt in einen 403 zu
  laufen. Er steht bewusst VOR der Paywall: Der Probemonat startet erst mit der
  Freischaltung.
* `ui/verification/VerificationGateScreen` zeigt den Stand (Schritt 1, Schritt 2,
  in Prüfung, Neu-Upload nötig, abgelehnt) samt Prüfgrund aus dem festen Katalog.
  Ausloggen und Kontolöschung bleiben dort erreichbar — sonst wäre eine
  abgelehnte Prüfung eine Sackgasse.
* `ui/verification/DocumentScreen` nimmt den Ausweis über die **Rückkamera** auf
  (Selfies laufen weiter über die Frontkamera). Die Kamera öffnet erst auf
  Tippen eines Aufnahmeplatzes. Personalausweis und Führerschein verlangen
  Vorder- und Rückseite, der Reisepass nur die Datenseite — welcher Typ was
  braucht, sagt der Server (`document_types`), die App pflegt keine eigene Liste.
* Die Aufnahmen gehen per Presigned PUT direkt in einen **privaten** Bereich des
  Objekt-Storage und bekommen nie eine öffentliche Adresse.

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

Stand 04.10.2026 — die vollständige Liste der Console-Angaben steht in
[PLAY-CONSOLE.md](PLAY-CONSOLE.md), Abschnitt 0 und 1.

1. **Interner Test-Track vor der Freigabe.** Die App lief seit September auf dem
   Gerät des Betreibers, aber nur der Test-Track prüft genau das, was Nutzer
   bekommen — mit Play Billing (Testkauf) und App-Link-Verifizierung. Auf dieser
   Maschine gibt es weder Emulator noch Gerät (`adb devices` bleibt leer).
2. **Datensicherheit in der Console** nach PLAY-CONSOLE.md: Fotos (inkl.
   Ausweisaufnahme, nicht „flüchtig“), Geräte- oder andere IDs (Geräte-ID,
   FCM-Token), Kaufverlauf, sexuelle Orientierung; Web-Adresse zur Kontolöschung.
3. **App-Zugriff:** ein bereits freigeschaltetes Testkonto für Googles Prüfer
   hinterlegen — ohne kommen sie nicht an der Ausweisprüfung vorbei.
4. **Abo-Produkt** „FLEXR Premium“ in der Console angelegt und aktiv, mit
   derselben Produkt-ID wie im Backend.
5. ~~**Suchumkreis bis 580 km und Startboost**~~ — **erledigt in 2.7.23**
   (Abschnitt oben). Ursprüngliche Notiz (seit 13.10.2026, siehe
   Haupt-`HANDOFF.md`): Der Server erlaubt jetzt bis 580 km (vorher 250) und
   liefert bis 31.12.2026 `max_radius_km = 580` auch ohne Premium. **2.7.22
   kappt das auf 250** (`AccountViewModel.MAX_RADIUS_KM = 250`,
   `status.maxRadiusKm.coerceAtMost(MAX_RADIUS_KM)`), funktioniert also, nur
   eben bis 250 km, und nennt in den Texten noch 250 km. Für den nächsten Build:
   - `MAX_RADIUS_KM = 580` in `AccountViewModel.kt`. Der Regler
     (`valueRange` in `AccountScreen.kt`) ist linear. Die Web-App hat auf eine
     quadratische Skala umgestellt, weil 50 km sonst bei 8 % der Schiene
     lägen (km = 2 + 578·p², `frontend/app/index.html`, `radiusSetzen`).
   - Texte: `premium_feature_radius` in `res/values*/strings.xml` („Voller
     Suchumkreis bis 250 km“) und die AGB-Kurzfassung in
     `ui/legal/LegalContent.kt` („Suchumkreis bis 250 km“), beide auf 580.
     Die AGB haben jetzt die Fassung 2026-10-13 mit der Startaktion als Punkt 7 e.
   - Optional der Startboost-Hinweis unter dem Regler und der Zusatz „bis
     31.12.2026 für alle frei“ am Premium-Vorteil, gesteuert über
     `radius_boost_last_day` (ISO-Datum oder `null`) in
     `MembershipStatusDto`/`Membership`, wie in der Web-App.
   - Ab 01.01.2027 gilt auch in 2.7.22 wieder der alte Zustand ohne Premium:
     Der Server liefert 50, und `account_radius_capped` erscheint, wenn mehr
     gespeichert ist.

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

**Android:** `./gradlew :app:testProdReleaseUnitTest` — 42 Tests in 9 Klassen, grün.

Seit 04.08.2026 sind auch **ViewModels testbar**. Bausteine liegen unter
`app/src/test/java/flexr/social/app/testing/`:

| | |
|---|---|
| `MainDispatcherRule` | ersetzt `Dispatchers.Main`; ohne sie scheitert schon der Konstruktor jedes ViewModels |
| `FakeFlexrApi` | alle 29 Endpunkte, jeder scheitert mit klarer Meldung — ein Test überschreibt nur, was er braucht |
| `FakeSessionStore` | Sitzung im Arbeitsspeicher |
| `FakeMatchDao` / `FakeMessageDao` | Room-DAOs im Arbeitsspeicher, inkl. der Sortierung |
| `TestDaten.kt` | DTO-Bausteine mit Vorgabewerten |

Getestet wird gegen die **echten** Repositories — nur die Retrofit-Schnittstelle
und die Sitzung sind ersetzt. Damit läuft die DTO-Abbildung mit durch die Tests,
statt von einer nachgebauten Fassade verdeckt zu werden.

Dafür musste `SessionStore` zur Schnittstelle werden (Umsetzung:
`DataStoreSessionStore`, gebunden in `di/SessionModule.kt`). Vorher hing daran
der Android-Context, und damit war jedes Repository und jedes ViewModel darüber
in reinen JVM-Tests nicht konstruierbar.

Erster Nutzer: `SwipeViewModelTest` — der Regressionstest zum Deck-Fehler aus
2.0.8. Gegen den Stand vor dem Fix fallen zwei seiner drei Fälle um.

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
