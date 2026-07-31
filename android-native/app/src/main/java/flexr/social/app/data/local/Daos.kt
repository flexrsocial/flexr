package flexr.social.app.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import kotlinx.coroutines.flow.Flow

@Dao
interface MatchDao {

    /**
     * Sortierung wie im Backend: zuletzt geschriebene Unterhaltung zuerst,
     * Matches ohne Nachricht nach ihrem Match-Zeitpunkt.
     */
    @Query("SELECT * FROM matches ORDER BY COALESCE(lastMessageAt, matchedAt) DESC")
    fun observeAll(): Flow<List<MatchEntity>>

    @Query("SELECT * FROM matches WHERE lastMessageId IS NOT NULL ORDER BY lastMessageAt DESC")
    fun observeWithConversation(): Flow<List<MatchEntity>>

    @Query("SELECT * FROM matches WHERE matchId = :matchId")
    fun observeById(matchId: String): Flow<MatchEntity?>

    @Query("SELECT * FROM matches WHERE matchId = :matchId")
    suspend fun findById(matchId: String): MatchEntity?

    @Query("SELECT COALESCE(SUM(unreadCount), 0) FROM matches")
    fun observeUnreadTotal(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(matches: List<MatchEntity>)

    @Query("DELETE FROM matches WHERE matchId = :matchId")
    suspend fun deleteById(matchId: String)

    @Query("DELETE FROM matches WHERE matchId NOT IN (:keepIds)")
    suspend fun deleteMissing(keepIds: List<String>)

    @Query("DELETE FROM matches")
    suspend fun deleteAll()

    @Query("UPDATE matches SET unreadCount = 0 WHERE matchId = :matchId")
    suspend fun clearUnread(matchId: String)

    @Transaction
    suspend fun replaceAll(matches: List<MatchEntity>) {
        if (matches.isEmpty()) {
            deleteAll()
        } else {
            deleteMissing(matches.map { it.matchId })
            upsertAll(matches)
        }
    }
}

@Dao
interface MessageDao {

    @Query("SELECT * FROM messages WHERE matchId = :matchId ORDER BY createdAt ASC")
    fun observeForMatch(matchId: String): Flow<List<MessageEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(messages: List<MessageEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(message: MessageEntity)

    @Query("DELETE FROM messages WHERE matchId = :matchId")
    suspend fun deleteForMatch(matchId: String)

    @Query("DELETE FROM messages WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM messages WHERE matchId = :matchId AND isPending = 0")
    suspend fun deleteSyncedForMatch(matchId: String)

    @Query("DELETE FROM messages")
    suspend fun deleteAll()

    /**
     * Serverstand für einen Chat übernehmen: bestätigte Nachrichten werden
     * ersetzt, noch nicht zugestellte (optimistische) bleiben erhalten.
     */
    @Transaction
    suspend fun replaceSynced(matchId: String, messages: List<MessageEntity>) {
        deleteSyncedForMatch(matchId)
        upsertAll(messages)
    }
}
