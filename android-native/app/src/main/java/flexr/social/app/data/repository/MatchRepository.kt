package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.local.MatchDao
import flexr.social.app.data.local.MessageDao
import flexr.social.app.data.local.toDomain
import flexr.social.app.data.local.toEntity
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.domain.model.MatchSummary
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Match-Liste mit lokalem Cache als Single Source of Truth: die Oberfläche
 * liest ausschließlich aus Room, das Netz füllt den Cache nach. Dadurch sind
 * Matches und Chats sofort und auch offline sichtbar — im Web war jede
 * Ansicht ein Ladebalken.
 */
@Singleton
class MatchRepository @Inject constructor(
    private val api: FlexrApi,
    private val matchDao: MatchDao,
    private val messageDao: MessageDao,
) {

    val matches: Flow<List<MatchSummary>> =
        matchDao.observeAll().map { rows -> rows.map { it.toDomain() } }

    /** Nur Matches mit laufender Unterhaltung — der Menüpunkt „Chats". */
    val conversations: Flow<List<MatchSummary>> =
        matchDao.observeWithConversation().map { rows -> rows.map { it.toDomain() } }

    val unreadTotal: Flow<Int> = matchDao.observeUnreadTotal()

    fun match(matchId: String): Flow<MatchSummary?> =
        matchDao.observeById(matchId).map { it?.toDomain() }

    suspend fun findMatch(matchId: String): MatchSummary? = matchDao.findById(matchId)?.toDomain()

    suspend fun refresh(): List<MatchSummary> {
        val remote = apiCall { api.getMatches() }.map { it.toDomain() }
        matchDao.replaceAll(remote.map { it.toEntity() })
        return remote
    }

    /** Ungelesen-Zähler lokal zurücksetzen, sobald ein Chat geöffnet wurde. */
    suspend fun markRead(matchId: String) = matchDao.clearUnread(matchId)

    /**
     * Match auflösen: Match und Chatverlauf werden serverseitig gelöscht, der
     * eigene Swipe ebenfalls — die Person erscheint dadurch erneut im Deck.
     * Eine Sperre wie beim Blockieren ist das ausdrücklich nicht.
     */
    suspend fun unmatch(matchId: String) {
        apiCall { api.unmatch(matchId) }
        messageDao.deleteForMatch(matchId)
        matchDao.deleteById(matchId)
    }

    /**
     * "Chat löschen": anders als [unmatch] bleibt das Match serverseitig
     * bestehen - nur die Unterhaltung verschwindet aus dem "Chats"-Tab, bis
     * erneut eine Nachricht eintrifft. Lokal reicht ein [refresh], das den
     * jetzt aktualisierten inChats-Wert vom Server übernimmt.
     */
    suspend fun deleteChat(matchId: String) {
        apiCall { api.deleteChat(matchId) }
        messageDao.deleteForMatch(matchId)
        refresh()
    }

    /** Nach dem Blockieren verschwindet das Match beidseitig aus der Liste. */
    suspend fun removeLocally(matchId: String) {
        messageDao.deleteForMatch(matchId)
        matchDao.deleteById(matchId)
    }
}
