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
        return SwipeOutcome(matched: result.matched, likesRemaining: result.likesRemaining)
    }

    /// Wer mich geliket hat — eine Premium-Funktion.
    ///
    /// Ohne Premium wirft der Server bewusst keinen Fehler, sondern liefert die
    /// Anzahl ohne Profile. Die Oberfläche unterscheidet die beiden Fälle an
    /// `IncomingLikes.premiumRequired`.
    func incomingLikes() async throws -> IncomingLikes {
        try await api.incomingLikes().toDomain()
    }

    /// Letzten Swipe zurücknehmen — eine Premium-Funktion.
    ///
    /// Ohne Premium kommt 403 mit `code = premium_required`, bei einem bereits
    /// entstandenen Match 409. Beides reicht der Aufrufer als Meldung durch,
    /// statt es hier zu verschlucken: Der Unterschied ist für den Nutzer
    /// erheblich („brauchst Premium" gegen „daraus ist schon ein Match
    /// geworden").
    func rewindLastSwipe() async throws -> RewindOutcome {
        let result = try await api.rewindLastSwipe()
        return RewindOutcome(toUserID: result.toUserId, likesRemaining: result.likesRemaining)
    }
}

/// FLEXR Premium: Abo-Status, Grenzen des kostenlosen Kontos und die
/// Stripe-Übergänge.
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

    /// Restliche Likes nachziehen, ohne `/api/billing/status` erneut zu holen.
    ///
    /// Sowohl der Swipe als auch das Zurücknehmen liefern den neuen Stand in
    /// ihrer eigenen Antwort mit — ein zweiter Aufruf nach jedem Like wäre
    /// reine Verschwendung. Web und Android machen es an derselben Stelle
    /// genauso. `nil` heißt unbegrenzt und bleibt dann auch nil.
    func updateLikesRemaining(_ remaining: Int?) {
        guard let current = membership else { return }
        membership = current.withLikesRemaining(remaining)
    }

    /// Beide Erklärungen müssen vor dem Aufruf aktiv bestätigt worden sein
    /// (§ 10 und § 18 Abs. 1 Z 1 FAGG) — das Backend lehnt `false` oder ein
    /// fehlendes Feld mit 422 ab.
    func checkoutURL(immediateStart: Bool, withdrawalAck: Bool) async throws -> String {
        try await api.createCheckout(
            CheckoutRequestDTO(immediateStart: immediateStart, withdrawalAck: withdrawalAck)
        ).checkoutUrl
    }

    /// Self-Service-Verwaltung/Kündigung über das Stripe Billing Portal.
    func portalURL() async throws -> String {
        try await api.createPortal().portalUrl
    }
}
