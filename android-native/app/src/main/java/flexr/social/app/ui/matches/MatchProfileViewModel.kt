package flexr.social.app.ui.matches

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.repository.SafetyRepository
import flexr.social.app.domain.model.MatchSummary
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed interface MatchProfileEvent {
    data class Message(val text: String) : MatchProfileEvent
    data object Closed : MatchProfileEvent
}

@HiltViewModel
class MatchProfileViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val matchRepository: MatchRepository,
    private val safetyRepository: SafetyRepository,
) : ViewModel() {

    private val matchId: String = checkNotNull(savedStateHandle["matchId"])

    private val _events = Channel<MatchProfileEvent>(Channel.BUFFERED)
    val events: Flow<MatchProfileEvent> = _events.receiveAsFlow()

    val match: StateFlow<MatchSummary?> = matchRepository.match(matchId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun report(reason: String) {
        val userId = match.value?.profile?.id ?: return
        viewModelScope.launch {
            runCatching { safetyRepository.report(userId, reason) }
                .onSuccess {
                    _events.send(MatchProfileEvent.Message("Meldung gesendet. Danke für dein Feedback."))
                }
                .onFailure {
                    _events.send(MatchProfileEvent.Message(it.message ?: "Meldung fehlgeschlagen."))
                }
        }
    }

    fun block() {
        val profile = match.value?.profile ?: return
        viewModelScope.launch {
            runCatching { safetyRepository.block(profile.id) }
                .onSuccess {
                    matchRepository.removeLocally(matchId)
                    _events.send(MatchProfileEvent.Message("${profile.name} blockiert."))
                    _events.send(MatchProfileEvent.Closed)
                }
                .onFailure {
                    _events.send(MatchProfileEvent.Message(it.message ?: "Blockieren fehlgeschlagen."))
                }
        }
    }

    fun unmatch() {
        val name = match.value?.profile?.name.orEmpty()
        viewModelScope.launch {
            runCatching { matchRepository.unmatch(matchId) }
                .onSuccess {
                    _events.send(MatchProfileEvent.Message("Match mit $name aufgelöst."))
                    _events.send(MatchProfileEvent.Closed)
                }
                .onFailure {
                    _events.send(MatchProfileEvent.Message(it.message ?: "Auflösen fehlgeschlagen."))
                }
        }
    }
}
