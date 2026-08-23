# HANDOFF — native iOS-App

Stand: **23.08.2026**. Für Aufbau, Build-Befehle und die Migrationstabelle siehe
[README.md](README.md) — hier steht nur, was daraus *nicht* hervorgeht.

---

## Was am 23.08.2026 nachgezogen wurde

Die App stand zuletzt auf dem Stand vom 15.08.2026 (Commit `eb93e15`).
Zwischen diesem Tag und dem 23.08.2026 sind 107 Commits ins Backend, ins
Web-Frontend und in die Android-App gegangen; diese Sitzung hat den für iOS
maßgeblichen Teil davon portiert. Version steht jetzt auf **2.4.9**, gleich
mit Android (`versionCode 37`).

### Vertragsbrüche, die die App sonst kaputt gemacht hätten

1. **`POST /api/billing/checkout` braucht seit 17.08. einen Körper.**
   `{immediate_start, withdrawal_ack}`, beide zwingend `true` (§ 10 und § 18
   Abs. 1 Z 1 FAGG, `CheckoutRequest` in `backend/app/schemas.py`). Die App
   schickte gar keinen — jeder Abo-Abschluss wäre mit **422** gescheitert.
   Neu: `CheckoutConsentSheet` (in `UI/Account/AccountView.swift`) mit zwei
   getrennten, nicht vorangekreuzten Kästchen, Wortlaut identisch mit Web und
   Android. Konto-Bildschirm und Paywall nutzen dasselbe Blatt.
2. **`in_chats` auf `MatchOut`.** Der „Chats"-Tab filterte auf
   `lastMessage != nil`. Nach „Chatverlauf leeren" liefert der Server korrekt
   `last_message: null` — der Chat verschwand dadurch ganz aus der Liste
   statt leer stehen zu bleiben (derselbe Bug, der in Web und Android am
   21.08. behoben wurde). `MatchRepository.conversations` filtert jetzt auf
   `inChats`, `MatchListItem` zeigt bei fehlender Nachricht
   „Chatverlauf geleert".
3. **`DELETE /api/matches/{id}/chat`.** „Chat löschen" rief bislang
   `unmatch` auf und löschte damit Match, Swipe und Verlauf — obwohl der
   Knopf etwas anderes verspricht. Jetzt bleibt das Match bestehen.
4. **`POST /api/auth/reactivate`.** Ein Login auf ein selbstgelöschtes Konto
   antwortet innerhalb der 30-Tage-Karenz mit `403` und
   `detail.code = "account_deleted"`. `FlexrAPIError` trägt jetzt `code`,
   `LoginView` bietet daraufhin die Reaktivierung an statt in einer Sackgasse
   zu enden.
5. **Einwilligungen (`GET/POST /api/profiles/me/consents[/revoke|/grant]`).**
   Neu im Konto unter „Datenschutz & Sicherheit": aufklappbare Liste mit
   Sofort-Widerruf und Rücknahme des Widerrufs (Art. 7 Abs. 3 DSGVO). Wie in
   Web und Android erscheint pro Art nur die **neueste** Zeile, und
   `immediate_start` gar nicht — die maßgebliche FAGG-Erklärung liegt
   unveränderlich im `CheckoutConsent`-Datensatz, ein Widerruf hätte dort
   nichts bewirkt. Der Widerruf von `sensitive_data` fragt vorher nach: er
   leert das Deck in beide Richtungen.

### Angleichungen an Web und Android

- **Thumbnail-Zuschnitt** senkrecht bei 0.15 statt mittig
  (`Core/Media/ImageProcessor`) — mittig schnitt Hochformat-Portraits die
  Stirn ab. Wirkt nur für **neu** hochgeladene Fotos.
- **Chat-Kopfzeile:** Der Ring um den Avatar zeigt jetzt den echten
  Online-Status (stand vorher unbedingt); „Melden" und „Blockieren" sind aus
  der Kopfzeile ins Menü gewandert.
- **Toast** 20 s statt 4 s, dazu ein Schließen-Knopf — die
  Widerrufs-Folgetexte sind zu lang für vier Sekunden.
- **Kürzere Foto- und Swipe-Texte**, wortgleich mit Android.
- **Rechtstexte:** Telefonprüfung raus (auch aus der Behörden-Datenübersicht),
  Bestandsdaten-Zeile präzisiert, Verifizierungs-Selfies/Ausweisaufnahmen als
  „in der Regel nein", Brevo als Auftragsverarbeiter ergänzt, Hinweis zu den
  Auftragsverarbeitungsbedingungen neu gefasst.
