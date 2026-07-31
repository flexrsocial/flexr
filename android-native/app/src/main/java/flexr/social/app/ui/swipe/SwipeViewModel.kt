package flexr.social.app.ui.swipe

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.LocationRepository
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.SafetyRepository
import flexr.social.app.data.repository.SwipeRepository
import flexr.social.app.domain.model.Profile
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SwipeUiState(
    val deck: List<Profile> = emptyList(),
    val currentIndex: Int = 0,
    val isLoading: Boolean = true,
    val error: String? = null,
    /** Profil, mit dem gerade ein Match entstanden ist (Overlay). */
    val matchedWith: Profile? = null,
    val ownAvatarUrl: String? = null,
    val usesGpsLocation: Boolean = false,
    val searchRadiusKm: Int = 20,
) {
    val current: Profile? get() = deck.getOrNull(currentIndex)
    val next: Profile? get() = deck.getOrNull(currentIndex + 1)
    val isExhausted: Boolean get() = !isLoading && currentIndex >= deck.size
}

/** Einmalige Rückmeldungen an die Oberfläche. */
sealed interface SwipeEvent {
    data class Message(val text: String) : SwipeEvent
    data class OpenChat(val matchId: String) : SwipeEvent
}

/**
 * Swipe-Deck: Standortabgleich, Kandidatenliste, Like/Pass und die
 * Sicherheitsaktionen direkt auf der Karte.
 */
@HiltViewModel
class SwipeViewModel @Inject constructor(
    private val swipeRepository: SwipeRepository,
    private val profileRepository: ProfileRepository,
    private val locationRepository: LocationRepository,
    private val safetyRepository: SafetyRepository,
    private val matchRepository: MatchRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(SwipeUiState())
    val uiState: StateFlow<SwipeUiState> = _uiState.asStateFlow()

    private val _events = Channel<SwipeEvent>(Channel.BUFFERED)
    val events: Flow<SwipeEvent> = _events.receiveAsFlow()

    init {
        syncLocationAndLoadDeck()
    }

    /**
     * Bei jedem Start: Standort abgleichen, dann das Deck laden.
     *
     * Mit Freigabe geht die GPS-Position ans Backend, ohne Freigabe wird eine
     * gespeicherte Position gelöscht — dann greift die Koordinate der PLZ.
     * Der Abgleich darf das Laden nie blockieren, deshalb kapselt
     * [LocationRepository] ein eigenes Zeitlimit.
     */
    fun syncLocationAndLoadDeck() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            syncLocation()
            loadDeck()
        }
    }

    private suspend fun syncLocation() {
        runCatching {
            val location = locationRepository.currentLocation()
            if (location != null) {
                profileRepository.updateLocation(location.latitude, location.longitude)
            } else if (profileRepository.myProfile.value?.hasGpsLocation == true) {
                profileRepository.clearLocation()
            } else {
                profileRepository.myProfile.value
            }
        }.onSuccess { profile ->
            profile?.let {
                _uiState.update { state ->
                    state.copy(
                        usesGpsLocation = it.hasGpsLocation,
                        searchRadiusKm = it.searchRadiusKm,
                        ownAvatarUrl = it.photos.firstOrNull()?.avatarUrl,
                    )
                }
            }
        }
    }

    fun loadDeck() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            runCatching { swipeRepository.loadDeck() }
                .onSuccess { profiles ->
                    _uiState.update { it.copy(deck = profiles, currentIndex = 0, isLoading = false) }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            error = (throwable as? FlexrApiException)?.message
                                ?: "Profile konnten nicht geladen werden.",
                        )
                    }
                }
        }
    }

    /** Nach der Berechtigungsabfrage: Standort neu abgleichen und Deck aktualisieren. */
    fun onLocationPermissionResult(granted: Boolean) {
        if (granted) syncLocationAndLoadDeck() else loadDeck()
    }

    fun like() = swipe(isLike = true)

    fun pass() = swipe(isLike = false)

    private fun swipe(isLike: Boolean) {
        val target = _uiState.value.current ?: return
        // Die Karte ist bereits weggeflogen — sofort weiterschalten, damit sich
        // die Oberfläche nie am Netz aufhält.
        _uiState.update { it.copy(currentIndex = it.currentIndex + 1) }

        viewModelScope.launch {
            runCatching {
                if (isLike) swipeRepository.like(target.id) else swipeRepository.pass(target.id)
            }.onSuccess { outcome ->
                if (outcome.matched) {
                    _uiState.update { it.copy(matchedWith = target) }
                    runCatching { matchRepository.refresh() }
                }
            }.onFailure { throwable ->
                _events.send(
                    SwipeEvent.Message(
                        (throwable as? FlexrApiException)?.message ?: "Swipe fehlgeschlagen.",
                    ),
                )
            }
        }
    }

    fun dismissMatchOverlay() = _uiState.update { it.copy(matchedWith = null) }

    /** „Nachricht schreiben" aus dem Match-Overlay heraus. */
    fun openChatWithMatch() {
        val profile = _uiState.value.matchedWith ?: return
        dismissMatchOverlay()
        viewModelScope.launch {
            val matches = runCatching { matchRepository.refresh() }.getOrDefault(emptyList())
            val match = matches.firstOrNull { it.profile.id == profile.id }
            if (match != null) {
                _events.send(SwipeEvent.OpenChat(match.matchId))
            } else {
                _events.send(SwipeEvent.Message("Chat konnte nicht geöffnet werden."))
            }
        }
    }

    fun report(userId: String, reason: String) {
        viewModelScope.launch {
            runCatching { safetyRepository.report(userId, reason) }
                .onSuccess { _events.send(SwipeEvent.Message("Meldung gesendet. Danke für dein Feedback.")) }
                .onFailure {
                    _events.send(SwipeEvent.Message(it.message ?: "Meldung fehlgeschlagen."))
                }
        }
    }

    fun block(userId: String, name: String) {
        viewModelScope.launch {
            runCatching { safetyRepository.block(userId) }
                .onSuccess {
                    // Blockierte Person überspringen, ohne dafür einen Swipe zu senden.
                    _uiState.update { state ->
                        if (state.current?.id == userId) state.copy(currentIndex = state.currentIndex + 1)
                        else state
                    }
                    _events.send(SwipeEvent.Message("$name blockiert."))
                }
                .onFailure {
                    _events.send(SwipeEvent.Message(it.message ?: "Blockieren fehlgeschlagen."))
                }
        }
    }
}
