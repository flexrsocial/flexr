import Combine
import Foundation

/// Startzustand der App — steuert, welcher Navigationsbaum aktiv ist.
enum AppState: Equatable {
    case loading
    case loggedOut
    // `case locked` ist am 10.09.2026 entfallen: Es gibt keinen Zustand mehr,
    // in dem ein angemeldetes Konto die App aus Zahlungsgründen nicht benutzen
    // darf — die Nutzung von FLEXR ist dauerhaft kostenlos.

    /// Angemeldet, aber nicht freigeschaltet: Die Alters- und
    /// Identitätsprüfung steht noch aus oder ist gescheitert.
    ///
    /// Ein eigener Zustand und nicht ein Hinweis innerhalb der App, weil das
    /// Backend Deck, Matches und Chat mit 403 sperrt
    /// (`require_activated_account`). Ohne ihn zeigte die App die volle
    /// Oberfläche, in der jeder Aufruf ins Leere liefe — die Entsprechung des
    /// eigenen Navigationsgraphen der Android-App.
    case verificationRequired(profile: MyProfile)

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
    ///
    /// Gelesen wird **durch** auf das Repository, nicht aus der Kopie im
    /// `state`: Das Restkontingent ändert sich nach jedem Like und nach jedem
    /// zurückgenommenen Swipe (`BillingRepository.updateLikesRemaining`). Die
    /// Kopie im Zustand entsteht nur beim Anmelden — die Pille im Kopf zeigte
    /// sonst den Stand vom App-Start, bis sich jemand neu anmeldet. Der
    /// Rückfall auf den Zustand bleibt, damit `.ready` weiterhin das Kriterium
    /// dafür ist, ob überhaupt etwas anzuzeigen ist.
    var membership: Membership? {
        guard case .ready(_, let fromState) = state else { return nil }
        return container.billing.membership ?? fromState
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

        // 403 `verification_required`: Die Freischaltung wurde während der
        // laufenden Sitzung entzogen. Die Anmeldung bleibt, der Zustand wird
        // neu bestimmt — daraufhin steht die App im Gate.
        container.auth.verificationRequired
            .receive(on: DispatchQueue.main)
            .sink { [weak self] in
                MainActor.assumeIsolated {
                    guard let self else { return }
                    guard case .ready = self.state else { return }
                    Task { await self.loadSession() }
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

    /// Hintergrundabgleich anmelden, wenn die App in den Hintergrund geht.
    ///
    /// Genau dann und nicht bei jedem Laden der Sitzung: `BGTaskScheduler`
    /// merkt sich je Kennung **einen** Auftrag, und jedes erneute `submit`
    /// setzt dessen `earliestBeginDate` wieder auf "in 15 Minuten". Da
    /// `loadSession()` bei jeder Rückkehr in den Vordergrund läuft, schob
    /// bisher jeder App-Start den frühestmöglichen Lauf weiter nach hinten —
    /// wer die App oft öffnete, bei dem kam der Abgleich nie dran, und die
    /// Benachrichtigung erschien erst beim nächsten Öffnen. Der Wechsel in
    /// den Hintergrund ist auch der von Apple dafür vorgesehene Zeitpunkt.
    func scheduleBackgroundRefresh() {
        guard case .ready = state else { return }
        container.notifications.schedule()
        container.activityNotifications.schedule()
    }

    /// Nach Login/Registrierung: Profil und Mitgliedschaft laden.
    func loadSession() async {
        do {
            let profile = try await container.profiles.refresh()
            await syncLanguage(profileLanguage: profile.language)

            // Vor allem anderen: Ein nicht freigeschaltetes Konto bekommt nur
            // das Gate zu sehen. Abo-Status und Benachrichtigungen bleiben
            // dabei ungefragt — es gibt weder Matches noch Nachrichten, über
            // die zu benachrichtigen wäre.
            guard profile.isAccountActivated else {
                container.notifications.cancel()
                container.activityNotifications.cancel()
                state = .verificationRequired(profile: profile)
                return
            }

            let membership = try await container.billing.refresh()
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
