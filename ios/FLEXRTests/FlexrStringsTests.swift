import XCTest

@testable import FLEXR

/// Jeder Textschlüssel steht deutsch und englisch, mit denselben Platzhaltern
/// in derselben Reihenfolge.
///
/// Fehlt die englische Fassung, fällt `FlexrStrings` still auf Deutsch zurück -
/// das sieht niemand, der die App auf Deutsch benutzt. Und ein vertauschter
/// Platzhalter (`%@` statt `%d`) stürzt erst beim Formatieren ab, also mitten
/// in der Benutzung. Entspricht `test_app_texte_gibt_es_in_beiden_sprachen` für
/// die Web-App.
final class FlexrStringsTests: XCTestCase {

    func testJederSchluesselHatEinenDeutschenText() {
        let fehlend = L.allCases.filter { (FlexrStrings.german[$0] ?? "").isEmpty }
        XCTAssertEqual(fehlend, [], "Ohne deutschen Text: \(fehlend)")
    }

    func testJederSchluesselHatEinenEnglischenText() {
        let fehlend = L.allCases.filter { (FlexrStrings.english[$0] ?? "").isEmpty }
        XCTAssertEqual(fehlend, [], "Ohne englischen Text: \(fehlend)")
    }

    func testPlatzhalterStimmenInBeidenSprachenUeberein() {
        for key in L.allCases {
            guard let deutsch = FlexrStrings.german[key], let englisch = FlexrStrings.english[key] else {
                continue
            }
            XCTAssertEqual(
                platzhalter(deutsch), platzhalter(englisch),
                "Platzhalter von \(key) weichen ab"
            )
        }
    }

    func testReiterUndSendenSindUebersetzt() {
        XCTAssertEqual(FlexrStrings(language: .english)(AuthTab.register.titleKey), "Sign up")
        XCTAssertEqual(FlexrStrings(language: .german)(AuthTab.login.titleKey), "Einloggen")
        XCTAssertEqual(FlexrStrings(language: .english)(.chatSend), "Send")
    }

    private func platzhalter(_ text: String) -> [String] {
        let muster = try! NSRegularExpression(pattern: "%(?:\\d+\\$)?(?:l?d|@|f|s)")
        let bereich = NSRange(text.startIndex..., in: text)
        return muster.matches(in: text, range: bereich).compactMap {
            Range($0.range, in: text).map { String(text[$0]) }
        }
    }
}
