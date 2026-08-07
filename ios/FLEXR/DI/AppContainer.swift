import SwiftUI

/// Zentraler Zusammenbau der App.
///
/// Ersetzt Hilt: Es gibt genau eine Instanz jedes Dienstes, sie wird beim Start
/// erzeugt und über die SwiftUI-Umgebung weitergereicht. Ein Grafen-Framework
/// wäre bei dieser Größe Ballast — der Aufbau steht hier in einer Datei und ist
/// damit leichter nachzuvollziehen als eine Sammlung von Modulen.
@MainActor
@Observable
final class AppContainer {

    let session: SessionStore
    let store: FlexrStore
    let api: FlexrAPI

    let auth: AuthRepository
    let profiles: ProfileRepository
    let billing: BillingRepository
    let matches: MatchRepository
    let messages: MessageRepository
    let swipes: SwipeRepository
    let gyms: GymRepository
    let plz: PlzRepository
    let safety: SafetyRepository
    let verification: VerificationRepository
    let notifications: MessageRefreshService

    init() {
        let session = SessionStore()
        let store = FlexrStore()

        let backendClient = APIClient(baseURL: APIConfiguration.baseURL, sessionStore: session)

        let api = FlexrAPI(client: backendClient)
        let plzRepository = PlzRepository(api: BackendPlzAPI(client: backendClient))
        let matchRepository = MatchRepository(api: api, store: store)

        self.session = session
        self.store = store
        self.api = api

        auth = AuthRepository(api: api, session: session, store: store)
        profiles = ProfileRepository(api: api, session: session)
        billing = BillingRepository(api: api)
        matches = matchRepository
        messages = MessageRepository(api: api, store: store)
        swipes = SwipeRepository(api: api)
        plz = plzRepository
        gyms = GymRepository(api: api, plzRepository: plzRepository)
        safety = SafetyRepository(api: api)
        verification = VerificationRepository(api: api)
        notifications = MessageRefreshService(session: session, matches: matchRepository)
    }
}

// Weitergereicht wird der Container über `.environment(container)` in
// `FlexrApp`; Bildschirme holen ihn mit `@Environment(AppContainer.self)`.
// Bewusst ohne `EnvironmentKey`-Vorgabewert: eine zweite, versehentlich
// erzeugte Instanz hätte einen eigenen lokalen Bestand und eigene Sitzung.
