import XCTest

@testable import FLEXR

@MainActor
final class PlzRepositoryTests: XCTestCase {

    /// Ortsverzeichnis ohne Netz.
    private final class FakeLookup: PostalCodeLookup, @unchecked Sendable {
        private let response: [OpenPlzLocalityDTO]
        private(set) var callCount = 0

        init(_ response: [OpenPlzLocalityDTO]) {
            self.response = response
        }

        func localities(postalCode: String) async throws -> [OpenPlzLocalityDTO] {
            callCount += 1
            return response
        }
    }

    private func locality(_ name: String, municipality: String?) -> OpenPlzLocalityDTO {
        OpenPlzLocalityDTO(
            name: name,
            postalCode: nil,
            municipality: municipality.map { OpenPlzMunicipalityDTO(name: $0) }
        )
    }

    func testHaeufigsteGemeindeGewinnt() async throws {
        // Wien 1100 liefert mehrere Ortschaften, aber dieselbe Gemeinde —
        // gespeichert wird die Gemeinde, weil darauf die Umkreissuche aufsetzt.
        let api = FakeLookup([
            locality("Wien, Favoriten", municipality: "Wien"),
            locality("Wien, Innere Stadt", municipality: "Wien"),
            locality("Irgendwo", municipality: "Andere Gemeinde"),
        ])
        let repository = PlzRepository(api: api)
        let result = try await repository.municipality(forPostalCode: "1100")
        XCTAssertEqual(result, "Wien")
    }

    func testOhneGemeindenamenGreiftDerOrtsname() async throws {
        let api = FakeLookup([locality("Grafendorf bei Hartberg", municipality: nil)])
        let repository = PlzRepository(api: api)
        let result = try await repository.municipality(forPostalCode: "8232")
        XCTAssertEqual(result, "Grafendorf bei Hartberg")
    }

    func testLeereAntwortMeldetUnbekanntePlz() async {
        let repository = PlzRepository(api: FakeLookup([]))
        do {
            _ = try await repository.municipality(forPostalCode: "9999")
            XCTFail("Erwartet: UnknownPostalCodeError")
        } catch {
            XCTAssertTrue(error is UnknownPostalCodeError)
        }
    }

    func testUngueltigesFormatWirdGarNichtErstAngefragt() async {
        let api = FakeLookup([])
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
        let api = FakeLookup([locality("Graz", municipality: "Graz")])
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
