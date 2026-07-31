package flexr.social.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/*
 * Eins-zu-eins-Abbildung der Pydantic-Schemas aus backend/app/schemas.py.
 * Die Feldnamen bleiben in snake_case (@SerialName), damit der Vertrag mit dem
 * bestehenden Backend unverändert bleibt.
 */

// ---------- Auth ----------

@Serializable
data class RegisterRequestDto(
    val email: String,
    val password: String,
    val name: String,
    val birthdate: String,
    val plz: String,
    val city: String,
    val gender: String,
    val gym: String,
    val bio: String? = null,
    @SerialName("consent_sensitive_data") val consentSensitiveData: Boolean,
    @SerialName("consent_withdrawal_waiver") val consentWithdrawalWaiver: Boolean,
)

@Serializable
data class LoginRequestDto(val email: String, val password: String)

@Serializable
data class TokenResponseDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("token_type") val tokenType: String = "bearer",
)

// ---------- Profile ----------

@Serializable
data class PhotoDto(
    val id: String,
    val url: String,
    @SerialName("thumb_url") val thumbUrl: String? = null,
    val position: Int = 0,
    val status: String = "pending",
)

@Serializable
data class ProfileDto(
    val id: String,
    val name: String,
    val age: Int,
    val city: String,
    val gender: String,
    val gym: String,
    val bio: String? = null,
    @SerialName("is_online") val isOnline: Boolean = false,
    @SerialName("is_verified") val isVerified: Boolean = false,
    @SerialName("distance_km") val distanceKm: Int? = null,
    val photos: List<PhotoDto> = emptyList(),
)

@Serializable
data class MyProfileDto(
    val id: String,
    val name: String,
    val age: Int,
    val city: String,
    val gender: String,
    val gym: String,
    val bio: String? = null,
    @SerialName("is_online") val isOnline: Boolean = false,
    @SerialName("is_verified") val isVerified: Boolean = false,
    @SerialName("distance_km") val distanceKm: Int? = null,
    val photos: List<PhotoDto> = emptyList(),
    val plz: String,
    val birthdate: String,
    @SerialName("search_radius_km") val searchRadiusKm: Int = 20,
    @SerialName("has_gps_location") val hasGpsLocation: Boolean = false,
    // phone/phone_verified liefert das Backend zwar mit, die App nutzt sie
    // nicht — die Telefonprüfung ist auch im Web verworfen worden.
    @SerialName("messaging_muted_until") val messagingMutedUntil: String? = null,
)

@Serializable
data class UpdateProfileRequestDto(
    val plz: String? = null,
    val city: String? = null,
    val gym: String? = null,
    val bio: String? = null,
    @SerialName("search_radius_km") val searchRadiusKm: Int? = null,
)

@Serializable
data class DeleteAccountRequestDto(val password: String)

@Serializable
data class LocationUpdateRequestDto(val lat: Double, val lon: Double)

@Serializable
data class PresignPhotoRequestDto(@SerialName("content_type") val contentType: String)

@Serializable
data class PresignPhotoResponseDto(
    @SerialName("upload_url") val uploadUrl: String,
    @SerialName("object_key") val objectKey: String,
)

@Serializable
data class AddPhotoRequestDto(
    @SerialName("object_key") val objectKey: String,
    @SerialName("thumb_object_key") val thumbObjectKey: String? = null,
)

// ---------- Billing ----------

@Serializable
data class MembershipStatusDto(
    @SerialName("is_subscribed") val isSubscribed: Boolean,
    @SerialName("trial_ends_at") val trialEndsAt: String,
    @SerialName("is_active") val isActive: Boolean,
)

@Serializable
data class CheckoutUrlDto(@SerialName("checkout_url") val checkoutUrl: String)

@Serializable
data class PortalUrlDto(@SerialName("portal_url") val portalUrl: String)

// ---------- Swipes & Matches ----------

@Serializable
data class SwipeRequestDto(
    @SerialName("to_user_id") val toUserId: String,
    val action: String,
)

@Serializable
data class SwipeResultDto(val matched: Boolean)

@Serializable
data class MessageDto(
    val id: String,
    @SerialName("match_id") val matchId: String,
    @SerialName("sender_id") val senderId: String,
    val content: String,
    @SerialName("created_at") val createdAt: String,
    @SerialName("read_at") val readAt: String? = null,
    @SerialName("was_censored") val wasCensored: Boolean = false,
)

@Serializable
data class SendMessageRequestDto(val content: String)

@Serializable
data class MatchDto(
    @SerialName("match_id") val matchId: String,
    val profile: ProfileDto,
    @SerialName("last_message") val lastMessage: MessageDto? = null,
    @SerialName("unread_count") val unreadCount: Int = 0,
    @SerialName("is_online") val isOnline: Boolean = false,
)

// ---------- Gyms ----------

@Serializable
data class GymDto(
    val id: String,
    val name: String,
    val street: String,
    @SerialName("house_number") val houseNumber: String,
    val plz: String,
    val city: String,
    val label: String,
)

@Serializable
data class GymSuggestRequestDto(
    val name: String,
    val street: String,
    @SerialName("house_number") val houseNumber: String,
    val plz: String,
    val city: String? = null,
)

// ---------- Sicherheit ----------

@Serializable
data class ReportRequestDto(
    @SerialName("reported_user_id") val reportedUserId: String,
    val reason: String,
)

@Serializable
data class BlockRequestDto(@SerialName("user_id") val userId: String)

// ---------- Foto-Verifizierung ----------

@Serializable
data class VerificationStatusDto(
    val status: String,
    val prompts: List<String>? = null,
)

@Serializable
data class VerificationSelfieDto(
    val prompt: String,
    @SerialName("object_key") val objectKey: String,
)

@Serializable
data class VerificationSubmitRequestDto(val selfies: List<VerificationSelfieDto>)

// ---------- PLZ-Lookup (OpenPLZ API, openplzapi.org) ----------

@Serializable
data class OpenPlzLocalityDto(
    val name: String? = null,
    val postalCode: String? = null,
    val municipality: OpenPlzMunicipalityDto? = null,
)

@Serializable
data class OpenPlzMunicipalityDto(val name: String? = null)
