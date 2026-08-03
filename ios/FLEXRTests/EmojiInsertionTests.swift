import XCTest

@testable import FLEXR

/// Einfügeregeln des Emoji-Pickers — dieselben wie im Web-Frontend und in der
/// Android-App: an der Cursorposition, ersetzt eine Auswahl, respektiert das
/// Längenlimit.
final class EmojiInsertionTests: XCTestCase {

    private func caret(_ location: Int) -> NSRange {
        NSRange(location: location, length: 0)
    }

    func testFuegtAnDerCursorpositionEin() {
        let result = EmojiInsertion.insert(
            "💪",
            into: "Training macht Spass",
            selection: caret(8),
            maxLength: 280
        )
        XCTAssertEqual(result.text, "Training💪 macht Spass")
    }

    func testSetztDenCursorHinterDasEingefuegteEmoji() {
        let result = EmojiInsertion.insert("🔥", into: "ab", selection: caret(1), maxLength: nil)
        XCTAssertEqual(result.text, "a🔥b")
        // Gerechnet wird in UTF-16-Einheiten, weil UITextView seine Auswahl als
        // NSRange führt — „🔥" belegt zwei davon.
        XCTAssertEqual(result.selection.location, 1 + ("🔥" as NSString).length)
        XCTAssertEqual(result.selection.length, 0)
    }

    func testHaengtBeiLeeremFeldEinfachAn() {
        let result = EmojiInsertion.insert("🏋️", into: "", selection: caret(0), maxLength: 280)
        XCTAssertEqual(result.text, "🏋️")
    }

    func testErsetztEineMarkierteAuswahl() {
        let result = EmojiInsertion.insert(
            "🌊",
            into: "Hallo Welt",
            selection: NSRange(location: 6, length: 4),
            maxLength: 280
        )
        XCTAssertEqual(result.text, "Hallo 🌊")
    }

    func testLaesstDenTextUnveraendertWennDasLimitUeberschrittenWuerde() {
        let voll = String(repeating: "x", count: 280)
        let result = EmojiInsertion.insert("💯", into: voll, selection: caret(280), maxLength: 280)
        XCTAssertEqual(result.text, voll)
        XCTAssertEqual(result.text.backendLength, 280)
    }

    func testOhneLimitWirdImmerEingefuegt() {
        let lang = String(repeating: "y", count: 5_000)
        let result = EmojiInsertion.insert("✨", into: lang, selection: caret(0), maxLength: nil)
        XCTAssertTrue(result.text.hasPrefix("✨"))
    }

    func testCursorHinterDemTextendeWirdAbgefangen() {
        // Kann auftreten, wenn der Text von außen gekürzt wurde, die alte
        // Auswahl aber noch steht.
        let result = EmojiInsertion.insert("🎯", into: "kurz", selection: caret(99), maxLength: 280)
        XCTAssertEqual(result.text, "kurz🎯")
    }

    func testKatalogIstFreiVonDoppeltenEintraegenUndNichtLeer() {
        let liste = EmojiCatalog.emojis
        XCTAssertGreaterThan(liste.count, 150)
        XCTAssertEqual(liste.count, Set(liste).count)
        XCTAssertTrue(liste.contains("💪"))
    }

    /// Die Längenprüfung zählt Codepoints wie Pythons `len()` im Backend —
    /// sonst ginge eine Bio durch, die der Server mit 422 zurückweist.
    func testLaengeWirdInCodepointsGezaehlt() {
        XCTAssertEqual("💪".backendLength, 1)
        XCTAssertEqual("🏋️‍♀️".backendLength, 5)
        XCTAssertEqual("abc".backendLength, 3)

        let fastVoll = String(repeating: "x", count: 277)
        // „🏋️‍♀️" braucht fünf Codepoints, es bleiben aber nur drei frei.
        let abgelehnt = EmojiInsertion.insert(
            "🏋️‍♀️",
            into: fastVoll,
            selection: caret(277),
            maxLength: 280
        )
        XCTAssertEqual(abgelehnt.text, fastVoll)
    }

    func testKuerzenSchneidetKeinEmojiAuseinander() {
        let text = "abc🏋️‍♀️"
        XCTAssertEqual(text.truncatedToBackendLength(5), "abc")
        XCTAssertEqual(text.truncatedToBackendLength(8), text)
    }
}
