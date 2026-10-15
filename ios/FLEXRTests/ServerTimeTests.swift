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

    // MARK: - Chat

    private var wien: Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "Europe/Vienna")!
        return calendar
    }

    func testTageZurueckZaehltKalendertageInOrtszeit() {
        let now = utc("2026-10-15T10:00:00Z")
        // 22:30 UTC am 14.10. ist in Wien schon der 15.10.
        XCTAssertEqual(ServerTime.daysAgo(utc("2026-10-14T22:30:00Z"), now: now, calendar: wien), 0)
        XCTAssertEqual(ServerTime.daysAgo(utc("2026-10-14T21:30:00Z"), now: now, calendar: wien), 1)
        XCTAssertEqual(ServerTime.daysAgo(utc("2026-10-10T07:18:00Z"), now: now, calendar: wien), 5)
    }

    func testTagestrennerNenntWochentagUndDatum() {
        let now = utc("2026-10-15T10:00:00Z")
        XCTAssertEqual(
            ServerTime.formatChatDay(utc("2026-10-10T07:18:00Z"), language: .german, now: now, calendar: wien),
            "Samstag, 10. Oktober"
        )
        XCTAssertEqual(
            ServerTime.formatChatDay(utc("2025-12-31T09:00:00Z"), language: .german, now: now, calendar: wien),
            "Mittwoch, 31. Dezember 2025"
        )
        XCTAssertEqual(
            ServerTime.formatChatDay(utc("2026-10-10T07:18:00Z"), language: .english, now: now, calendar: wien),
            "Saturday 10 October"
        )
    }

    func testChatlisteZeigtUhrzeitOderDatum() {
        let now = utc("2026-10-15T10:00:00Z")
        XCTAssertEqual(
            ServerTime.formatChatListTime(utc("2026-10-15T08:13:00Z"), language: .german, now: now, calendar: wien),
            "10:13"
        )
        XCTAssertEqual(
            ServerTime.formatChatListTime(utc("2026-10-01T07:18:00Z"), language: .german, now: now, calendar: wien),
            "01.10."
        )
        XCTAssertEqual(
            ServerTime.formatChatListTime(utc("2025-12-31T09:00:00Z"), language: .german, now: now, calendar: wien),
            "31.12.25"
        )
    }

    func testVorDerErstenNachrichtJedesTagesStehtEinTrenner() {
        func nachricht(_ id: String, _ zeit: String) -> Message {
            Message(id: id, matchID: "m", senderID: "a", content: id,
                    createdAt: utc(zeit), readAt: nil, wasCensored: false)
        }
        let eintraege = ChatEntry.withDaySeparators(
            [
                nachricht("1", "2026-10-10T07:18:00Z"),
                nachricht("2", "2026-10-14T17:07:00Z"),
                nachricht("3", "2026-10-14T18:00:00Z"),
                nachricht("4", "2026-10-14T22:30:00Z"),
            ],
            calendar: wien
        )
        XCTAssertEqual(
            eintraege.map(\.id),
            ["tag-2026-10-10", "1", "tag-2026-10-14", "2", "3", "tag-2026-10-15", "4"]
        )
    }
}
