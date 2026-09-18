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
    /// aktualisiert, neue angelegt, verschwundene entfernt. Noch nicht
    /// zugestellte (optimistische) bleiben unangetastet.
    ///
    /// Bis zum 18.09.2026 stand hier „alles löschen, alles neu einfügen". Das
    /// ist bei `@Attribute(.unique)` (siehe `MessageEntity.messageID`) genau
    /// der Fall, den man nicht bauen darf: Löschung und Neuanlage **derselben**
    /// Kennung liegen dann in einem einzigen Speichervorgang, und der
    /// eindeutige Schlüssel entscheidet den Konflikt. Scheitert das Speichern
    /// dabei, bleiben die Änderungen offen im Kontext stehen, jeder folgende
    /// `save()` läuft in denselben Konflikt — und die Oberfläche zeigt
    /// unverändert den alten Stand, ohne dass irgendwo ein Fehler auftaucht.
    ///
    /// Jetzt derselbe Weg wie bei den Matches (`replaceMatches`): vorhandene
    /// Zeilen werden beschrieben, nicht ersetzt. Damit gibt es den Konflikt
    /// gar nicht erst.
    func replaceSyncedMessages(matchID: String, with messages: [Message]) {
        let vorhanden = Dictionary(
            self.messages(matchID: matchID).map { ($0.messageID, $0) },
            uniquingKeysWith: { first, _ in first }
        )
        let vomServer = Set(messages.map(\.id))

        // Entfernt wird nur, was der Server nicht mehr kennt — wer noch auf
        // seine Zustellung wartet, bleibt stehen.
        for (id, entity) in vorhanden where !entity.isPending && !vomServer.contains(id) {
            context.delete(entity)
        }
        for message in messages {
            if let entity = vorhanden[message.id] {
                entity.apply(message)
            } else {
                context.insert(MessageEntity.make(message))
            }
        }
        save()
    }

    func insert(_ message: Message, isPending: Bool) {
        // Beschreiben statt löschen-und-neu-anlegen, aus demselben Grund wie in
        // `replaceSyncedMessages`: Beides in einem Speichervorgang stellt den
        // eindeutigen Schlüssel gegen sich selbst.
        if let existing = self.message(id: message.id) {
            existing.apply(message)
            existing.isPending = isPending
        } else {
            context.insert(MessageEntity.make(message, isPending: isPending))
        }
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

    /// Speichern — und ein Scheitern nicht verschlucken.
    ///
    /// `try?` allein war hier die gefährlichere Hälfte des Fehlers vom
    /// 18.09.2026: Geht ein `save()` schief, bleiben die Änderungen offen im
    /// Kontext liegen. Der nächste Abgleich legt seine eigenen obendrauf,
    /// scheitert am selben Konflikt — und so weiter. Der Bestand steht dann
    /// dauerhaft still, über App-Neustarts hinweg, ohne eine einzige Meldung:
    /// Die Oberfläche liest ja brav, was in der Datei steht, nur kommt dort
    /// nichts Neues mehr an.
    ///
    /// `rollback()` verwirft den kaputten Stapel und macht den Kontext wieder
    /// arbeitsfähig. Verloren geht dabei nichts, was nicht zu ersetzen wäre:
    /// Der Bestand ist reiner Spiegel des Servers, der nächste Abruf füllt ihn
    /// neu. In Debug-Builds bricht es stattdessen ab — so ein Konflikt ist ein
    /// Fehler im Programm und soll nicht erst beim Nutzer auffallen.
    private func save() {
        do {
            try context.save()
        } catch {
            #if DEBUG
            assertionFailure("FlexrStore: Speichern fehlgeschlagen — \(error)")
            #endif
            context.rollback()
        }
    }
}
