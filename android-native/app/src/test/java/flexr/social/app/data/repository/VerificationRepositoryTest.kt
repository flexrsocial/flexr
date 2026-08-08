package flexr.social.app.data.repository

import flexr.social.app.data.remote.dto.PresignPhotoResponseDto
import flexr.social.app.data.remote.dto.VerificationDocumentPresignRequestDto
import flexr.social.app.data.remote.dto.VerificationDocumentSubmitRequestDto
import flexr.social.app.data.remote.dto.VerificationStatusDto
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.testing.FakeFlexrApi
import kotlinx.coroutines.test.runTest
import okhttp3.RequestBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Ausweisaufnahmen gehen per Presigned PUT direkt in den Objekt-Storage.
 * Geprüft wird, dass genau die dort abgelegten Schlüssel eingereicht werden —
 * ein vertauschter Schlüssel würde die Prüfung dem falschen Vorgang zuordnen.
 */
class VerificationRepositoryTest {

    private class Api : FakeFlexrApi() {
        val presignAufrufe = mutableListOf<VerificationDocumentPresignRequestDto>()
        val hochgeladen = mutableListOf<String>()
        var eingereicht: VerificationDocumentSubmitRequestDto? = null

        override suspend fun presignDocument(
            body: VerificationDocumentPresignRequestDto,
        ): PresignPhotoResponseDto {
            presignAufrufe += body
            val nummer = presignAufrufe.size
            return PresignPhotoResponseDto(
                uploadUrl = "https://storage.example/upload-$nummer",
                objectKey = "verification-documents/vorgang/$nummer.jpg",
            )
        }

        override suspend fun uploadToPresignedUrl(
            url: String,
            contentType: String,
            body: RequestBody,
        ) {
            hochgeladen += url
        }

        override suspend fun submitDocument(
            body: VerificationDocumentSubmitRequestDto,
        ): VerificationStatusDto {
            eingereicht = body
            return VerificationStatusDto(status = "submitted", nextStep = "wait")
        }
    }

    @Test
    fun `Ausweis mit Vorder- und Rueckseite wird vollstaendig eingereicht`() = runTest {
        val api = Api()
        val repository = VerificationRepository(api)

        val state = repository.submitDocument(
            documentType = "id_card",
            front = ByteArray(120) { 1 },
            back = ByteArray(90) { 2 },
        )

        assertEquals(2, api.presignAufrufe.size)
        assertEquals(2, api.hochgeladen.size)
        // Die gemeldete Größe muss der tatsächlichen entsprechen - der Server
        // lehnt zu große Aufnahmen bereits beim Presign ab.
        assertEquals(120, api.presignAufrufe[0].byteSize)
        assertEquals(90, api.presignAufrufe[1].byteSize)
        assertTrue(api.presignAufrufe.all { it.contentType == "image/jpeg" })

        val eingereicht = requireNotNull(api.eingereicht)
        assertEquals("id_card", eingereicht.documentType)
        assertEquals("verification-documents/vorgang/1.jpg", eingereicht.frontObjectKey)
        assertEquals("verification-documents/vorgang/2.jpg", eingereicht.backObjectKey)
        assertEquals(VerificationStatus.SUBMITTED, state.status)
    }

    @Test
    fun `Reisepass kommt ohne Rueckseite aus`() = runTest {
        val api = Api()
        val repository = VerificationRepository(api)

        repository.submitDocument(documentType = "passport", front = ByteArray(50), back = null)

        assertEquals(1, api.presignAufrufe.size)
        assertEquals(1, api.hochgeladen.size)
        assertNull(requireNotNull(api.eingereicht).backObjectKey)
    }
}
