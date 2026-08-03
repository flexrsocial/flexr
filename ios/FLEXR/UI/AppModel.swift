import Combine
import Foundation

/// Startzustand der App — steuert, welcher Navigationsbaum aktiv ist.
enum AppState: Equatable {
    case loading
    case loggedOut
    /// Angemeldet, aber Probemonat abgelaufen und kein Abo: nur die Paywall.
    case locked(Membership)
    case ready(profile: MyProfile, membership: Membership)
}

/// Hält den app-weiten Sitzungszustand: angemeldet, zahlungspflichtig gesperrt
/// oder einsatzbereit.
///
/// Entspricht der `boot()`/`goToApp()`-Logik des Web-Frontends und dem
/// `MainViewModel` der Android-App — hier aber als beobachtbarer Zustand statt
/// als imperativer Bildschirmwechsel.
@MainActor
@Observable
final class AppModel {

    private(set) var state: AppState = .loading
    var selectedTab: TopLevelDestination = .swipe

    /// Kurze Rückmeldung am unteren Rand (Ersatz für die Snackbar).
    var toast: String?

    @ObservationIgnored private let container: AppContainer
    @ObservationIgnored private var cancellables: Set<AnyCancellable> = []

    var unreadCount: Int { container.matches.unreadTotal }

    init(container: AppContainer) {
        self.container = container

        // `receive(on:)` ist nicht kosmetisch: Der 401-Zweig des APIClient feuert
        // aus dem URLSession-Thread, der Zustand hier gehört auf den MainActor.
        container.auth.isLoggedIn
            .receive(on: DispatchQueue.main)
            .sink { [weak self] loggedIn in
                MainActor.assumeIsolated {
                    guard let self else { return }
                    if loggedIn {
                        Task { await self.loadSession() }
                    } else {
                        self.state = .loggedOut
                    }
                }
            }
            .store(in: &cancellables)

        // 401 vom Backend: Sitzung ist weg, zurück auf den Login.
        container.auth.sessionExpired
            .receive(on: DispatchQueue.main)
            .sink { [weak self] in
                MainActor.assumeIsolated {
                    guard let self else { return }
                    Task { await self.logout() }
                }
            }
            .store(in: &cancellables)
    }

    /// Nach Login/Registrierung: Profil und Mitgliedschaft laden.
    func loadSession() async {
        do {
            let profile = try await container.profiles.refresh()
            let membership = try await container.billing.refresh()
            if membership.isActive {
                container.notifications.schedule()
                state = .ready(profile: profile, membership: membership)
            } else {
                container.notifications.cancel()
                state = .locked(membership)
            }
        } catch {
            // Token ungültig oder Server nicht erreichbar — bei 401 hat der
            // APIClient bereits abgemeldet und `sessionExpired` gefeuert.
            if state == .loading { state = .loggedOut }
        }
    }

    /// Nach Rückkehr aus dem Stripe-Checkout: Abo-Status neu holen.
    func refreshMembership() async {
        guard container.session.isLoggedInNow else { return }
        await loadSession()
    }

    func logout() async {
        container.notifications.cancel()
        await container.auth.logout()
        container.profiles.clear()
        container.billing.clear()
        container.matches.clearLocalCache()
        selectedTab = .swipe
        state = .loggedOut
    }

    func show(_ message: String) {
        toast = message
    }

    func openChatsTab() {
        selectedTab = .chats
    }
}
