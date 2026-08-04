package flexr.social.app.ui.swipe

import flexr.social.app.data.remote.dto.MyProfileDto
import flexr.social.app.data.remote.dto.ProfileDto
import flexr.social.app.data.remote.dto.UpdateProfileRequestDto
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.SafetyRepository
import flexr.social.app.data.repository.SwipeRepository
import flexr.social.app.testing.FakeFlexrApi
import flexr.social.app.testing.FakeMatchDao
import flexr.social.app.testing.FakeMessageDao
import flexr.social.app.testing.FakeSessionStore
import flexr.social.app.testing.MainDispatcherRule
import flexr.social.app.testing.meinProfilDto
import flexr.social.app.testing.profilDto
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

/**
 * Der Suchumkreis wird im Konto-Tab eingestellt, das Deck lebt im Swipe-Tab.
 * Weil die untere Navigation beide Bildschirme am Leben hält
 * (`saveState`/`restoreState` in FlexrApp), muss das ViewModel die Änderung
 * von sich aus mitbekommen — genau daran ist Version 2.0.8 gescheitert: der
 * Swipe-Bildschirm zeigte weiter das Deck und die Kilometerangabe vom
 * App-Start.
 */
// advanceUntilIdle() ist noch als experimentell markiert - ohne diese
// Zustimmung warnt der Compiler in jedem Testfall.
@OptIn(ExperimentalCoroutinesApi::class)
class SwipeViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    /**
     * Backend-Ersatz für die drei Endpunkte, die hier eine Rolle spielen.
     * `updateMyProfile` verhält sich wie der echte PATCH: es übernimmt die
     * gesetzten Felder und gibt das vollständige Profil zurück.
     */
    private class TestApi(
        private var profil: MyProfileDto,
        private val decks: List<List<ProfileDto>>,
    ) : FakeFlexrApi() {

        var deckAufrufe = 0
            private set

        override suspend fun getMyProfile(): MyProfileDto = profil

        override suspend fun getDeck(): List<ProfileDto> {
            val deck = decks[minOf(deckAufrufe, decks.lastIndex)]
            deckAufrufe++
            return deck
        }

        override suspend fun updateMyProfile(body: UpdateProfileRequestDto): MyProfileDto {
            profil = profil.copy(
                plz = body.plz ?: profil.plz,
                city = body.city ?: profil.city,
                gym = body.gym ?: profil.gym,
                bio = body.bio ?: profil.bio,
                searchRadiusKm = body.searchRadiusKm ?: profil.searchRadiusKm,
            )
            return profil
        }
    }

    /**
     * Baut die echten Repositories über [TestApi] auf und liefert das
     * ViewModel im selben Zustand wie beim Start der App: das eigene Profil
     * ist bereits geladen (MainGraph zeigt den Swipe-Tab erst dann).
     */
    private suspend fun aufbau(api: TestApi): Pair<SwipeViewModel, ProfileRepository> {
        val profileRepository = ProfileRepository(api, FakeSessionStore())
        profileRepository.refresh()
        val viewModel = SwipeViewModel(
            swipeRepository = SwipeRepository(api),
            profileRepository = profileRepository,
            safetyRepository = SafetyRepository(api),
            matchRepository = MatchRepository(api, FakeMatchDao(), FakeMessageDao()),
        )
        return viewModel to profileRepository
    }

    @Test
    fun `deck und kilometerangabe folgen einem verkleinerten suchumkreis`() = runTest {
        val api = TestApi(
            profil = meinProfilDto(searchRadiusKm = 200),
            decks = listOf(
                listOf(profilDto(id = "1", name = "Lea"), profilDto(id = "2", name = "Nora")),
                listOf(profilDto(id = "1", name = "Lea")),
            ),
        )
        val (viewModel, profileRepository) = aufbau(api)
        advanceUntilIdle()

        assertEquals(200, viewModel.uiState.value.searchRadiusKm)
        assertEquals(listOf("Lea", "Nora"), viewModel.uiState.value.deck.map { it.name })

        // Wie im Konto-Tab: Umkreis verkleinern und speichern.
        profileRepository.updateProfile(
            plz = "1100",
            city = "Wien",
            gymLabel = "McFit — Triester Straße 64, 1100",
            bio = "",
            searchRadiusKm = 5,
        )
        advanceUntilIdle()

        assertEquals("Kopfzeile zeigt den neuen Umkreis", 5, viewModel.uiState.value.searchRadiusKm)
        assertEquals(
            "Deck ist neu geladen",
            listOf("Lea"),
            viewModel.uiState.value.deck.map { it.name },
        )
        assertEquals("einmal beim Start, einmal nach der Änderung", 2, api.deckAufrufe)
    }

    @Test
    fun `ein gymwechsel laedt das deck neu`() = runTest {
        // Das Gym ist der Mittelpunkt der Umkreissuche — ein Wechsel verschiebt
        // das Deck genauso wie ein anderer Radius.
        val api = TestApi(meinProfilDto(), decks = listOf(emptyList()))
        val (_, profileRepository) = aufbau(api)
        advanceUntilIdle()
        assertEquals(1, api.deckAufrufe)

        profileRepository.updateProfile(
            plz = "1100",
            city = "Wien",
            gymLabel = "FITINN — Favoritenstraße 88-90, 1100 Wien",
            bio = "",
            searchRadiusKm = 20,
        )
        advanceUntilIdle()

        assertEquals(2, api.deckAufrufe)
    }

    @Test
    fun `eine aenderung ohne bezug zur suche laedt das deck nicht neu`() = runTest {
        // Eine neue Bio ändert nichts daran, wer im Umkreis liegt — ein
        // Neuladen wäre hier nur eine überflüssige Anfrage.
        val api = TestApi(
            profil = meinProfilDto(),
            decks = listOf(listOf(profilDto(id = "1", name = "Lea"))),
        )
        val (viewModel, profileRepository) = aufbau(api)
        advanceUntilIdle()

        profileRepository.updateProfile(
            plz = "1100",
            city = "Wien",
            gymLabel = "McFit — Triester Straße 64, 1100",
            bio = "Neue Bio",
            searchRadiusKm = 20,
        )
        advanceUntilIdle()

        assertEquals(1, api.deckAufrufe)
        assertEquals(listOf("Lea"), viewModel.uiState.value.deck.map { it.name })
    }
}
