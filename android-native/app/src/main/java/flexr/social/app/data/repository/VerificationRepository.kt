package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.PresignPhotoRequestDto
import flexr.social.app.data.remote.dto.VerificationDocumentPresignRequestDto
import flexr.social.app.data.remote.dto.VerificationDocumentSubmitRequestDto
import flexr.social.app.data.remote.dto.VerificationSelfieDto
import flexr.social.app.data.remote.dto.VerificationSubmitRequestDto
import flexr.social.app.domain.model.VerificationState
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Alters- und Identitätsprüfung — ein Vorgang in zwei Schritten.
 *
 * Schritt 1: Der Server gibt die Anweisung vor ("Schau direkt in die Kamera"),
 * das Selfie entsteht live über die Kamera — kein Galerie-Upload.
 *
 * Schritt 2: eine Aufnahme des amtlichen Lichtbildausweises. Danach vergleicht
 * ein Mensch Profilfoto, Selfie und Ausweisfoto und gleicht das Geburtsdatum
 * ab — es findet keine automatisierte biometrische Auswertung statt.
 */
@Singleton
class VerificationRepository @Inject constructor(
    private val api: FlexrApi,
) {

    suspend fun status(): VerificationState = apiCall { api.getVerificationStatus() }.toDomain()

    suspend fun start(): VerificationState = apiCall { api.startVerification() }.toDomain()

    /**
     * Lädt die Aufnahmen hoch und reicht sie ein. Sie müssen exakt der
     * ausgegebenen Anweisungsliste entsprechen, sonst weist das Backend die
     * Einreichung zurück.
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

    /**
     * Schritt 2: Aufnahmen des amtlichen Lichtbildausweises.
     *
     * Die Bilder gehen per Presigned PUT direkt in einen privaten Bereich des
     * Objekt-Storage — sie laufen nicht durchs Backend und bekommen nie eine
     * öffentliche Adresse. Der Server prüft danach Größe und tatsächliches
     * Bildformat und löscht die Aufnahmen nach der Entscheidung.
     */
    suspend fun submitDocument(
        documentType: String,
        front: ByteArray,
        back: ByteArray? = null,
    ): VerificationState {
        val frontKey = upload(front)
        val backKey = back?.let { upload(it) }
        return apiCall {
            api.submitDocument(
                VerificationDocumentSubmitRequestDto(
                    documentType = documentType,
                    frontObjectKey = frontKey,
                    backObjectKey = backKey,
                ),
            )
        }.toDomain()
    }

    /** Eingereichte Aufnahmen zurückziehen, solange noch niemand geprüft hat. */
    suspend fun discardDocuments(): VerificationState =
        apiCall { api.discardDocuments() }.toDomain()

    private suspend fun upload(bytes: ByteArray): String {
        val presign = apiCall {
            api.presignDocument(
                VerificationDocumentPresignRequestDto(
                    contentType = MIME_TYPE,
                    byteSize = bytes.size,
                ),
            )
        }
        apiCall {
            api.uploadToPresignedUrl(
                url = presign.uploadUrl,
                contentType = MIME_TYPE,
                body = bytes.toRequestBody(MIME_TYPE.toMediaType()),
            )
        }
        return presign.objectKey
    }

    private companion object {
        const val MIME_TYPE = "image/jpeg"
    }
}
