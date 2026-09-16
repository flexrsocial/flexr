import SwiftUI

/// Alle Matches — der Einstieg ins Profil und von dort in den Chat.
///
/// Beide Listen (Matches und Chats) lesen aus demselben lokalen Bestand:
/// „Matches" zeigt alle, „Chats" nur die mit laufender Unterhaltung — genau die
/// Trennung, die auch die Web-App vornimmt.
struct MatchesView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    /// Gleiche Kadenz wie der Web-Poll (`refreshUnreadBadge`, alle 20s).
    private static let pollInterval: Duration = .seconds(20)

    let onOpenMatchProfile: (String) -> Void
    let onOpenIncoming: () -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel
    @State private var isRefreshing = true
    @State private var incoming: IncomingLikes?

    var body: some View {
        MatchListScreen(
            eyebrow: s(.matchesEyebrow),
            title: s(.matchesTitle),
            matches: container.matches.matches,
            isRefreshing: isRefreshing,
            emptyIcon: .symbol(FlexrIcon.matches),
            emptyTitle: s(.matchesEmptyTitle),
            emptyMessage: s(.matchesEmptySub),
            onRefresh: refresh,
            header: {
                // Die Karte zeigt die Zahl immer, die Namen nur mit Premium.
                // Ohne offene Likes bleibt sie ganz weg — eine „0" wäre eine
                // Enttäuschung ohne Anlass.
                if let incoming, incoming.count > 0 {
                    IncomingLikesCard(
                        count: incoming.count,
                        premiumRequired: incoming.premiumRequired,
                        onTap: onOpenIncoming
                    )
                    .padding(.horizontal, 20)
                    .padding(.top, 16)
                }
            }
        ) { match in
            MatchListItem(match: match, onTap: { onOpenMatchProfile(match.matchID) })
        }
        .task { await refresh() }
        .task { await pollWhileVisible() }
    }

    private func refresh() async {
        isRefreshing = true
        do {
            _ = try await container.matches.refresh()
        } catch {
            appModel.show(
                (error as? FlexrAPIError)?.message ?? s(.matchesLoadFailed)
            )
        }
        await loadIncoming()
        isRefreshing = false
    }

    /// Beiwerk über der Matchliste: Ein Fehler hier darf die Liste nicht
    /// verderben, deshalb ohne Meldung — die Karte bleibt dann einfach weg.
    private func loadIncoming() async {
        incoming = try? await container.swipes.incomingLikes()
    }

    /// Hält die Liste aktuell, während der Bildschirm sichtbar ist — SwiftUI
    /// bricht die Aufgabe beim Verlassen automatisch ab (wie `ChatModel.poll()`).
    /// Bewusst ohne Ladezustand/Fehlerbanner: ein 20s-Hintergrundabgleich soll
    /// nicht sichtbar aufblitzen, das übernimmt weiterhin `refresh()` beim
    /// Betreten und beim Ziehen zum Aktualisieren.
    private func pollWhileVisible() async {
        while !Task.isCancelled {
            try? await Task.sleep(for: Self.pollInterval)
            _ = try? await container.matches.refresh()
            await loadIncoming()
        }
    }
}

/// Nur Matches mit laufender Unterhaltung.
struct ChatsView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    /// Gleiche Kadenz wie der Web-Poll (`refreshUnreadBadge`, alle 20s).
    private static let pollInterval: Duration = .seconds(20)

    let ownUserID: String
    let onOpenChat: (String) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel
    @State private var isRefreshing = true

    var body: some View {
        MatchListScreen(
            eyebrow: s(.chatsEyebrow),
            title: s(.chatsTitle),
            matches: container.matches.conversations,
            isRefreshing: isRefreshing,
            emptyIcon: .symbol(FlexrIcon.chats),
            emptyTitle: s(.chatsEmptyTitle),
            emptyMessage: s(.chatsEmptySub),
            onRefresh: refresh,
            header: { EmptyView() }
        ) { match in
            MatchListItem(
                match: match,
                onTap: { onOpenChat(match.matchID) },
                ownUserID: ownUserID,
                showsLastMessage: true
            )
        }
        .task { await refresh() }
        .task { await pollWhileVisible() }
    }

    private func refresh() async {
        isRefreshing = true
        do {
            _ = try await container.matches.refresh()
        } catch {
            appModel.show(
                (error as? FlexrAPIError)?.message ?? s(.matchesLoadFailed)
            )
        }
        isRefreshing = false
    }

    /// Hält die Liste aktuell, während der Bildschirm sichtbar ist — SwiftUI
    /// bricht die Aufgabe beim Verlassen automatisch ab (wie `ChatModel.poll()`).
    /// Bewusst ohne Ladezustand/Fehlerbanner: ein 20s-Hintergrundabgleich soll
    /// nicht sichtbar aufblitzen, das übernimmt weiterhin `refresh()` beim
    /// Betreten und beim Ziehen zum Aktualisieren.
    private func pollWhileVisible() async {
        while !Task.isCancelled {
            try? await Task.sleep(for: Self.pollInterval)
            _ = try? await container.matches.refresh()
        }
    }
}

/// Gemeinsames Gerüst beider Listen inklusive Zum-Aktualisieren-Ziehen.
private struct MatchListScreen<Row: View, Header: View>: View {

    let eyebrow: String
    let title: String
    let matches: [MatchSummary]
    let isRefreshing: Bool
    let emptyIcon: FlexrGlyph.Kind
    let emptyTitle: String
    let emptyMessage: String
    let onRefresh: () async -> Void
    /// Zwischen Überschrift und Liste — die Chats-Ansicht lässt ihn leer.
    @ViewBuilder let header: () -> Header
    @ViewBuilder let row: (MatchSummary) -> Row

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ScreenHeader(eyebrow: eyebrow, title: title)
                .padding(.top, 18)
                .padding(.horizontal, 20)

            header()

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

/// „Wer dich geliket hat" als Karte über der Matchliste (`.incoming-card`).
///
/// Die Zahl steht im Kreis links daneben — deshalb kommt sie im Satz daneben
/// nicht noch einmal vor.
private struct IncomingLikesCard: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let count: Int
    let premiumRequired: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                Text("\(count)")
                    .flexrText(.titleMedium)
                    .foregroundStyle(FlexrColor.plateInk)
                    .frame(width: 34, height: 34)
                    .background(Circle().fill(FlexrColor.plate))

                VStack(alignment: .leading, spacing: 2) {
                    Text(count == 1 ? s(.incomingTitleOne) : s(.incomingTitle))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalk)
                        .lineLimit(1)
                    Text(premiumRequired ? s(.incomingSubFree) : s(.incomingSubPremium))
                        .flexrText(.bodySmall)
                        .foregroundStyle(FlexrColor.chalkDim)
                        .lineLimit(1)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                Image(systemName: FlexrIcon.forward)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(FlexrColor.chalkDim)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 11)
            .flexrSurface(
                fill: FlexrColor.plate.opacity(0.08),
                border: FlexrColor.plateDim
            )
        }
        .buttonStyle(.plain)
    }
}
