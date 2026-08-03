package flexr.social.app.data.repository

import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.BlockRequestDto
import flexr.social.app.data.remote.dto.ReportRequestDto
import flexr.social.app.domain.model.ModerationNotice
import flexr.social.app.domain.model.MyReport
import flexr.social.app.domain.model.ReportAck
import flexr.social.app.domain.model.ReportOutcome
import javax.inject.Inject
import javax.inject.Singleton

/** Melden und Blockieren. Entspricht backend/app/routers/safety.py. */
@Singleton
class SafetyRepository @Inject constructor(
    private val api: FlexrApi,
) {

    /**
     * Meldet einen Nutzer. Die Antwort ist die Empfangsbestätigung mit
     * Aktenzeichen — sie muss dem Melder angezeigt werden (Art. 16 Abs. 4 DSA).
     */
    suspend fun report(userId: String, reason: String): ReportAck {
        val ack = apiCall { api.report(ReportRequestDto(userId, reason.trim())) }
        return ReportAck(reference = ack.reference, message = ack.message)
    }

    /** Eigene Meldungen samt Entscheidung der Moderation. */
    suspend fun myReports(): List<MyReport> = apiCall { api.myReports() }.map { dto ->
        MyReport(
            reference = dto.reference,
            reason = dto.reason,
            createdAt = ServerTime.parse(dto.createdAt),
            outcome = ReportOutcome.from(dto.outcome),
            decisionNote = dto.decisionNote,
            decidedAt = ServerTime.parse(dto.decidedAt),
        )
    }

    /** Laufende Beschränkung des eigenen Kontos, oder null wenn keine besteht. */
    suspend fun moderationNotice(): ModerationNotice? =
        apiCall { api.moderationNotice() }?.let { dto ->
            ModerationNotice(
                reason = dto.reason,
                mutedUntil = ServerTime.parse(dto.mutedUntil),
                appealHint = dto.appealHint,
            )
        }

    /** Blockieren wirkt beidseitig: das Match verschwindet auf beiden Seiten. */
    suspend fun block(userId: String) {
        apiCall { api.block(BlockRequestDto(userId)) }
    }

    suspend fun blockedUserIds(): List<String> = apiCall { api.listBlocks() }

    suspend fun unblock(userId: String) {
        apiCall { api.unblock(userId) }
    }
}
