import XCTest

/// Fährt die App von A bis Z ab und hält jeden Schritt als Bildschirmfoto fest.
///
/// Läuft nur im Codemagic-Workflow `ios-screenshots`: Der startet vorher ein
/// lokales Backend mit Testdaten (tools/ios-screenshots/) und reicht Zugang und
/// Adresse über `TEST_RUNNER_FLEXR_SHOT_*` herein. Ohne diese Angaben wird der
/// Test übersprungen - in Xcode lokal oder in `ios-tests` passiert nichts.
///
/// Testdaten (seed.py): Lukas ist angemeldet, hat Matches mit Lena (Chat über
/// drei Tage), Viktoria (eine Nachricht) und Mia (noch kein Chat); Theresa hat
/// ihn geliked, Julia und Anna liegen im Deck. Ein Like auf Theresa ergibt also
/// ein Match - der Test liked deshalb, bis das Match-Overlay erscheint.
///
/// Die Bilder landen als Anhang im Ergebnisbündel (`xcresult`) und, wenn
/// `FLEXR_SHOT_DIR` gesetzt ist, zusätzlich als PNG in diesem Ordner.
/// Einzelne Schritte dürfen scheitern - die übrigen Bilder entstehen trotzdem.
/// Gescheiterte Schritte stehen als „… nicht gefunden" im Testprotokoll.
final class ScreenshotTests: XCTestCase {

    private var app: XCUIApplication!
    private var zielordner: URL?
    private var email = ""
    private var passwort = ""

    override func setUpWithError() throws {
        let env = ProcessInfo.processInfo.environment
        guard let email = env["FLEXR_SHOT_EMAIL"], let passwort = env["FLEXR_SHOT_PASSWORD"],
              !email.isEmpty, !passwort.isEmpty else {
            throw XCTSkip("Nur im Codemagic-Workflow ios-screenshots (FLEXR_SHOT_EMAIL fehlt).")
        }
        self.email = email
        self.passwort = passwort
        continueAfterFailure = true
        if let ordner = env["FLEXR_SHOT_DIR"], !ordner.isEmpty {
            zielordner = URL(fileURLWithPath: ordner, isDirectory: true)
            try? FileManager.default.createDirectory(at: zielordner!, withIntermediateDirectories: true)
        }
        app = XCUIApplication()
        app.launchArguments = [
            "-FlexrAPIBaseURL", env["FLEXR_SHOT_API"] ?? "http://127.0.0.1:8000/",
            // Sprache fest auf Deutsch, unabhängig von Gerät und Zeitzone der
            // Build-Maschine (LanguageStore liest denselben Schlüssel).
            "-flexr_language", "de",
            "-AppleLanguages", "(de)",
            "-AppleLocale", "de_AT",
        ]
        _ = addUIInterruptionMonitor(withDescription: "Systemdialog") { dialog in
            for titel in ["Erlauben", "Allow", "OK", "Nicht erlauben", "Don’t Allow"] {
                let knopf = dialog.buttons[titel]
                if knopf.exists { knopf.tap(); return true }
            }
            return false
        }
        app.launch()
    }

    func testAppVonAbisZ() {
        ausgeloggt()
        einloggen()
        systemdialogeSchliessen()
        deck()
        matches()
        chats()
        konto()
        englisch()
        abmelden()
        gate()
    }

    // MARK: - A: ausgeloggt

    private func ausgeloggt() {
        guard app.textFields.firstMatch.waitForExistence(timeout: 20) else {
            foto("00-start")
            XCTFail("Kein Login-Feld")
            return
        }
        foto("00-login")

        if tippe(knopf: "Passwort vergessen?") {
            warte(1)
            foto("00-passwort-vergessen")
            tippe(knopf: "Abbrechen")
            warte(1)
        }

        // Falsches Passwort: Die Fehlermeldung muss am Formular stehen.
        tippeFeld(app.textFields.firstMatch, text: email)
        // Zeilenschaltung im Passwortfeld = "Los" auf der Tastatur = Login.
        tippeFeld(app.secureTextFields.firstMatch, text: "falsch-\(passwort)\n")
        warte(3)
        foto("00-login-fehler")

        if tippe(knopf: "EN") {
            warte(1)
            foto("00-login-englisch")
            tippe(knopf: "DE")
            warte(1)
        }

        if tippe(knopf: "Registrieren") {
            warte(2)
            foto("00-registrieren-1")
            app.swipeUp()
            warte(1)
            foto("00-registrieren-2")
            app.swipeUp()
            warte(1)
            foto("00-registrieren-3")
            // Leer abschicken: Die Prüfung springt zum ersten offenen Feld.
            if tippe(knopf: "Profil kostenlos erstellen", scrollen: true) {
                warte(2)
                foto("00-registrieren-fehler")
            }
            for _ in 0..<6 { app.swipeDown() }
            tippe(knopf: "Einloggen")
            warte(2)
        }
    }