- **Ein** Live-Selfie statt „drei" in `NSCameraUsageDescription`, im
  Verifizierungshinweis und in den Store-Texten — die Prüfung nimmt seit
  Commit `66be588` genau eines auf.

### Nebenbei behoben

`Data/Repository/ProfileRepository.swift` trug zwei verwaiste
`@discardableResult`-Attribute ohne zugehörige Funktion (Rest einer früher
entfernten GPS-Funktion). Das wäre beim ersten Übersetzen ein **Fehler**
gewesen, kein Hinweis.

### Noch offen für iOS

- Die Rechtstexte weichen an zwei Stellen zwischen iOS und Android ab, beide
  älter als diese Sitzung und beide inhaltlich vertretbar: iOS formuliert die
  Speicherdauer der Verifizierungsaufnahmen ausführlicher (näher am Web),
  Android knapper. Nicht angeglichen — das ist eine rechtliche, keine
  technische Entscheidung.
- `frontend/`-only-Themen (Rücktrittsformular nach § 13a, Landingpage,
  Admin-Tool) sind wie bisher nicht Teil der App.

---

## Wo das Projekt steht

`ios/` enthält eine vollständige SwiftUI-Neuimplementierung der nativen
Android-App: ~60 Swift-Dateien, Swift + SwiftUI, MVVM + Repository, SwiftData,
URLSession, AVFoundation, BackgroundTasks. Alle Bildschirme der Android-Fassung
sind portiert, ebenso die Rechtstexte im Wortlaut.

**Das Projekt wurde nie kompiliert.** Es ist auf einem Linux-Rechner ohne Xcode
und ohne Swift-Toolchain entstanden; weder `swiftc` noch `xcodebuild` waren
verfügbar. Der erste Lauf auf einem Mac ist damit zugleich der erste
Übersetzungsvorgang — plane Zeit für Kleinigkeiten ein, die kein Mensch ohne
Compiler ausschließen kann (Argumentreihenfolgen, `some View`-Ableitungen,
Nebenläufigkeitswarnungen).

### Was stattdessen statisch geprüft wurde

Ersatzweise sind drei Dinge maschinell gegengelesen worden — das ersetzt keinen
Compiler, fängt aber die Fehlerklassen ab, die sich ohne ihn überhaupt finden
lassen:

1. **Argumentreihenfolge und Pflichtfelder aller 129 synthetisierten
   Initializer** samt der Frage, auf welchem Parameter eine abschließende
   Closure landet. Dabei kamen zwei echte Fehler heraus: bei
   `EmojiPickerPanel` und `EmojiToggleButton` stand die Closure nicht zuletzt,
   die abschließende Closure wäre also auf `height` bzw. `size` gelaufen. Beide
   Typen tragen jetzt einen Kommentar an der Stelle, damit das beim nächsten
   Feld nicht wieder passiert.
2. **Mitglieder-Zugriffe** (`model.x`, `container.repository.methode`) gegen die
   tatsächlichen Klassen — ohne Beanstandung.
3. **Nutzersichtbare Texte** gegen die Android-Fassung. Ergebnis: alle Meldungen
   sind übernommen, aber die `contentDescription` der Profilfotos fehlte. Ohne
   sie bleiben Fotos für VoiceOver stumm — in einer App, deren Inhalt Fotos
   sind. Nachgezogen in `PhotoImage`/`AvatarImage` und an allen Aufrufstellen,
   die auf Android eine hatten.

Erwartbare Stellen, an denen es trotzdem zuerst hakt:

- **`Sendable`-Warnungen** rund um `AVCaptureSession` (`CameraController`) und
  `UIImage` (`ImageProcessor`). Im Swift-5-Modus sind das Warnungen; wer auf den
  Swift-6-Modus umstellt, muss dort nachziehen.
- **`GrowingTextView`** — das `UITextView`-Wrapping für Cursorposition und
  mitwachsende Höhe ist der fummeligste Teil und will am Gerät gesehen werden.
- **SwiftData**: `MessageEntity` heißt sein Schlüsselfeld bewusst `messageID`
  und nicht `id`, weil `PersistentModel` bereits ein `id` mitbringt.

---

## Weg zum TestFlight-Build

Alles, was ohne Mac vorbereitet werden konnte, ist vorbereitet. Was bleibt,
braucht zwingend Xcode und ein Apple-Developer-Konto:

0. **Xcode installieren** (App Store), danach einmal
   `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` und
   `sudo xcodebuild -license accept`.
