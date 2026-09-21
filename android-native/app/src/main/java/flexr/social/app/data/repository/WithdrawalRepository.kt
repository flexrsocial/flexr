package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.WithdrawalRequestDto
import flexr.social.app.domain.model.WithdrawalAck
import javax.inject.Inject
import javax.inject.Singleton

/** Online-Rücktrittsfunktion (§ 13a FAGG). Entspricht backend/app/routers/withdrawal.py. */
@Singleton
class WithdrawalRepository @Inject constructor(
    private val api: FlexrApi,
) {

    suspend fun declare(
        name: String,
        email: String,
        contractReference: String?,
        message: String?,
        requestId: String,
        language: String,
    ): WithdrawalAck {
        val ack = apiCall {
            api.declareWithdrawal(
                WithdrawalRequestDto(
                    name = name.trim(),
                    email = email.trim(),
                    contractReference = contractReference?.trim()?.ifBlank { null },
                    message = message?.trim()?.ifBlank { null },
                    confirmed = true,
                    requestId = requestId,
                    language = language,
                ),
            )
        }
        return WithdrawalAck(
            reference = ack.reference,
            declarationText = ack.declarationText,
            confirmationSent = ack.confirmationSent,
            message = ack.message,
        )
    }
}
