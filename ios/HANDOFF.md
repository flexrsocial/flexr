# HANDOFF — native iOS-App

Stand: **03.08.2026**. Für Aufbau, Build-Befehle und die Migrationstabelle siehe
[README.md](README.md) — hier steht nur, was daraus *nicht* hervorgeht.

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

1. **Team-ID eintragen.** In `FLEXR.xcodeproj/project.pbxproj` steht auf
   Projektebene `FLEXR_DEVELOPMENT_TEAM = ""`. Einmal die zehnstellige Team-ID
   eintragen, dann signieren App- und Testziel. Alternativ in Xcode unter
   *Signing & Capabilities*.
2. **Übersetzen und Tests laufen lassen** (⌘U). Erster Compile-Durchgang
   überhaupt — siehe oben.
3. **Im Simulator durchspielen**, danach auf einem Gerät: Registrierung inkl.
   Foto-Upload, Swipe, Chat, Verifizierung (braucht ein echtes Gerät, der
   Simulator hat keine Kamera), Rückkehr aus dem Stripe-Checkout.
4. **App-ID anlegen** in App Store Connect mit Bundle-ID `social.flexr.app`,
   SKU `flexr-ios`, Verfügbarkeit Österreich. Texte in
   [store/store-texte.md](store/store-texte.md).
5. **Archivieren und hochladen** (*Product → Archive → Distribute App → App Store
   Connect*). Die Exportbestimmungen sind über `ITSAppUsesNonExemptEncryption`
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
