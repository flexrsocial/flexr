import XCTest

@testable import FLEXR

/// Seit 13.10.2026 reicht der Umkreis-Regler bis 580 km und läuft quadratisch
/// (siehe `RadiusSkala`). Linear lägen 50 km bei 8 % der Schiene - die kleinen
/// Umkreise wären mit dem Finger kaum zu treffen.
final class RadiusSkalaTests: XCTestCase {

    func testEndenDesReglersSindMinimumUndMaximum() {
        XCTAssertEqual(RadiusSkala.maxKm, 580)
        XCTAssertEqual(RadiusSkala.radius(fromPosition: 0, maxKm: RadiusSkala.maxKm), RadiusSkala.minKm)
        XCTAssertEqual(RadiusSkala.radius(fromPosition: 1, maxKm: RadiusSkala.maxKm), RadiusSkala.maxKm)
    }

    func testKleineUmkreiseBekommenEinenBrauchbarenTeilDerSchiene() {
        let bei50 = RadiusSkala.position(fromRadius: 50, maxKm: RadiusSkala.maxKm)
        let bei20 = RadiusSkala.position(fromRadius: 20, maxKm: RadiusSkala.maxKm)
        XCTAssertEqual(bei50, 0.288, accuracy: 0.01)
        XCTAssertEqual(bei20, 0.176, accuracy: 0.01)
    }

    /// Der Regler zeigt den gespeicherten Wert an; das Zurückrechnen darf ihn
    /// nicht verschieben, sonst ändert schon das Öffnen des Kontos den Umkreis.
    func testJederWertUeberstehtDenWegUeberDieStellung() {
        for km in RadiusSkala.minKm...RadiusSkala.maxKm {
            let stellung = RadiusSkala.position(fromRadius: km, maxKm: RadiusSkala.maxKm)
            XCTAssertEqual(RadiusSkala.radius(fromPosition: stellung, maxKm: RadiusSkala.maxKm), km)
        }
        for km in RadiusSkala.minKm...50 {
            XCTAssertEqual(RadiusSkala.radius(fromPosition: RadiusSkala.position(fromRadius: km, maxKm: 50), maxKm: 50), km)
        }
    }

    func testAusserhalbLiegendeWerteWerdenGekappt() {
        XCTAssertEqual(RadiusSkala.position(fromRadius: 900, maxKm: RadiusSkala.maxKm), 1)
        XCTAssertEqual(RadiusSkala.position(fromRadius: 0, maxKm: RadiusSkala.maxKm), 0)
        XCTAssertEqual(RadiusSkala.radius(fromPosition: 1.5, maxKm: RadiusSkala.maxKm), RadiusSkala.maxKm)
        XCTAssertEqual(RadiusSkala.position(fromRadius: 2, maxKm: 2), 1)
    }

    /// `radius_boost_last_day` kommt als ISO-Datum und wird als Kalendertag
    /// angezeigt, ohne dass die Zeitzone des Geräts den Tag verschiebt.
    func testStartboostDatumWirdGelesenUndAlsTagAngezeigt() throws {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let json = """
        {"is_premium": false, "limits_active": true, "free_max_radius_km": 50,
         "max_radius_km": 580, "radius_boost_last_day": "2026-12-31"}
        """
        let membership = try decoder.decode(MembershipStatusDTO.self, from: Data(json.utf8)).toDomain()
        XCTAssertEqual(membership.maxRadiusKm, 580)
        let bis = try XCTUnwrap(membership.radiusBoostLastDay)
        XCTAssertEqual(ServerTime.formatCalendarDay(bis), "31.12.2026")
        XCTAssertEqual(ServerTime.formatCalendarDay(bis, plusDays: 1), "01.01.2027")

        let ohne = try decoder.decode(MembershipStatusDTO.self, from: Data(#"{"max_radius_km": 50}"#.utf8)).toDomain()
        XCTAssertNil(ohne.radiusBoostLastDay)
    }
}
