package flexr.social.app.data.repository

import flexr.social.app.core.media.PreparedPhoto
import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.AddPhotoRequestDto
import flexr.social.app.data.remote.dto.ConsentDto
import flexr.social.app.data.remote.dto.ConsentGrantRequestDto
import flexr.social.app.data.remote.dto.ConsentGrantResponseDto
import flexr.social.app.data.remote.dto.ConsentRevokeRequestDto
import flexr.social.app.data.remote.dto.ConsentRevokeResponseDto
import flexr.social.app.data.remote.dto.DeleteAccountRequestDto
import flexr.social.app.data.remote.dto.NotificationSettingsRequestDto
import flexr.social.app.data.remote.dto.PresignPhotoRequestDto
import flexr.social.app.data.remote.dto.ReorderPhotosRequestDto
import flexr.social.app.data.remote.dto.UpdateProfileRequestDto
import flexr.social.app.data.session.SessionStore
import flexr.social.app.domain.model.MyProfile
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Eigenes Profil: Stammdaten, Standort und Fotos.
 *
 * Das aktuelle Profil liegt als [StateFlow] vor, damit alle Bildschirme
 * (Konto, Chat-Sperre, Match-Overlay) dieselbe Wahrheit sehen — das ersetzt
 * die globale `myProfile`-Variable des Web-Frontends durch beobachtbaren Zustand.
 */
@Singleton
class ProfileRepository @Inject constructor(
    private val api: FlexrApi,
    private val sessionStore: SessionStore,
) {

    private val _myProfile = MutableStateFlow<MyProfile?>(null)
    val myProfile: StateFlow<MyProfile?> = _myProfile.asStateFlow()

    suspend fun refresh(): MyProfile {
        val profile = apiCall { api.getMyProfile() }.toDomain()
        _myProfile.value = profile
        sessionStore.saveUserId(profile.id)
        return profile
    }

    fun clear() {
        _myProfile.value = null
    }

    suspend fun updateProfile(
        plz: String,
        city: String,
        gymLabel: String,
        bio: String,
        searchRadiusKm: Int,
    ): MyProfile {
        val updated = apiCall {
            api.updateMyProfile(
                UpdateProfileRequestDto(
                    plz = plz,
                    city = city,
                    gym = gymLabel,
                    // Leere Bio bedeutet serverseitig „Bio entfernen".
                    bio = bio,
                    searchRadiusKm = searchRadiusKm,
                ),
            )
        }.toDomain()
        _myProfile.value = updated
        return updated
    }

    suspend fun deleteAccount(password: String) {
        apiCall { api.deleteMyAccount(DeleteAccountRequestDto(password)) }
        _myProfile.value = null
    }

    suspend fun consents(): List<ConsentDto> = apiCall { api.getMyConsents() }

    suspend fun revokeConsent(consentType: String): ConsentRevokeResponseDto = apiCall {
        api.revokeMyConsent(ConsentRevokeRequestDto(consentType))
    }

    suspend fun grantConsent(consentType: String): ConsentGrantResponseDto = apiCall {
        api.grantMyConsent(ConsentGrantRequestDto(consentType))
    }

    /** GPS-Position speichern — sie hat für die Umkreissuche Vorrang vor der PLZ. */

    /** Ohne Standortfreigabe: gespeicherte Position löschen, es gilt wieder die PLZ. */

    /**
     * Lädt Vollbild und Thumbnail direkt in den Objekt-Storage und registriert
     * anschließend die object_keys — es fließen keine Bilddaten durchs Backend.
     */
    suspend fun addPhoto(photo: PreparedPhoto): MyProfile {
        val fullKey = uploadToStorage(photo.full, photo.mimeType)
        val thumbKey = uploadToStorage(photo.thumbnail, photo.mimeType)
        val updated = apiCall {
            api.addPhoto(AddPhotoRequestDto(objectKey = fullKey, thumbObjectKey = thumbKey))
        }.toDomain()
        _myProfile.value = updated
        return updated
    }

    suspend fun deletePhoto(photoId: String): MyProfile {
        val updated = apiCall { api.deletePhoto(photoId) }.toDomain()
        _myProfile.value = updated
        return updated
    }

    /**
     * Neue Reihenfolge speichern. Erwartet die vollstaendige Liste der eigenen
     * Foto-IDs; photos[0] wird zum Hauptfoto (Swipe-Karte, Avatar, Chat-Kopf).
     */
    suspend fun reorderPhotos(photoIds: List<String>): MyProfile {
        val updated = apiCall { api.reorderPhotos(ReorderPhotosRequestDto(photoIds)) }.toDomain()
        _myProfile.value = updated
        return updated
    }

    suspend fun updateNotificationSettings(
        request: NotificationSettingsRequestDto,
    ): MyProfile {
        val updated = apiCall { api.updateNotificationSettings(request) }.toDomain()
        _myProfile.value = updated
        return updated
    }

    private suspend fun uploadToStorage(bytes: ByteArray, mimeType: String): String {
        val presign = apiCall { api.presignPhoto(PresignPhotoRequestDto(mimeType)) }
        apiCall {
            api.uploadToPresignedUrl(
                url = presign.uploadUrl,
                contentType = mimeType,
                body = bytes.toRequestBody(mimeType.toMediaType()),
            )
        }
        return presign.objectKey
    }
}
