package flexr.social.app.ui.verification

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.VerificationRepository
import flexr.social.app.domain.model.VerificationState
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.domain.model.VerificationStep
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class VerificationGateUiState(
    val verification: VerificationState? = null,
    val isLoading: Boolean = true,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    // Kontolöschung bleibt auch für ein gesperrtes Konto erreichbar - sonst
    // waere eine abgelehnte Verifizierung eine Sackgasse.
    val deleteDialogVisible: Boolean = false,
    val deletePassword: String = "",
    val deleteError: String? = null,
    val isDeleting: Boolean = false,
) {
    val step: VerificationStep get() = verification?.nextStep ?: VerificationStep.SELFIE
    val status: VerificationStatus get() = verification?.status ?: VerificationStatus.NONE
    val isWaiting: Boolean get() = status == VerificationStatus.SUBMITTED
    val isRejected: Boolean get() = status == VerificationStatus.REJECTED

    /** Der Prüfer hat eine neue Aufnahme angefordert. */
    val needsNewUpload: Boolean get() = status == VerificationStatus.REUPLOAD_REQUIRED
}

/**
 * Übersicht der Alters- und Identitätsprüfung für ein noch nicht
 * freigeschaltetes Konto: Was steht an, was wurde bemängelt, wie geht es weiter.
 */
@HiltViewModel
class VerificationGateViewModel @Inject constructor(
    private val verificationRepository: VerificationRepository,
    private val profileRepository: ProfileRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(VerificationGateUiState())
    val uiState: StateFlow<VerificationGateUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun load() {
        _uiState.update { it.copy(isLoading = it.verification == null, error = null) }
        viewModelScope.launch {
            runCatching { verificationRepository.status() }
                .onSuccess { state ->
                    _uiState.update {
                        it.copy(verification = state, isLoading = false, error = null)
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            error = (throwable as? FlexrApiException)?.message
                                ?: "Status konnte nicht geladen werden.",
                        )
                    }
                }
        }
    }

    /**
     * "Status aktualisieren" im Wartezustand: Profil neu laden — ist die
     * Prüfung durch, wechselt die App über den beobachteten Sitzungszustand
     * von selbst in die Hauptansicht.
     */
    fun refresh(onStillWaiting: () -> Unit) {
        _uiState.update { it.copy(isRefreshing = true) }
        viewModelScope.launch {
            val profile = runCatching { profileRepository.refresh() }.getOrNull()
            runCatching { verificationRepository.status() }
                .onSuccess { state -> _uiState.update { it.copy(verification = state) } }
            _uiState.update { it.copy(isRefreshing = false) }
            if (profile == null || !profile.isAccountActivated) onStillWaiting()
        }
    }

    // ---------- Konto löschen ----------

    fun showDeleteDialog() =
        _uiState.update { it.copy(deleteDialogVisible = true, deletePassword = "", deleteError = null) }

    fun hideDeleteDialog() =
        _uiState.update { it.copy(deleteDialogVisible = false, deletePassword = "", deleteError = null) }

    fun onDeletePasswordChange(value: String) =
        _uiState.update { it.copy(deletePassword = value, deleteError = null) }

    fun confirmDelete(onDeleted: (String) -> Unit) {
        val password = _uiState.value.deletePassword
        if (password.isBlank()) {
            _uiState.update { it.copy(deleteError = "Bitte gib zur Bestätigung dein Passwort ein.") }
            return
        }
        _uiState.update { it.copy(isDeleting = true, deleteError = null) }
        viewModelScope.launch {
            runCatching { profileRepository.deleteAccount(password) }
                .onSuccess {
                    _uiState.update { it.copy(isDeleting = false, deleteDialogVisible = false) }
                    onDeleted("Dein Konto wurde deaktiviert und wird in 30 Tagen endgültig gelöscht.")
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isDeleting = false,
                            deleteError = (throwable as? FlexrApiException)?.message
                                ?: "Löschen fehlgeschlagen.",
                        )
                    }
                }
        }
    }
}
