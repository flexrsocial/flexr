import Foundation

/// Steuert die eingebettete Online-Rücktrittsfunktion (§ 13a FAGG) — die native
/// Entsprechung des Formulars auf flexr.social/widerruf.html. Ist die Person
/// angemeldet, ordnet der Server die Erklärung serverseitig automatisch ihrem
/// Konto zu (siehe routers/withdrawal.py); die App muss dafür nichts extra tun.
@MainActor
@Observable
final class WithdrawalModel {

    var name: String
    var email: String
    var contractReference = ""
    var message = ""
    var confirmed = false
    var isSubmitting = false
    var error: String?
    var result: WithdrawalAck?

    var canSubmit: Bool {
        !name.isEmpty && !email.isEmpty && confirmed && !isSubmitting
    }

    @ObservationIgnored private let withdrawalRepository: WithdrawalRepository
    @ObservationIgnored private let languageStore: LanguageStore
    private var s: FlexrStrings { languageStore.strings }

    // Eine UUID pro Bildschirmaufruf, nicht pro Klick - siehe
    // frontend/widerruf.html: ein Doppelklick oder ein Netzwerk-Retry auf
    // denselben Submit schickt dieselbe ID erneut, der Server legt dafür keine
    // zweite Erklärung an.
    private let requestId = UUID().uuidString

    init(
        withdrawalRepository: WithdrawalRepository,
        profile: MyProfile?,
        languageStore: LanguageStore
    ) {
        self.withdrawalRepository = withdrawalRepository
        self.languageStore = languageStore
        name = profile?.profile.name ?? ""
        email = profile?.email ?? ""
    }

    func onFieldChange() {
        error = nil
    }

    func submit() async {
        guard canSubmit else { return }
        isSubmitting = true
        error = nil
        do {
            result = try await withdrawalRepository.declare(
                name: name,
                email: email,
                contractReference: contractReference,
                message: message,
                requestId: requestId,
                language: languageStore.language.rawValue
            )
        } catch {
            self.error = (error as? FlexrAPIError)?.message ?? s(.withdrawalErrorGeneric)
        }
        isSubmitting = false
    }
}
