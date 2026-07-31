package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.PresignPhotoRequestDto
import flexr.social.app.data.remote.dto.VerificationSelfieDto
import flexr.social.app.data.remote.dto.VerificationSubmitRequestDto
import flexr.social.app.domain.model.VerificationState
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Foto-Verifizierung (blauer Haken).
 *
 * Der Server gibt drei zufällige Posen vor, die Selfies entstehen live über die
 * Kamera — kein Galerie-Upload. Das ist der Liveness-Schutz: nur eine echte
 * Person vor der Kamera kann die verlangten Posen spontan liefern.
 */
@Singleton
class VerificationRepository @Inject constructor(
    private val api: FlexrApi,
) {

    suspend fun status(): VerificationState = apiCall { api.getVerificationStatus() }.toDomain()

    suspend fun start(): VerificationState = apiCall { api.startVerification() }.toDomain()

    /**
     * Lädt die drei Aufnahmen hoch und reicht sie ein. Die Reihenfolge muss
     * exakt der ausgegebenen Posenliste entsprechen, sonst weist das Backend
     * die Einreichung zurück.
     */
    suspend fun submit(selfies: List<Pair<String, ByteArray>>): VerificationState {
        val uploaded = selfies.map { (prompt, bytes) ->
            val presign = apiCall { api.presignSelfie(PresignPhotoRequestDto(MIME_TYPE)) }
            apiCall {
                api.uploadToPresignedUrl(
                    url = presign.uploadUrl,
                    contentType = MIME_TYPE,
                    body = bytes.toRequestBody(MIME_TYPE.toMediaType()),
                )
            }
            VerificationSelfieDto(prompt = prompt, objectKey = presign.objectKey)
        }
        return apiCall { api.submitVerification(VerificationSubmitRequestDto(uploaded)) }.toDomain()
    }

    private companion object {
        const val MIME_TYPE = "image/jpeg"
    }
}