1. **Team-ID eintragen.** In `FLEXR.xcodeproj/project.pbxproj` steht auf
   Projektebene `FLEXR_DEVELOPMENT_TEAM = ""`. Einmal die zehnstellige Team-ID
   eintragen, dann signieren App- und Testziel:

   ```bash
   ./ios/tools/mac-build.sh team ABCDE12345
   ```

   Alternativ in Xcode unter *Signing & Capabilities*.
2. **Übersetzen und Tests laufen lassen** — `./ios/tools/mac-build.sh test`
   (oder ⌘U). Erster Compile-Durchgang überhaupt, siehe oben; das Skript legt
   die vollständige Ausgabe in `ios/build/test.log` ab.
3. **Im Simulator durchspielen**, danach auf einem Gerät: Registrierung inkl.
   Foto-Upload, Swipe, Chat, Verifizierung (braucht ein echtes Gerät, der
   Simulator hat keine Kamera), Rückkehr aus dem Stripe-Checkout.
4. **App-ID anlegen** in App Store Connect mit Bundle-ID `social.flexr.app`,
   SKU `flexr-ios`, Verfügbarkeit Österreich. Texte in
   [store/store-texte.md](store/store-texte.md).
5. **Archivieren und hochladen** — `./ios/tools/mac-build.sh archive` baut das
   Archiv und schreibt die passende `ExportOptions.plist`,
   `./ios/tools/mac-build.sh upload` exportiert die `.ipa` und nennt den
   `altool`-Befehl. Von Hand geht dasselbe über *Product → Archive → Distribute
   App → App Store Connect*. Die Exportbestimmungen sind über `ITSAppUsesNonExemptEncryption`
   in der Info.plist bereits beantwortet, das Privacy-Manifest liegt als
   `FLEXR/PrivacyInfo.xcprivacy` bei — ohne das weist der Upload seit Mai 2024
   mit ITMS-91053 zurück.
6. **App-Datenschutzangaben** in App Store Connect ausfüllen. Die Tabelle in
   `store/store-texte.md` ist eins zu eins die Auswahl, die dort anzuklicken
   ist, und deckungsgleich mit dem Privacy-Manifest.
7. **Altersfreigabe 18+** setzen; die App ist eine Dating-Plattform.
8. **Interne Tester** freischalten — dafür braucht es nichts weiter. Für
   **externe** Tester kommt eine Beta-App-Review dazu: Beschreibung,
   Feedback-Adresse und ein Testzugang stehen fertig in `store/store-texte.md`,
   das Testkonto selbst muss noch angelegt werden.

Screenshots braucht TestFlight nicht. Für die spätere Veröffentlichung erzeugt
`python3 ios/store/gen.py` sie in den verlangten Größen — es sind
Marketing-Panels mit nachgestelltem App-Screen, dieselbe Machart wie die
Play-Store-Assets, kein Abzug der laufenden App.

### Der wahrscheinlichste Streitpunkt im Review: Stripe

Die App schickt zum Bezahlen in eine externe Browser-Sitzung
(`SFSafariViewController`). Für **digitale Inhalte innerhalb der App** verlangt
Apple nach Richtlinie 3.1.1 grundsätzlich In-App-Kauf; ein Link nach draußen
gilt dort als „Steering". Die Android-Fassung hat dieses Problem nicht.

Drei gangbare Wege, in aufsteigendem Aufwand:

1. **StoreKit-2-Abo zusätzlich einbauen** und das Backend um einen
   Beleg-/`Transaction`-Abgleich erweitern, parallel zu Stripe. Sauberste,
   teuerste Lösung (Apple behält 15–30 %).
2. **External Purchase Link Entitlement** beantragen (in der EU über den
   Link-Out-Weg möglich, mit Provision und Pflichthinweis).
3. **„Reader"-Argumentation** — hier nicht tragfähig, weil der Kauf den Zugang
   zur App selbst freischaltet.

Das ist eine Produktentscheidung, keine technische: Deshalb ist der Code so
gebaut, dass `BillingRepository` die einzige Stelle ist, die den Kaufweg kennt.
Ein StoreKit-Weg käme dort hinein, ohne die Bildschirme anzufassen.

---

## Nicht offensichtliche Entscheidungen

**Zeitstempel des Backends sind naives UTC.** `datetime.utcnow()` liefert keinen
Offset. `Core/Common/ServerTime` interpretiert fehlende Offsets deshalb explizit
als UTC — sonst wäre eine stundengenaue Chat-Sperre um den lokalen Offset
verschoben. Dieselbe Falle steckt serverseitig in `stripe_client.py` und ist auf
Android identisch gelöst.

