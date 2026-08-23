import Foundation

/// Match-Liste mit lokalem Bestand als Single Source of Truth.
///
/// Die Oberfläche liest ausschließlich aus [FlexrStore], das Netz füllt nach.
/// Dadurch sind Matches und Chats sofort und auch offline sichtbar — im Web war
/// jede Ansicht ein Ladebalken.
@MainActor
@Observable
final class MatchRepository {

    /// Aktueller Stand aus dem lokalen Bestand, nie direkt vom Server.
    private(set) var matches: [MatchSummary] = []

    /// Der Menüpunkt „Chats".
    ///
    /// Bewusst `inChats` statt `lastMessage != nil`: Nach „Chatverlauf leeren"
    /// liefert der Server korrekt `last_message = null`, der Chat soll aber
    /// gelistet bleiben — nur eben leer. Erst „Chat löschen" setzt `in_chats`
    /// zurück, bis eine neue Nachricht eintrifft.
    var conversations: [MatchSummary] { matches.filter(\.inChats) }

    var unreadTotal: Int { matches.reduce(0) { $0 + $1.unreadCount } }

    @ObservationIgnored private let api: FlexrAPI
    @ObservationIgnored private let store: FlexrStore

    init(api: FlexrAPI, store: FlexrStore) {
        self.api = api
        self.store = store
        reload()
    }

    func match(id: String) -> MatchSummary? {
        matches.first { $0.matchID == id }
    }

    @discardableResult
    func refresh() async throws -> [MatchSummary] {
        let remote = try await api.matches().map { $0.toDomain() }
        store.replaceMatches(remote)
        reload()
        return remote
    }

    /// Ungelesen-Zähler lokal zurücksetzen, sobald ein Chat geöffnet wurde.
    func markRead(matchID: String) {
        store.clearUnread(matchID: matchID)
        reload()
    }

    /// Match auflösen: Match und Chatverlauf werden serverseitig gelöscht, der
    /// eigene Swipe ebenfalls — die Person erscheint dadurch erneut im Deck.
    /// Eine Sperre wie beim Blockieren ist das ausdrücklich nicht.
    func unmatch(matchID: String) async throws {
        try await api.unmatch(matchID: matchID)
        store.deleteMatch(id: matchID)
        reload()
    }

    /// „Chat löschen": anders als [unmatch] bleibt das Match serverseitig
    /// bestehen — nur die Unterhaltung verschwindet aus dem „Chats"-Tab, bis
    /// erneut eine Nachricht eintrifft. Lokal reicht ein [refresh], das den
    /// jetzt aktualisierten `inChats`-Wert vom Server übernimmt.
    func deleteChat(matchID: String) async throws {
        try await api.deleteChat(matchID: matchID)
        store.deleteMessages(matchID: matchID)
        try await refresh()
    }

    /// Nach dem Blockieren verschwindet das Match beidseitig aus der Liste.
    func removeLocally(matchID: String) {
        store.deleteMatch(id: matchID)
        reload()
    }

    func clearLocalCache() {
        store.deleteAll()
        reload()
    }

    private func reload() {
        matches = store.allMatches().map { $0.toDomain() }
    }
}
