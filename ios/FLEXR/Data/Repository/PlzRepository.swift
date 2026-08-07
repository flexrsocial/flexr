import Foundation

/// Fehler, wenn zu einer eingegebenen PLZ kein österreichischer Ort existiert.
struct UnknownPostalCodeError: LocalizedError {
    var errorDescription: String? { "Postleitzahl nicht gefunden. Bitte prüfen." }
}

/// Fehler, wenn die Eingabe gar keine vierstellige PLZ ist.
struct InvalidPostalCodeError: LocalizedError {
    var errorDescription: String? { "Ungültige Postleitzahl." }
}

/// Ortsermittlung zur Postleitzahl über das eigene Backend.
///
/// Gespeichert wird der amtliche Ortsname zur PLZ (z. B. „Wien", „Linz"), nicht
/// die einzelne Ortschaft. Bis Version 2.0.9 fragten alle Clients dafür
/// openplzapi.org direkt an und wählten aus dessen Ortschaftsliste die
/// häufigste Gemeinde — das lieferte bei großen PLZ die Umlandgemeinde (4020
/// wurde zu „Leonding" statt „Linz") und war für die Apps zeitweise gar nicht
/// erreichbar.
@MainActor
final class PlzRepository {

    /// Vier ASCII-Ziffern — dasselbe Muster wie serverseitig.
    static func isValidPostalCode(_ value: String) -> Bool {
        value.count == 4 && value.allSatisfy { $0.isASCII && $0.isNumber }
    }

    private let api: any PostalCodeLookup
    private var cache: [String: String] = [:]

    init(api: any PostalCodeLookup) {
        self.api = api
    }

    func municipality(forPostalCode postalCode: String) async throws -> String {
        let plz = postalCode.trimmingCharacters(in: .whitespaces)
        // Ungültiges Format wird gar nicht erst angefragt.
        guard Self.isValidPostalCode(plz) else {
            throw InvalidPostalCodeError()
        }
        if let cached = cache[plz] { return cached }

        let city: String
        do {
            city = try await api.lookupPostalCode(plz).city
        } catch let error as FlexrAPIError where error.statusCode == 404 {
            throw UnknownPostalCodeError()
        }

        cache[plz] = city
        return city
    }
}

/// Fitnessstudios: durchsuchbare Liste (OSM-Import + freigegebene Vorschläge)
/// und die Vorschlagsfunktion für fehlende Studios.
@MainActor
final class GymRepository {

    private let api: FlexrAPI
    private let plzRepository: PlzRepository

    init(api: FlexrAPI, plzRepository: PlzRepository) {
        self.api = api
        self.plzRepository = plzRepository
    }

    func search(query: String) async throws -> [Gym] {
        try await api.searchGyms(query: query.trimmingCharacters(in: .whitespaces))
            .map { $0.toDomain() }
    }

    /// Vorschlag einreichen. Der Ort wird — wie im Web — still über die
    /// PLZ-Datenbank ermittelt; schlägt das fehl, bleibt er leer und der Admin
    /// ergänzt ihn bei der Freigabe.
    func suggest(name: String, street: String, houseNumber: String, plz: String) async throws -> Gym {
        let city = try? await plzRepository.municipality(forPostalCode: plz)
        return try await api.suggestGym(
            GymSuggestRequestDTO(
                name: name.trimmingCharacters(in: .whitespaces),
                street: street.trimmingCharacters(in: .whitespaces),
                houseNumber: houseNumber.trimmingCharacters(in: .whitespaces),
                plz: plz.trimmingCharacters(in: .whitespaces),
                city: (city?.isEmpty ?? true) ? nil : city
            )
        ).toDomain()
    }
}
