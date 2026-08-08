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
    val messagingMutedUntil: Instant?,
    /**
     * Alters- und Identitätsprüfung. Ein Konto mit verificationRequired = true
     * und isAccountActivated = false ist angelegt, aber noch nicht nutzbar:
     * kein Deck, keine Matches, kein Chat.
     */
    val verificationRequired: Boolean = false,
    val isAccountActivated: Boolean = true,
    val ageVerified: Boolean = false,
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

/**
 * Stand der Alters- und Identitätsprüfung.
 *
 * ID_REQUIRED und REUPLOAD_REQUIRED gehören zum Ausweisschritt, den diese App
 * noch nicht selbst anbietet — siehe VerificationHint in AccountScreen.kt.
 */
enum class VerificationStatus {
    NONE, IN_PROGRESS, ID_REQUIRED, REUPLOAD_REQUIRED, SUBMITTED, APPROVED, REJECTED;

    /** Der Ausweisschritt steht noch aus. */
    val needsDocument: Boolean
        get() = this == ID_REQUIRED || this == REUPLOAD_REQUIRED

    companion object {
        fun from(raw: String?): VerificationStatus = when (raw?.lowercase()) {
            "in_progress" -> IN_PROGRESS
            "id_required" -> ID_REQUIRED
            "reupload_required" -> REUPLOAD_REQUIRED
            "submitted" -> SUBMITTED
            "approved" -> APPROVED
            "rejected" -> REJECTED
            else -> NONE
        }
    }
}

/** Was der Nutzer als Nächstes beitragen muss. */
enum class VerificationStep {
    SELFIE, DOCUMENT, WAIT, NONE;

    companion object {
        fun from(raw: String?): VerificationStep = when (raw?.lowercase()) {
            "selfie" -> SELFIE
            "document" -> DOCUMENT
            "wait" -> WAIT
            else -> NONE
        }
    }
}

/** Zugelassener Ausweistyp, vom Server geliefert. */
data class VerificationDocumentType(
    val value: String,
    val label: String,
    val needsBack: Boolean,
)

data class VerificationState(
    val status: VerificationStatus,
    val prompts: List<String>,
    val nextStep: VerificationStep = VerificationStep.NONE,
    /** Sachlicher Grund aus festem Katalog, wenn etwas nachzuholen ist. */
    val reason: String? = null,
    val verificationRequired: Boolean = false,
    val accountActivated: Boolean = true,
    val documentTypes: List<VerificationDocumentType> = emptyList(),
)

/** Ergebnis der Altersprüfung im Registrierungsformular. */
data class AgeCheck(
    val eligible: Boolean,
    val age: Int?,
    val message: String?,
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

/**
 * Begründete Mitteilung zu einer Beschränkung des eigenen Kontos (Art. 17 DSA)
 * — Grund, Dauer und der Weg zum Widerspruch.
 */
data class ModerationNotice(
    val reason: String,
    val mutedUntil: Instant?,
    val appealHint: String,
)
