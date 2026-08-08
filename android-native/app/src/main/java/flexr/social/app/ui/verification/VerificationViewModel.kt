package flexr.social.app.ui.verification

import android.graphics.Bitmap
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.VerificationRepository
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class VerificationUiState(
    val prompts: List<String> = emptyList(),
    val currentIndex: Int = 0,
    /** Aufgenommene Selfies als JPEG, in der Reihenfolge der Posen. */
    val captures: List<ByteArray> = emptyList(),
    val isStarting: Boolean = true,
    val isSubmitting: Boolean = false,
    val error: String? = null,
    val cameraDenied: Boolean = false,
) {
    val currentPrompt: String? get() = prompts.getOrNull(currentIndex)
    val total: Int get() = prompts.size
    val isComplete: Boolean get() = prompts.isNotEmpty() && captures.size == prompts.size
}

sealed interface VerificationEvent {
    data class Message(val text: String) : VerificationEvent
    data object Finished : VerificationEvent
}

/**
 * Foto-Verifizierung: ein Selfie in einer vom Server vorgegebenen Pose, live
 * aufgenommen.
 *
 * Bewusst kein Galerie-Upload — nur eine echte Person vor der Kamera kann die
 * verlangte Pose spontan liefern (Liveness-Prinzip).
 */
@HiltViewModel
class VerificationViewModel @Inject constructor(
    private val verificationRepository: VerificationRepository,
    private val profileRepository: ProfileRepository,
    private val imageProcessor: ImageProcessor,
) : ViewModel() {

    private val _uiState = MutableStateFlow(VerificationUiState())
    val uiState: StateFlow<VerificationUiState> = _uiState.asStateFlow()

    private val _events = Channel<VerificationEvent>(Channel.BUFFERED)
    val events: Flow<VerificationEvent> = _events.receiveAsFlow()

    init {
        start()
    }

    fun start() {
        _uiState.update { it.copy(isStarting = true, error = null) }
        viewModelScope.launch {
            runCatching { verificationRepository.start() }
                .onSuccess { state ->
                    _uiState.update {
                        it.copy(
                            prompts = state.prompts,
                            currentIndex = 0,
                            captures = emptyList(),
                            isStarting = false,
                        )
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isStarting = false,
                            error = (throwable as? FlexrApiException)?.message
                                ?: "Verifizierung konnte nicht gestartet werden.",
                        )
                    }
                }
        }
    }

    fun onCameraDenied() = _uiState.update {
        it.copy(
            cameraDenied = true,
            error = "Kamerazugriff abgelehnt. Die Verifizierung braucht Live-Aufnahmen über die Kamera.",
        )
    }

    fun onCaptured(bitmap: Bitmap) {
        viewModelScope.launch {
            val bytes = runCatching { imageProcessor.compressSelfie(bitmap) }.getOrElse {
                _uiState.update { state -> state.copy(error = "Aufnahme fehlgeschlagen, bitte erneut.") }
                return@launch
            }
            val state = _uiState.updateAndGet { current ->
                current.copy(captures = current.captures + bytes, currentIndex = current.currentIndex + 1, error = null)
            }
            if (state.isComplete) submit()
        }
    }

    private fun MutableStateFlow<VerificationUiState>.updateAndGet(
        transform: (VerificationUiState) -> VerificationUiState,
    ): VerificationUiState {
        update(transform)
        return value
    }

    private fun submit() {
        val state = _uiState.value
        _uiState.update { it.copy(isSubmitting = true, error = null) }
        viewModelScope.launch {
            runCatching {
                verificationRepository.submit(state.prompts.zip(state.captures))
            }.onSuccess {
                _uiState.update { it.copy(isSubmitting = false) }
                runCatching { profileRepository.refresh() }
                _events.send(
                    VerificationEvent.Message("Selfie eingereicht — deine Verifizierung ist in Prüfung."),
                )
                _events.send(VerificationEvent.Finished)
            }.onFailure { throwable ->
                // Aufnahmen behalten, damit nur der Upload wiederholt werden muss.
                _uiState.update {
                    it.copy(
                        isSubmitting = false,
                        error = (throwable as? FlexrApiException)?.message
                            ?: "Einreichen fehlgeschlagen. Bitte erneut versuchen.",
                    )
                }
            }
        }
    }

    fun retrySubmit() {
        if (_uiState.value.isComplete) submit()
    }
}
