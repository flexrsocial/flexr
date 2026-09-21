import Foundation

/// Online-Rücktrittsfunktion (§ 13a FAGG). Entspricht backend/app/routers/withdrawal.py.
@MainActor
final class WithdrawalRepository {

    private let api: FlexrAPI

    init(api: FlexrAPI) {
        self.api = api
    }

    func declare(
        name: String,
        email: String,
        contractReference: String?,
        message: String?,
        requestId: String,
        language: String
    ) async throws -> WithdrawalAck {
        let trimmedContractReference = contractReference?.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedMessage = message?.trimmingCharacters(in: .whitespacesAndNewlines)
        let ack = try await api.declareWithdrawal(
            WithdrawalRequestDTO(
                name: name.trimmingCharacters(in: .whitespacesAndNewlines),
                email: email.trimmingCharacters(in: .whitespacesAndNewlines),
                contractReference: (trimmedContractReference?.isEmpty ?? true) ? nil : trimmedContractReference,
                message: (trimmedMessage?.isEmpty ?? true) ? nil : trimmedMessage,
                confirmed: true,
                requestId: requestId,
                language: language
            )
        )
        return WithdrawalAck(
            reference: ack.reference,
            declarationText: ack.declarationText,
            confirmationSent: ack.confirmationSent,
            message: ack.message
        )
    }
}
