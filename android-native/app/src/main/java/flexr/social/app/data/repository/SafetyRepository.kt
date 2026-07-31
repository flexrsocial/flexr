package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.BlockRequestDto
import flexr.social.app.data.remote.dto.ReportRequestDto
import javax.inject.Inject
import javax.inject.Singleton

/** Melden und Blockieren. Entspricht backend/app/routers/safety.py. */
@Singleton
class SafetyRepository @Inject constructor(
    private val api: FlexrApi,
) {

    suspend fun report(userId: String, reason: String) {
        apiCall { api.report(ReportRequestDto(userId, reason.trim())) }
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
