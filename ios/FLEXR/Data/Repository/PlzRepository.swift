import Foundation

/// Fehler, wenn zu einer eingegebenen PLZ kein österreichischer Ort existiert.
struct UnknownPostalCodeError: LocalizedError {
    var errorDescription: String? { "Postleitzahl nicht gefunden. Bitte prüfen." }
}

/// Fehler, wenn die Eingabe gar keine vierstellige PLZ ist.
struct InvalidPostalCodeError: LocalizedError {
    var errorDescription: String? { "Ungültige Postleitzahl." }
}

/// Ortsermittlung zur Postleitzahl über die OpenPLZ-API.
///
/// Gespeichert wird der GEMEINDE-Name (z. B. „Wien", „Graz"), nicht die einzelne
/// Ortschaft („Wien, Favoriten") — die Gemeinde ist die sinnvolle Ebene für die
/// Umkreissuche. Heuristik wie im Web: der häufigste Gemeindename unter allen
/// Treffern der PLZ.
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

        let localities = try await api.localities(postalCode: plz)
        if localities.isEmpty { throw UnknownPostalCodeError() }

        var counts: [String: Int] = [:]
        for locality in localities {
            guard let name = locality.municipality?.name else { continue }
            counts[name, default: 0] += 1
        }

        let municipality = counts.max { lhs, rhs in
            lhs.value == rhs.value ? lhs.key > rhs.key : lhs.value < rhs.value
        }?.key
            ?? localities.compactMap(\.name).first

        guard let municipality else { throw UnknownPostalCodeError() }

        cache[plz] = municipality
        return municipality
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
