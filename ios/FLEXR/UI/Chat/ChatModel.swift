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
    /// Das Kontingent an gleichzeitigen Unterhaltungen ist voll
    /// (`premium.ensure_chat_allowed`, Code `chat_limit_reached`).
    ///
    /// Als eigener Zustand und nicht nur als flüchtige Meldung: Wer hier
    /// anstößt, bekommt in *diesem* Chat nie eine Nachricht durch, solange kein
    /// Platz frei wird. Eine Einblendung, die nach 20 Sekunden verschwindet,
    /// liest sich dann wie eine Störung — und es sieht aus, als käme beim
    /// Gegenüber einfach nichts an. Der Hinweis bleibt deshalb stehen, bis es
    /// wirklich klappt.
    var limitNotice: String?
    /// Der Verlauf ließ sich nicht holen und es gibt auch örtlich keinen.
    ///
    /// Bis zum 18.09.2026 verschwand ein solcher Fehler spurlos — der
    /// Hintergrundabgleich schluckte ihn, und die Ansicht zeigte denselben
    /// Leerzustand wie ein Chat, in dem wirklich noch nichts steht
    /// („Schreib die erste"). Wer keine Nachrichten bekam, konnte gar nicht
    /// unterscheiden, ob keine da sind oder keine ankommen.
    ///
    /// Nur bei leerem örtlichem Bestand: Ein Aussetzer über einem vorhandenen
    /// Verlauf ist kein Grund, den Verlauf gegen eine Fehlerseite zu tauschen.
    var loadError: String?
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
    /// Nur fuer die Empfangsbestaetigung mit Aktenzeichen einer Profilmeldung
    /// (Art. 16 Abs. 4 DSA) - bleibt stehen statt nach zwei Sekunden zu
    /// verschwinden (siehe AppModel.showSticky).
    @ObservationIgnored private let onStickyMessage: (String) -> Void

    /// Texte in der gewählten Sprache. Als Referenz auf den Speicher und nicht
    /// als Kopie: eine Umstellung mitten in der Sitzung wirkt dann sofort auch
    /// auf Meldungen, die dieses Modell danach erzeugt.
    @ObservationIgnored private let languageStore: LanguageStore
    private var s: FlexrStrings { languageStore.strings }

    init(
        matchID: String,
        container: AppContainer,
        languageStore: LanguageStore,
        onMessage: @escaping (String) -> Void,
        onStickyMessage: @escaping (String) -> Void
    ) {
        self.matchID = matchID
        self.languageStore = languageStore
        messageRepository = container.messages
        matches = container.matches
        safety = container.safety
        profiles = container.profiles
        self.onMessage = onMessage
        self.onStickyMessage = onStickyMessage
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
            await refreshOnce()
            isLoading = false
            try? await Task.sleep(for: Self.pollInterval)
        }
    }

    /// Ein Abgleich mit dem Server.
    ///
    /// Ohne Netz bleibt der örtliche Stand stehen — dafür gibt es kein
    /// Fehlerbanner, das wäre bei einem Abgleich alle vier Sekunden eine
    /// Belästigung. Steht aber gar nichts da, dann ist der Fehler die einzige
    /// Auskunft, die es gibt, und er gehört auf den Schirm: Sonst sieht ein
    /// Chat, der nicht geladen werden kann, genauso aus wie ein leerer.
    private func refreshOnce() async {
        do {
            try await messageRepository.refresh(matchID: matchID)
            matches.markRead(matchID: matchID)
            loadError = nil
        } catch {
            loadError = messageRepository.messages(matchID: matchID).isEmpty
                ? ((error as? FlexrAPIError)?.message ?? s(.chatLoadFailed))
                : nil
        }
        reload()
    }

    /// „Erneut versuchen" aus dem Fehlerzustand heraus — ohne auf den nächsten
    /// Durchlauf des Abgleichs zu warten.
    func retryLoad() async {
        loadError = nil
        isLoading = true
        await refreshOnce()
        isLoading = false
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
        // Erst die Zeile anlegen, dann die Liste neu lesen: andersherum wäre
        // die eigene Nachricht bis zur Antwort des Servers unsichtbar.
        let pendingID = messageRepository.insertPending(
            matchID: matchID,
            senderID: senderID,
            content: content
        )
        reload()

        do {
            _ = try await messageRepository.send(
                matchID: matchID,
                pendingID: pendingID,
                content: content
            )
            reload()
            limitNotice = nil
            _ = try? await matches.refresh()
        } catch {
            let apiError = error as? FlexrAPIError
            // Getippten Text nicht verlieren.
            draft = content
            mutedUntil = apiError?.mutedUntil ?? mutedUntil
            muteReason = apiError?.moderationReason ?? muteReason
            appealHint = apiError?.appealHint ?? appealHint
            reload()

            if apiError?.code == "chat_limit_reached" {
                // Stehender Hinweis statt Einblendung — und bewusst nicht
                // beides, das wäre dieselbe Nachricht zweimal. Der Wortlaut
                // kommt vom Server: Dort steht die Zahl, die auch durchgesetzt
                // wird; hier eine eigene zu führen hiesse, sie an zwei Stellen
                // zu pflegen.
                limitNotice = apiError?.message ?? s(.chatSendFailed)
            } else if apiError?.mutedUntil == nil {
                if apiError?.statusCode == 403 { await refreshMuteState() }
                onMessage(apiError?.message ?? s(.chatSendFailed))
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
                onMessage(s(.chatCleared))
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
                onMessage(s(.chatDeleted))
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
                onStickyMessage(ack.message)
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
                onMessage(s(.blockDone, profile.name))
                isClosed = true
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }
}