**Längen werden in Unicode-Codepoints gezählt, nicht in Zeichen.** Pydantic
prüft mit Pythons `len()`. Swifts `count` zählt Graphemcluster: „🏋️‍♀️" ist für
Swift ein Zeichen, für Python fünf. Nach `count` gekappte Bios würde der Server
mit 422 zurückweisen. Siehe `String.backendLength` in `Core/Common/TextLength`.

**Das Gym wird als volles Label gespeichert** (`Name — Straße 1, 1100 Wien`).
Nur das erkennt `gyms.gym_exists_for_profile()` als gültig; der bloße Name gilt
ausschließlich für Bestandsprofile.

**Der `APIClient` hängt Header nur an `/api/`-Pfade.** Ein Authorization-Header
auf einer Presigned-S3-URL würde die Signatur ungültig machen. Die
PLZ-Datenbank läuft über einen zweiten Client, der 401 nicht als Sitzungsende
meldet — sonst würde eine fremde API die eigene Anmeldung beenden.

**Der Bildspeicher ignoriert HTTP-Cache-Header bewusst.** `AsyncImage` hält
nichts auf der Platte und richtet sich sonst nach den Headern; R2 lieferte lange
gar keine. Die Objektschlüssel sind UUIDs und werden nie überschrieben — ein
geladenes Bild bleibt gültig. Dieselbe Begründung wie bei Coils
`respectCacheHeaders(false)` auf Android.

**Kein `didSet` in `@Observable`-Klassen.** Das Makro schreibt gespeicherte
Eigenschaften in berechnete um, Property-Observer sind dort nicht zulässig. Die
PLZ-Ermittlung stößt deshalb die Ansicht über `.onChange` an — wer das
zurückbaut, bekommt einen Übersetzungsfehler oder still totes Verhalten.

**`BGTaskScheduler.register` läuft auf der Hauptwarteschlange** (`using: .main`).
Die Repositories sind MainActor-isoliert; mit `nil` liefe der Handler auf einer
Hintergrundwarteschlange und `MainActor.assumeIsolated` würde abstürzen.

**Die Combine-Abonnements in `AppModel` gehen durch `receive(on: .main)`.** Der
401-Zweig des `APIClient` feuert aus dem URLSession-Thread; der Zustand gehört
auf den MainActor.

**Das Icon ist ein volles Quadrat ohne Alpha.** Details in der README unter
„Marke und Assets".

---

## Zustand der Test-Suites

**iOS:** vier Testklassen (`ServerTime`, `APIErrorParser`, `PlzRepository`,
`EmojiInsertion`) plus `DTOMapping` — sie spiegeln die vier Android-Tests und
prüfen zusätzlich den snake_case-Vertrag der DTOs. **Nie ausgeführt**, siehe
oben: kein Xcode auf der Maschine, auf der sie entstanden sind.

Am 23.08.2026 dazugekommen: `in_chats` (gesetzt, fehlend und nach dem Leeren
des Verlaufs), das Lesen der Einwilligungs-Einträge und der Widerrufsantwort,
der snake_case-Körper von `CheckoutRequestDTO`/`ConsentRevokeRequestDTO` sowie
`detail.code = "account_deleted"` im Fehler-Parser.

Der DTO-Test ist der wichtigste von ihnen: Anders als die Android-Fassung, die
jedes Feld per `@SerialName` benennt, verlässt sich die iOS-App auf
`convertFromSnakeCase`. Fällt ein Feldname aus dem Muster, bleibt das sonst bis
zur Laufzeit unbemerkt und das Feld ist still leer.

**Android und Backend** sind davon unberührt und stehen wie in
`android-native/HANDOFF.md` beschrieben.

---

## Wenn als Nächstes etwas dazukommt

- **Neuer Endpunkt:** DTO in `Data/Remote/DTOs.swift`, Aufruf in `FlexrAPI`,
  Übersetzung in `Repository/Mappers.swift`, dann das Repository.
- **Neuer Bildschirm:** Ordner unter `UI/`, ein `@Observable`-Model plus View,
  Ziel in `UI/Navigation/Destinations.swift` und in `FlexrRoutes` (RootView).
  Neue Dateien landen dank der dateisystem-synchronisierten Gruppe automatisch
  im Target — die `project.pbxproj` muss nicht angefasst werden.
- **Telefonprüfung nachrüsten:** neues `PhoneRepository` gegen `/api/phone/*`.
- **Rechtstexte ändern:** `UI/Legal/LegalContent.swift` **und**
  `android-native/.../LegalContent.kt` **und** die HTML-Fassungen unter
  `frontend/` zusammen pflegen — sie sind rechtsverbindlich und müssen
  wortgleich bleiben.
