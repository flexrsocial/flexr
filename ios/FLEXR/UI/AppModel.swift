import Combine
import Foundation

/// Startzustand der App — steuert, welcher Navigationsbaum aktiv ist.
enum AppState: Equatable {
    case loading
    case loggedOut
    // `case locked` ist am 10.09.2026 entfallen: Es gibt keinen Zustand mehr,
    // in dem ein angemeldetes Konto die App nicht benutzen darf — die Nutzung
    // von FLEXR ist dauerhaft kostenlos.
    case ready(profile: MyProfile, membership: Membership)
}

/// Hält den app-weiten Sitzungszustand: abgemeldet, ladend oder einsatzbereit.
///
/// Entspricht der `boot()`/`goToApp()`-Logik des Web-Frontends und dem
/// `MainViewModel` der Android-App — hier aber als beobachtbarer Zustand statt
/// als imperativer Bildschirmwechsel.
@MainActor
@Observable
final class AppModel {

    private(set) var state: AppState = .loading
    var selectedTab: TopLevelDestination = .swipe

    /// Der aktuelle Premium-Status, sofern die Sitzung schon steht.
    ///
    /// Bequemlichkeit für Views, die nur die Zahlen brauchen (Preis, Grenzen,
    /// Restkontingent) und nicht den ganzen Zustand auseinandernehmen wollen.
    var membership: Membership? {
        if case .ready(_, let membership) = state { return membership }
        return nil
    }

    /// Kurze Rückmeldung am unteren Rand (Ersatz für die Snackbar).
    var toast: String?

    @ObservationIgnored private let container: AppContainer
    /// Gehört dem App-Delegierten, nicht dem Container: Die Sprachwahl ist eine
    /// Einstellung des Geräts und überlebt das Abmelden (siehe [LanguageStore]).
    @ObservationIgnored private let languageStore: LanguageStore
    @ObservationIgnored private var cancellables: Set<AnyCancellable> = []

    var unreadCount: Int { container.matches.unreadTotal }

    init(container: AppContainer, languageStore: LanguageStore) {
        self.container = container
        self.languageStore = languageStore

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

    /// Sprache zwischen Gerät und Profil abgleichen.
    ///
    /// Wer auf diesem Gerät schon einmal ausdrücklich gewählt hat, hat das
    /// letzte Wort — die Wahl geht ans Profil. Wer noch nie gewählt hat (frische
    /// Installation, neues Gerät), übernimmt, was am Profil steht: Sonst bekäme
    /// jemand, der auf Englisch gestellt hat, auf dem nächsten Gerät wieder
    /// Deutsch, obwohl der Server seine Mails längst auf Englisch schickt.
    ///
    private func syncLanguage(profileLanguage: String) async {
        if languageStore.hasExplicitChoice {
            await container.profiles.reportLanguage(languageStore.language.rawValue)
        } else if let vomProfil = AppLanguage(rawValue: profileLanguage) {
            languageStore.adopt(vomProfil)
        }
    }

    /// Nach Login/Registrierung: Profil und Mitgliedschaft laden.
    func loadSession() async {
        do {
            let profile = try await container.profiles.refresh()
            await syncLanguage(profileLanguage: profile.language)
            let membership = try await container.billing.refresh()
            container.notifications.schedule()
            container.activityNotifications.schedule()
            state = .ready(profile: profile, membership: membership)
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
        container.activityNotifications.cancel()
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

    /// Reiter aus einer angetippten Benachrichtigung heraus wechseln.
    ///
    /// Der Zielwert kommt vom Server (`PushNotification.target`) und wird
    /// bewusst gegen `TopLevelDestination` geprüft statt blind übernommen:
    /// ein unbekannter Wert — etwa aus einer neueren Serverfassung — soll die
    /// App einfach nur öffnen, nicht in einen leeren Zustand schicken.
    func open(target rawValue: String) {
        guard let destination = TopLevelDestination(rawValue: rawValue) else { return }
        selectedTab = destination
    }
}
