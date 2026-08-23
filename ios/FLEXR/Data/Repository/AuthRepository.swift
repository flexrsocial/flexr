import Combine
import Foundation

/// Registrierung, Anmeldung und Sitzungsende.
///
/// Entspricht backend/app/routers/auth.py. Das Feld „interessiert an" gibt es
/// bewusst nicht: das Backend leitet es gegengeschlechtlich aus dem Geschlecht
/// ab (Produktentscheidung), die App bildet das genauso ab.
@MainActor
final class AuthRepository {

    private let api: FlexrAPI
    private let session: SessionStore
    private let store: FlexrStore

    init(api: FlexrAPI, session: SessionStore, store: FlexrStore) {
        self.api = api
        self.session = session
        self.store = store
    }

    var isLoggedIn: AnyPublisher<Bool, Never> { session.isLoggedIn }

    /// Feuert, sobald das Backend eine Anmeldung als abgelaufen zurückweist (401).
    var sessionExpired: AnyPublisher<Void, Never> { session.sessionExpired }

    func register(
        email: String,
        password: String,
        name: String,
        birthdate: Date,
        plz: String,
        city: String,
        gender: Gender,
        gymLabel: String,
        bio: String?,
        consentSensitiveData: Bool,
        consentWithdrawalWaiver: Bool
    ) async throws {
        let trimmedBio = bio?.trimmingCharacters(in: .whitespacesAndNewlines)
        let response = try await api.register(
            RegisterRequestDTO(
                email: email.trimmingCharacters(in: .whitespaces),
                password: password,
                name: name.trimmingCharacters(in: .whitespaces),
                birthdate: ServerTime.formatDate(birthdate),
                plz: plz.trimmingCharacters(in: .whitespaces),
                city: city.trimmingCharacters(in: .whitespaces),
                gender: gender.apiValue,
                gym: gymLabel,
                bio: (trimmedBio?.isEmpty ?? true) ? nil : trimmedBio,
                consentSensitiveData: consentSensitiveData,
                consentWithdrawalWaiver: consentWithdrawalWaiver
            )
        )
        session.save(token: response.accessToken)
    }

    func login(email: String, password: String) async throws {
        let response = try await api.login(
            LoginRequestDTO(email: email.trimmingCharacters(in: .whitespaces), password: password)
        )
        session.save(token: response.accessToken)
    }

    /// Macht eine Selbstlöschung innerhalb der 30-Tage-Karenzzeit rückgängig
    /// und meldet gleich an. Nimmt dieselben Zugangsdaten wie [login] entgegen.
    func reactivate(email: String, password: String) async throws {
        let response = try await api.reactivate(
            LoginRequestDTO(email: email.trimmingCharacters(in: .whitespaces), password: password)
        )
        session.save(token: response.accessToken)
    }

    /// Abmelden: Token verwerfen und den lokalen Bestand leeren.
    func logout() async {
        session.clear()
        store.deleteAll()
        await ImageStore.shared.clear()
    }
}
