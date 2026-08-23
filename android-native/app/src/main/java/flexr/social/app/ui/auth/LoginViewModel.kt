package flexr.social.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LoginUiState(
    val email: String = "",
    val password: String = "",
    val isSubmitting: Boolean = false,
    val error: String? = null,
    val success: Boolean = false,
    /** Konto innerhalb der 30-Tage-Karenz nach Selbstlöschung - Login bietet
     *  die Reaktivierung an, statt in eine Sackgasse zu führen. */
    val reactivateMessage: String? = null,
    val isReactivating: Boolean = false,
    val reactivateError: String? = null,
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    fun onEmailChange(value: String) = _uiState.update { it.copy(email = value, error = null) }

    fun onPasswordChange(value: String) = _uiState.update { it.copy(password = value, error = null) }

    fun login() {
        val state = _uiState.value
        if (state.isSubmitting) return
        if (state.email.isBlank() || state.password.isBlank()) {
            _uiState.update { it.copy(error = "Bitte E-Mail und Passwort angeben.") }
            return
        }

        _uiState.update { it.copy(isSubmitting = true, error = null) }
        viewModelScope.launch {
            runCatching { authRepository.login(state.email, state.password) }
                .onSuccess { _uiState.update { it.copy(isSubmitting = false, success = true) } }
                .onFailure { throwable ->
                    val apiError = throwable as? FlexrApiException
                    if (apiError?.isAccountDeleted == true) {
                        _uiState.update {
                            it.copy(isSubmitting = false, reactivateMessage = apiError.message)
                        }
                    } else {
                        _uiState.update {
                            it.copy(isSubmitting = false, error = apiError?.message ?: "Login fehlgeschlagen.")
                        }
                    }
                }
        }
    }

    fun dismissReactivateDialog() = _uiState.update { it.copy(reactivateMessage = null, reactivateError = null) }

    fun reactivate() {
        val state = _uiState.value
        if (state.isReactivating) return

        _uiState.update { it.copy(isReactivating = true, reactivateError = null) }
        viewModelScope.launch {
            runCatching { authRepository.reactivate(state.email, state.password) }
                .onSuccess {
                    _uiState.update {
                        it.copy(isReactivating = false, reactivateMessage = null, success = true)
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isReactivating = false,
                            reactivateError = (throwable as? FlexrApiException)?.message
                                ?: "Reaktivierung fehlgeschlagen.",
                        )
                    }
                }
        }
    }
}
