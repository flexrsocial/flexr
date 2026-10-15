package flexr.social.app.ui.swipe

import flexr.social.app.data.remote.dto.MyProfileDto
import flexr.social.app.data.remote.dto.ProfileDto
import flexr.social.app.data.repository.BillingRepository
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.SafetyRepository
import flexr.social.app.data.repository.SwipeRepository
import flexr.social.app.data.repository.toDomain
import flexr.social.app.domain.model.PhotoVisibility
import flexr.social.app.testing.FakeAppStrings
import flexr.social.app.testing.FakeFlexrApi
import flexr.social.app.testing.FakeMatchDao
import flexr.social.app.testing.FakeMessageDao
import flexr.social.app.testing.FakeSessionStore
import flexr.social.app.testing.MainDispatcherRule
import flexr.social.app.testing.fotoDto
import flexr.social.app.testing.meinProfilDto
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

/**
 * Hinweis "in der Suche nicht sichtbar" (Bugfix-Runde 14.10.2026): Wer nach
 * der Freischaltung noch auf die Fotofreigabe wartet oder eine Ablehnung
 * bekommt, soll das ueber dem Deck sehen - nicht nur klein im Konto.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class SichtbarkeitsHinweisTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private class TestApi(var profil: MyProfileDto) : FakeFlexrApi() {
        override suspend fun getMyProfile(): MyProfileDto = profil
        override suspend fun getDeck(): List<ProfileDto> = emptyList()
    }

    private suspend fun aufbau(api: TestApi): Pair<SwipeViewModel, ProfileRepository> {
        val profileRepository = ProfileRepository(api, FakeSessionStore())
        profileRepository.refresh()
        val viewModel = SwipeViewModel(
            swipeRepository = SwipeRepository(api),
            billingRepository = BillingRepository(api),
            profileRepository = profileRepository,
            safetyRepository = SafetyRepository(api),
            matchRepository = MatchRepository(api, FakeMatchDao(), FakeMessageDao()),
            strings = FakeAppStrings(),
        )
        return viewModel to profileRepository
    }

    @Test
    fun `server sagt in pruefung - hinweis ueber dem deck`() = runTest {
        val api = TestApi(
            meinProfilDto(photos = listOf(fotoDto(id = "a", status = "pending")))
                .copy(photoVisibility = "pending"),
        )
        val (viewModel, _) = aufbau(api)
        advanceUntilIdle()
        assertEquals(PhotoVisibility.PENDING, viewModel.uiState.value.ownPhotoVisibility)
    }

    @Test
    fun `freigabe im hintergrund laesst den hinweis beim zurueckkehren verschwinden`() = runTest {
        val api = TestApi(
            meinProfilDto(photos = listOf(fotoDto(id = "a", status = "rejected")))
                .copy(photoVisibility = "rejected"),
        )
        val (viewModel, _) = aufbau(api)
        advanceUntilIdle()
        assertEquals(PhotoVisibility.REJECTED, viewModel.uiState.value.ownPhotoVisibility)

        api.profil = meinProfilDto(photos = listOf(fotoDto(id = "b", status = "approved")))
            .copy(photoVisibility = "visible")
        viewModel.refreshOwnProfile()
        advanceUntilIdle()
        assertEquals(PhotoVisibility.VISIBLE, viewModel.uiState.value.ownPhotoVisibility)
    }

    @Test
    fun `nicht freigeschaltetes konto bekommt keinen hinweis`() = runTest {
        val api = TestApi(
            meinProfilDto(photos = listOf(fotoDto(id = "a", status = "pending")))
                .copy(photoVisibility = "pending", verificationRequired = true, isAccountActivated = false),
        )
        val (viewModel, _) = aufbau(api)
        advanceUntilIdle()
        assertEquals(PhotoVisibility.VISIBLE, viewModel.uiState.value.ownPhotoVisibility)
    }

    @Test
    fun `aelteres backend - app rechnet aus den fotos`() {
        fun sicht(vararg stati: String) = meinProfilDto(
            photos = stati.mapIndexed { i, st -> fotoDto(id = "f$i", status = st) },
        ).toDomain().photoVisibility

        // Seit 15.10.2026: ins Deck erst mit drei freigegebenen Fotos.
        assertEquals(PhotoVisibility.NONE, sicht())
        assertEquals(PhotoVisibility.NONE, sicht("approved", "pending"))
        assertEquals(PhotoVisibility.PENDING, sicht("approved", "pending", "pending", "rejected"))
        assertEquals(PhotoVisibility.REJECTED, sicht("approved", "approved", "rejected"))
        assertEquals(PhotoVisibility.VISIBLE, sicht("approved", "approved", "approved", "pending"))
    }
}
