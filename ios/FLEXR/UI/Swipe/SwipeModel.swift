import Foundation

/// Swipe-Deck: Standortabgleich, Kandidatenliste, Like/Pass und die
/// Sicherheitsaktionen direkt auf der Karte.
@MainActor
@Observable
final class SwipeModel {

    var deck: [Profile] = []
    var currentIndex = 0
    var isLoading = true
    var error: String?
    /// Profil, mit dem gerade ein Match entstanden ist (Overlay).
    var matchedWith: Profile?
    var ownAvatarURL: String?
    var searchRadiusKm = 20
    /// Läuft ein Premium-Abo? Nur dann gibt es den Zurücknehmen-Knopf.
    var isPremium: Bool { billing.membership?.isPremium == true }
    var isRewinding = false

    var current: Profile? { deck[safe: currentIndex] }
    var next: Profile? { deck[safe: currentIndex + 1] }
    var isExhausted: Bool { !isLoading && currentIndex >= deck.count }

    @ObservationIgnored private let swipes: SwipeRepository
    /// `BillingRepository` ist selbst `@Observable`; `isPremium` liest darauf
    /// durch, statt den Wert zu kopieren. Wer im Kontobereich abschließt oder
    /// kündigt, bekommt den Zurücknehmen-Knopf dadurch ohne Neustart — eine
    /// Kopie im eigenen Zustand wäre ab dem Kopieren veraltet.
    @ObservationIgnored private let billing: BillingRepository
    @ObservationIgnored private let profiles: ProfileRepository
    @ObservationIgnored private let safety: SafetyRepository
    @ObservationIgnored private let matches: MatchRepository
    @ObservationIgnored private let onMessage: (String) -> Void
    @ObservationIgnored private let onOpenChat: (String) -> Void

    /// Texte in der gewählten Sprache. Als Referenz auf den Speicher und nicht
    /// als Kopie: eine Umstellung mitten in der Sitzung wirkt dann sofort auch
    /// auf Meldungen, die dieses Modell danach erzeugt.
    @ObservationIgnored private let languageStore: LanguageStore
    private var s: FlexrStrings { languageStore.strings }

    init(
        container: AppContainer,
        languageStore: LanguageStore,
        onMessage: @escaping (String) -> Void,
        onOpenChat: @escaping (String) -> Void
    ) {
        self.languageStore = languageStore
        swipes = container.swipes
        billing = container.billing
        profiles = container.profiles
        safety = container.safety
        matches = container.matches
        self.onMessage = onMessage
        self.onOpenChat = onOpenChat
    }

    /// Beim Start: eigenes Profil übernehmen (Radius und Avatar für den
    /// Kopfbereich), dann das Deck laden.
    ///
    /// Ein Standortabgleich findet nicht mehr statt: die Umkreissuche geht von
    /// der Adresse des eingetragenen Gyms aus, nicht von der Geräteposition.
    func loadProfileAndDeck() async {
        isLoading = true
        error = nil
        if let profile = profiles.myProfile {
            searchRadiusKm = profile.searchRadiusKm
            ownAvatarURL = profile.photos.first?.avatarURL
        }
        await loadDeck()
    }

    func loadDeck() async {
        isLoading = true
        error = nil
        do {
            deck = try await swipes.loadDeck()
            currentIndex = 0
        } catch {
            self.error = (error as? FlexrAPIError)?.message ?? s(.swipeLoadFailed)
        }
        isLoading = false
    }

    func like() { swipe(isLike: true) }

    func pass() { swipe(isLike: false) }

    private func swipe(isLike: Bool) {
        guard let target = current else { return }
        // Die Karte ist bereits weggeflogen — sofort weiterschalten, damit sich
        // die Oberfläche nie am Netz aufhält.
        let gewischterIndex = currentIndex
        currentIndex += 1

        Task {
            do {
                let outcome = isLike
                    ? try await swipes.like(userID: target.id)
                    : try await swipes.pass(userID: target.id)
                // Der Server rechnet das Kontingent ohnehin schon aus und
                // liefert es mit - die Pille im Kopf zieht darüber nach.
                billing.updateLikesRemaining(outcome.likesRemaining)
                if outcome.matched {
                    matchedWith = target
                    _ = try? await matches.refresh()
                }
            } catch {
                let apiError = error as? FlexrAPIError
                // Aufgebrauchtes Like-Kontingent: Die Karte kommt zurück.
                // Vorher blieb sie weg, obwohl der Like nie gezählt hat — das
                // Profil war damit ohne Zutun und ohne Hinweis übersprungen und
                // im Deck nicht wieder zu finden.
                //
                // `min` und nicht `-= 1`: Wer schnell wischt, hat bis zur
                // Antwort des Servers vielleicht schon weitergewischt. Auf den
                // Index der abgelehnten Karte zurückzugehen ist dann richtig,
                // einen Schritt zurück wäre eine beliebige andere Karte.
                if apiError?.code == "like_limit_reached" {
                    currentIndex = min(currentIndex, gewischterIndex)
                }
                onMessage(apiError?.message ?? s(.swipeFailed))
            }
        }
    }

    /// Letzten Swipe zurücknehmen (Premium).
    ///
    /// Danach wird das Deck neu geladen: Der Server hat den Swipe gelöscht, das
    /// Profil gehört also wieder hinein. Ein Zurückschieben des `currentIndex`
    /// wäre kürzer, aber falsch — der zurückgenommene Swipe muss nicht der
    /// letzte im aktuellen Deck gewesen sein (etwa nach einem Neuladen wegen
    /// geänderter Suchkriterien).
    ///
    /// Fehler kommen im Klartext des Servers durch: „brauchst Premium" (403)
    /// und „daraus ist schon ein Match geworden" (409) sind für den Nutzer zwei
    /// sehr verschiedene Nachrichten.
    func rewindLastSwipe() {
        guard !isRewinding else { return }
        isRewinding = true
        Task {
            do {
                let outcome = try await swipes.rewindLastSwipe()
                billing.updateLikesRemaining(outcome.likesRemaining)
                onMessage(s(.premiumRewindDone))
                await loadDeck()
            } catch {
                onMessage((error as? FlexrAPIError)?.message ?? s(.premiumRewindFailed))
            }
            isRewinding = false
        }
    }

    func dismissMatchOverlay() { matchedWith = nil }

    /// „Nachricht schreiben" aus dem Match-Overlay heraus.
    func openChatWithMatch() {
        guard let profile = matchedWith else { return }
        dismissMatchOverlay()
        Task {
            let refreshed = (try? await matches.refresh()) ?? matches.matches
            if let match = refreshed.first(where: { $0.profile.id == profile.id }) {
                onOpenChat(match.matchID)
            } else {
                onMessage(s(.chatOpenFailed))
            }
        }
    }

    func report(userID: String, reason: String) {
        Task {
            do {
                // Empfangsbestätigung mit Aktenzeichen (Art. 16 Abs. 4 DSA)
                let ack = try await safety.report(userID: userID, reason: reason)
                onMessage(ack.message)
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }

    func block(userID: String, name: String) {
        Task {
            do {
                try await safety.block(userID: userID)
                // Blockierte Person überspringen, ohne dafür einen Swipe zu senden.
                if current?.id == userID { currentIndex += 1 }
                onMessage(s(.blockDone, name))
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }
}
