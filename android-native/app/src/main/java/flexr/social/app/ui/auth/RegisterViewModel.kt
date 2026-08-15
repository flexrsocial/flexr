package flexr.social.app.ui.auth

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.core.media.PhotoTooSmallException
import flexr.social.app.core.media.PreparedPhoto
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.AuthRepository
import flexr.social.app.data.repository.GymRepository
import flexr.social.app.data.repository.PlzRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.UnknownPostalCodeException
import flexr.social.app.domain.model.Gender
import flexr.social.app.domain.model.Gym
import flexr.social.app.ui.components.GymPickerState
import flexr.social.app.ui.components.GymSuggestionState
import flexr.social.app.ui.components.PlzLookupState
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.LocalDate
import javax.inject.Inject

/** Ein im Onboarding gewähltes Foto: Vorschau plus fertig aufbereitete Daten. */
data class PendingPhoto(
    val id: String,
    val previewUri: Uri,
    val prepared: PreparedPhoto,
)

data class RegisterUiState(
    val email: String = "",
    val password: String = "",
    val passwordConfirm: String = "",
    val name: String = "",
    val birthdate: LocalDate? = null,
    val postalCode: String = "",
    val plzLookup: PlzLookupState = PlzLookupState.Idle,
    val gender: Gender? = null,
    val gymPicker: GymPickerState = GymPickerState(),
    val gymSuggestion: GymSuggestionState? = null,
    val bio: String = "",
    val photos: List<PendingPhoto> = emptyList(),
    val photoError: String? = null,
    val isPreparingPhoto: Boolean = false,
    val consentSensitiveData: Boolean = false,
    val isSubmitting: Boolean = false,
    val error: String? = null,
    val success: Boolean = false,
    val successNotice: String? = null,
) {
    val resolvedCity: String? get() = (plzLookup as? PlzLookupState.Resolved)?.city

    val age: Int? get() = birthdate?.let { ServerTime.ageFrom(it) }

    /** Zweite Eingabe deckt Tippfehler auf - vergeben wird nur, was zweimal gleich kam. */
    val passwordsMatch: Boolean get() = password == passwordConfirm

    /** Fehlerhinweis am Wiederholungsfeld, aber erst wenn dort etwas steht. */
    val passwordConfirmError: String?
        get() = if (passwordConfirm.isNotEmpty() && !passwordsMatch) {
            "Die Passwörter stimmen nicht überein."
        } else {
            null
        }

    val canSubmit: Boolean
        get() = !isSubmitting &&
            email.isNotBlank() &&
            password.length >= MIN_PASSWORD_LENGTH &&
            passwordsMatch &&
            name.isNotBlank() &&
            birthdate != null &&
            resolvedCity != null &&
            gender != null &&
            gymPicker.selectedLabel != null &&
            photos.isNotEmpty() &&
            consentSensitiveData

    companion object {
        const val MIN_PASSWORD_LENGTH = 8
        const val MIN_AGE = 18
        const val MAX_AGE = 99
        const val BIO_MAX_LENGTH = 280
    }
}

/**
 * Registrierung inklusive Profilanlage.
 *
 * Ablauf wie im Web: erst das Konto anlegen (dabei entsteht der Token), dann
 * die im Onboarding gewählten Fotos hochladen — vorher gibt es keine
 * Nutzer-ID, unter der sie abgelegt werden könnten.
 */
