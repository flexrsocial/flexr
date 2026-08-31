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
    // consent_withdrawal_waiver wird seit dem 15.08.2026 nicht mehr geschickt.
    // Der Server nimmt das Feld noch entgegen, damit ausgelieferte Fassungen
    // weiter registrieren können, wertet es aber nicht aus.
)

@Serializable
data class LoginRequestDto(val email: String, val password: String)

/** Vorabprüfung des Geburtsdatums im Registrierungsformular. */
@Serializable
data class AgeCheckRequestDto(val birthdate: String)

@Serializable
data class AgeCheckResponseDto(
    val eligible: Boolean,
    val age: Int? = null,
    val message: String? = null,
    @SerialName("verification_required") val verificationRequired: Boolean = true,
)

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
    // Nur in der eigenen Ansicht - der Nutzer muss sehen, an welche Adresse die
    // Bestaetigungsmail ging. Default leer: aeltere Backends liefern sie nicht.
    val email: String = "",
    @SerialName("email_verified") val emailVerified: Boolean = true,
    @SerialName("search_radius_km") val searchRadiusKm: Int = 20,
    // phone/phone_verified liefert das Backend zwar mit, die App nutzt sie
    // nicht — die Telefonprüfung ist auch im Web verworfen worden.
    @SerialName("messaging_muted_until") val messagingMutedUntil: String? = null,
    // Alters- und Identitätsprüfung. Bestandskonten liefern verification_required
    // = false; Defaults hier so gewählt, dass ein älteres Backend ohne diese
    // Felder ein nutzbares Konto ergibt.
    @SerialName("verification_required") val verificationRequired: Boolean = false,
    @SerialName("is_account_activated") val isAccountActivated: Boolean = true,
    @SerialName("age_verified") val ageVerified: Boolean = false,
    // Schalterstellung unter "Benachrichtigungen". Default an - ein aelteres
    // Backend ohne diese Felder soll nicht so aussehen, als haette der Nutzer
    // alles abgeschaltet.
    @SerialName("notify_match_email") val notifyMatchEmail: Boolean = true,
    @SerialName("notify_match_push") val notifyMatchPush: Boolean = true,
    @SerialName("notify_queue_email") val notifyQueueEmail: Boolean = true,
    @SerialName("notify_queue_push") val notifyQueuePush: Boolean = true,
    @SerialName("notify_inactive_email") val notifyInactiveEmail: Boolean = true,
    @SerialName("notify_inactive_push") val notifyInactivePush: Boolean = true,
)

/** Einzelner Schalter - nur das gesetzte Feld wird geschickt. */
@Serializable
data class NotificationSettingsRequestDto(
    @SerialName("notify_match_email") val notifyMatchEmail: Boolean? = null,
    @SerialName("notify_match_push") val notifyMatchPush: Boolean? = null,
    @SerialName("notify_queue_email") val notifyQueueEmail: Boolean? = null,
    @SerialName("notify_queue_push") val notifyQueuePush: Boolean? = null,
    @SerialName("notify_inactive_email") val notifyInactiveEmail: Boolean? = null,
    @SerialName("notify_inactive_push") val notifyInactivePush: Boolean? = null,
)

/** Neue Reihenfolge der eigenen Fotos (Drag & Drop im Profil). */
@Serializable
data class ReorderPhotosRequestDto(
    @SerialName("photo_ids") val photoIds: List<String>,
)

/**
 * Eine vom Server bereitgelegte App-Benachrichtigung.
 *
 * FLEXR hat kein FCM: der Hintergrundabgleich holt diese Eintraege ab und zeigt
 * sie lokal an (siehe ActivityNotificationWorker).
 */
