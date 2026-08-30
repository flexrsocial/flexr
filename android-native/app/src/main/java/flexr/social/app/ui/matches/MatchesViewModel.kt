package flexr.social.app.ui.matches

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.domain.model.MatchSummary
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Match- und Chatlisten.
 *
 * Beide Bildschirme lesen aus demselben lokalen Bestand: „Matches" zeigt alle,
 * „Chats" nur die mit laufender Unterhaltung — genau die Trennung, die auch
 * die Web-App vornimmt.
 */
@HiltViewModel
class MatchesViewModel @Inject constructor(
    private val matchRepository: MatchRepository,
) : ViewModel() {

    val matches: StateFlow<List<MatchSummary>> = matchRepository.matches
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val conversations: StateFlow<List<MatchSummary>> = matchRepository.conversations
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    private val _isRefreshing = MutableStateFlow(true)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _isRefreshing.value = true
            runCatching { matchRepository.refresh() }
                .onSuccess { _error.value = null }
                .onFailure { throwable ->
                    _error.value = (throwable as? FlexrApiException)?.message
                        ?: "Matches konnten nicht geladen werden."
                }
            _isRefreshing.value = false
        }
    }

    /**
     * Stiller Hintergrund-Abgleich für die Auto-Aktualisierung, während der
     * Bildschirm sichtbar ist — anders als refresh() weder Ladeanzeige noch
     * Fehlermeldung, die würden bei jedem 20s-Tick unnötig aufblitzen. Schreibt
     * nur in Room; die sichtbare Liste (matches/conversations) zieht über den
     * Room-Flow automatisch nach, kein separater Zeichenschritt nötig.
     */
    fun silentRefresh() {
        viewModelScope.launch {
            runCatching { matchRepository.refresh() }
        }
    }
}
