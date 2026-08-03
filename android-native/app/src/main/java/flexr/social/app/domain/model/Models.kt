package flexr.social.app.domain.model

import java.time.Instant
import java.time.LocalDate

enum class PhotoStatus { PENDING, APPROVED, REJECTED;

    companion object {
        fun from(raw: String?): PhotoStatus = when (raw?.lowercase()) {
            "approved" -> APPROVED
            "rejected" -> REJECTED
            else -> PENDING
        }
    }
}

enum class Gender(val apiValue: String, val label: String) {
    MANN("mann", "Mann"),
    FRAU("frau", "Frau");

    companion object {
        fun from(raw: String?): Gender = if (raw?.lowercase() == "frau") FRAU else MANN
    }
}

data class Photo(
    val id: String,
    val url: String,
    val thumbUrl: String?,
    val position: Int,
    val status: PhotoStatus,
) {
    /** Für kleine Avatare: Thumbnail bevorzugen, sonst Vollbild (Bestandsfotos). */
    val avatarUrl: String get() = thumbUrl ?: url
}

data class Profile(
    val id: String,
    val name: String,
    val age: Int,
    val city: String,
    val gender: Gender,
    val gym: String,
    val bio: String?,
    val isOnline: Boolean,
    val isVerified: Boolean,
    val distanceKm: Int?,
    val photos: List<Photo>,
) {
    /** Gym wird als volles Label "Name — Straße 1, 1100 Wien" gespeichert. */
    val gymName: String get() = gym.substringBefore(" — ")
    val primaryPhoto: Photo? get() = photos.firstOrNull()
}

data class MyProfile(
    val profile: Profile,
    val plz: String,
    val birthdate: LocalDate?,
    val searchRadiusKm: Int,
    val hasGpsLocation: Boolean,
    val messagingMutedUntil: Instant?,
) {
    val id: String get() = profile.id
    val name: String get() = profile.name
    val photos: List<Photo> get() = profile.photos

    /** Aktive Chat-Sperre ("Abmahnung"), sonst null. */
    fun activeMuteUntil(now: Instant = Instant.now()): Instant? =
        messagingMutedUntil?.takeIf { it.isAfter(now) }
}

data class Membership(
    val isSubscribed: Boolean,
    val trialEndsAt: Instant,
    val isActive: Boolean,
)

data class Message(
    val id: String,
    val matchId: String,
    val senderId: String,
    val content: String,
    val createdAt: Instant,
    val readAt: Instant?,
    val wasCensored: Boolean,
)

data class MatchSummary(
    val matchId: String,
    val profile: Profile,
    val lastMessage: Message?,
    val unreadCount: Int,
    val isOnline: Boolean,
)

data class Gym(
    val id: String,
    val name: String,
    val street: String,
    val houseNumber: String,
    val plz: String,
    val city: String,
    val label: String,
) {
    val addressLine: String
        get() = listOf("$street $houseNumber".trim(), "$plz $city".trim())
            .filter { it.isNotBlank() }
            .joinToString(", ")
}

enum class VerificationStatus { NONE, IN_PROGRESS, SUBMITTED, APPROVED, REJECTED;

    companion object {
        fun from(raw: String?): VerificationStatus = when (raw?.lowercase()) {
            "in_progress" -> IN_PROGRESS
            "submitted" -> SUBMITTED
            "approved" -> APPROVED
            "rejected" -> REJECTED
            else -> NONE
        }
    }
}

data class VerificationState(
    val status: VerificationStatus,
    val prompts: List<String>,
)

/** Ergebnis eines Swipes. */
data class SwipeOutcome(val matched: Boolean)

/**
 * Bestätigung einer abgegebenen Meldung. Das Aktenzeichen macht sie für den
 * Melder nachverfolgbar (Art. 16 Abs. 4 DSA).
 */
data class ReportAck(
    val reference: String,
    val message: String,
)

enum class ReportOutcome { OPEN, NO_ACTION, ACTION_TAKEN;

    companion object {
        fun from(raw: String?): ReportOutcome = when (raw?.lowercase()) {
            "no_action" -> NO_ACTION
            "action_taken" -> ACTION_TAKEN
            else -> OPEN
        }
    }
}

/** Eigene Meldung mit dem Stand der Prüfung (Art. 16 Abs. 5 DSA). */
data class MyReport(
    val reference: String,
    val reason: String,
    val createdAt: Instant?,
    val outcome: ReportOutcome,
    val decisionNote: String?,
    val decidedAt: Instant?,
)

/**
 * Begründete Mitteilung zu einer Beschränkung des eigenen Kontos (Art. 17 DSA)
 * — Grund, Dauer und der Weg zum Widerspruch.
 */
data class ModerationNotice(
    val reason: String,
    val mutedUntil: Instant?,
    val appealHint: String,
)
