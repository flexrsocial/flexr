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
    var usesGPSLocation = false
    var searchRadiusKm = 20

    var current: Profile? { deck[safe: currentIndex] }
    var next: Profile? { deck[safe: currentIndex + 1] }
    var isExhausted: Bool { !isLoading && currentIndex >= deck.count }

    @ObservationIgnored private let swipes: SwipeRepository
    @ObservationIgnored private let profiles: ProfileRepository
    @ObservationIgnored private let location: LocationRepository
    @ObservationIgnored private let safety: SafetyRepository
    @ObservationIgnored private let matches: MatchRepository
    @ObservationIgnored private let onMessage: (String) -> Void
    @ObservationIgnored private let onOpenChat: (String) -> Void

    init(
        container: AppContainer,
        onMessage: @escaping (String) -> Void,
        onOpenChat: @escaping (String) -> Void
    ) {
        swipes = container.swipes
        profiles = container.profiles
        location = container.location
        safety = container.safety
        matches = container.matches
        self.onMessage = onMessage
        self.onOpenChat = onOpenChat
    }

    /// Beim Start: Standort abgleichen, dann das Deck laden.
    ///
    /// Mit Freigabe geht die GPS-Position ans Backend, ohne Freigabe wird eine
    /// gespeicherte Position gelöscht — dann greift die Koordinate der PLZ.
    /// Der Abgleich darf das Laden nie blockieren, deshalb kapselt
    /// [LocationRepository] ein eigenes Zeitlimit.
    func syncLocationAndLoadDeck() async {
        isLoading = true
        error = nil
        await syncLocation()
        await loadDeck()
    }

    /// Berechtigung im Kontext erfragen: erst hier ist erkennbar, wofür sie
    /// gebraucht wird (Umkreissuche) — das ist die von Apple empfohlene Praxis.
    func requestLocationPermissionIfNeeded() async {
        guard location.isUndetermined else { return }
        _ = await location.requestPermission()
    }

    private func syncLocation() async {
        do {
            if let position = await location.currentLocation() {
                _ = try await profiles.updateLocation(
                    latitude: position.latitude,
                    longitude: position.longitude
                )
            } else if profiles.myProfile?.hasGPSLocation == true {
                _ = try await profiles.clearLocation()
            }
        } catch {
            // Der Standort ist eine Verbesserung, keine Voraussetzung — das
            // Deck lädt auch ohne ihn.
        }
        if let profile = profiles.myProfile {
            usesGPSLocation = profile.hasGPSLocation
            searchRadiusKm = profile.searchRadiusKm
            ownAvatarURL = profile.photos.first?.avatarURL
        }
    }

    func loadDeck() async {
        isLoading = true
        error = nil
        do {
            deck = try await swipes.loadDeck()
            currentIndex = 0
        } catch {
            self.error = (error as? FlexrAPIError)?.message ?? "Profile konnten nicht geladen werden."
        }
        isLoading = false
    }

    func like() { swipe(isLike: true) }

    func pass() { swipe(isLike: false) }

    private func swipe(isLike: Bool) {
        guard let target = current else { return }
        // Die Karte ist bereits weggeflogen — sofort weiterschalten, damit sich
        // die Oberfläche nie am Netz aufhält.
        currentIndex += 1

        Task {
            do {
                let outcome = isLike
                    ? try await swipes.like(userID: target.id)
                    : try await swipes.pass(userID: target.id)
                if outcome.matched {
                    matchedWith = target
                    _ = try? await matches.refresh()
                }
            } catch {
                onMessage((error as? FlexrAPIError)?.message ?? "Swipe fehlgeschlagen.")
            }
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
                onMessage("Chat konnte nicht geöffnet werden.")
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
                onMessage("\(name) blockiert.")
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }
}
