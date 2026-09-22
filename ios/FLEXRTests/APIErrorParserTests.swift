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

    /// Login innerhalb der 30-Tage-Karenz nach Selbstlöschung: Das Backend
    /// schickt ein strukturiertes Detail mit `code`, damit der Login die
    /// Reaktivierung anbieten kann statt in eine Sackgasse zu führen.
    func testGeloeschtesKontoWirdAmCodeErkannt() {
        let error = parse(
            403,
            #"{"detail":{"code":"account_deleted","message":"Dieses Konto wurde gelöscht.","#
                + #""reactivate_until":"2026-09-22T18:00:00"}}"#
        )
        XCTAssertTrue(error.isAccountDeleted)
        XCTAssertEqual(error.code, "account_deleted")
        XCTAssertEqual(error.message, "Dieses Konto wurde gelöscht.")
    }

    /// Deck, Matches und Chat sind gesperrt, solange die Alters- und
    /// Identitätsprüfung nicht bestanden ist (`require_activated_account`).
    /// Am Code erkannt und nicht am Text: Die App schaltet daraufhin in das
    /// Verifizierungs-Gate, und daran darf keine Formulierung hängen.
    func testGesperrtesKontoWirdAmCodeErkannt() {
        let error = parse(
            403,
            #"{"detail":{"code":"verification_required","message":"Dein Konto ist noch nicht freigeschaltet."}}"#
        )
        XCTAssertTrue(error.isVerificationRequired)
        XCTAssertEqual(error.message, "Dein Konto ist noch nicht freigeschaltet.")
    }

    func testGewoehnlicherFehlerHatKeinenCode() {
        XCTAssertFalse(parse(403, #"{"detail":"Zugriff nicht möglich."}"#).isAccountDeleted)
        XCTAssertFalse(parse(403, #"{"detail":"Zugriff nicht möglich."}"#).isVerificationRequired)
        // Derselbe Code mit anderem Status ist nicht dieselbe Lage — der
        // Gate-Wechsel hängt an beidem.
        XCTAssertFalse(parse(400, #"{"detail":{"code":"verification_required"}}"#).isVerificationRequired)
    }

    /// 402 hiess frueher "Probemonat abgelaufen". Den Probemonat gibt es seit
    /// dem 10.09.2026 nicht mehr (FLEXR ist dauerhaft kostenlos); der Server
    /// sendet 402 nirgends mehr. Bleibt ein aelterer Server doch einmal dabei,
    /// soll die App eine neutrale Meldung zeigen - nicht die alte Bezahlwand.
    func testZahlungErforderlichZeigtNeutraleMeldung() {
        let error = parse(402, "{}")
        XCTAssertTrue(error.isPaymentRequired)
        XCTAssertNil(error.mutedUntil)
        XCTAssertEqual(error.message, "Diese Funktion steht gerade nicht zur Verfügung.")
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
