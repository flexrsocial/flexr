package flexr.social.app.ui.matches

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.R
import flexr.social.app.core.locale.AppStrings
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.repository.SwipeRepository
import flexr.social.app.domain.model.IncomingLikes
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
    private val swipeRepository: SwipeRepository,
    private val strings: AppStrings,
) : ViewModel() {

    val matches: StateFlow<List<MatchSummary>> = matchRepository.matches
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val conversations: StateFlow<List<MatchSummary>> = matchRepository.conversations
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    private val _isRefreshing = MutableStateFlow(true)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    /**
     * Offene Likes fuer die Karte ueber der Matchliste.
     *
     * `null` heisst "noch nicht geladen oder Abruf gescheitert" - in beiden
     * Faellen bleibt die Karte weg. Bewusst kein eigener Fehlerzustand: Das
     * ist Beiwerk ueber der Matchliste, ein Fehlerbalken dafuer wuerde einen
     * funktionierenden Bildschirm wie einen kaputten aussehen lassen.
     */
    private val _incoming = MutableStateFlow<IncomingLikes?>(null)
    val incoming: StateFlow<IncomingLikes?> = _incoming.asStateFlow()

    init {
        refresh()
    }

    fun loadIncoming() {
        viewModelScope.launch {
            _incoming.value = runCatching { swipeRepository.incomingLikes() }.getOrNull()
        }
    }

    /** Zeitpunkt des letzten Abrufs (System.nanoTime), fuer [refreshOnEnter]. */
    private var lastRefreshAt = 0L

    fun refresh() {
        lastRefreshAt = System.nanoTime()
        viewModelScope.launch {
            _isRefreshing.value = true
            runCatching { matchRepository.refresh() }
                .onSuccess { _error.value = null }
                .onFailure { throwable ->
                    _error.value = (throwable as? FlexrApiException)?.message
                        ?: strings.get(R.string.matches_load_failed)
                }
            _isRefreshing.value = false
        }
        loadIncoming()
    }

    /**
     * Stiller Hintergrund-Abgleich für die Auto-Aktualisierung, während der
     * Bildschirm sichtbar ist — anders als refresh() weder Ladeanzeige noch
     * Fehlermeldung, die würden bei jedem 20s-Tick unnötig aufblitzen. Schreibt
     * nur in Room; die sichtbare Liste (matches/conversations) zieht über den
     * Room-Flow automatisch nach, kein separater Zeichenschritt nötig.
     */
    /**
     * Beim (Wieder-)Betreten von Matches oder Chats. Die Tabs behalten ihr
     * ViewModel (saveState/restoreState), `init` laeuft also nur beim ersten
     * Mal - danach stand die Liste bis zum naechsten 20-s-Abgleich auf dem
     * alten Stand (Online-Punkt, neue Nachricht, gerade aufgeloestes Match).
     * Direkt nach einem Abruf (erster Aufbau) nicht noch einmal.
     */
    fun refreshOnEnter() {
        if (System.nanoTime() - lastRefreshAt > ENTER_REFRESH_MIN_GAP_NS) silentRefresh()
    }

    fun silentRefresh() {
        lastRefreshAt = System.nanoTime()
        viewModelScope.launch {
            runCatching { matchRepository.refresh() }
        }
        loadIncoming()
    }
}

private const val ENTER_REFRESH_MIN_GAP_NS = 3_000_000_000L
