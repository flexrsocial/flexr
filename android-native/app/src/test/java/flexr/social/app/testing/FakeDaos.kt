package flexr.social.app.testing

import flexr.social.app.data.local.MatchDao
import flexr.social.app.data.local.MatchEntity
import flexr.social.app.data.local.MessageDao
import flexr.social.app.data.local.MessageEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map

/**
 * Room-DAOs im Arbeitsspeicher.
 *
 * Room selbst braucht einen Android-Context, in reinen JVM-Tests gibt es also
 * keine echte Datenbank. Die DAOs sind Schnittstellen — diese Fassungen bilden
 * ihr Verhalten mit Listen nach, inklusive der Sortierung, auf die sich die
 * Repositories verlassen.
 *
 * `replaceAll` und `replaceSynced` sind in den Schnittstellen bereits
 * ausformuliert und laufen hier unverändert über die überschriebenen Methoden.
 */
class FakeMatchDao(
    initial: List<MatchEntity> = emptyList(),
) : MatchDao {

    val rows = MutableStateFlow(initial)

    private fun sortiert(list: List<MatchEntity>) =
        list.sortedByDescending { it.lastMessageAt ?: it.matchedAt }

    override fun observeAll(): Flow<List<MatchEntity>> = rows.map(::sortiert)

    override fun observeWithConversation(): Flow<List<MatchEntity>> =
        rows.map { list -> sortiert(list.filter { it.lastMessageId != null }) }

    override fun observeById(matchId: String): Flow<MatchEntity?> =
        rows.map { list -> list.firstOrNull { it.matchId == matchId } }

    override suspend fun findById(matchId: String): MatchEntity? =
        rows.value.firstOrNull { it.matchId == matchId }

    override fun observeUnreadTotal(): Flow<Int> =
        rows.map { list -> list.sumOf { it.unreadCount } }

    override suspend fun upsertAll(matches: List<MatchEntity>) {
        val neueIds = matches.map { it.matchId }.toSet()
        rows.value = rows.value.filterNot { it.matchId in neueIds } + matches
    }

    override suspend fun deleteById(matchId: String) {
        rows.value = rows.value.filterNot { it.matchId == matchId }
    }

    override suspend fun deleteMissing(keepIds: List<String>) {
        rows.value = rows.value.filter { it.matchId in keepIds }
    }

    override suspend fun deleteAll() {
        rows.value = emptyList()
    }

    override suspend fun clearUnread(matchId: String) {
        rows.value = rows.value.map {
            if (it.matchId == matchId) it.copy(unreadCount = 0) else it
        }
    }
}

class FakeMessageDao(
    initial: List<MessageEntity> = emptyList(),
) : MessageDao {

    val rows = MutableStateFlow(initial)

    override fun observeForMatch(matchId: String): Flow<List<MessageEntity>> =
        rows.map { list -> list.filter { it.matchId == matchId }.sortedBy { it.createdAt } }

    override suspend fun upsertAll(messages: List<MessageEntity>) {
        val neueIds = messages.map { it.id }.toSet()
        rows.value = rows.value.filterNot { it.id in neueIds } + messages
    }

    override suspend fun upsert(message: MessageEntity) = upsertAll(listOf(message))

    override suspend fun deleteForMatch(matchId: String) {
        rows.value = rows.value.filterNot { it.matchId == matchId }
    }

    override suspend fun deleteById(id: String) {
        rows.value = rows.value.filterNot { it.id == id }
    }

    override suspend fun deleteSyncedForMatch(matchId: String) {
        rows.value = rows.value.filterNot { it.matchId == matchId && !it.isPending }
    }

    override suspend fun deleteAll() {
        rows.value = emptyList()
    }
}
