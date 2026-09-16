import Foundation

/// Chatverlauf eines Matches.
///
/// Der lokale Bestand ist die Anzeigequelle, das Netz der Lieferant. Gesendete
/// Nachrichten erscheinen sofort als „pending" in der Liste und werden durch die
/// Serverantwort ersetzt — das Web-Frontend musste dafür neu laden.
@MainActor
final class MessageRepository {

    private let api: FlexrAPI
    private let store: FlexrStore

    init(api: FlexrAPI, store: FlexrStore) {
        self.api = api
        self.store = store
    }

    func messages(matchID: String) -> [Message] {
        store.messages(matchID: matchID).map { $0.toDomain() }
    }

    /// Holt den Verlauf. Der Aufruf markiert serverseitig zugleich alle
    /// Nachrichten der Gegenseite als gelesen (siehe messages.py).
    func refresh(matchID: String) async throws {
        let remote = try await api.messages(matchID: matchID).map { $0.toDomain() }
        store.replaceSyncedMessages(matchID: matchID, with: remote)
    }

    /// Legt die Zeile sofort örtlich an und liefert ihre Kennung.
    ///
    /// Bewusst getrennt von [send] und nicht `async`: Die eigene Nachricht soll
    /// im selben Bild erscheinen, in dem der Knopf gedrückt wurde — nicht erst
    /// nach der Antwort des Servers. Vorher steckte das Einfügen im
    /// Netzaufruf, und die Ansicht lud ihre Liste davor neu: Die Zeile war
    /// bis zur Serverantwort unsichtbar.
    func insertPending(matchID: String, senderID: String, content: String) -> String {
        let pendingID = "pending-\(UUID().uuidString)"
        let pending = Message(
            id: pendingID,
            matchID: matchID,
            senderID: senderID,
            content: content,
            createdAt: Date(),
            readAt: nil,
            wasCensored: false
        )
        store.insert(pending, isPending: true)
        return pendingID
    }

    /// Schickt eine mit [insertPending] angelegte Zeile ab und ersetzt sie
    /// durch die Fassung des Servers (der den Text zensiert haben kann).
    @discardableResult
    func send(matchID: String, pendingID: String, content: String) async throws -> Message {
        do {
            let sent = try await api.sendMessage(
                matchID: matchID,
                body: SendMessageRequestDTO(content: content)
            ).toDomain()
            store.deleteMessage(id: pendingID)
            store.insert(sent, isPending: false)
            return sent
        } catch {
            // Fehlgeschlagene Nachricht nicht als „zugestellt" stehen lassen —
            // der Eingabetext wird im ViewModel wiederhergestellt.
            store.deleteMessage(id: pendingID)
            throw error
        }
    }

    /// Chatverlauf leeren — wirkt nur für die leerende Seite. Serverseitig wird
    /// lediglich ein „geleert ab"-Zeitpunkt gesetzt, für die andere Person
    /// bleibt der Verlauf erhalten.
    func clearHistory(matchID: String) async throws {
        try await api.clearMessages(matchID: matchID)
        store.deleteMessages(matchID: matchID)
    }
}
