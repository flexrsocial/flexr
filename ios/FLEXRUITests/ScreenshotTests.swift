import XCTest

/// Fährt die wichtigsten Screens ab und hält jeden als Bildschirmfoto fest.
///
/// Läuft nur im Codemagic-Workflow `ios-screenshots`: Der startet vorher ein
/// lokales Backend mit Testdaten (tools/ios-screenshots/) und reicht Zugang und
/// Adresse über `TEST_RUNNER_FLEXR_SHOT_*` herein. Ohne diese Angaben wird der
/// Test übersprungen - in Xcode lokal oder in `ios-tests` passiert nichts.
///
/// Die Bilder landen als Anhang im Ergebnisbündel (`xcresult`) und, wenn
/// `FLEXR_SHOT_DIR` gesetzt ist, zusätzlich als PNG in diesem Ordner.
/// Einzelne Schritte dürfen scheitern - die übrigen Bilder entstehen trotzdem.
final class ScreenshotTests: XCTestCase {

    private var app: XCUIApplication!
    private var nummer = 0
    private var zielordner: URL?

    override func setUpWithError() throws {
        let env = ProcessInfo.processInfo.environment
        guard let email = env["FLEXR_SHOT_EMAIL"], let passwort = env["FLEXR_SHOT_PASSWORD"],
              !email.isEmpty, !passwort.isEmpty else {
            throw XCTSkip("Nur im Codemagic-Workflow ios-screenshots (FLEXR_SHOT_EMAIL fehlt).")
        }
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
        einloggen(email: email, passwort: passwort)
    }

    func testScreensAbfahren() {
        systemdialogeSchliessen()
        warte(3)
        foto("01-deck")

        if tippe(knopf: "Matches") {
            warte(2)
            foto("02-matches")
            if tippe(beginntMit: "Mia") || tippe(beginntMit: "Lena") {
                warte(2)
                foto("03-match-profil")
                tippe(knopf: "Zurück")
            }
            if tippe(knopf: "Hallo sagen") {
                warte(2)
                foto("04-chat-leer")
                tippe(knopf: "Zurück")
            }
        }

        if tippe(knopf: "Chats") {
            warte(2)
            foto("05-chats")
            if tippe(beginntMit: "Lena") {
                warte(2)
                foto("06-chat")
                tippe(knopf: "Zurück")
            }
        }

        if tippe(knopf: "Konto") {
            warte(2)
            foto("07-konto")
            for teil in 1...3 {
                app.swipeUp()
                warte(1)
                foto("08-konto-\(teil)")
            }
        }
    }

    // MARK: - Schritte

    private func einloggen(email: String, passwort: String) {
        let feld = app.textFields.firstMatch
        guard feld.waitForExistence(timeout: 20) else {
            foto("00-start")
            XCTFail("Kein Login-Feld")
            return
        }
        feld.tap()
        feld.typeText(email)
        let pw = app.secureTextFields.firstMatch
        pw.tap()
        pw.typeText(passwort)
        foto("00-login")
        // "Einloggen" gibt es zweimal (Reiter oben, Knopf unten) - der Knopf
        // ist der untere.
        let knoepfe = app.buttons.matching(NSPredicate(format: "label ==[c] %@", "Einloggen"))
            .allElementsBoundByIndex.filter { $0.isHittable }
        knoepfe.max(by: { $0.frame.minY < $1.frame.minY })?.tap()
        if !app.buttons["Konto"].waitForExistence(timeout: 30) {
            foto("00-nach-login")
            XCTFail("Nach dem Login keine Tab-Leiste")
        }
    }

    /// Mitteilungs-Abfrage u. ä. - der Monitor greift erst bei der nächsten
    /// Berührung der App, deshalb ein harmloser Tipp oben auf die Kopfzeile.
    private func systemdialogeSchliessen() {
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        for titel in ["Erlauben", "Allow"] {
            let knopf = springboard.buttons[titel]
            if knopf.waitForExistence(timeout: 2) { knopf.tap() }
        }
        app.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.06)).tap()
    }

    @discardableResult
    private func tippe(knopf label: String) -> Bool {
        let treffer = app.buttons.matching(NSPredicate(format: "label ==[c] %@", label)).firstMatch
        guard treffer.waitForExistence(timeout: 8), treffer.isHittable else {
            XCTContext.runActivity(named: "Knopf \"\(label)\" nicht gefunden") { _ in }
            return false
        }
        treffer.tap()
        return true
    }

    @discardableResult
    private func tippe(beginntMit text: String) -> Bool {
        let treffer = app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", text)).firstMatch
        guard treffer.waitForExistence(timeout: 8), treffer.isHittable else { return false }
        treffer.tap()
        return true
    }

    private func warte(_ sekunden: TimeInterval) {
        _ = XCTWaiter.wait(for: [XCTestExpectation(description: "warten")], timeout: sekunden)
    }

    private func foto(_ name: String) {
        nummer += 1
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
