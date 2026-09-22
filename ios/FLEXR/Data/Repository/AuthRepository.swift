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

    /// Läuft gerade eine Registrierung samt Erstupload?
    ///
    /// Siehe [isLoggedIn]: Der Token liegt nach dem Anlegen des Kontos sofort
    /// vor, die Fotos sind aber noch unterwegs.
    private let registrationInFlight = CurrentValueSubject<Bool, Never>(false)

    /// Angemeldet **und** einsatzbereit.
    ///
    /// Während der Registrierung bleibt das bewusst `false`, bis die Fotos oben
    /// sind. Sonst schaltet `AppModel` beim Speichern des Tokens sofort auf die
    /// fertige App um, SwiftUI räumt `RegisterView` ab — und nimmt den noch
    /// laufenden Upload-Task mit. Das Konto stünde dann ohne Fotos da, was der
    /// Server als unfertiges Profil behandelt. Entspricht
    /// `registrationInFlight` der Android-App.
    var isLoggedIn: AnyPublisher<Bool, Never> {
        session.isLoggedIn
            .combineLatest(registrationInFlight)
            .map { loggedIn, inFlight in loggedIn && !inFlight }
            .removeDuplicates()
            .eraseToAnyPublisher()
    }

    /// Klammer um Registrierung und Erstupload. Immer mit `defer` schließen.
    func beginRegistration() { registrationInFlight.send(true) }

    func finishRegistration() { registrationInFlight.send(false) }

    /// Feuert, sobald das Backend eine Anmeldung als abgelaufen zurückweist (401).
    var sessionExpired: AnyPublisher<Void, Never> { session.sessionExpired }

    /// Feuert bei einem 403 mit `verification_required` — das Konto ist
    /// angemeldet, aber nicht freigeschaltet.
    var verificationRequired: AnyPublisher<Void, Never> { session.verificationRequired }

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
        /// Sprache, in der gerade registriert wird ("de" oder "en"). Kommt als
        /// Parameter statt aus dem `LanguageStore`: Der ist an den MainActor
        /// gebunden, dieses Repository soll es nicht sein müssen.
        language: String
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
                language: language
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
    /// „Passwort vergessen": Der Server verrät nicht, ob es das Konto gibt.
    func forgotPassword(email: String, language: String) async throws {
        _ = try await api.forgotPassword(
            PasswordForgotRequestDTO(email: email.trimmingCharacters(in: .whitespaces), language: language)
        )
    }

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
