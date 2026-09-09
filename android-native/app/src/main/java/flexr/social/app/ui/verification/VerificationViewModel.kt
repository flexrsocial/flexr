package flexr.social.app.ui.verification

import android.graphics.Bitmap
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.R
import flexr.social.app.core.locale.AppStrings
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.VerificationRepository
import flexr.social.app.domain.model.VerificationStep
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
    /** Aufgenommene Selfies als JPEG, in der Reihenfolge der Anweisungen. */
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
 * Foto-Verifizierung: ein Selfie, frontal in die Kamera, live aufgenommen.
 *
 * Bewusst kein Galerie-Upload — die Aufnahme muss vor der Kamera entstehen.
 */
@HiltViewModel
class VerificationViewModel @Inject constructor(
    private val verificationRepository: VerificationRepository,
    private val profileRepository: ProfileRepository,
    private val imageProcessor: ImageProcessor,
    private val strings: AppStrings,
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
                            // Der Server antwortet ohne Anweisung, wenn der
                            // Selfie-Schritt schon hinter dem Konto liegt. Dann
                            // ist dieser Bildschirm nur noch eine Sackgasse -
                            // also sagen, was stattdessen ansteht.
                            error = if (state.prompts.isEmpty()) {
                                when (state.nextStep) {
                                    VerificationStep.DOCUMENT -> strings.get(R.string.verify_selfie_exists)
                                    VerificationStep.WAIT -> strings.get(R.string.verify_already_submitted)
                                    else -> strings.get(R.string.verify_none_running)
                                }
                            } else {
                                null
                            },
                        )
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isStarting = false,
                            error = (throwable as? FlexrApiException)?.message
                                ?: strings.get(R.string.verify_start_failed),
                        )
                    }
                }
        }
    }

    fun onCameraDenied() = _uiState.update {
        it.copy(
            cameraDenied = true,
            error = strings.get(R.string.verify_camera_denied),
        )
    }

    fun onCaptured(bitmap: Bitmap) {
        // Ohne laufenden Vorgang gibt es keine Anweisung, der die Aufnahme zugeordnet
        // werden könnte - sie würde nur stumm im Speicher landen.
        if (_uiState.value.prompts.isEmpty()) return
        viewModelScope.launch {
            val bytes = runCatching { imageProcessor.compressSelfie(bitmap) }.getOrElse {
                _uiState.update { state -> state.copy(error = strings.get(R.string.verify_capture_failed)) }
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
                // Nach dem Selfie steht der Ausweis an - geprüft wird erst
                // danach. "In Prüfung" wäre hier schlicht falsch und lässt
                // Nutzer auf eine Entscheidung warten, die niemand trifft.
                _events.send(
                    VerificationEvent.Message(strings.get(R.string.verify_selfie_saved)),
                )
                _events.send(VerificationEvent.Finished)
            }.onFailure { throwable ->
                // Aufnahmen behalten, damit nur der Upload wiederholt werden muss.
                _uiState.update {
                    it.copy(
                        isSubmitting = false,
                        error = (throwable as? FlexrApiException)?.message
                            ?: strings.get(R.string.verify_submit_failed),
                    )
                }
            }
        }
    }

    fun retrySubmit() {
        if (_uiState.value.isComplete) submit()
    }
}