@HiltViewModel
class RegisterViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val profileRepository: ProfileRepository,
    private val gymRepository: GymRepository,
    private val plzRepository: PlzRepository,
    private val imageProcessor: ImageProcessor,
) : ViewModel() {

    private val _uiState = MutableStateFlow(RegisterUiState())
    val uiState: StateFlow<RegisterUiState> = _uiState.asStateFlow()

    private var plzLookupJob: Job? = null
    private var gymSearchJob: Job? = null

    // ---------- Eingaben ----------

    fun onEmailChange(value: String) = _uiState.update { it.copy(email = value, error = null) }
    fun onPasswordChange(value: String) = _uiState.update { it.copy(password = value, error = null) }
    fun onPasswordConfirmChange(value: String) =
        _uiState.update { it.copy(passwordConfirm = value, error = null) }
    fun onNameChange(value: String) = _uiState.update { it.copy(name = value, error = null) }
    fun onGenderChange(value: Gender) = _uiState.update { it.copy(gender = value, error = null) }
    fun onBioChange(value: String) =
        _uiState.update { it.copy(bio = value.take(RegisterUiState.BIO_MAX_LENGTH), error = null) }

    fun onBirthdateChange(value: LocalDate) = _uiState.update { it.copy(birthdate = value, error = null) }

    fun onConsentSensitiveDataChange(value: Boolean) =
        _uiState.update { it.copy(consentSensitiveData = value, error = null) }

    // ---------- PLZ ----------

    fun onPostalCodeChange(value: String) {
        _uiState.update { it.copy(postalCode = value, plzLookup = PlzLookupState.Idle, error = null) }
        plzLookupJob?.cancel()
        if (!PlzRepository.POSTAL_CODE_PATTERN.matches(value)) return

        plzLookupJob = viewModelScope.launch {
            delay(LOOKUP_DEBOUNCE_MS)
            _uiState.update { it.copy(plzLookup = PlzLookupState.Loading) }
            val result = runCatching { plzRepository.municipalityFor(value) }
            _uiState.update {
                it.copy(
                    plzLookup = result.fold(
                        onSuccess = { city -> PlzLookupState.Resolved(city) },
                        onFailure = { throwable ->
                            PlzLookupState.Failed(
                                if (throwable is UnknownPostalCodeException) throwable.message.orEmpty()
                                else "Ort konnte nicht ermittelt werden. Bitte später erneut versuchen.",
                            )
                        },
                    ),
                )
            }
        }
    }

    // ---------- Gym ----------

    fun onGymQueryChange(value: String) {
        _uiState.update { state ->
            val keepSelection = state.gymPicker.selectedLabel
                ?.substringBefore(" — ")
                ?.equals(value, ignoreCase = false) == true
            state.copy(
                gymPicker = state.gymPicker.copy(
                    query = value,
                    expanded = true,
                    selectedLabel = if (keepSelection) state.gymPicker.selectedLabel else null,
                ),
                error = null,
            )
        }
        searchGyms(value)
    }

    fun onGymSelected(gym: Gym) {
        _uiState.update {
            it.copy(
                gymPicker = it.gymPicker.copy(
                    query = gym.name,
                    selectedLabel = gym.label,
                    expanded = false,
                ),
            )
        }
    }

    private fun searchGyms(query: String) {
        gymSearchJob?.cancel()
        gymSearchJob = viewModelScope.launch {
            delay(LOOKUP_DEBOUNCE_MS)
            _uiState.update { it.copy(gymPicker = it.gymPicker.copy(isSearching = true)) }
            val results = runCatching { gymRepository.search(query) }.getOrDefault(emptyList())
            _uiState.update {
                it.copy(gymPicker = it.gymPicker.copy(results = results, isSearching = false))
            }
        }
    }

    fun openGymSuggestion() {
        _uiState.update {
            it.copy(
                gymSuggestion = GymSuggestionState(name = it.gymPicker.query.trim()),
                gymPicker = it.gymPicker.copy(expanded = false),
            )
        }
    }

    fun closeGymSuggestion() = _uiState.update { it.copy(gymSuggestion = null) }

    fun onGymSuggestionChange(transform: (GymSuggestionState) -> GymSuggestionState) =
        _uiState.update { it.copy(gymSuggestion = it.gymSuggestion?.let(transform)) }

    fun submitGymSuggestion() {
        val suggestion = _uiState.value.gymSuggestion ?: return
        if (!suggestion.isValid || suggestion.isSubmitting) return

        _uiState.update { it.copy(gymSuggestion = suggestion.copy(isSubmitting = true, error = null)) }
        viewModelScope.launch {
            runCatching {
                gymRepository.suggest(
                    name = suggestion.name,
                    street = suggestion.street,
                    houseNumber = suggestion.houseNumber,
                    plz = suggestion.postalCode,
                )
            }.onSuccess { gym ->
                _uiState.update {
                    it.copy(
                        gymSuggestion = null,
                        gymPicker = it.gymPicker.copy(
                            query = gym.name,
                            selectedLabel = gym.label,
                            expanded = false,
                        ),
                        successNotice = "Danke! Vorschlag eingereicht — du kannst das Gym sofort verwenden.",
                    )
                }
            }.onFailure { throwable ->
                _uiState.update {
                    it.copy(
                        gymSuggestion = suggestion.copy(
                            isSubmitting = false,
                            error = throwable.message ?: "Vorschlag konnte nicht eingereicht werden.",
                        ),
                    )
                }
            }
        }
    }

    // ---------- Fotos ----------

    fun onPhotoPicked(uri: Uri) {
        if (_uiState.value.photos.size >= ImageProcessor.MAX_PHOTOS) {
            _uiState.update { it.copy(photoError = "Maximal ${ImageProcessor.MAX_PHOTOS} Fotos.") }
            return
        }
        _uiState.update { it.copy(isPreparingPhoto = true, photoError = null) }
        viewModelScope.launch {
            runCatching { imageProcessor.prepare(uri) }
                .onSuccess { prepared ->
                    _uiState.update {
                        it.copy(
                            isPreparingPhoto = false,
                            photos = it.photos + PendingPhoto(uri.toString(), uri, prepared),
                        )
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isPreparingPhoto = false,
                            photoError = when (throwable) {
                                is PhotoTooSmallException -> throwable.message
                                else -> "Foto konnte nicht geladen werden."
                            },
                        )
                    }
                }
        }
    }

    fun onPhotoRemoved(id: String) =
        _uiState.update { it.copy(photos = it.photos.filterNot { photo -> photo.id == id }) }

    fun consumeSuccessNotice() = _uiState.update { it.copy(successNotice = null) }

    // ---------- Absenden ----------

    fun register() {
        val state = _uiState.value
        validate(state)?.let { message ->
            _uiState.update { it.copy(error = message) }
            return
        }

        _uiState.update { it.copy(isSubmitting = true, error = null) }
        viewModelScope.launch {
            // Bis die Fotos oben sind, gilt das Konto app-intern noch nicht als
            // angemeldet: sonst schaltet MainViewModel schon auf den
            // Verifizierungsschirm um, während der Upload noch läuft, und der
            // Server lehnt den Start mangels Profilfoto ab.
            authRepository.beginRegistration()
            try {
                runCatching {
                    authRepository.register(
                        email = state.email,
                        password = state.password,
                        name = state.name,
                        birthdate = requireNotNull(state.birthdate),
                        plz = state.postalCode,
                        city = requireNotNull(state.resolvedCity),
                        gender = requireNotNull(state.gender),
                        gymLabel = requireNotNull(state.gymPicker.selectedLabel),
                        bio = state.bio,
                        consentSensitiveData = state.consentSensitiveData,
                    )
                }.onSuccess {
                    val failures = uploadPhotos(state.photos)
                    // Das Konto ist damit angelegt, aber noch nicht freigeschaltet:
                    // Als Nächstes steht die Alters- und Identitätsprüfung an.
                    val notice = when {
                        // Nicht mehr "im Konto nachholen": Der Konto-Bildschirm
                        // gehört zum Hauptgraphen und ist ohne Freischaltung
                        // gar nicht erreichbar. Der Upload wartet jetzt direkt
                        // auf dem Verifizierungs-Schirm (VerificationGateScreen).
                        failures == state.photos.size ->
                            "Profil erstellt — Foto-Upload fehlgeschlagen. Du kannst das Foto gleich nachreichen."
                        failures > 0 -> "Profil erstellt — nicht alle Fotos konnten hochgeladen werden."
                        else -> "Profil erstellt. Jetzt noch die Alters- und Identitätsprüfung 💪"
                    }
                    _uiState.update {
                        it.copy(isSubmitting = false, success = true, successNotice = notice)
                    }
                }.onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isSubmitting = false,
                            error = (throwable as? FlexrApiException)?.message
                                ?: "Registrierung fehlgeschlagen.",
                        )
                    }
                }
            } finally {
                authRepository.finishRegistration()
            }
        }
    }

    /** Lädt die Fotos einzeln hoch und liefert die Anzahl der Fehlschläge. */
    private suspend fun uploadPhotos(photos: List<PendingPhoto>): Int {
        var failures = 0
        photos.forEach { photo ->
            runCatching { profileRepository.addPhoto(photo.prepared) }
                .onFailure { failures++ }
        }
        return failures
    }

    private fun validate(state: RegisterUiState): String? {
        if (state.email.isBlank() ||
            state.password.length < RegisterUiState.MIN_PASSWORD_LENGTH ||
            state.name.isBlank() ||
            state.birthdate == null
        ) {
            return "Bitte E-Mail, Passwort (min. ${RegisterUiState.MIN_PASSWORD_LENGTH} Zeichen), " +
                "Name und Geburtsdatum angeben."
        }
        if (!state.passwordsMatch) {
            return "Die beiden Passwörter stimmen nicht überein."
        }
        val age = ServerTime.ageFrom(state.birthdate)
        // Wortgleich mit der serverseitigen Antwort (backend/app/age.py) - die
        // Grenze prüft verbindlich der Server, hier geht es nur um die Führung.
        if (age < RegisterUiState.MIN_AGE) {
            return "Du musst mindestens 18 Jahre alt sein, um FLEXR nutzen zu können."
        }
        if (age > RegisterUiState.MAX_AGE) return "Bitte ein gültiges Geburtsdatum angeben."
        if (state.resolvedCity == null) {
            return "Bitte eine gültige österreichische Postleitzahl eingeben (Ort wird automatisch ermittelt)."
        }
        if (state.gender == null) return "Bitte ein Geschlecht auswählen."
        if (state.gymPicker.selectedLabel == null) return "Bitte ein Gym aus der Liste auswählen."
        if (state.photos.isEmpty()) return "Bitte lade mindestens ein Foto hoch."
        if (!state.consentSensitiveData) {
            return "Ohne die Einwilligung zur Verarbeitung von Geschlecht und gesuchtem " +
                "Geschlecht können wir dir keine Profile vorschlagen - sie ist die " +
                "Grundlage des Matchings."
        }
        return null
    }

    private companion object {
        const val LOOKUP_DEBOUNCE_MS = 300L
    }
}
