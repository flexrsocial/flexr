package flexr.social.app.data.local

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.TypeConverter
import flexr.social.app.domain.model.Gender
import flexr.social.app.domain.model.MatchSummary
import flexr.social.app.domain.model.Message
import flexr.social.app.domain.model.Photo
import flexr.social.app.domain.model.PhotoStatus
import flexr.social.app.domain.model.Profile
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.time.Instant

private val converterJson = Json { ignoreUnknownKeys = true }

@Serializable
data class StoredPhoto(
    val id: String,
    val url: String,
    val thumbUrl: String? = null,
    val position: Int = 0,
    val status: String = "approved",
)

class RoomConverters {

    @TypeConverter
    fun photosToJson(photos: List<StoredPhoto>?): String =
        converterJson.encodeToString(photos ?: emptyList())

    @TypeConverter
    fun jsonToPhotos(raw: String?): List<StoredPhoto> =
        if (raw.isNullOrBlank()) emptyList()
        else runCatching { converterJson.decodeFromString<List<StoredPhoto>>(raw) }.getOrDefault(emptyList())

    @TypeConverter
    fun instantToLong(instant: Instant?): Long? = instant?.toEpochMilli()

    @TypeConverter
    fun longToInstant(millis: Long?): Instant? = millis?.let(Instant::ofEpochMilli)
}

/**
 * Lokaler Spiegel der Match-Liste. Dient als Single Source of Truth für die
 * Oberfläche: Matches und Chats sind sofort sichtbar, auch ohne Netz, und
 * werden im Hintergrund aufgefrischt.
 */
@Entity(tableName = "matches")
data class MatchEntity(
    @PrimaryKey val matchId: String,
    val profileId: String,
    val name: String,
    val age: Int,
    val city: String,
    val gender: String,
    val gym: String,
    val bio: String?,
    val isVerified: Boolean,
    val isOnline: Boolean,
    val distanceKm: Int?,
    val photos: List<StoredPhoto>,
    val unreadCount: Int,
    val lastMessageId: String?,
    val lastMessageContent: String?,
    val lastMessageSenderId: String?,
    val lastMessageAt: Instant?,
    val matchedAt: Instant,
)

@Entity(
    tableName = "messages",
    indices = [Index("matchId"), Index("createdAt")],
)
data class MessageEntity(
    @PrimaryKey val id: String,
    val matchId: String,
    val senderId: String,
    val content: String,
    val createdAt: Instant,
    val readAt: Instant?,
    val wasCensored: Boolean,
    /** true, solange die Nachricht nur lokal existiert (optimistisch gesendet). */
    val isPending: Boolean = false,
)

// ---------- Mapping Entity <-> Domain ----------

fun StoredPhoto.toDomain() = Photo(
    id = id,
    url = url,
    thumbUrl = thumbUrl,
    position = position,
    status = PhotoStatus.from(status),
)

fun Photo.toStored() = StoredPhoto(
    id = id,
    url = url,
    thumbUrl = thumbUrl,
    position = position,
    status = status.name.lowercase(),
)

fun MatchEntity.toDomain(): MatchSummary = MatchSummary(
    matchId = matchId,
    profile = Profile(
        id = profileId,
        name = name,
        age = age,
        city = city,
        gender = Gender.from(gender),
        gym = gym,
        bio = bio,
        isOnline = isOnline,
        isVerified = isVerified,
        distanceKm = distanceKm,
        photos = photos.map { it.toDomain() },
    ),
    lastMessage = lastMessageId?.let { id ->
        Message(
            id = id,
            matchId = matchId,
            senderId = lastMessageSenderId.orEmpty(),
            content = lastMessageContent.orEmpty(),
            createdAt = lastMessageAt ?: matchedAt,
            readAt = null,
            wasCensored = false,
        )
    },
    unreadCount = unreadCount,
    isOnline = isOnline,
)

fun MatchSummary.toEntity(matchedAt: Instant = Instant.now()) = MatchEntity(
    matchId = matchId,
    profileId = profile.id,
    name = profile.name,
    age = profile.age,
    city = profile.city,
    gender = profile.gender.apiValue,
    gym = profile.gym,
    bio = profile.bio,
    isVerified = profile.isVerified,
    isOnline = profile.isOnline,
    distanceKm = profile.distanceKm,
    photos = profile.photos.map { it.toStored() },
    unreadCount = unreadCount,
    lastMessageId = lastMessage?.id,
    lastMessageContent = lastMessage?.content,
    lastMessageSenderId = lastMessage?.senderId,
    lastMessageAt = lastMessage?.createdAt,
    matchedAt = lastMessage?.createdAt ?: matchedAt,
)

fun MessageEntity.toDomain() = Message(
    id = id,
    matchId = matchId,
    senderId = senderId,
    content = content,
    createdAt = createdAt,
    readAt = readAt,
    wasCensored = wasCensored,
)

fun Message.toEntity(isPending: Boolean = false) = MessageEntity(
    id = id,
    matchId = matchId,
    senderId = senderId,
    content = content,
    createdAt = createdAt,
    readAt = readAt,
    wasCensored = wasCensored,
    isPending = isPending,
)
