package flexr.social.app.ui.swipe

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.network.FlexrApiException
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
import kotlinx.coroutines.flow.filterNotNull
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
 * Swipe-Deck: Kandidatenliste, Like/Pass und die Sicherheitsaktionen direkt
 * auf der Karte. Der Suchmittelpunkt kommt vom Backend aus der Adresse des
 * eingetragenen Gyms - die App ermittelt dafür keine Position.
 */
@HiltViewModel
class SwipeViewModel @Inject constructor(
    private val swipeRepository: SwipeRepository,
    private val profileRepository: ProfileRepository,
    private val safetyRepository: SafetyRepository,
    private val matchRepository: MatchRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(SwipeUiState())
    val uiState: StateFlow<SwipeUiState> = _uiState.asStateFlow()

    private val _events = Channel<SwipeEvent>(Channel.BUFFERED)
    val events: Flow<SwipeEvent> = _events.receiveAsFlow()

    init {
        observeMyProfile()
        loadDeck()
    }

    /**
     * Eigenes Profil laufend beobachten - Radius und Avatar für den Kopfbereich,
     * und ein neues Deck, sobald sich die Suchkriterien ändern.
     *
     * Der Bildschirm bleibt samt ViewModel im Hintergrund erhalten, solange die
     * untere Navigation genutzt wird (`saveState`/`restoreState` in FlexrApp).
     * Ein einmaliges Auslesen beim Start würde deshalb den Stand vom App-Start
     * einfrieren: Wer im Konto-Tab den Umkreis ändert, bekäme hier weiterhin
     * das alte Deck und die alte Kilometerangabe zu sehen.
     *
     * Ein Standortabgleich findet nicht statt: die Umkreissuche geht von der
     * Adresse des eingetragenen Gyms aus, nicht von der Geräteposition. Genau
     * deshalb zählt neben dem Radius auch das Gym als Suchkriterium.
     */
    private fun observeMyProfile() {
        viewModelScope.launch {
            var letzteSuchkriterien: Pair<Int, String>? = null
            profileRepository.myProfile.filterNotNull().collect { profile ->
                _uiState.update { state ->
                    state.copy(
                        searchRadiusKm = profile.searchRadiusKm,
                        ownAvatarUrl = profile.photos.firstOrNull()?.avatarUrl,
                    )
                }
                val suchkriterien = profile.searchRadiusKm to profile.profile.gym
                // Beim ersten Durchlauf nicht nachladen - das erledigt init().
                if (letzteSuchkriterien != null && letzteSuchkriterien != suchkriterien) {
                    loadDeck()
                }
                letzteSuchkriterien = suchkriterien
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
                // Empfangsbestätigung mit Aktenzeichen (Art. 16 Abs. 4 DSA)
                .onSuccess { _events.send(SwipeEvent.Message(it.message)) }
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
