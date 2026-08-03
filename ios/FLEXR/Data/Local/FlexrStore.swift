import Foundation
import SwiftData

/// Lokaler Bestand für Matches und Nachrichten.
///
/// Entspricht der Room-Datenbank der Android-App: Die Oberfläche liest
/// ausschließlich hier, das Netz füllt nach. Wer Listen „direkt vom Server"
/// rendern will, bricht die Offline-Fähigkeit.
///
/// Der Inhalt ist reiner Cache. Scheitert das Öffnen (etwa nach einer
/// Schemaänderung), wird die Datei weggeworfen statt migriert — Neuaufbau ist
/// günstiger als eine Migration und kostet nur einen Netzabruf.
@MainActor
final class FlexrStore {

    let container: ModelContainer
    private var context: ModelContext { container.mainContext }

    init() {
        let schema = Schema([MatchEntity.self, MessageEntity.self])
        let configuration = ModelConfiguration("flexr", schema: schema)
        if let container = try? ModelContainer(for: schema, configurations: configuration) {
            self.container = container
        } else {
            Self.removeStoreFiles()
            // Zweiter Versuch auf leerer Datei; scheitert auch der, ist das Gerät
            // in einem Zustand, in dem die App ohnehin nicht arbeiten kann.
            self.container = try! ModelContainer(for: schema, configurations: configuration)
        }
    }

    private static func removeStoreFiles() {
        let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        for suffix in ["", "-shm", "-wal"] {
            try? FileManager.default.removeItem(at: support.appendingPathComponent("flexr.store\(suffix)"))
        }
    }

    // MARK: - Matches

    /// Sortierung wie im Backend: zuletzt geschriebene Unterhaltung zuerst.
    func allMatches() -> [MatchEntity] {
        let descriptor = FetchDescriptor<MatchEntity>(
            sortBy: [SortDescriptor(\.sortedAt, order: .reverse)]
        )
        return (try? context.fetch(descriptor)) ?? []
    }

    func match(id: String) -> MatchEntity? {
        var descriptor = FetchDescriptor<MatchEntity>(predicate: #Predicate { $0.matchID == id })
        descriptor.fetchLimit = 1
        return try? context.fetch(descriptor).first
    }

    /// Serverstand übernehmen: fehlende Matches entfernen, vorhandene
    /// aktualisieren, neue anlegen.
    func replaceMatches(_ summaries: [MatchSummary]) {
        let keep = Set(summaries.map(\.matchID))
        for existing in allMatches() where !keep.contains(existing.matchID) {
            context.delete(existing)
        }
        for summary in summaries {
            if let existing = match(id: summary.matchID) {
                existing.apply(summary)
            } else {
                context.insert(MatchEntity.make(summary))
            }
        }
        save()
    }

    func deleteMatch(id: String) {
        if let entity = match(id: id) { context.delete(entity) }
        deleteMessages(matchID: id)
        save()
    }

    func clearUnread(matchID: String) {
        guard let entity = match(id: matchID), entity.unreadCount != 0 else { return }
        entity.unreadCount = 0
        save()
    }

    // MARK: - Nachrichten

    func messages(matchID: String) -> [MessageEntity] {
        let descriptor = FetchDescriptor<MessageEntity>(
            predicate: #Predicate { $0.matchID == matchID },
            sortBy: [SortDescriptor(\.createdAt, order: .forward)]
        )
        return (try? context.fetch(descriptor)) ?? []
    }

    /// Serverstand für einen Chat übernehmen: bestätigte Nachrichten werden
    /// ersetzt, noch nicht zugestellte (optimistische) bleiben erhalten.
    func replaceSyncedMessages(matchID: String, with messages: [Message]) {
        for existing in self.messages(matchID: matchID) where !existing.isPending {
            context.delete(existing)
        }
        for message in messages {
            context.insert(MessageEntity.make(message))
        }
        save()
    }

    func insert(_ message: Message, isPending: Bool) {
        if let existing = self.message(id: message.id) {
            context.delete(existing)
        }
        context.insert(MessageEntity.make(message, isPending: isPending))
        save()
    }

    func message(id: String) -> MessageEntity? {
        var descriptor = FetchDescriptor<MessageEntity>(predicate: #Predicate { $0.messageID == id })
        descriptor.fetchLimit = 1
        return try? context.fetch(descriptor).first
    }

    func deleteMessage(id: String) {
        if let entity = message(id: id) { context.delete(entity) }
        save()
    }

    func deleteMessages(matchID: String) {
        for entity in messages(matchID: matchID) { context.delete(entity) }
        save()
    }

    /// Beim Abmelden: alles wegwerfen, der Bestand gehört zum Konto.
    func deleteAll() {
        try? context.delete(model: MessageEntity.self)
        try? context.delete(model: MatchEntity.self)
        save()
    }

    private func save() {
        try? context.save()
    }
}
