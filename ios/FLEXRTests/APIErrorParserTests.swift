import XCTest

@testable import FLEXR

final class APIErrorParserTests: XCTestCase {

    private func parse(_ code: Int, _ body: String) -> FlexrAPIError {
        APIErrorParser.fromResponse(statusCode: code, body: Data(body.utf8))
    }

    func testDetailAlsTextWirdUebernommen() {
        let error = parse(409, #"{"detail":"E-Mail bereits registriert."}"#)
        XCTAssertEqual(error.statusCode, 409)
        XCTAssertEqual(error.message, "E-Mail bereits registriert.")
    }

    func testPydanticFehlerlisteWirdZusammengefasst() {
        let error = parse(
            422,
            #"{"detail":[{"msg":"Du musst mindestens 18 Jahre alt sein."},{"msg":"PLZ ungültig."}]}"#
        )
        XCTAssertEqual(error.message, "Du musst mindestens 18 Jahre alt sein., PLZ ungültig.")
    }

    func testChatSperreLiefertDasEnddatum() {
        let error = parse(
            403,
            #"{"detail":{"reason":"messaging_muted","muted_until":"2026-08-01T10:00:00","#
                + #""message":"Deine Chat-Sperre ist noch aktiv."}}"#
        )
        XCTAssertTrue(error.isMessagingMuted)
        XCTAssertEqual(error.mutedUntil, ServerTime.parse("2026-08-01T10:00:00"))
        XCTAssertEqual(error.message, "Deine Chat-Sperre ist noch aktiv.")
    }

    func testModerationsbegruendungWirdMitgefuehrt() {
        // Art. 17 DSA: Grund und Widerspruchsweg gehören zur Beschränkung dazu.
        let error = parse(
            403,
            #"{"detail":{"message":"Konto gesperrt.","moderation_reason":"Spam",""#
                + #"appeal_hint":"Widerspruch an flexr.social@proton.me"}}"#
        )
        XCTAssertEqual(error.moderationReason, "Spam")
        XCTAssertEqual(error.appealHint, "Widerspruch an flexr.social@proton.me")
    }

    func testAbgelaufeneMitgliedschaftWirdErkannt() {
        let error = parse(402, "{}")
        XCTAssertTrue(error.isPaymentRequired)
        XCTAssertNil(error.mutedUntil)
        XCTAssertEqual(error.message, "Probemonat abgelaufen. Bitte Abo abschließen.")
    }

    func testNetzfehlerWerdenInVerstaendlicheMeldungenUebersetzt() {
        XCTAssertEqual(
            APIErrorParser.fromTransport(URLError(.notConnectedToInternet)).message,
            "Keine Internetverbindung."
        )
        XCTAssertEqual(
            APIErrorParser.fromTransport(URLError(.timedOut)).message,
            "Zeitüberschreitung. Bitte Verbindung prüfen und erneut versuchen."
        )
        XCTAssertEqual(
            APIErrorParser.fromTransport(URLError(.networkConnectionLost)).message,
            "Verbindung fehlgeschlagen. Bitte erneut versuchen."
        )
    }

    func testBereitsUebersetzterFehlerBleibtUnveraendert() {
        let original = FlexrAPIError(statusCode: 418, message: "Bereits übersetzt.")
        XCTAssertEqual(APIErrorParser.fromTransport(original), original)
    }
}
