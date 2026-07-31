package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.local.MessageDao
import flexr.social.app.data.local.MessageEntity
import flexr.social.app.data.local.toDomain
import flexr.social.app.data.local.toEntity
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.SendMessageRequestDto
import flexr.social.app.domain.model.Message
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.Instant
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Chatverlauf eines Matches.
 *
 * Room ist die Anzeigequelle, das Netz der Lieferant. Gesendete Nachrichten
 * erscheinen sofort als „pending" in der Liste und werden durch die
 * Serverantwort ersetzt — das Web-Frontend musste dafür neu laden.
 */
@Singleton
class MessageRepository @Inject constructor(
    private val api: FlexrApi,
    private val messageDao: MessageDao,
) {

    fun messages(matchId: String): Flow<List<Message>> =
        messageDao.observeForMatch(matchId).map { rows -> rows.map { it.toDomain() } }

    /**
     * Holt den Verlauf. Der Aufruf markiert serverseitig zugleich alle
     * Nachrichten der Gegenseite als gelesen (siehe messages.py).
     */
    suspend fun refresh(matchId: String) {
        val remote = apiCall { api.getMessages(matchId) }.map { it.toDomain() }
        messageDao.replaceSynced(matchId, remote.map { it.toEntity() })
    }

    suspend fun send(matchId: String, senderId: String, content: String): Message {
        val pendingId = "pending-${UUID.randomUUID()}"
        val pending = MessageEntity(
            id = pendingId,
            matchId = matchId,
            senderId = senderId,
            content = content,
            createdAt = Instant.now(),
            readAt = null,
            wasCensored = false,
            isPending = true,
        )
        messageDao.upsert(pending)

        return try {
            val sent = apiCall {
                api.sendMessage(matchId, SendMessageRequestDto(content))
            }.toDomain()
            messageDao.deleteById(pendingId)
            messageDao.upsert(sent.toEntity())
            sent
        } catch (throwable: Throwable) {
            // Fehlgeschlagene Nachricht nicht als „zugestellt" stehen lassen —
            // der Eingabetext wird im ViewModel wiederhergestellt.
            messageDao.deleteById(pendingId)
            throw throwable
        }
    }

    /**
     * Chatverlauf leeren — wirkt nur für die leerende Seite. Serverseitig wird
     * lediglich ein „geleert ab"-Zeitpunkt gesetzt, für die andere Person
     * bleibt der Verlauf erhalten.
     */
    suspend fun clearHistory(matchId: String) {
        apiCall { api.clearMessages(matchId) }
        messageDao.deleteForMatch(matchId)
    }
}
