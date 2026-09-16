package flexr.social.app.ui.incoming

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.R
import flexr.social.app.core.locale.AppStrings
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.SwipeRepository
import flexr.social.app.domain.model.IncomingLikes
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class IncomingUiState(
    val isLoading: Boolean = true,
    val likes: IncomingLikes? = null,
    val error: String? = null,
)

/**
 * „Wer dich geliket hat" — eine Premium-Funktion.
 *
 * Ohne Premium liefert der Server keine Fehlermeldung, sondern die Anzahl ohne
 * Profile ([IncomingLikes.premiumRequired]). Diese Unterscheidung bleibt bis in
 * die Oberfläche erhalten: „3 Leute warten auf dich" ist die ehrliche Antwort
 * und zugleich der beste Grund, sich Premium anzusehen — eine Fehlermeldung
 * wäre beides nicht.
 *
 * Eigenes ViewModel statt eines geteilten mit der Matchliste: Der Bildschirm
 * wird selten geöffnet und soll beim Öffnen frisch laden, während die Karte
 * über der Matchliste nur die Zahl braucht.
 */
@HiltViewModel
class IncomingViewModel @Inject constructor(
    private val swipeRepository: SwipeRepository,
    private val strings: AppStrings,
) : ViewModel() {

    private val _uiState = MutableStateFlow(IncomingUiState())
    val uiState: StateFlow<IncomingUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            runCatching { swipeRepository.incomingLikes() }
                .onSuccess { likes ->
                    _uiState.value = IncomingUiState(isLoading = false, likes = likes)
                }
                .onFailure { throwable ->
                    _uiState.value = IncomingUiState(
                        isLoading = false,
                        error = (throwable as? FlexrApiException)?.message
                            ?: strings.get(R.string.incoming_load_failed),
                    )
                }
        }
    }
}
