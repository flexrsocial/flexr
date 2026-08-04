import SwiftUI

/// Einstiegspunkt der Oberfläche.
///
/// Je nach Sitzungszustand läuft ein eigener Navigationsbaum: ausgeloggt,
/// zahlungspflichtig gesperrt oder vollständige App. Das hält die Ziele sauber
/// getrennt — ein gesperrtes Konto kann gar nicht erst auf das Deck navigieren,
/// statt dort auf einen 402 zu laufen.
struct RootView: View {

    @Environment(AppModel.self) private var appModel
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        @Bindable var model = appModel

        ZStack {
            FlexrBackground()

            switch appModel.state {
            case .loading:
                LoadingStateView()

            case .loggedOut:
                AuthFlow()

            case .locked(let membership):
                LockedFlow(membership: membership)

            case .ready(let profile, let membership):
                MainFlow(ownUserID: profile.id, membership: membership)
            }
        }
        .overlay(ToastOverlay(message: $model.toast))
        // Der Sitzungszustand kommt aus dem `isLoggedIn`-Strom des
        // SessionStore; `AppModel` abonniert ihn bei seiner Erzeugung und
        // startet von sich aus mit `.loading`. Bis das Profil geladen ist,
        // steht hier derselbe Ladezustand wie auf dem Startbildschirm — die App
        // springt also nie kurz auf den Login, um dann umzuschalten.
        .onChange(of: scenePhase) { _, phase in
            // Rückkehr aus dem Stripe-Checkout im Browser: Abo-Status neu holen.
            guard phase == .active, case .locked = appModel.state else { return }
            Task { await appModel.refreshMembership() }
        }
        .onOpenURL { url in
            guard url.scheme == "flexr" else { return }
            Task { await appModel.refreshMembership() }
        }
    }
}

// MARK: - Ausgeloggt

private struct AuthFlow: View {

    @State private var path: [Route] = []

    var body: some View {
        NavigationStack(path: $path) {
            VStack(spacing: 0) {
                FlexrTopBar { EmptyView() }
                LoginView(onOpenLegal: { path.append(.legal($0)) })
            }
            .navigationBarHidden(true)
            .flexrRoutes(path: $path)
        }
    }
}

// MARK: - Angemeldet, aber Probemonat abgelaufen

private struct LockedFlow: View {

    let membership: Membership
    @State private var path: [Route] = []

    var body: some View {
        NavigationStack(path: $path) {
            VStack(spacing: 0) {
                FlexrTopBar { MembershipPill(membership: membership) }
                PaywallView()
            }
            .navigationBarHidden(true)
            .flexrRoutes(path: $path)
        }
    }
}

// MARK: - Vollständige App

private struct MainFlow: View {

    let ownUserID: String
    let membership: Membership

    @Environment(AppModel.self) private var appModel
    @Environment(AppContainer.self) private var container

    @State private var swipePath: [Route] = []
    @State private var matchesPath: [Route] = []
    @State private var chatsPath: [Route] = []
    @State private var accountPath: [Route] = []

    var body: some View {
        @Bindable var model = appModel

        VStack(spacing: 0) {
            if isTopLevel {
                FlexrTopBar { MembershipPill(membership: membership) }
            }

            Group {
                switch appModel.selectedTab {
                case .swipe:
                    NavigationStack(path: $swipePath) {
                        SwipeView(onOpenChat: { swipePath.append(.chat(matchID: $0)) })
                            .navigationBarHidden(true)
                            .flexrRoutes(path: $swipePath)
                    }
                case .matches:
                    NavigationStack(path: $matchesPath) {
                        MatchesView(onOpenMatchProfile: { matchesPath.append(.matchProfile(matchID: $0)) })
                            .navigationBarHidden(true)
                            .flexrRoutes(path: $matchesPath)
                    }
                case .chats:
                    NavigationStack(path: $chatsPath) {
                        ChatsView(
                            ownUserID: ownUserID,
                            onOpenChat: { chatsPath.append(.chat(matchID: $0)) }
                        )
                        .navigationBarHidden(true)
                        .flexrRoutes(path: $chatsPath)
                    }
                case .account:
                    NavigationStack(path: $accountPath) {
                        AccountView(onOpen: { accountPath.append($0) })
                            .navigationBarHidden(true)
                            .flexrRoutes(path: $accountPath)
                    }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            if isTopLevel {
                FlexrTabBar(selection: $model.selectedTab, unreadCount: appModel.unreadCount)
            }
        }
    }

    /// Unterseiten (Chat, Profil, Verifizierung, Rechtstexte) laufen wie in der
    /// Android-App ohne Kopf- und Fußleiste — sie bringen ihre eigene mit.
    private var isTopLevel: Bool {
        switch appModel.selectedTab {
        case .swipe: swipePath.isEmpty
        case .matches: matchesPath.isEmpty
        case .chats: chatsPath.isEmpty
        case .account: accountPath.isEmpty
        }
    }
}

// MARK: - Gemeinsame Ziele

private struct FlexrRoutes: ViewModifier {

    @Binding var path: [Route]

    func body(content: Content) -> some View {
        content.navigationDestination(for: Route.self) { route in
            Group {
                switch route {
                case .chat(let matchID):
                    ChatView(matchID: matchID, onBack: { pop() })
                case .matchProfile(let matchID):
                    MatchProfileView(
                        matchID: matchID,
                        onBack: { pop() },
                        onOpenChat: { path.append(.chat(matchID: $0)) }
                    )
                case .verification:
                    VerificationView(onBack: { pop() })
                case .legal(let document):
                    LegalView(document: document, onBack: { pop() })
                }
            }
            .navigationBarHidden(true)
            .background(FlexrBackground())
        }
    }

    private func pop() {
        if !path.isEmpty { path.removeLast() }
    }
}

extension View {
    /// Rechtstexte und Unterseiten sind aus jedem Tab erreichbar.
    func flexrRoutes(path: Binding<[Route]>) -> some View {
        modifier(FlexrRoutes(path: path))
    }
}
