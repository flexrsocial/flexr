package flexr.social.app.ui.verification

import android.graphics.Bitmap
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.VerificationRepository
import flexr.social.app.domain.model.VerificationDocumentType
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/** Vorder- oder Rückseite des Dokuments. */
enum class DocumentSide(val label: String) {
    FRONT("Vorderseite"),
    BACK("Rückseite"),
}

data class DocumentUiState(
    val documentTypes: List<VerificationDocumentType> = emptyList(),
    val selectedType: VerificationDocumentType? = null,
    /** Aufnahmen als JPEG, je Seite. */
    val captures: Map<DocumentSide, ByteArray> = emptyMap(),
    /** Welche Seite gerade aufgenommen wird — null heißt: Übersicht. */
    val capturing: DocumentSide? = null,
    val isLoading: Boolean = true,
    val isSubmitting: Boolean = false,
    val error: String? = null,
    val cameraDenied: Boolean = false,
) {
    /** Für den gewählten Typ benötigte Aufnahmen. */
    val requiredSides: List<DocumentSide>
        get() = if (selectedType?.needsBack == true) {
            listOf(DocumentSide.FRONT, DocumentSide.BACK)
        } else {
            listOf(DocumentSide.FRONT)
        }

    val isComplete: Boolean
        get() = selectedType != null && requiredSides.all { captures[it] != null }
}

sealed interface DocumentEvent {
    data class Message(val text: String) : DocumentEvent

    /** Eingereicht — der Vorgang wartet jetzt auf die Prüfung. */
    data object Submitted : DocumentEvent

    /** Der Schritt passt nicht mehr zum Serverzustand (z. B. Selfies verworfen). */
    data object StepNoLongerOpen : DocumentEvent
}

/**
 * Schritt 2 der Alters- und Identitätsprüfung: amtlicher Lichtbildausweis.
 *
 * Die Aufnahmen entstehen über die Rückkamera und werden per Presigned PUT
 * direkt in einen privaten Bereich des Objekt-Storage geladen. Sie bekommen
 * nie eine öffentliche Adresse und werden nach der Prüfung gelöscht.
 */
@HiltViewModel
class DocumentViewModel @Inject constructor(
    private val verificationRepository: VerificationRepository,
    private val profileRepository: ProfileRepository,
    private val imageProcessor: ImageProcessor,
) : ViewModel() {

    private val _uiState = MutableStateFlow(DocumentUiState())
    val uiState: StateFlow<DocumentUiState> = _uiState.asStateFlow()

    private val _events = Channel<DocumentEvent>(Channel.BUFFERED)
    val events: Flow<DocumentEvent> = _events.receiveAsFlow()

    init {
        load()
    }

    private fun load() {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            runCatching { verificationRepository.status() }
                .onSuccess { state ->
                    // Der Server bestimmt, welche Dokumente zulässig sind und ob
                    // dieser Schritt überhaupt ansteht.
                    if (state.nextStep != flexr.social.app.domain.model.VerificationStep.DOCUMENT) {
                        _events.send(DocumentEvent.StepNoLongerOpen)
                        return@onSuccess
                    }
                    _uiState.update {
                        it.copy(
                            documentTypes = state.documentTypes,
                            selectedType = state.documentTypes.firstOrNull(),
                            isLoading = false,
                        )
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

    fun onTypeSelected(type: VerificationDocumentType) = _uiState.update { state ->
        // Wird auf einen Typ ohne Rückseite gewechselt, ist eine bereits
        // gemachte Rückseiten-Aufnahme gegenstandslos.
        val captures = if (type.needsBack) state.captures else state.captures - DocumentSide.BACK
        state.copy(selectedType = type, captures = captures, error = null)
    }

    fun onCaptureRequested(side: DocumentSide) =
        _uiState.update { it.copy(capturing = side, error = null) }

    fun onCaptureCancelled() = _uiState.update { it.copy(capturing = null) }

    fun onCameraDenied() = _uiState.update {
        it.copy(
            capturing = null,
            cameraDenied = true,
            error = "Kamerazugriff abgelehnt. Für die Aufnahme des Ausweises wird die Kamera gebraucht.",
        )
    }

    fun onCaptured(bitmap: Bitmap) {
        val side = _uiState.value.capturing ?: DocumentSide.FRONT
        viewModelScope.launch {
            val bytes = runCatching { imageProcessor.compressDocument(bitmap) }.getOrElse {
                _uiState.update {
                    it.copy(capturing = null, error = "Aufnahme fehlgeschlagen, bitte erneut.")
                }
                return@launch
            }
            _uiState.update {
                it.copy(captures = it.captures + (side to bytes), capturing = null, error = null)
            }
        }
    }

    fun onRetake(side: DocumentSide) =
        _uiState.update { it.copy(captures = it.captures - side, capturing = side) }

    fun submit() {
        val state = _uiState.value
        val type = state.selectedType ?: return
        val front = state.captures[DocumentSide.FRONT] ?: return
        if (!state.isComplete) return

        _uiState.update { it.copy(isSubmitting = true, error = null) }
        viewModelScope.launch {
            runCatching {
                verificationRepository.submitDocument(
                    documentType = type.value,
                    front = front,
                    back = state.captures[DocumentSide.BACK],
                )
            }.onSuccess {
                // Aufnahmen sofort aus dem Speicher nehmen - sie liegen jetzt
                // beim Server und werden dort nach der Prüfung gelöscht.
                _uiState.update {
                    it.copy(isSubmitting = false, captures = emptyMap())
                }
                runCatching { profileRepository.refresh() }
                _events.send(DocumentEvent.Message("Verifizierung eingereicht — wir prüfen deine Angaben."))
                _events.send(DocumentEvent.Submitted)
            }.onFailure { throwable ->
                // Aufnahmen behalten, damit nur der Upload zu wiederholen ist.
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
}
