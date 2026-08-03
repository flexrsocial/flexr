import Foundation

/// Swipe-Deck und Like/Pass. Entspricht backend/app/routers/swipes.py.
@MainActor
final class SwipeRepository {

    private let api: FlexrAPI

    init(api: FlexrAPI) {
        self.api = api
    }

    /// Kandidaten im gewählten Umkreis, bereits serverseitig nach Entfernung
    /// sortiert und auf Profile mit mindestens einem freigegebenen Foto gefiltert.
    func loadDeck() async throws -> [Profile] {
        try await api.deck().map { $0.toDomain() }
    }

    func like(userID: String) async throws -> SwipeOutcome {
        try await swipe(userID: userID, action: "like")
    }

    func pass(userID: String) async throws -> SwipeOutcome {
        try await swipe(userID: userID, action: "pass")
    }

    private func swipe(userID: String, action: String) async throws -> SwipeOutcome {
        let result = try await api.swipe(SwipeRequestDTO(toUserId: userID, action: action))
        return SwipeOutcome(matched: result.matched)
    }
}

/// Mitgliedschaft: Probemonat, Abo-Status und die Stripe-Übergänge.
///
/// Checkout und Kündigung laufen bewusst über eine externe Browser-Sitzung.
/// Zahlungsdaten werden dadurch nie in der App eingegeben oder verarbeitet —
/// die App kennt nur den Status.
@MainActor
@Observable
final class BillingRepository {

    private(set) var membership: Membership?

    @ObservationIgnored private let api: FlexrAPI

    init(api: FlexrAPI) {
        self.api = api
    }

    @discardableResult
    func refresh() async throws -> Membership {
        let status = try await api.membershipStatus().toDomain()
        membership = status
        return status
    }

    func clear() {
        membership = nil
    }

    func checkoutURL() async throws -> String {
        try await api.createCheckout().checkoutUrl
    }

    /// Self-Service-Verwaltung/Kündigung über das Stripe Billing Portal.
    func portalURL() async throws -> String {
        try await api.createPortal().portalUrl
    }
}
