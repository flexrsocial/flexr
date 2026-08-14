package flexr.social.app.ui.verification

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import android.net.Uri
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.media.PhotoPreparer
import flexr.social.app.core.media.PreparedPhoto
import flexr.social.app.core.media.PhotoTooSmallException
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.VerificationRepository
import flexr.social.app.domain.model.VerificationState
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.domain.model.VerificationStep
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class VerificationGateUiState(
    val verification: VerificationState? = null,
    val isLoading: Boolean = true,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    /**
     * Ohne Profilfoto lehnt der Server den Start der Prüfung ab. Das passiert,
     * wenn der Upload während der Registrierung scheitert - und ohne einen Weg,
     * das Foto hier nachzureichen, bliebe das Konto dauerhaft stecken: Der
     * Konto-Bildschirm liegt im Hauptgraphen und ist von hier nicht erreichbar.
     */
    val hasProfilePhoto: Boolean = true,
    val isUploadingPhoto: Boolean = false,
    val photoError: String? = null,
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

    /**
     * Die Prüfung ist durch und das Konto freigeschaltet. Der Bildschirm darf
     * dann nicht stehen bleiben - er ist der einzige des Verifizierungsgraphen,
     * und der Graph selbst wechselt erst, wenn die Sitzung neu geladen wird.
     */
    val isActivated: Boolean get() = verification?.accountActivated == true

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
    private val photoPreparer: PhotoPreparer,
) : ViewModel() {

    private val _uiState = MutableStateFlow(VerificationGateUiState())
    val uiState: StateFlow<VerificationGateUiState> = _uiState.asStateFlow()

    init {
        // MainViewModel hat das Profil schon geladen, bevor es auf diesen
        // Graphen umgeschaltet hat - der Fotostand liegt also bereits vor.
        profileRepository.myProfile
            .onEach { profile ->
                _uiState.update { it.copy(hasProfilePhoto = profile?.photos?.isNotEmpty() ?: true) }
            }
            .launchIn(viewModelScope)
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
     * "Status aktualisieren" im Wartezustand.
     *
     * Bisher wurde hier das Profil neu geladen und darauf gebaut, dass die App
     * daraufhin von selbst weiterschaltet. Das tat sie nie: MainViewModel
     * beobachtet nur `isLoggedIn`, nicht das Profil. Wer während der Wartezeit
     * freigeschaltet wurde, drückte den Knopf, bekam nicht einmal die Meldung
     * "läuft noch" — und blieb auf dem Wartebildschirm sitzen.
     *
     * Die Freischaltung steht bereits in der Statusantwort selbst
     * (`account_activated`); sie landet im UI-Zustand, und der Bildschirm
     * stößt daraufhin das Neuladen der Sitzung an.
     */
    fun refresh(onStillWaiting: () -> Unit) {
        _uiState.update { it.copy(isRefreshing = true, error = null) }
        viewModelScope.launch {
            runCatching { verificationRepository.status() }
                .onSuccess { state ->
                    _uiState.update { it.copy(verification = state, isRefreshing = false) }
                    if (!state.accountActivated) onStillWaiting()
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isRefreshing = false,
                            error = (throwable as? FlexrApiException)?.message
                                ?: "Status konnte nicht geladen werden.",
                        )
                    }
                }
        }
    }

    /**
     * Profilfoto nachreichen, wenn der Upload bei der Registrierung scheiterte.
     *
     * Der Server verlangt für /verification/start mindestens ein Foto. Ohne
     * diesen Weg blieb nur Ausloggen (was zurück auf denselben Schirm führt)
     * oder Kontolöschung - der Konto-Bildschirm samt Fotoverwaltung gehört zum
     * Hauptgraphen, den ein nicht freigeschaltetes Konto nie erreicht.
     */
    fun onPhotoPicked(uri: Uri) {
        _uiState.update { it.copy(isUploadingPhoto = true, photoError = null) }
        viewModelScope.launch { storePhoto { photoPreparer.prepare(uri) } }
    }

    /**
     * Der Teil ohne `android.net.Uri` — und damit der Teil, der sich in einem
     * reinen JVM-Test prüfen lässt: Dort liefert `Uri.EMPTY` null, ein Aufruf
     * von [onPhotoPicked] scheitert also schon an der Parameterprüfung.
     */
    internal suspend fun storePhoto(prepare: suspend () -> PreparedPhoto) {
        runCatching { profileRepository.addPhoto(prepare()) }
            .onSuccess {
                // hasProfilePhoto zieht über den beobachteten Profilfluss nach.
                _uiState.update { it.copy(isUploadingPhoto = false) }
                load()
            }
            .onFailure { throwable ->
                _uiState.update {
                    it.copy(
                        isUploadingPhoto = false,
                        photoError = when (throwable) {
                            is PhotoTooSmallException -> throwable.message
                            is FlexrApiException -> throwable.message
                            else -> "Foto konnte nicht hochgeladen werden."
                        },
                    )
                }
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
