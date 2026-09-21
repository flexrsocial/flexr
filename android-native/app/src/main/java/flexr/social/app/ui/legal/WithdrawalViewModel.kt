package flexr.social.app.ui.legal

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.R
import flexr.social.app.core.locale.AppStrings
import flexr.social.app.core.locale.LanguageStore
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.WithdrawalRepository
import flexr.social.app.domain.model.WithdrawalAck
import java.util.UUID
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class WithdrawalUiState(
    val name: String = "",
    val email: String = "",
    val contractReference: String = "",
    val message: String = "",
    val confirmed: Boolean = false,
    val isSubmitting: Boolean = false,
    val error: String? = null,
    val result: WithdrawalAck? = null,
) {
    val canSubmit: Boolean
        get() = name.isNotBlank() && email.isNotBlank() && confirmed && !isSubmitting
}

/**
 * Steuert die eingebettete Online-Rücktrittsfunktion (§ 13a FAGG) - die native
 * Entsprechung des Formulars auf flexr.social/widerruf.html. Ist die Person
 * angemeldet, ordnet der Server die Erklärung serverseitig automatisch ihrem
 * Konto zu (siehe routers/withdrawal.py); die App muss dafür nichts extra tun.
 */
@HiltViewModel
class WithdrawalViewModel @Inject constructor(
    private val withdrawalRepository: WithdrawalRepository,
    profileRepository: ProfileRepository,
    private val languageStore: LanguageStore,
    private val strings: AppStrings,
) : ViewModel() {

    private val _uiState = MutableStateFlow(
        profileRepository.myProfile.value?.let { profile ->
            WithdrawalUiState(name = profile.name, email = profile.email)
        } ?: WithdrawalUiState(),
    )
    val uiState: StateFlow<WithdrawalUiState> = _uiState.asStateFlow()

    // Eine UUID pro Bildschirmaufruf, nicht pro Klick - siehe
    // frontend/widerruf.html: ein Doppelklick oder ein Netzwerk-Retry auf
    // denselben Submit schickt dieselbe ID erneut, der Server legt dafür keine
    // zweite Erklärung an.
    private val requestId = UUID.randomUUID().toString()

    fun onNameChange(value: String) = _uiState.update { it.copy(name = value, error = null) }
    fun onEmailChange(value: String) = _uiState.update { it.copy(email = value, error = null) }
    fun onContractReferenceChange(value: String) = _uiState.update { it.copy(contractReference = value) }
    fun onMessageChange(value: String) = _uiState.update { it.copy(message = value) }
    fun onConfirmedChange(value: Boolean) = _uiState.update { it.copy(confirmed = value, error = null) }

    fun submit() {
        val state = _uiState.value
        if (!state.canSubmit) return
        _uiState.update { it.copy(isSubmitting = true, error = null) }
        viewModelScope.launch {
            runCatching {
                withdrawalRepository.declare(
                    name = state.name,
                    email = state.email,
                    contractReference = state.contractReference,
                    message = state.message,
                    requestId = requestId,
                    language = languageStore.current.code,
                )
            }.onSuccess { ack ->
                _uiState.update { it.copy(isSubmitting = false, result = ack) }
            }.onFailure { throwable ->
                _uiState.update {
                    it.copy(
                        isSubmitting = false,
                        error = (throwable as? FlexrApiException)?.message
                            ?: strings.get(R.string.withdrawal_error_generic),
                    )
                }
            }
        }
    }
}