@Serializable
data class PushNotificationDto(
    val id: String,
    val topic: String,
    val title: String,
    val body: String,
    val target: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class MarkDeliveredRequestDto(val ids: List<String>)

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
data class ConsentDto(
    @SerialName("consent_type") val consentType: String,
    val version: String,
    @SerialName("granted_at") val grantedAt: String,
    @SerialName("revoked_at") val revokedAt: String? = null,
    val active: Boolean,
)

@Serializable
data class ConsentRevokeRequestDto(@SerialName("consent_type") val consentType: String)

@Serializable
data class ConsentRevokeResponseDto(
    val revoked: Boolean,
    @SerialName("consent_type") val consentType: String,
    val consequence: String,
)

@Serializable
data class ConsentGrantRequestDto(@SerialName("consent_type") val consentType: String)

@Serializable
data class ConsentGrantResponseDto(
    val granted: Boolean,
    @SerialName("consent_type") val consentType: String,
    val consequence: String,
)

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
data class CheckoutRequestDto(
    @SerialName("immediate_start") val immediateStart: Boolean,
    @SerialName("withdrawal_ack") val withdrawalAck: Boolean,
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
    @SerialName("in_chats") val inChats: Boolean = false,
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

/** Empfangsbestätigung einer Meldung (Art. 16 Abs. 4 DSA). */
@Serializable
data class ReportAckDto(
    val reference: String,
    @SerialName("created_at") val createdAt: String,
    val message: String,
)

/** Begründete Mitteilung zu einer laufenden Maßnahme (Art. 17 DSA). */
@Serializable
data class ModerationNoticeDto(
    val action: String,
    val reason: String,
    @SerialName("action_at") val actionAt: String,
    @SerialName("muted_until") val mutedUntil: String? = null,
    @SerialName("appeal_hint") val appealHint: String,
)

@Serializable
data class BlockRequestDto(@SerialName("user_id") val userId: String)

/**
 * Blockierte Person für die Verwaltungsliste im Konto — entspricht
 * `backend/app/schemas.py::BlockedUserOut`. Bewusst nur das Nötigste zum
 * Wiedererkennen, kein Bio/Gym/Entfernung (siehe dortiger Docstring).
 */
@Serializable
data class BlockedUserDto(
    @SerialName("user_id") val userId: String,
    val name: String,
    val age: Int? = null,
    @SerialName("photo_url") val photoUrl: String? = null,
    @SerialName("blocked_at") val blockedAt: String? = null,
)

// ---------- Alters- und Identitätsprüfung ----------

@Serializable
data class VerificationStatusDto(
    val status: String,
    val prompts: List<String>? = null,
    /** Was als Nächstes zu tun ist: selfie | document | wait | none. */
    @SerialName("next_step") val nextStep: String? = null,
    /** Sachlicher Grund aus dem festen Katalog, wenn etwas nachzuholen ist. */
    val reason: String? = null,
    @SerialName("verification_required") val verificationRequired: Boolean = false,
    @SerialName("account_activated") val accountActivated: Boolean = true,
    // Default true: Ein aelteres Backend ohne dieses Feld soll den Schritt
    // nicht faelschlich als offen anzeigen.
    @SerialName("email_verified") val emailVerified: Boolean = true,
    @SerialName("document_types") val documentTypes: List<VerificationDocumentTypeDto>? = null,
)

@Serializable
data class VerificationDocumentTypeDto(
    val value: String,
    val label: String,
    @SerialName("needs_back") val needsBack: Boolean = false,
)

@Serializable
data class VerificationDocumentPresignRequestDto(
    @SerialName("content_type") val contentType: String,
    @SerialName("byte_size") val byteSize: Int,
)

@Serializable
data class VerificationDocumentSubmitRequestDto(
    @SerialName("document_type") val documentType: String,
    @SerialName("front_object_key") val frontObjectKey: String,
    @SerialName("back_object_key") val backObjectKey: String? = null,
)

@Serializable
data class VerificationSelfieDto(
    val prompt: String,
    @SerialName("object_key") val objectKey: String,
)

@Serializable
data class VerificationSubmitRequestDto(val selfies: List<VerificationSelfieDto>)

// ---------- PLZ-Lookup (eigenes Backend, GET /api/geo/plz/{plz}) ----------

@Serializable
data class PlzLookupDto(val plz: String, val city: String)

/** Neuen Aktivierungslink anfordern - Antwort auf POST /api/auth/email/resend. */
@Serializable
data class EmailResendResponseDto(
    val email: String,
    @SerialName("valid_hours") val validHours: Int = 24,
)

/** Token aus dem Aktivierungslink einlösen. */
@Serializable
data class EmailConfirmRequestDto(val token: String)

@Serializable
data class EmailConfirmResponseDto(
    val email: String,
    val name: String,
    val confirmed: Boolean = true,
)
