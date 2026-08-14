package flexr.social.app.ui.verification

import flexr.social.app.core.media.PhotoPreparer
import flexr.social.app.core.media.PreparedPhoto
import flexr.social.app.data.remote.dto.AddPhotoRequestDto
import flexr.social.app.data.remote.dto.EmailResendResponseDto
import flexr.social.app.data.remote.dto.MyProfileDto
import flexr.social.app.data.remote.dto.PresignPhotoRequestDto
import flexr.social.app.data.remote.dto.PresignPhotoResponseDto
import flexr.social.app.data.remote.dto.VerificationStatusDto
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.VerificationRepository
import flexr.social.app.testing.FakeFlexrApi
import flexr.social.app.testing.FakeSessionStore
import flexr.social.app.testing.MainDispatcherRule
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import flexr.social.app.testing.meinProfilDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

/**
 * "Status aktualisieren" auf dem Wartebildschirm.
 *
 * Wer während der Prüfung freigeschaltet wird, drückte den Knopf und bekam
 * nichts: keine Meldung, keinen Wechsel in die App. Der alte Code lud das
 * Profil und verließ sich darauf, dass die App dem Sitzungszustand folgt — nur
 * beobachtet MainViewModel ausschließlich `isLoggedIn`, nicht das Profil.
 *
 * Die Freischaltung steht in der Statusantwort selbst; sie muss im UI-Zustand
 * ankommen, damit der Bildschirm das Neuladen der Sitzung anstoßen kann.
 */
