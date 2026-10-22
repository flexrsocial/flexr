import Combine
import SwiftUI

/// Einstiegspunkt der Oberfläche.
///
/// Je nach Sitzungszustand läuft ein eigener Navigationsbaum: ausgeloggt,
/// zahlungspflichtig gesperrt oder vollständige App. Das hält die Ziele sauber
/// getrennt — ein gesperrtes Konto kann gar nicht erst auf das Deck navigieren,
/// statt dort auf einen 402 zu laufen.
struct RootView: View {

    @Environment(AppModel.self) private var appModel
    @Environment(LanguageStore.self) private var languageStore
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

            case .verificationRequired:
                VerificationGateFlow()

            case .ready(let profile, let membership):
                MainFlow(ownUserID: profile.id, membership: membership)
            }
        }
        .overlay(
            ToastOverlay(
                message: $model.toast,
                bottomInset: toastBottomInset
            )
        )
        .alert(
            languageStore.strings(.reportAckTitle),
            isPresented: Binding(
                get: { model.meldungsBestaetigung != nil },
                set: { if !$0 { model.meldungsBestaetigung = nil } }
            ),
            actions: {
                Button(languageStore.strings(.commonOk)) { model.meldungsBestaetigung = nil }
            },
            message: { Text(model.meldungsBestaetigung ?? "") }
        )
        // Der Sitzungszustand kommt aus dem `isLoggedIn`-Strom des
        // SessionStore; `AppModel` abonniert ihn bei seiner Erzeugung und
        // startet von sich aus mit `.loading`. Bis das Profil geladen ist,
        // steht hier derselbe Ladezustand wie auf dem Startbildschirm — die App
        // springt also nie kurz auf den Login, um dann umzuschalten.
        .onChange(of: scenePhase) { _, phase in
            // Hintergrund: Erst hier wird der Abgleich für Nachrichten und
            // Aktivität angemeldet — siehe AppModel.scheduleBackgroundRefresh().
            if phase == .background {
                appModel.scheduleBackgroundRefresh()
                return
            }
            // Rückkehr aus dem Stripe-Checkout im Browser: Premium-Status neu
            // holen. Früher nur im gesperrten Zustand — den gibt es nicht mehr,
            // also bei jeder Rückkehr in den Vordergrund. Der Aufruf ist billig
            // und hält zugleich das Like-Kontingent aktuell.
            guard phase == .active, case .ready = appModel.state else { return }
            Task { await appModel.refreshMembership() }
        }
        .onOpenURL { url in
            // Mail-Links über die Web-App (Passwort, Reiter), sonst die
            // Rückkehr aus dem Stripe-Checkout.
            if appModel.handleLink(url) { return }
            guard url.scheme == "flexr" else { return }
            Task { await appModel.refreshMembership() }
        }
        .sheet(isPresented: Binding(
            get: { model.resetToken != nil },
            set: { if !$0 { model.resetToken = nil } }
        )) {
            if let token = model.resetToken {
                // Je Link ein frisches Blatt (wie `key(token)` unter Android).
                ResetPasswordSheet(token: token).id(token)
            }
        }
    }
}

extension RootView {
    /// In der App über der Tab-Leiste bzw. im Chat über der Eingabezeile -
    /// mit 12 pt Abstand zum Rand verdeckte die Meldung beides zwei Sekunden
    /// lang. Vor dem Login gibt es unten nichts zu verdecken.
    private var toastBottomInset: CGFloat {
        if case .ready = appModel.state { return 76 }
        return 12
    }
}

// MARK: - Ausgeloggt

private struct AuthFlow: View {

    @State private var path: [Route] = []

    var body: some View {
        NavigationStack(path: $path) {
            VStack(spacing: 0) {
                // Vor dem Login die einzige Stelle, an der die Sprache zu
                // erreichen ist — der Kontobereich setzt ein Konto voraus.
                FlexrTopBar { LanguageSwitch() }
                LoginView(onOpenLegal: { path.append(.legal($0)) })
            }
            .navigationBarHidden(true)
            .flexrRoutes(path: $path)
        }
    }
}

// MARK: - Angemeldet, aber nicht freigeschaltet