    private func einloggen() {
        let feld = app.textFields.firstMatch
        guard feld.waitForExistence(timeout: 10) else {
            XCTFail("Kein Login-Feld nach der Registrierung")
            return
        }
        leere(feld)
        tippeFeld(feld, text: email)
        let pw = app.secureTextFields.firstMatch
        leere(pw)
        tippeFeld(pw, text: passwort + "\n")
        if !app.buttons["Konto"].waitForExistence(timeout: 15) { einloggenKnopf() }
        if !app.buttons["Konto"].waitForExistence(timeout: 30) {
            foto("00-nach-login")
            XCTFail("Nach dem Login keine Tab-Leiste")
        }
    }

    /// "Einloggen" gibt es zweimal (Reiter oben, Knopf unten) - der Knopf ist
    /// der untere.
    private func einloggenKnopf() {
        let knoepfe = app.buttons.matching(NSPredicate(format: "label ==[c] %@", "Einloggen"))
            .allElementsBoundByIndex.filter { $0.isHittable }
        knoepfe.max(by: { $0.frame.minY < $1.frame.minY })?.tap()
    }

    // MARK: - B: Deck

    private func deck() {
        warte(3)
        foto("01-deck")

        // Tipp aufs Foto öffnet die Galerie.
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.45)).tap()
        warte(2)
        foto("01-deck-galerie")
        tippe(knopf: "Schließen")
        warte(1)

        if tippe(knopf: "Melden") {
            warte(1)
            foto("01-deck-melden")
            let grund = app.textViews.firstMatch
            if grund.waitForExistence(timeout: 3) {
                grund.tap()
                // Das Blatt wächst mit der Tastatur - erst danach tippen.
                warte(2)
                grund.typeText("Testmeldung aus dem UI-Test")
                warte(1)
                foto("01-deck-melden-grund")
                // Der Knopf im Blatt ist der untere der beiden "Melden".
                if let senden = untersterKnopf("Melden") {
                    senden.tap()
                    warte(3)
                    foto("01-deck-gemeldet")
                    tippe(knopf: "Schließen", warten: 2)
                } else {
                    tippe(knopf: "Abbrechen")
                }
            } else {
                tippe(knopf: "Abbrechen")
            }
            warte(1)
        }
        if tippe(knopf: "Blockieren") {
            warte(1)
            foto("01-deck-blockieren")
            tippeImDialog("Abbrechen")
            warte(1)
        }

        // Liken, bis das Match-Overlay kommt (Theresa hat Lukas geliked).
        var matchGesehen = false
        for runde in 0..<4 {
            guard tippe(knopf: "Gefällt mir") else { break }
            warte(3)
            if knopf("Weiter swipen").waitForExistence(timeout: 2) {
                foto("01-deck-match")
                tippe(knopf: "Weiter swipen")
                warte(1)
                matchGesehen = true
                break
            }
            foto("01-deck-nach-like-\(runde + 1)")
        }
        if !matchGesehen {
            XCTContext.runActivity(named: "Kein Match-Overlay nach den Likes") { _ in }
        }
        // Die nächste Karte wirklich blockieren - im Konto wird sie wieder
        // freigegeben.
        if tippe(knopf: "Blockieren", warten: 3) {
            warte(1)
            tippeImDialog("Blockieren")
            warte(2)
            foto("01-deck-blockiert")
        }
        // Rest ablehnen, bis das Deck leer ist.
        for _ in 0..<4 {
            guard tippe(knopf: "Ablehnen", warten: 2) else { break }
            warte(2)
        }
        foto("01-deck-leer")
    }

    // MARK: - C: Matches und Match-Profil

    private func matches() {
        guard tippe(knopf: "Matches") else { return }
        warte(2)
        foto("02-matches")

        if tippe(enthaelt: "geliked") {
            warte(2)
            foto("02-offene-likes")
            tippe(knopf: "Zurück")
            warte(1)
        }

        if tippe(enthaelt: "Mia") {
            warte(2)
            foto("03-match-profil")
            if tippe(knopf: "Match auflösen") {
                warte(1)
                foto("03-match-aufloesen")
                tippeImDialog("Abbrechen")
                warte(1)
            }
            if tippe(knopf: "Nachricht schreiben") {
                warte(2)
                foto("04-chat-leer")
                // Gesprächseinstieg übernehmen und senden.
                if tippe(enthaelt: "diese Woche") {
                    warte(1)
                    foto("04-chat-vorschlag")
                    tippe(knopf: "Senden")
                    warte(3)
                    foto("04-chat-gesendet")
                }
                tippe(knopf: "Zurück")
                warte(1)
            }
            tippe(knopf: "Zurück")
            warte(1)
        }

        // Viktoria wirklich auflösen.
        if tippe(enthaelt: "Viktoria") {
            warte(2)
            if tippe(knopf: "Match auflösen") {
                warte(1)
                tippeImDialog("Auflösen")
                warte(3)
                foto("03-match-aufgeloest")
            } else {
                tippe(knopf: "Zurück")
            }
        }
    }

    // MARK: - D: Chats

    private func chats() {
        guard tippe(knopf: "Chats") else { return }
        warte(2)
        foto("05-chats")
        guard tippe(enthaelt: "Lena") else { return }
        warte(2)
        foto("06-chat")

        let eingabe = app.textViews.firstMatch
        if eingabe.waitForExistence(timeout: 5) {
            eingabe.tap()
            eingabe.typeText("Klingt gut! Samstag um 9 im Studio?")
            warte(1)
            foto("06-chat-tippen")
            tippe(knopf: "Senden")
            warte(3)
            foto("06-chat-gesendet")
        }
        if tippe(knopf: "Emoji einfügen") {
            warte(1)
            foto("06-chat-emoji")
            tippe(knopf: "Emoji-Auswahl schließen")
        }
        if tippe(knopf: "Weitere Optionen") {
            warte(1)
            foto("06-chat-menue")
            app.coordinate(withNormalizedOffset: CGVector(dx: 0.3, dy: 0.5)).tap()
            warte(1)
        }
        // Entwurf stehen lassen: Er muss nach dem Tab-Wechsel wieder da sein.
        if eingabe.exists {
            eingabe.tap()
            eingabe.typeText("Entwurf bleibt stehen")
            app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.3)).tap()
        }
        // Kopf antippen öffnet das Profil, "Nachricht schreiben" führt zurück.
        if tippe(enthaelt: "Lena, ") {
            warte(2)
            foto("06-chat-profil")
            tippe(knopf: "Nachricht schreiben")
            warte(2)
        }
        tippe(knopf: "Zurück")
        warte(1)
        if tippe(enthaelt: "Mia") {
            warte(2)
            if tippe(knopf: "Weitere Optionen") {
                warte(1)
                tippe(knopf: "Chatverlauf leeren")
                warte(1)
                tippeImDialog("Leeren")
                warte(3)
                foto("06-chat-geleert")
            }
            tippe(knopf: "Zurück")
            warte(1)
        }
        tippe(knopf: "Swipe")
        warte(1)
        tippe(knopf: "Chats")
        warte(2)
        if tippe(enthaelt: "Lena") {
            warte(2)
            foto("06-chat-entwurf-nach-tabwechsel")
            tippe(knopf: "Zurück")
            warte(1)
        }
    }

    // MARK: - E: Konto

    private func konto() {
        guard tippe(knopf: "Konto") else { return }
        warte(3)
        systemdialogeSchliessen()
        foto("07-konto")

        // Ungespeicherte Änderung muss den Tab-Wechsel überstehen.
        let bio = app.textViews.firstMatch
        if bio.waitForExistence(timeout: 5) {
            bio.tap()
            warte(1)
            // Länger als ein Wort: Fehlende Zeichen fielen hier sofort auf.
            bio.typeText(" Suche Trainingspartner fürs Kreuzheben.")
            // Tastatur schließen, sonst liegt sie über der Tab-Leiste.
            if !tippe(knopf: "Fertig", warten: 2) { app.swipeDown() }
            warte(1)
            foto("07-konto-ungespeichert")
            tippe(knopf: "Swipe")
            warte(2)
            tippe(knopf: "Konto")
            warte(2)
            foto("07-konto-nach-tabwechsel")
            if tippe(knopf: "Profil speichern", scrollen: true) {
                warte(2)
                foto("07-konto-gespeichert")
            }
        }

        for teil in 1...7 {
            app.swipeUp()
            warte(1)
            foto("08-konto-\(teil)")
        }

        if tippe(enthaelt: "Matches, Profile", scrollen: true) {
            warte(2)
            foto("09-benachrichtigungen")
            schliesseSheet()
        }
        if tippe(enthaelt: "Einwilligungen", scrollen: true) {
            warte(2)
            foto("10-einwilligungen")
        }
        if tippe(enthaelt: "Blockierte", scrollen: true) {
            warte(2)
            foto("10-blockiert")
            if tippe(knopf: "Aufheben", scrollen: true) {
                warte(2)
                foto("10-blockierung-aufgehoben")
            }
        }
        if tippe(enthaelt: "Meine Meldungen", scrollen: true) {
            warte(2)
            foto("10-meldungen")
        }
        if tippe(knopf: "E-Mail-Adresse ändern", scrollen: true) {
            warte(2)
            foto("11-email-aendern")
            tippe(knopf: "Abbrechen")
            warte(1)
        }
        if tippe(knopf: "Passwort ändern", scrollen: true) {
            warte(2)
            foto("11-passwort-aendern")
            tippe(knopf: "Abbrechen")
            warte(1)
        }
        if tippe(knopf: "Konto löschen", scrollen: true) {
            warte(2)
            foto("11-konto-loeschen")
            tippe(knopf: "Abbrechen")
            warte(1)
        }
        for (dokument, name) in [
            ("Häufige Fragen", "faq"), ("Impressum", "impressum"),
            ("Datenschutzerklärung", "datenschutz"), ("Rücktrittsrecht", "ruecktritt"),
        ] where tippe(enthaelt: dokument, scrollen: true) {
            warte(2)
            foto("12-recht-\(name)")
            if name == "ruecktritt" {
                app.swipeUp()
                app.swipeUp()
                warte(1)
                foto("12-recht-ruecktritt-formular")
            }
            tippe(knopf: "Zurück")
            warte(1)
        }
    }

    // MARK: - F: Englisch

    private func englisch() {
        guard tippe(knopf: "EN", scrollen: true) else { return }
        warte(2)
        foto("13-konto-englisch")
        for _ in 0..<12 { app.swipeDown() }
        warte(1)
        foto("13-konto-englisch-oben")
        if tippe(knopf: "Swipe") {
            warte(2)
            foto("13-deck-englisch")
        }
        if tippe(knopf: "Matches") {
            warte(2)
            foto("13-matches-englisch")
        }
        if tippe(knopf: "Chats") {
            warte(2)
            if tippe(enthaelt: "Lena") {
                warte(2)
                foto("13-chat-englisch")
                tippe(knopf: "Back")
                warte(1)
            }
        }
        if tippe(knopf: "Account") {
            warte(2)
            tippe(knopf: "DE", scrollen: true)
            warte(1)
        }
    }

    // MARK: - G: Abmelden

    private func abmelden() {
        tippe(knopf: "Konto")
        warte(1)
        if tippe(knopf: "Ausloggen", scrollen: true) {
            warte(3)
            foto("14-ausgeloggt")
        }
    }

    // MARK: - H: Konto vor der Freischaltung

    /// Nora (seed.py) ist noch nicht freigeschaltet: Nach dem Login steht das
    /// Verifizierungs-Gate statt der Tab-Leiste.
    private func gate() {
        let feld = app.textFields.firstMatch
        guard feld.waitForExistence(timeout: 10) else { return }
        leere(feld)
        tippeFeld(feld, text: "nora@example.com")
        let pw = app.secureTextFields.firstMatch
        leere(pw)
        tippeFeld(pw, text: passwort + "\n")
        warte(5)
        systemdialogeSchliessen()
        foto("15-gate")
        app.swipeUp()
        warte(1)
        foto("15-gate-2")
        if tippe(knopf: "Ausloggen", scrollen: true) {
            warte(2)
        }
    }

    // MARK: - Hilfsschritte

    /// Mitteilungs-Abfrage und „Passwort sichern?" nach dem Login. Letzteres
    /// lag im ersten Lauf über dem Deck und schluckte den nächsten Tipp. Der
    /// Monitor greift erst bei der nächsten Berührung der App, deshalb zum
    /// Schluss ein harmloser Tipp oben auf die Kopfzeile.
    private func systemdialogeSchliessen() {
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        for _ in 0..<3 {
            var getroffen = false
            for quelle in [app!, springboard] {
                for titel in ["Not Now", "Jetzt nicht", "Erlauben", "Allow"] {
                    let knopf = quelle.buttons[titel]
                    if knopf.waitForExistence(timeout: 2) {
                        knopf.tap()
                        getroffen = true
                    }
                }
            }
            if !getroffen { break }
        }
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.06)).tap()
    }

    private func knopf(_ label: String) -> XCUIElement {
        app.buttons.matching(NSPredicate(format: "label ==[c] %@", label)).firstMatch
    }

    @discardableResult
    private func tippe(knopf label: String, scrollen: Bool = false, warten: TimeInterval = 8) -> Bool {
        tippe(app.buttons.matching(NSPredicate(format: "label ==[c] %@", label)),
              name: label, scrollen: scrollen, warten: warten)
    }

    /// Listenzeilen heißen für XCUITest „Profilfoto von Lena, Lena, 30, …" -
    /// deshalb enthält statt beginnt mit.
    @discardableResult
    private func tippe(enthaelt text: String, scrollen: Bool = false) -> Bool {
        tippe(app.buttons.matching(NSPredicate(format: "label CONTAINS[c] %@", text)),
              name: text, scrollen: scrollen, warten: 8)
    }

    /// Den antippbaren Treffer nehmen. Meldet XCUITest keinen als antippbar
    /// (erster Lauf: die Reiter der eigenen Tab-Leiste), auf die Mitte des
    /// ersten sichtbaren tippen - die Koordinate trifft trotzdem. Mit
    /// `scrollen` wird vorher nach unten gewischt, bis der Treffer im Bild ist.
    private func tippe(_ abfrage: XCUIElementQuery, name: String, scrollen: Bool, warten: TimeInterval) -> Bool {
        _ = abfrage.firstMatch.waitForExistence(timeout: warten)
        if scrollen {
            // Erst nach unten suchen, dann zurück nach oben - das Ziel kann
            // auch über der aktuellen Stelle liegen.
            for _ in 0..<12 where !abfrage.allElementsBoundByIndex.contains(where: { $0.isHittable }) {
                app.swipeUp()
            }
            for _ in 0..<24 where !abfrage.allElementsBoundByIndex.contains(where: { $0.isHittable }) {
                app.swipeDown()
            }
        }
        let alle = abfrage.allElementsBoundByIndex
        if let ziel = alle.first(where: { $0.isHittable }) {
            ziel.tap()
            return true
        }
        let bildschirm = app.frame
        if let ziel = alle.first(where: { !$0.frame.isEmpty && bildschirm.intersects($0.frame) }) {
            ziel.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
            return true
        }
        XCTContext.runActivity(named: "\"\(name)\" nicht gefunden (\(alle.count) Treffer)") { _ in }
        return false
    }

    /// Von mehreren gleich beschrifteten Knöpfen den untersten (etwa den im
    /// Blatt statt des gleichnamigen auf der Karte dahinter).
    private func untersterKnopf(_ label: String) -> XCUIElement? {
        app.buttons.matching(NSPredicate(format: "label ==[c] %@", label))
            .allElementsBoundByIndex
            .filter { $0.isHittable }
            .max(by: { $0.frame.minY < $1.frame.minY })
    }

    private func tippeImDialog(_ label: String) {
        let dialog = app.alerts.firstMatch
        if dialog.waitForExistence(timeout: 3), dialog.buttons[label].exists {
            dialog.buttons[label].tap()
        } else {
            tippe(knopf: label)
        }
    }

    private func tippeFeld(_ feld: XCUIElement, text: String) {
        guard feld.waitForExistence(timeout: 5) else { return }
        feld.tap()
        feld.typeText(text)
    }

    private func leere(_ feld: XCUIElement) {
        guard feld.waitForExistence(timeout: 3) else { return }
        feld.tap()
        let laenge = (feld.value as? String)?.count ?? 0
        if laenge > 0 {
            feld.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: laenge + 4))
        }
    }

    /// Sheets ohne Abbrechen-Knopf: nach unten wegwischen.
    private func schliesseSheet() {
        if !tippe(knopf: "Fertig", warten: 1), !tippe(knopf: "Schließen", warten: 1) {
            app.swipeDown(velocity: .fast)
        }
        warte(1)
    }

    private func warte(_ sekunden: TimeInterval) {
        _ = XCTWaiter.wait(for: [XCTestExpectation(description: "warten")], timeout: sekunden)
    }

    private func foto(_ name: String) {
        let bild = XCUIScreen.main.screenshot()
        let anhang = XCTAttachment(screenshot: bild)
        anhang.name = name
        anhang.lifetime = .keepAlways
        add(anhang)
        if let zielordner {
            try? bild.pngRepresentation.write(to: zielordner.appendingPathComponent("\(name).png"))
        }
    }
}
