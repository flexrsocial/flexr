package flexr.social.app.ui.chat

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.repository.MessageRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.SafetyRepository
import flexr.social.app.domain.model.MatchSummary
import flexr.social.app.domain.model.Message
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.time.Instant
import javax.inject.Inject

data class ChatUiState(
    val draft: String = "",
    val isSending: Boolean = false,
    val isLoading: Boolean = true,
    val mutedUntil: Instant? = null,
    /** Begründung und Widerspruchshinweis zur Sperre (Art. 17 DSA). */
    val muteReason: String? = null,
    val appealHint: String? = null,
) {
    val canSend: Boolean get() = draft.isNotBlank() && !isSending && mutedUntil == null
}

sealed interface ChatEvent {
    data class Message(val text: String) : ChatEvent
    data object Closed : ChatEvent
}

/**
 * Ein Chatverlauf.
 *
 * Die Nachrichten kommen aus dem lokalen Bestand und werden im Vordergrund
 * regelmäßig aufgefrischt (das Backend bietet kein Push). Beim Abrufen markiert
 * der Server die Nachrichten der Gegenseite zugleich als gelesen.
 */
@HiltViewModel
class ChatViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val messageRepository: MessageRepository,
    private val matchRepository: MatchRepository,
    private val safetyRepository: SafetyRepository,
    private val profileRepository: ProfileRepository,
) : ViewModel() {

    val matchId: String = checkNotNull(savedStateHandle["matchId"])

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    private val _events = Channel<ChatEvent>(Channel.BUFFERED)
    val events: Flow<ChatEvent> = _events.receiveAsFlow()

    val messages: StateFlow<List<Message>> = messageRepository.messages(matchId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val match: StateFlow<MatchSummary?> = matchRepository.match(matchId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    val ownUserId: StateFlow<String?> = profileRepository.myProfile
        .map { it?.id }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5_000),
            profileRepository.myProfile.value?.id,
        )

    private var pollJob: Job? = null

    init {
        refreshMuteState()
        startPolling()
        viewModelScope.launch { matchRepository.markRead(matchId) }
    }

    private fun startPolling() {
        pollJob?.cancel()
        pollJob = viewModelScope.launch {
            while (isActive) {
                runCatching { messageRepository.refresh(matchId) }
                    .onSuccess {
                        _uiState.update { it.copy(isLoading = false) }
                        matchRepository.markRead(matchId)
                    }
                    .onFailure { _uiState.update { it.copy(isLoading = false) } }
                delay(POLL_INTERVAL_MS)
            }
        }
    }

    override fun onCleared() {
        pollJob?.cancel()
        super.onCleared()
    }

    /**
     * Chat-Sperre kann während der Sitzung verhängt worden sein — beim Öffnen
     * des Chats den Profilstand nachziehen.
     */
    private fun refreshMuteState() {
        viewModelScope.launch {
            val profile = runCatching { profileRepository.refresh() }.getOrNull()
                ?: profileRepository.myProfile.value
            val until = profile?.activeMuteUntil()
            _uiState.update { it.copy(mutedUntil = until) }
            // Art. 17 DSA: Zur Sperre gehört die Begründung samt Widerspruchsweg.
            if (until != null) {
                val notice = runCatching { safetyRepository.moderationNotice() }.getOrNull()
                _uiState.update {
                    it.copy(muteReason = notice?.reason, appealHint = notice?.appealHint)
                }
            } else {
                _uiState.update { it.copy(muteReason = null, appealHint = null) }
            }
        }
    }

    fun onDraftChange(value: String) = _uiState.update { it.copy(draft = value.take(MAX_LENGTH)) }

    fun send() {
        val state = _uiState.value
        val content = state.draft.trim()
        if (content.isEmpty() || state.isSending) return
        if (state.mutedUntil != null) return

        val senderId = profileRepository.myProfile.value?.id ?: return
        _uiState.update { it.copy(draft = "", isSending = true) }

        viewModelScope.launch {
            runCatching { messageRepository.send(matchId, senderId, content) }
                .onSuccess {
                    _uiState.update { it.copy(isSending = false) }
                    runCatching { matchRepository.refresh() }
                }
                .onFailure { throwable ->
                    val apiError = throwable as? FlexrApiException
                    // Getippten Text nicht verlieren.
                    _uiState.update {
                        it.copy(
                            isSending = false,
                            draft = content,
                            mutedUntil = apiError?.mutedUntil ?: it.mutedUntil,
                            muteReason = apiError?.moderationReason ?: it.muteReason,
                            appealHint = apiError?.appealHint ?: it.appealHint,
                        )
                    }
                    if (apiError?.mutedUntil == null) {
                        if (apiError?.statusCode == 403) refreshMuteState()
                        _events.send(
                            ChatEvent.Message(
                                apiError?.message ?: "Nachricht konnte nicht gesendet werden.",
                            ),
                        )
                    }
                }
        }
    }

    /** Verlauf leeren — nur für die eigene Seite. */
    fun clearHistory() {
        viewModelScope.launch {
            runCatching { messageRepository.clearHistory(matchId) }
                .onSuccess {
                    _events.send(ChatEvent.Message("Chatverlauf geleert."))
                    runCatching { matchRepository.refresh() }
                }
                .onFailure { _events.send(ChatEvent.Message(it.message ?: "Leeren fehlgeschlagen.")) }
        }
    }

    /** Chat löschen = Match auflösen (Verlauf und Match verschwinden). */
    fun deleteChat() {
        viewModelScope.launch {
            runCatching { matchRepository.unmatch(matchId) }
                .onSuccess {
                    _events.send(ChatEvent.Message("Chat gelöscht."))
                    _events.send(ChatEvent.Closed)
                }
                .onFailure { _events.send(ChatEvent.Message(it.message ?: "Löschen fehlgeschlagen.")) }
        }
    }

    fun report(reason: String) {
        val userId = match.value?.profile?.id ?: return
        viewModelScope.launch {
            runCatching { safetyRepository.report(userId, reason) }
                // Art. 16 Abs. 4 DSA: Der Melder bekommt die Bestätigung mit
                // Aktenzeichen zu sehen, nicht nur ein "danke".
                .onSuccess { _events.send(ChatEvent.Message(it.message)) }
                .onFailure { _events.send(ChatEvent.Message(it.message ?: "Meldung fehlgeschlagen.")) }
        }
    }

    fun block() {
        val profile = match.value?.profile ?: return
        viewModelScope.launch {
            runCatching { safetyRepository.block(profile.id) }
                .onSuccess {
                    matchRepository.removeLocally(matchId)
                    _events.send(ChatEvent.Message("${profile.name} blockiert."))
                    _events.send(ChatEvent.Closed)
                }
                .onFailure { _events.send(ChatEvent.Message(it.message ?: "Blockieren fehlgeschlagen.")) }
        }
    }

    private companion object {
        const val POLL_INTERVAL_MS = 4_000L
        const val MAX_LENGTH = 2_000
    }
}
