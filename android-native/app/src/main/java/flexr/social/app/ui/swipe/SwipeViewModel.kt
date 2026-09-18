package flexr.social.app.ui.swipe

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.R
import flexr.social.app.core.locale.AppStrings
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.BillingRepository
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
    /** Laeuft ein Premium-Abo? Nur dann gibt es den Zuruecknehmen-Knopf. */
    val isPremium: Boolean = false,
    val isRewinding: Boolean = false,
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
    private val billingRepository: BillingRepository,
    private val profileRepository: ProfileRepository,
    private val safetyRepository: SafetyRepository,
    private val matchRepository: MatchRepository,
    private val strings: AppStrings,
) : ViewModel() {

    private val _uiState = MutableStateFlow(SwipeUiState())
    val uiState: StateFlow<SwipeUiState> = _uiState.asStateFlow()

    private val _events = Channel<SwipeEvent>(Channel.BUFFERED)
    val events: Flow<SwipeEvent> = _events.receiveAsFlow()

    init {
        observeMembership()
        observeMyProfile()
        loadDeck()
    }

    /**
     * Premium-Status mitlesen statt einmalig abfragen: Wer im Kontobereich
     * abschliesst oder kuendigt, soll den Zuruecknehmen-Knopf ohne Neustart
     * bekommen oder verlieren. Der Bildschirm bleibt samt ViewModel im
     * Hintergrund bestehen (siehe observeMyProfile), ein einmaliges Auslesen
     * fror den Stand vom App-Start ein.
     */
    private fun observeMembership() {
        viewModelScope.launch {
            billingRepository.membership.filterNotNull().collect { membership ->
                _uiState.update { it.copy(isPremium = membership.isPremium) }
            }
        }
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
                                ?: strings.get(R.string.swipe_load_failed),
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
        val gewischterIndex = _uiState.value.currentIndex
        _uiState.update { it.copy(currentIndex = it.currentIndex + 1) }

        viewModelScope.launch {
            runCatching {
                if (isLike) swipeRepository.like(target.id) else swipeRepository.pass(target.id)
            }.onSuccess { outcome ->
                // Der Server rechnet das Kontingent ohnehin schon aus und
                // liefert es mit - die Pille im Kopf zieht darueber nach.
                billingRepository.updateLikesRemaining(outcome.likesRemaining)
                if (outcome.matched) {
                    _uiState.update { it.copy(matchedWith = target) }
                    runCatching { matchRepository.refresh() }
                }
            }.onFailure { throwable ->
                val fehler = throwable as? FlexrApiException
                // Aufgebrauchtes Like-Kontingent: Die Karte kommt zurueck.
                // Vorher blieb sie weg, obwohl der Like nie gezaehlt hat - das
                // Profil war damit ohne Zutun uebersprungen und im Deck nicht
                // wieder zu finden.
                //
                // `coerceAtMost` und nicht "einen zurueck": Wer schnell wischt,
                // hat bis zur Antwort des Servers vielleicht schon
                // weitergewischt. Auf den Index der abgelehnten Karte
                // zurueckzugehen ist dann richtig, ein Schritt zurueck waere
                // eine beliebige andere Karte.
                if (fehler?.code == "like_limit_reached") {
                    _uiState.update { it.copy(currentIndex = it.currentIndex.coerceAtMost(gewischterIndex)) }
                }
                _events.send(
                    SwipeEvent.Message(fehler?.message ?: strings.get(R.string.swipe_failed)),
                )
            }
        }
    }

    /**
     * Letzten Swipe zuruecknehmen (Premium).
     *
     * Danach wird das Deck neu geladen: Der Server hat den Swipe geloescht,
     * das Profil taucht dort also wieder auf. Ein Zurueckschieben des
     * `currentIndex` waere kuerzer, aber falsch - der zurueckgenommene Swipe
     * muss nicht der letzte im aktuellen Deck gewesen sein (etwa nach einem
     * Neuladen wegen geaenderter Suchkriterien).
     *
     * Fehler kommen im Klartext des Servers durch: "brauchst Premium" (403)
     * und "daraus ist schon ein Match geworden" (409) sind fuer den Nutzer
     * zwei sehr verschiedene Nachrichten.
     */
    fun rewindLastSwipe() {
        if (_uiState.value.isRewinding) return
        _uiState.update { it.copy(isRewinding = true) }
        viewModelScope.launch {
            runCatching { swipeRepository.rewindLastSwipe() }
                .onSuccess { outcome ->
                    billingRepository.updateLikesRemaining(outcome.likesRemaining)
                    _events.send(SwipeEvent.Message(strings.get(R.string.premium_rewind_done)))
                    loadDeck()
                }
                .onFailure { throwable ->
                    _events.send(
                        SwipeEvent.Message(
                            (throwable as? FlexrApiException)?.message
                                ?: strings.get(R.string.premium_rewind_failed),
                        ),
                    )
                }
            _uiState.update { it.copy(isRewinding = false) }
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
                _events.send(SwipeEvent.Message(strings.get(R.string.chat_open_failed)))
            }
        }
    }

    fun report(userId: String, reason: String) {
        viewModelScope.launch {
            runCatching { safetyRepository.report(userId, reason) }
                // Empfangsbestätigung mit Aktenzeichen (Art. 16 Abs. 4 DSA)
                .onSuccess { _events.send(SwipeEvent.Message(it.message)) }
                .onFailure {
                    _events.send(SwipeEvent.Message(it.message ?: strings.get(R.string.report_failed)))
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
                    _events.send(SwipeEvent.Message(strings.get(R.string.block_done, name)))
                }
                .onFailure {
                    _events.send(SwipeEvent.Message(it.message ?: strings.get(R.string.block_failed)))
                }
        }
    }
}
