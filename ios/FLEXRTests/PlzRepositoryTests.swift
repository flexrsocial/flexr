import XCTest

@testable import FLEXR

@MainActor
final class PlzRepositoryTests: XCTestCase {

    /// PLZ-Lookup ohne Netz.
    private final class FakeLookup: PostalCodeLookup, @unchecked Sendable {
        private let response: () throws -> PlzLookupDTO
        private(set) var callCount = 0

        init(_ response: @escaping () throws -> PlzLookupDTO) {
            self.response = response
        }

        func lookupPostalCode(_ plz: String) async throws -> PlzLookupDTO {
            callCount += 1
            return try response()
        }
    }

    func testOrtKommtVomBackend() async throws {
        let api = FakeLookup { PlzLookupDTO(plz: "4020", city: "Linz") }
        let repository = PlzRepository(api: api)
        let result = try await repository.municipality(forPostalCode: "4020")
        XCTAssertEqual(result, "Linz")
    }

    func testNichtGefundenMeldetUnbekanntePlz() async {
        let api = FakeLookup {
            throw FlexrAPIError(statusCode: 404, message: "Postleitzahl nicht gefunden. Bitte prüfen.")
        }
        let repository = PlzRepository(api: api)
        do {
            _ = try await repository.municipality(forPostalCode: "9999")
            XCTFail("Erwartet: UnknownPostalCodeError")
        } catch {
            XCTAssertTrue(error is UnknownPostalCodeError)
        }
    }

    func testAndereFehlerBleibenUnterscheidbar() async {
        // Netzausfall darf nicht als „PLZ gibt es nicht" beim Nutzer landen.
        let api = FakeLookup {
            throw FlexrAPIError(statusCode: 0, message: "Keine Internetverbindung.")
        }
        let repository = PlzRepository(api: api)
        do {
            _ = try await repository.municipality(forPostalCode: "1010")
            XCTFail("Erwartet: FlexrAPIError")
        } catch let error as FlexrAPIError {
            XCTAssertEqual(error.statusCode, 0)
        } catch {
            XCTFail("Unerwarteter Fehler: \(error)")
        }
    }

    func testUngueltigesFormatWirdGarNichtErstAngefragt() async {
        let api = FakeLookup { PlzLookupDTO(plz: "1010", city: "Wien") }
        let repository = PlzRepository(api: api)
        do {
            _ = try await repository.municipality(forPostalCode: "10")
            XCTFail("Erwartet: InvalidPostalCodeError")
        } catch {
            XCTAssertTrue(error is InvalidPostalCodeError)
        }
        XCTAssertEqual(api.callCount, 0)
    }

    func testWiederholteAbfrageKommtAusDemCache() async throws {
        let api = FakeLookup { PlzLookupDTO(plz: "8010", city: "Graz") }
        let repository = PlzRepository(api: api)
        _ = try await repository.municipality(forPostalCode: "8010")
        _ = try await repository.municipality(forPostalCode: "8010")
        XCTAssertEqual(api.callCount, 1)
    }

    func testFormatpruefungAkzeptiertNurVierZiffern() {
        XCTAssertTrue(PlzRepository.isValidPostalCode("1010"))
        XCTAssertFalse(PlzRepository.isValidPostalCode("101"))
        XCTAssertFalse(PlzRepository.isValidPostalCode("10100"))
        XCTAssertFalse(PlzRepository.isValidPostalCode("A010"))
    }
}
