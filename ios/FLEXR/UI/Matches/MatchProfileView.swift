import SwiftUI

/// Profil eines Matches — der Zwischenschritt vor dem Chat.
///
/// Zeigt dieselbe Karte wie das Deck, aber ohne Wischgeste; stattdessen gibt es
/// „Match auflösen", „Melden" und „Blockieren" direkt auf der Karte.
struct MatchProfileView: View {

    let matchID: String
    let onBack: () -> Void
    let onOpenChat: (String) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var cardState = SwipeCardState()
    @State private var photoIndex = 0
    @State private var lightboxStartIndex: Int?
    @State private var showReportDialog = false
    @State private var showBlockDialog = false
    @State private var showUnmatchDialog = false

    private var match: MatchSummary? { container.matches.match(id: matchID) }

    var body: some View {
        VStack(spacing: 0) {
            BackHeader(
                title: match.map { "\($0.profile.name), \($0.profile.age)" } ?? "Profil",
                onBack: onBack
            )

            if let match {
                SwipeableCard(
                    profile: match.profile,
                    state: cardState,
                    onSwiped: { _ in },
                    onOpenPhotos: { lightboxStartIndex = $0 },
                    onReport: { showReportDialog = true },
                    onBlock: { showBlockDialog = true },
                    photoIndex: $photoIndex,
                    // Auf dem Profil wird nicht gewischt — nur betrachtet.
                    // Melden, Blockieren, Auflösen und die Galerie bleiben aktiv.
                    onUnmatch: { showUnmatchDialog = true },
                    isDraggable: false
                )
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding(.top, 16)

                FlexrButton(title: "Nachricht schreiben", icon: .symbol(FlexrIcon.chats)) {
                    onOpenChat(match.matchID)
                }
                .padding(.vertical, 16)
            } else {
                LoadingStateView()
            }
        }
        .padding(.horizontal, 20)
        .fullScreenCover(isPresented: Binding(
            get: { lightboxStartIndex != nil },
            set: { if !$0 { lightboxStartIndex = nil } }
        )) {
            if let startIndex = lightboxStartIndex, let match {
                PhotoLightbox(photos: match.profile.photos, startIndex: startIndex) { lastIndex in
                    photoIndex = lastIndex
                    lightboxStartIndex = nil
                }
            }
        }
        .sheet(isPresented: $showReportDialog) {
            if let match {
                ReportDialog(
                    userName: match.profile.name,
                    onSubmit: { reason in
                        showReportDialog = false
                        report(userID: match.profile.id, reason: reason)
                    },
                    onDismiss: { showReportDialog = false }
                )
            }
        }
        .confirmDialog(
            isPresented: $showBlockDialog,
            title: match.map { "\($0.profile.name) blockieren?" } ?? "Blockieren?",
            message: "Ihr seht euch danach nicht mehr — das Match und der Chat verschwinden.",
            confirmLabel: "Blockieren",
            onConfirm: block
        )
        .confirmDialog(
            isPresented: $showUnmatchDialog,
            title: match.map { "Match mit \($0.profile.name) auflösen?" } ?? "Match auflösen?",
            message: "Der Chatverlauf wird gelöscht. Die Person kann dir danach erneut "
                + "im Deck begegnen — eine Sperre ist das ausdrücklich nicht.",
            confirmLabel: "Auflösen",
            onConfirm: unmatch
        )
    }

    private func report(userID: String, reason: String) {
        Task {
            do {
                // Empfangsbestätigung mit Aktenzeichen (Art. 16 Abs. 4 DSA)
                let ack = try await container.safety.report(userID: userID, reason: reason)
                appModel.show(ack.message)
            } catch {
                appModel.show(error.localizedDescription)
            }
        }
    }

    private func block() {
        guard let match else { return }
        Task {
            do {
                try await container.safety.block(userID: match.profile.id)
                container.matches.removeLocally(matchID: matchID)
                appModel.show("\(match.profile.name) blockiert.")
                onBack()
            } catch {
                appModel.show(error.localizedDescription)
            }
        }
    }

    private func unmatch() {
        guard let match else { return }
        let name = match.profile.name
        Task {
            do {
                try await container.matches.unmatch(matchID: matchID)
                appModel.show("Match mit \(name) aufgelöst.")
                onBack()
            } catch {
                appModel.show(error.localizedDescription)
            }
        }
    }
}
