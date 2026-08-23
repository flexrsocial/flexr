import Foundation

/// Ein Chatverlauf.
///
/// Die Nachrichten kommen aus dem lokalen Bestand und werden im Vordergrund
/// regelmäßig aufgefrischt (das Backend bietet kein Push). Beim Abrufen markiert
/// der Server die Nachrichten der Gegenseite zugleich als gelesen.
@MainActor
@Observable
final class ChatModel {

    /// Serverseitiges Limit einer Nachricht — die Oberfläche kappt mit.
    static let maxLength = 2_000
    private static let pollInterval: Duration = .seconds(4)

    let matchID: String

    var messages: [Message] = []
    /// Die Längenbegrenzung übernimmt die Eingabezeile — Property-Observer sind
    /// in einer @Observable-Klasse nicht zulässig.
    var draft = ""
    var isSending = false
    var isLoading = true
    var mutedUntil: Date?
    /// Begründung und Widerspruchshinweis zur Sperre (Art. 17 DSA).
    var muteReason: String?
    var appealHint: String?
    /// Signalisiert der Ansicht, dass sie sich schließen soll.
    var isClosed = false

    var canSend: Bool {
        !draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !isSending
            && mutedUntil == nil
    }

    var match: MatchSummary? { matches.match(id: matchID) }
    var ownUserID: String? { profiles.myProfile?.id }

    @ObservationIgnored private let messageRepository: MessageRepository
    @ObservationIgnored private let matches: MatchRepository
    @ObservationIgnored private let safety: SafetyRepository
    @ObservationIgnored private let profiles: ProfileRepository
    @ObservationIgnored private let onMessage: (String) -> Void

    init(matchID: String, container: AppContainer, onMessage: @escaping (String) -> Void) {
        self.matchID = matchID
        messageRepository = container.messages
        matches = container.matches
        safety = container.safety
        profiles = container.profiles
        self.onMessage = onMessage
        messages = messageRepository.messages(matchID: matchID)
    }

    // MARK: - Laden

    func start() async {
        matches.markRead(matchID: matchID)
        await refreshMuteState()
        await poll()
    }

    /// Läuft, solange die Ansicht sichtbar ist — SwiftUI bricht die Aufgabe beim
    /// Verlassen ab, deshalb braucht es keinen eigenen Abbruchmechanismus.
    private func poll() async {
        while !Task.isCancelled {
            do {
                try await messageRepository.refresh(matchID: matchID)
                matches.markRead(matchID: matchID)
            } catch {
                // Ohne Netz bleibt der lokale Stand stehen — kein Fehlerbanner
                // für einen Hintergrundabgleich.
            }
            reload()
            isLoading = false
            try? await Task.sleep(for: Self.pollInterval)
        }
    }

    private func reload() {
        messages = messageRepository.messages(matchID: matchID)
    }

    /// Chat-Sperre kann während der Sitzung verhängt worden sein — beim Öffnen
    /// des Chats den Profilstand nachziehen.
    private func refreshMuteState() async {
        let profile = (try? await profiles.refresh()) ?? profiles.myProfile
        let until = profile?.activeMuteUntil()
        mutedUntil = until

        // Art. 17 DSA: Zur Sperre gehört die Begründung samt Widerspruchsweg.
        if until != nil {
            let notice = try? await safety.moderationNotice()
            muteReason = notice?.reason
            appealHint = notice?.appealHint
        } else {
            muteReason = nil
            appealHint = nil
        }
    }

    // MARK: - Senden

    func send() async {
        let content = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !content.isEmpty, !isSending, mutedUntil == nil else { return }
        guard let senderID = profiles.myProfile?.id else { return }

        draft = ""
        isSending = true
        reload()

        do {
            _ = try await messageRepository.send(
                matchID: matchID,
                senderID: senderID,
                content: content
            )
            reload()
            _ = try? await matches.refresh()
        } catch {
            let apiError = error as? FlexrAPIError
            // Getippten Text nicht verlieren.
            draft = content
            mutedUntil = apiError?.mutedUntil ?? mutedUntil
            muteReason = apiError?.moderationReason ?? muteReason
            appealHint = apiError?.appealHint ?? appealHint
            reload()

            if apiError?.mutedUntil == nil {
                if apiError?.statusCode == 403 { await refreshMuteState() }
                onMessage(apiError?.message ?? "Nachricht konnte nicht gesendet werden.")
            }
        }
        isSending = false
    }

    func insertEmoji(_ emoji: String, selection: NSRange) -> NSRange {
        let result = EmojiInsertion.insert(
            emoji,
            into: draft,
            selection: selection,
            maxLength: Self.maxLength
        )
        draft = result.text
        return result.selection
    }

    // MARK: - Aktionen

    /// Verlauf leeren — nur für die eigene Seite.
    func clearHistory() {
        Task {
            do {
                try await messageRepository.clearHistory(matchID: matchID)
                reload()
                onMessage("Chatverlauf geleert.")
                _ = try? await matches.refresh()
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }

    /// Chat löschen: anders als „Match auflösen" (MatchProfileView) bleibt das
    /// Match bestehen — der Chat verschwindet nur aus dem „Chats"-Tab, bis
    /// erneut eine Nachricht eintrifft.
    func deleteChat() {
        Task {
            do {
                try await matches.deleteChat(matchID: matchID)
                onMessage("Chat gelöscht.")
                isClosed = true
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }

    func report(reason: String) {
        guard let userID = match?.profile.id else { return }
        Task {
            do {
                // Art. 16 Abs. 4 DSA: Der Melder bekommt die Bestätigung mit
                // Aktenzeichen zu sehen, nicht nur ein „danke".
                let ack = try await safety.report(userID: userID, reason: reason)
                onMessage(ack.message)
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }

    func block() {
        guard let profile = match?.profile else { return }
        Task {
            do {
                try await safety.block(userID: profile.id)
                matches.removeLocally(matchID: matchID)
                onMessage("\(profile.name) blockiert.")
                isClosed = true
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }
}