/// Der Navigationsbaum eines Kontos, das die Alters- und Identitätsprüfung noch
/// vor sich hat: nur das Gate und die beiden Prüfschritte, keine Tab-Leiste.
///
/// Die Entsprechung des Verifizierungsgraphen der Android-App. Die Rechtstexte
/// bleiben über `flexrRoutes` erreichbar — die Datenschutzerklärung gehört zu
/// dem, was man vor dem Hochladen eines Ausweises lesen können muss.
private struct VerificationGateFlow: View {

    @State private var path: [Route] = []

    var body: some View {
        NavigationStack(path: $path) {
            VStack(spacing: 0) {
                // „Nicht freigeschaltet" gilt für den ganzen Baum, also
                // steht es im Kopf und nicht in einem einzelnen Schritt.
                FlexrTopBar { GateStatusPill() }
                VerificationGateView(
                    // Nach der Rückkehr aus Selfie- oder Ausweisschritt ist der
                    // Prüfstand ein anderer. Die Tiefe des Pfades als Auslöser
                    // statt `onAppear`: Der Wurzelbildschirm bleibt beim
                    // Weiterschalten in der Hierarchie stehen, sein `onAppear`
                    // feuert beim Zurückkommen nicht verlässlich.
                    reloadToken: path.count,
                    onStartSelfies: { path.append(.verification) },
                    onStartDocument: { path.append(.verificationDocument) }
                )
            }
            .navigationBarHidden(true)
            .flexrRoutes(path: $path)
        }
    }
}

/// „Nicht freigeschaltet" im Kopf des Verifizierungsbaums.
///
/// Eigener kleiner Typ, weil die Pille die gewählte Sprache braucht und
/// `VerificationGateFlow` sie sonst nur durchreichen würde.
private struct GateStatusPill: View {
    @Environment(LanguageStore.self) private var languageStore

    var body: some View {
        StatusPill(text: languageStore.strings(.statusNotUnlocked))
    }
}

// Hier stand bis zum 10.09.2026 der `LockedFlow`: der Zustand nach Ablauf des
// Probemonats, in dem nur noch die Bezahlwand erreichbar war. Die Plattform ist
// seither dauerhaft kostenlos — es gibt keinen Zustand mehr, in dem ein
// angemeldetes Konto die App nicht benutzen darf. `PaywallView` ist jetzt ein
// Ziel im Kontobereich und wird aufgerufen, nicht erzwungen.

// MARK: - Vollständige App

private struct MainFlow: View {

    let ownUserID: String
    let membership: Membership

    @Environment(AppModel.self) private var appModel
    @Environment(AppContainer.self) private var container
    @Environment(LanguageStore.self) private var languageStore

    @State private var swipePath: [Route] = []
    @State private var matchesPath: [Route] = []
    @State private var chatsPath: [Route] = []
    @State private var accountPath: [Route] = []
    /// Die Tab-Leiste zeigt immer nur einen Bereich; die anderen werden beim
    /// Wechsel abgebaut. Was den Wechsel überstehen muss, liegt deshalb hier:
    /// das Deck mit der aktuellen Karte und das Kontoformular mit
    /// ungespeicherten Änderungen. Matches und Chats laden beim Betreten
    /// ohnehin neu, ihr Bestand liegt im Repository.
    @State private var swipeModel: SwipeModel?
    @State private var accountModel: AccountModel?
    /// Bei offener Tastatur keine Tab-Leiste: Sie fuhr sonst auf der
    /// Tastatur mit nach oben und nahm dem Formular im Konto die halbe Höhe.
    @State private var isKeyboardVisible = false

