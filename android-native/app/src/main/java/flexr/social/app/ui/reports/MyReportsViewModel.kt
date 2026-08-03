package flexr.social.app.ui.reports

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.data.repository.SafetyRepository
import flexr.social.app.domain.model.MyReport
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class MyReportsUiState(
    val isLoading: Boolean = true,
    val reports: List<MyReport> = emptyList(),
    val error: String? = null,
)

@HiltViewModel
class MyReportsViewModel @Inject constructor(
    private val safetyRepository: SafetyRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(MyReportsUiState())
    val uiState: StateFlow<MyReportsUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            runCatching { safetyRepository.myReports() }
                .onSuccess { reports ->
                    _uiState.update { it.copy(isLoading = false, reports = reports) }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            error = throwable.message ?: "Bitte später erneut versuchen.",
                        )
                    }
                }
        }
    }
}