// advanceUntilIdle() ist noch als experimentell markiert.
@OptIn(ExperimentalCoroutinesApi::class)
class VerificationGateViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    /** Liefert nacheinander die vorgegebenen Statusantworten. */
    private open class TestApi(private val antworten: List<VerificationStatusDto>) : FakeFlexrApi() {
        var aufrufe = 0
            private set

        override suspend fun getVerificationStatus(): VerificationStatusDto {
            val antwort = antworten[minOf(aufrufe, antworten.lastIndex)]
            aufrufe++
            return antwort
        }
    }

    private fun viewModel(
        api: TestApi,
        preparer: PhotoPreparer = PhotoPreparer { PreparedPhoto(ByteArray(4), ByteArray(2)) },
    ) = VerificationGateViewModel(
        verificationRepository = VerificationRepository(api),
        profileRepository = ProfileRepository(api, FakeSessionStore()),
        photoPreparer = preparer,
    )

    private fun inPruefung() = VerificationStatusDto(
        status = "submitted",
        nextStep = "wait",
        verificationRequired = true,
        accountActivated = false,
    )

    private fun mailOffen() = VerificationStatusDto(
        status = "none",
        nextStep = "selfie",
        verificationRequired = true,
        accountActivated = false,
        emailVerified = false,
    )

    private fun freigeschaltet() = VerificationStatusDto(
        status = "approved",
        nextStep = "none",
        verificationRequired = true,
        accountActivated = true,
    )

    @Test
    fun `Freischaltung zwischen Laden und Knopfdruck wird erkannt`() = runTest {
        val api = TestApi(listOf(inPruefung(), freigeschaltet()))
        val viewModel = viewModel(api)
        advanceUntilIdle()

        assertTrue(viewModel.uiState.value.isWaiting)
        assertFalse(viewModel.uiState.value.isActivated)

        var nochInPruefung = false
        viewModel.refresh { nochInPruefung = true }
        advanceUntilIdle()

        assertTrue(viewModel.uiState.value.isActivated)
        // Kein "Die Prüfung läuft noch" für ein freigeschaltetes Konto.
        assertFalse(nochInPruefung)
    }

    @Test
    fun `laufende Pruefung meldet sich weiterhin als laufend`() = runTest {
        val api = TestApi(listOf(inPruefung()))
        val viewModel = viewModel(api)
        advanceUntilIdle()

        var nochInPruefung = false
        viewModel.refresh { nochInPruefung = true }
        advanceUntilIdle()

        assertTrue(nochInPruefung)
        assertFalse(viewModel.uiState.value.isActivated)
        assertTrue(viewModel.uiState.value.isWaiting)
    }

    /**
     * Scheitert der Foto-Upload während der Registrierung, existiert das Konto
     * ohne Foto. /verification/start lehnt dann ab ("Lade zuerst mindestens ein
     * Profilfoto hoch"), und der Konto-Bildschirm mit der Fotoverwaltung liegt
     * im Hauptgraphen, den ein nicht freigeschaltetes Konto nie erreicht - es
     * blieb nur die Kontolöschung.
     */
    @Test
    fun `fehlendes Profilfoto wird gemeldet und laesst sich nachreichen`() = runTest {
        val api = object : TestApi(listOf(inPruefung())) {
            var registriert: AddPhotoRequestDto? = null

            override suspend fun getMyProfile() = meinProfilDto(photos = emptyList())

            override suspend fun presignPhoto(body: PresignPhotoRequestDto) =
                PresignPhotoResponseDto(
                    uploadUrl = "https://storage.example/put",
                    objectKey = "users/ich/${body.contentType.substringAfter('/')}",
                )

            override suspend fun uploadToPresignedUrl(
                url: String,
                contentType: String,
                body: okhttp3.RequestBody,
            ) = Unit

            override suspend fun addPhoto(body: AddPhotoRequestDto): MyProfileDto {
                registriert = body
                return meinProfilDto()
            }
        }
        val profileRepository = ProfileRepository(api, FakeSessionStore())
        val viewModel = VerificationGateViewModel(
            verificationRepository = VerificationRepository(api),
            profileRepository = profileRepository,
            photoPreparer = { PreparedPhoto(ByteArray(8), ByteArray(4)) },
        )

        // Wie in der App: MainViewModel laedt das Profil, bevor der
        // Verifizierungsgraph ueberhaupt sichtbar wird.
        profileRepository.refresh()
        advanceUntilIdle()
        assertFalse(viewModel.uiState.value.hasProfilePhoto)

        // Wie onPhotoPicked(), nur ohne android.net.Uri (im JVM-Test null).
        viewModel.storePhoto { PreparedPhoto(ByteArray(8), ByteArray(4)) }
        advanceUntilIdle()

        assertNotNull(api.registriert)
        assertTrue(viewModel.uiState.value.hasProfilePhoto)
        assertFalse(viewModel.uiState.value.isUploadingPhoto)
    }

    /**
     * Die unbestätigte Adresse steht vor allem anderen - der Server lehnt
     * /verification/start sonst ab.
     */
    @Test
    fun `unbestaetigte Adresse wird als erster Schritt gemeldet`() = runTest {
        val api = TestApi(listOf(mailOffen()))
        val viewModel = viewModel(api)
        advanceUntilIdle()

        assertTrue(viewModel.uiState.value.needsEmailConfirmation)
        assertFalse(viewModel.uiState.value.isWaiting)
    }

    @Test
    fun `erneutes Senden meldet Adresse und Gueltigkeit zurueck`() = runTest {
        val api = object : TestApi(listOf(mailOffen())) {
            var aufgerufen = 0

            override suspend fun resendVerificationEmail(): EmailResendResponseDto {
                aufgerufen++
                return EmailResendResponseDto(email = "nina@example.com", validHours = 24)
            }
        }
        val viewModel = viewModel(api)
        advanceUntilIdle()

        var gemeldet: Pair<String, Int>? = null
        viewModel.resendVerificationEmail { adresse, stunden -> gemeldet = adresse to stunden }
        advanceUntilIdle()

        assertEquals(1, api.aufgerufen)
        assertEquals("nina@example.com" to 24, gemeldet)
        assertFalse(viewModel.uiState.value.isSendingMail)
        // Die gemeldete Adresse landet im Zustand - der Nutzer soll sie sehen.
        assertEquals("nina@example.com", viewModel.uiState.value.email)
    }

    @Test
    fun `auch das Auffrischen beim Zurueckkehren erkennt die Freischaltung`() = runTest {
        val api = TestApi(listOf(inPruefung(), freigeschaltet()))
        val viewModel = viewModel(api)
        advanceUntilIdle()
        assertFalse(viewModel.uiState.value.isActivated)

        // LifecycleEventEffect(ON_RESUME) im Bildschirm ruft load().
        viewModel.load()
        advanceUntilIdle()

        assertTrue(viewModel.uiState.value.isActivated)
    }
}
