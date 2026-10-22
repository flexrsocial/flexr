package flexr.social.app.ui.incoming

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
import flexr.social.app.domain.model.IncomingLikes
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

data class IncomingUiState(
    val isLoading: Boolean = true,
    val likes: IncomingLikes? = null,
    val error: String? = null,
    /** Angetipptes Profil: Karte mit X und Herz statt der Liste. */
    val selected: Profile? = null,
    /** Zurückgeliked - das Match-Overlay wie im Deck. */
    val matchedWith: Profile? = null,
    val ownAvatarUrl: String? = null,
    val isSwiping: Boolean = false,
)

sealed interface IncomingEvent {
    data class Message(val text: String, val sticky: Boolean = false) : IncomingEvent
    data class OpenChat(val matchId: String) : IncomingEvent
}

/**
 * „Wer dich geliket hat" — eine Premium-Funktion.
 *
 * Ohne Premium liefert der Server keine Fehlermeldung, sondern die Anzahl ohne
 * Profile ([IncomingLikes.premiumRequired]). Diese Unterscheidung bleibt bis in
 * die Oberfläche erhalten: „3 Leute warten auf dich" ist die ehrliche Antwort
 * und zugleich der beste Grund, sich Premium anzusehen — eine Fehlermeldung
 * wäre beides nicht.
 *
 * Seit 2.7.39 öffnet ein Tipp auf eine Zeile das Profil mit X und Herz: Der
 * Untertitel „Ansehen und zurückliken" versprach das schon länger, bis dahin
 * ging Zurückliken nur über das Deck. Ein Like hier ist immer ein Match.
 *
 * Eigenes ViewModel statt eines geteilten mit der Matchliste: Der Bildschirm
 * wird selten geöffnet und soll beim Öffnen frisch laden, während die Karte
 * über der Matchliste nur die Zahl braucht.
 */
@HiltViewModel
class IncomingViewModel @Inject constructor(
    private val swipeRepository: SwipeRepository,
    private val billingRepository: BillingRepository,
    private val profileRepository: ProfileRepository,
    private val safetyRepository: SafetyRepository,
    private val matchRepository: MatchRepository,
    private val strings: AppStrings,
) : ViewModel() {

    private val _uiState = MutableStateFlow(IncomingUiState())
    val uiState: StateFlow<IncomingUiState> = _uiState.asStateFlow()

    private val _events = Channel<IncomingEvent>(Channel.BUFFERED)
    val events: Flow<IncomingEvent> = _events.receiveAsFlow()

    init {
        load()
        viewModelScope.launch {
            profileRepository.myProfile.filterNotNull().collect { profile ->
                _uiState.update { it.copy(ownAvatarUrl = profile.ownAvatarUrl) }
            }
        }
    }

    fun load() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            runCatching { swipeRepository.incomingLikes() }
                .onSuccess { likes ->
                    _uiState.update { it.copy(isLoading = false, likes = likes, error = null) }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            likes = null,
                            error = (throwable as? FlexrApiException)?.message
                                ?: strings.get(R.string.incoming_load_failed),
                        )
                    }
                }
        }
    }

    fun openProfile(profile: Profile) = _uiState.update { it.copy(selected = profile) }

    fun closeProfile() = _uiState.update { it.copy(selected = null) }

    fun like() = swipe(isLike = true)

    fun pass() = swipe(isLike = false)

    private fun swipe(isLike: Boolean) {
        val target = _uiState.value.selected ?: return
        if (_uiState.value.isSwiping) return
        _uiState.update { it.copy(isSwiping = true) }
        viewModelScope.launch {
            runCatching {
                if (isLike) swipeRepository.like(target.id) else swipeRepository.pass(target.id)
            }.onSuccess { outcome ->
                billingRepository.updateLikesRemaining(outcome.likesRemaining)
                swipeRepository.alsErledigtMerken(target.id)
                _uiState.update {
                    it.copy(
                        selected = null,
                        isSwiping = false,
                        likes = it.likes?.ohne(target.id),
                        matchedWith = if (outcome.matched) target else null,
                    )
                }
                if (outcome.matched) runCatching { matchRepository.refresh() }
            }.onFailure { throwable ->
                // Etwa das aufgebrauchte Like-Kontingent: Die Karte bleibt offen.
                _uiState.update { it.copy(isSwiping = false) }
                _events.send(
                    IncomingEvent.Message(
                        (throwable as? FlexrApiException)?.message ?: strings.get(R.string.swipe_failed),
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
                _events.send(IncomingEvent.OpenChat(match.matchId))
            } else {
                _events.send(IncomingEvent.Message(strings.get(R.string.chat_open_failed)))
            }
        }
    }

    fun report(reason: String) {
        val target = _uiState.value.selected ?: return
        viewModelScope.launch {
            runCatching { safetyRepository.report(target.id, reason) }
                // Empfangsbestätigung mit Aktenzeichen (Art. 16 Abs. 4 DSA).
                // Der Server lässt die Person danach aus den offenen Likes weg.
                .onSuccess {
                    entferne(target.id)
                    _events.send(IncomingEvent.Message(it.message, sticky = true))
                }
                .onFailure {
                    _events.send(IncomingEvent.Message(it.message ?: strings.get(R.string.report_failed)))
                }
        }
    }

    fun block() {
        val target = _uiState.value.selected ?: return
        viewModelScope.launch {
            runCatching { safetyRepository.block(target.id) }
                .onSuccess {
                    entferne(target.id)
                    _events.send(IncomingEvent.Message(strings.get(R.string.block_done, target.name)))
                }
                .onFailure {
                    _events.send(IncomingEvent.Message(it.message ?: strings.get(R.string.block_failed)))
                }
        }
    }

    private fun entferne(userId: String) {
        swipeRepository.alsErledigtMerken(userId)
        _uiState.update { it.copy(selected = null, likes = it.likes?.ohne(userId)) }
    }
}

private fun IncomingLikes.ohne(userId: String): IncomingLikes = copy(
    count = (count - 1).coerceAtLeast(0),
    profiles = profiles.filterNot { it.id == userId },
)
