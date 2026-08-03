import XCTest

@testable import FLEXR

final class ServerTimeTests: XCTestCase {

    private func utc(_ iso: String) -> Date {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: iso) ?? ISO8601DateFormatter().date(from: iso)!
    }

    func testZeitstempelOhneZeitzoneWirdAlsUTCGelesen() {
        // Das Backend liefert datetime.utcnow() ohne Offset. Würde die App den
        // Wert als Lokalzeit lesen, wäre eine stundengenaue Chat-Sperre um den
        // lokalen Offset verschoben.
        XCTAssertEqual(ServerTime.parse("2026-07-26T20:30:00"), utc("2026-07-26T20:30:00Z"))
    }

    func testZeitstempelMitOffsetBehaeltSeinenOffset() {
        XCTAssertEqual(ServerTime.parse("2026-07-26T22:30:00+02:00"), utc("2026-07-26T20:30:00Z"))
    }

    func testMikrosekundenWerdenAkzeptiert() {
        let parsed = ServerTime.parse("2026-07-26T20:30:00.123456")
        XCTAssertNotNil(parsed)
        // Foundation rechnet Bruchteile auf Millisekunden — für Anzeige und
        // Sperrfristen ist das mehr als genau genug.
        XCTAssertEqual(
            parsed!.timeIntervalSince(utc("2026-07-26T20:30:00Z")),
            0.123,
            accuracy: 0.001
        )
    }

    func testLeererWertErgibtNil() {
        XCTAssertNil(ServerTime.parse(nil))
        XCTAssertNil(ServerTime.parse(""))
    }

    func testAlterWirdWieImBackendBerechnet() {
        let today = ServerTime.parseDate("2026-07-26")!
        // Geburtstag war heute
        XCTAssertEqual(ServerTime.age(from: ServerTime.parseDate("1996-07-26")!, today: today), 30)
        // Geburtstag ist morgen: noch ein Jahr jünger
        XCTAssertEqual(ServerTime.age(from: ServerTime.parseDate("1996-07-27")!, today: today), 29)
        XCTAssertEqual(ServerTime.age(from: ServerTime.parseDate("1996-07-25")!, today: today), 30)
    }

    func testResttageWerdenAufgerundetUndNieNegativ() {
        let now = utc("2026-07-26T12:00:00Z")
        XCTAssertEqual(ServerTime.daysUntil(utc("2026-07-27T00:00:00Z"), now: now), 1)
        XCTAssertEqual(ServerTime.daysUntil(utc("2026-07-28T06:00:00Z"), now: now), 2)
        XCTAssertEqual(ServerTime.daysUntil(utc("2026-07-25T12:00:00Z"), now: now), 0)
    }

    func testGeburtsdatumsgrenzenPassenZuDenAltersgrenzen() {
        let today = ServerTime.parseDate("2026-07-26")!
        let youngest = ServerTime.birthdate(yearsAgo: 18, from: today)
        XCTAssertEqual(ServerTime.age(from: youngest, today: today), 18)
        let oldest = ServerTime.birthdate(yearsAgo: 99, from: today)
        XCTAssertEqual(ServerTime.age(from: oldest, today: today), 99)
    }
}
