package flexr.social.app.data.repository

import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.remote.dto.PresignPhotoResponseDto
import flexr.social.app.data.remote.dto.VerificationDocumentPresignRequestDto
import flexr.social.app.data.remote.dto.VerificationDocumentSubmitRequestDto
import flexr.social.app.data.remote.dto.VerificationStatusDto
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.testing.FakeFlexrApi
import java.io.IOException
import kotlinx.coroutines.test.runTest
import okhttp3.RequestBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Ausweisaufnahmen gehen per Presigned PUT direkt in den Objekt-Storage.
 * Geprüft wird, dass genau die dort abgelegten Schlüssel eingereicht werden —
 * ein vertauschter Schlüssel würde die Prüfung dem falschen Vorgang zuordnen.
 */
class VerificationRepositoryTest {

    private open class Api : FakeFlexrApi() {
        val presignAufrufe = mutableListOf<VerificationDocumentPresignRequestDto>()
        val hochgeladen = mutableListOf<String>()
        var eingereicht: VerificationDocumentSubmitRequestDto? = null
        var einreichFehler: Exception? = null
        var presignFehler: Exception? = null
        var serverStand = "id_required"
        var statusAbfragen = 0

        override suspend fun getVerificationStatus(): VerificationStatusDto {
            statusAbfragen++
            return VerificationStatusDto(status = serverStand, nextStep = "wait")
        }

        override suspend fun presignDocument(
            body: VerificationDocumentPresignRequestDto,
        ): PresignPhotoResponseDto {
            presignFehler?.let { throw it }
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
            einreichFehler?.let { throw it }
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

    @Test
    fun `verlorene Antwort gilt als eingereicht, wenn der Server den Ausweis hat`() = runTest {
        // Der Server hat eingereicht, die Antwort ging unterwegs verloren.
        val api = Api().apply {
            einreichFehler = IOException("Verbindung abgebrochen")
            serverStand = "submitted"
        }

        val state = VerificationRepository(api).submitDocument("passport", ByteArray(50))

        assertEquals(VerificationStatus.SUBMITTED, state.status)
        assertEquals(1, api.statusAbfragen)
    }

    @Test
    fun `zweiter Versuch nach laengst eingereichtem Ausweis endet nicht im Fehler`() = runTest {
        // So am 13.10.2026: Der erste Versuch kam durch, der zweite scheiterte
        // schon beim Presign, weil der Vorgang in der Prüfung lag.
        val api = Api().apply {
            presignFehler = FlexrApiException(400, "Für diesen Schritt läuft keine offene Verifizierung.")
            serverStand = "submitted"
        }

        val state = VerificationRepository(api).submitDocument("passport", ByteArray(50))

        assertEquals(VerificationStatus.SUBMITTED, state.status)
    }

    @Test
    fun `echter Fehler bleibt ein Fehler`() = runTest {
        val fehler = FlexrApiException(400, "Die Aufnahme ist kein gültiges Bild oder zu groß.")
        val api = Api().apply { einreichFehler = fehler }

        val geworfen = runCatching {
            VerificationRepository(api).submitDocument("passport", ByteArray(50))
        }.exceptionOrNull()

        assertSame(fehler, geworfen)
        assertEquals(1, api.statusAbfragen)
    }
}
