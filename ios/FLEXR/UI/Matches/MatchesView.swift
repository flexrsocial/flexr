import SwiftUI

/// Alle Matches — der Einstieg ins Profil und von dort in den Chat.
///
/// Beide Listen (Matches und Chats) lesen aus demselben lokalen Bestand:
/// „Matches" zeigt alle, „Chats" nur die mit laufender Unterhaltung — genau die
/// Trennung, die auch die Web-App vornimmt.
struct MatchesView: View {

    let onOpenMatchProfile: (String) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel
    @State private var isRefreshing = true

    var body: some View {
        MatchListScreen(
            eyebrow: "Trefferquote",
            title: "Deine Matches",
            matches: container.matches.matches,
            isRefreshing: isRefreshing,
            emptyIcon: .symbol(FlexrIcon.matches),
            emptyTitle: "Noch keine Matches",
            emptyMessage: "Weiter swipen — dein nächster Trainingspartner wartet schon.",
            onRefresh: refresh
        ) { match in
            MatchListItem(match: match, onTap: { onOpenMatchProfile(match.matchID) })
        }
        .task { await refresh() }
    }

    private func refresh() async {
        isRefreshing = true
        do {
            _ = try await container.matches.refresh()
        } catch {
            appModel.show(
                (error as? FlexrAPIError)?.message ?? "Matches konnten nicht geladen werden."
            )
        }
        isRefreshing = false
    }
}

/// Nur Matches mit laufender Unterhaltung.
struct ChatsView: View {

    let ownUserID: String
    let onOpenChat: (String) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel
    @State private var isRefreshing = true

    var body: some View {
        MatchListScreen(
            eyebrow: "Im Gespräch",
            title: "Deine Chats",
            matches: container.matches.conversations,
            isRefreshing: isRefreshing,
            emptyIcon: .symbol(FlexrIcon.chats),
            emptyTitle: "Noch keine Chats",
            emptyMessage: "Schreib einem deiner Matches die erste Nachricht.",
            onRefresh: refresh
        ) { match in
            MatchListItem(
                match: match,
                onTap: { onOpenChat(match.matchID) },
                ownUserID: ownUserID,
                showsLastMessage: true
            )
        }
        .task { await refresh() }
    }

    private func refresh() async {
        isRefreshing = true
        do {
            _ = try await container.matches.refresh()
        } catch {
            appModel.show(
                (error as? FlexrAPIError)?.message ?? "Matches konnten nicht geladen werden."
            )
        }
        isRefreshing = false
    }
}

/// Gemeinsames Gerüst beider Listen inklusive Zum-Aktualisieren-Ziehen.
private struct MatchListScreen<Row: View>: View {

    let eyebrow: String
    let title: String
    let matches: [MatchSummary]
    let isRefreshing: Bool
    let emptyIcon: FlexrGlyph.Kind
    let emptyTitle: String
    let emptyMessage: String
    let onRefresh: () async -> Void
    @ViewBuilder let row: (MatchSummary) -> Row

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ScreenHeader(eyebrow: eyebrow, title: title)
                .padding(.top, 18)
                .padding(.horizontal, 20)

            if matches.isEmpty, !isRefreshing {
                ScrollView {
                    EmptyStateView(icon: emptyIcon, title: emptyTitle, message: emptyMessage)
                }
                .refreshable { await onRefresh() }
            } else {
                ScrollView {
                    LazyVStack(spacing: 10) {
                        ForEach(matches) { match in
                            row(match)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 16)
                    .padding(.bottom, 12)
                }
                .refreshable { await onRefresh() }
            }
        }
    }
}