    var body: some View {
        @Bindable var model = appModel

        VStack(spacing: 0) {
            if isTopLevel {
                FlexrTopBar {
                    HStack(spacing: 10) {
                        // Direkter Weg zum Angebot, unabhaengig vom
                        // Bildschirm - sichtbar nur, wenn es ueberhaupt
                        // etwas zu aktivieren gibt (nicht schon Premium,
                        // Kauf serverseitig moeglich). Entspricht dem Knopf
                        // im Web (#premiumCtaPill) und in der Android-App.
                        if !membership.isPremium && membership.storePurchaseAvailable {
                            PremiumActivatePill {
                                appModel.selectedTab = .account
                                accountPath.append(.premium)
                            }
                        }
                        MembershipPill(membership: membership)
                    }
                }
            }

            Group {
                switch appModel.selectedTab {
                case .swipe:
                    NavigationStack(path: $swipePath) {
                        SwipeView(model: $swipeModel, onOpenChat: { swipePath.append(.chat(matchID: $0)) })
                            .navigationBarHidden(true)
                            .flexrRoutes(path: $swipePath)
                    }
                case .matches:
                    NavigationStack(path: $matchesPath) {
                        MatchesView(
                            onOpenMatchProfile: { matchesPath.append(.matchProfile(matchID: $0)) },
                            onOpenIncoming: { matchesPath.append(.incoming) },
                            onOpenChat: { matchesPath.append(.chat(matchID: $0)) }
                        )
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
                        AccountView(model: $accountModel, onOpen: { accountPath.append($0) })
                            .navigationBarHidden(true)
                            .flexrRoutes(path: $accountPath)
                    }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            if isTopLevel && !isKeyboardVisible {
                FlexrTabBar(selection: $model.selectedTab, unreadCount: appModel.unreadCount)
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: UIResponder.keyboardWillShowNotification)) { _ in
            isKeyboardVisible = true
        }
        .onReceive(NotificationCenter.default.publisher(for: UIResponder.keyboardWillHideNotification)) { _ in
            isKeyboardVisible = false
        }
        // Über Kopfzeile und Tab-Leiste, wie im Web - nicht nur über dem Deck.
        .overlay {
            if let swipeModel, let matched = swipeModel.matchedWith {
                MatchOverlay(
                    matchedProfile: matched,
                    ownAvatarURL: swipeModel.ownAvatarURL,
                    ownName: languageStore.strings(.swipeOwnName),
                    // Der Chat öffnet im Swipe-Tab; kam die Antwort des
                    // Servers erst nach einem Tab-Wechsel, dorthin zurück.
                    onWriteMessage: {
                        appModel.selectedTab = .swipe
                        swipeModel.openChatWithMatch()
                    },
                    onKeepSwiping: swipeModel.dismissMatchOverlay
                )
                .transition(.opacity)
            }
        }
        .animation(.easeOut(duration: 0.2), value: swipeModel?.matchedWith?.id)
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
                    ChatView(
                        matchID: matchID,
                        onBack: { pop() },
                        onOpenProfile: { path.append(.matchProfile(matchID: $0)) }
                    )
                case .matchProfile(let matchID):
                    MatchProfileView(
                        matchID: matchID,
                        onBack: { pop() },
                        onOpenChat: { id in
                            // Aus dem Chat geöffnet (Tipp auf den Chatkopf):
                            // zurück in diesen Chat statt einen zweiten darauf.
                            if path.dropLast().last == .chat(matchID: id) {
                                pop()
                            } else {
                                path.append(.chat(matchID: id))
                            }
                        }
                    )
                case .verification:
                    VerificationView(
                        onBack: { pop() },
                        // Nach dem Selfie steht der Ausweis an — direkt weiter,
                        // ohne Umweg über den Kontobereich. Der Selfie-Schritt
                        // fällt dabei aus dem Pfad: zurück geht es von dort aus
                        // nicht noch einmal vor die Kamera.
                        onContinueToDocument: {
                            if !path.isEmpty { path.removeLast() }
                            path.append(.verificationDocument)
                        }
                    )
                case .verificationDocument:
                    DocumentView(onBack: { pop() }, onSubmitted: { pop() })
                case .premium:
                    PaywallView(onBack: { pop() })
                // Bewusst kein eigener Tab: Ohne offene Likes gäbe es dort
                // einen Reiter, der meistens ins Leere führt — so taucht der
                // Einstieg nur auf, wenn es etwas zu sehen gibt.
                case .incoming:
                    IncomingView(
                        onBack: { pop() },
                        onOpenPremium: { path.append(.premium) },
                        // Zurückgeliked und "Nachricht schreiben": Der Chat
                        // ersetzt die Liste, zurück geht es in die Matches.
                        onOpenChat: { id in
                            pop()
                            path.append(.chat(matchID: id))
                        }
                    )
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
