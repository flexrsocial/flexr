package flexr.social.app.ui.account

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.core.media.PhotoTooSmallException
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.repository.BillingRepository
import flexr.social.app.data.repository.GymRepository
import flexr.social.app.data.repository.PlzRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.SafetyRepository
import flexr.social.app.data.repository.UnknownPostalCodeException
import flexr.social.app.data.repository.VerificationRepository
import flexr.social.app.data.remote.dto.ConsentDto
import flexr.social.app.data.remote.dto.NotificationSettingsRequestDto
import flexr.social.app.data.session.SessionStore
import flexr.social.app.domain.model.BlockedUser
import flexr.social.app.domain.model.Gym
import flexr.social.app.domain.model.Membership
import flexr.social.app.domain.model.MyProfile
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.ui.components.GymPickerState
import flexr.social.app.ui.components.GymSuggestionState
import flexr.social.app.ui.components.PlzLookupState
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AccountUiState(
    val postalCode: String = "",
    val plzLookup: PlzLookupState = PlzLookupState.Idle,
    val gymPicker: GymPickerState = GymPickerState(),
    val gymSuggestion: GymSuggestionState? = null,
    val bio: String = "",
    val searchRadiusKm: Int = 20,
    val isSaving: Boolean = false,
    val saveError: String? = null,
    val photoError: String? = null,
    val isUploadingPhoto: Boolean = false,
    val verificationStatus: VerificationStatus = VerificationStatus.NONE,
    /** Bestätigter „verifiziert"-Hinweis wird dauerhaft ausgeblendet. */
    val verifiedHintDismissed: Boolean = false,
    val notificationsEnabled: Boolean = true,
    /** Läuft gerade ein Schalter unter "Benachrichtigungen" zum Server? */
    val isSavingNotifications: Boolean = false,
    val consents: List<ConsentDto> = emptyList(),
    val consentsLoading: Boolean = false,
    val consentError: String? = null,
    val revokingConsentType: String? = null,
    val grantingConsentType: String? = null,
    val blockedUsers: List<BlockedUser> = emptyList(),
    val blockedUsersLoading: Boolean = false,
    val blockedUsersError: String? = null,
    val unblockingUserId: String? = null,
    val checkoutDialogVisible: Boolean = false,
    val checkoutImmediateStart: Boolean = false,
    val checkoutWithdrawalAck: Boolean = false,
    val checkoutError: String? = null,
    val isStartingCheckout: Boolean = false,
    val deleteDialogVisible: Boolean = false,
    val deletePassword: String = "",
    val deleteError: String? = null,
    val isDeleting: Boolean = false,
) {
    val resolvedCity: String? get() = (plzLookup as? PlzLookupState.Resolved)?.city
}

sealed interface AccountEvent {
    data class Message(val text: String) : AccountEvent
    data class OpenUrl(val url: String) : AccountEvent
    data object LoggedOut : AccountEvent
    data object StartVerification : AccountEvent

    /** Selfies liegen vor, es fehlt nur noch der Lichtbildausweis. */
    data object ContinueWithDocument : AccountEvent
}

/**
 * Konto-Bereich: Profil bearbeiten, Fotos verwalten, Mitgliedschaft,
 * Verifizierung und Kontolöschung.
 */
@HiltViewModel
class AccountViewModel @Inject constructor(
    private val profileRepository: ProfileRepository,
    private val billingRepository: BillingRepository,
    private val gymRepository: GymRepository,
    private val plzRepository: PlzRepository,
    private val verificationRepository: VerificationRepository,
    private val safetyRepository: SafetyRepository,
    private val imageProcessor: ImageProcessor,
    private val sessionStore: SessionStore,
) : ViewModel() {

    private val _uiState = MutableStateFlow(AccountUiState())
    val uiState: StateFlow<AccountUiState> = _uiState.asStateFlow()

    private val _events = Channel<AccountEvent>(Channel.BUFFERED)
    val events: Flow<AccountEvent> = _events.receiveAsFlow()

    val profile: StateFlow<MyProfile?> = profileRepository.myProfile
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), profileRepository.myProfile.value)

    val membership: StateFlow<Membership?> = billingRepository.membership
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), billingRepository.membership.value)

    private var plzLookupJob: Job? = null
    private var gymSearchJob: Job? = null

    init {
        profileRepository.myProfile.value?.let(::prefillFrom)
        viewModelScope.launch {
            runCatching { profileRepository.refresh() }.getOrNull()?.let(::prefillFrom)
            runCatching { billingRepository.refresh() }
            refreshVerificationStatus()
            refreshConsents()
            refreshBlockedUsers()
            val notificationsEnabled = sessionStore.notificationsEnabled.first()
            val hintDismissed = sessionStore.verifiedHintDismissed.first()
            _uiState.update {
                it.copy(
                    notificationsEnabled = notificationsEnabled,
                    verifiedHintDismissed = hintDismissed,
                )
            }
        }
    }

    private fun prefillFrom(profile: MyProfile) {
        _uiState.update { state ->
            state.copy(
                postalCode = profile.plz,
                plzLookup = if (profile.profile.city.isNotBlank()) {
                    PlzLookupState.Resolved(profile.profile.city)
                } else {
                    PlzLookupState.Idle
                },
                gymPicker = state.gymPicker.copy(
                    query = profile.profile.gymName,
                    selectedLabel = profile.profile.gym.takeIf { it.isNotBlank() },
                    expanded = false,
                ),
                bio = profile.profile.bio.orEmpty(),
                searchRadiusKm = profile.searchRadiusKm,
            )
        }
    }

    // ---------- Profil bearbeiten ----------

    fun onPostalCodeChange(value: String) {
        _uiState.update { it.copy(postalCode = value, plzLookup = PlzLookupState.Idle, saveError = null) }
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
                                else "Ort konnte nicht ermittelt werden.",
                            )
                        },
                    ),
                )
            }
        }
    }

    fun onGymQueryChange(value: String) {
        _uiState.update { state ->
            val keepSelection = state.gymPicker.selectedLabel?.substringBefore(" — ") == value
            state.copy(
                gymPicker = state.gymPicker.copy(
                    query = value,
                    expanded = true,
                    selectedLabel = if (keepSelection) state.gymPicker.selectedLabel else null,
                ),
                saveError = null,
            )
        }
        gymSearchJob?.cancel()
        gymSearchJob = viewModelScope.launch {
            delay(LOOKUP_DEBOUNCE_MS)
            _uiState.update { it.copy(gymPicker = it.gymPicker.copy(isSearching = true)) }
            val results = runCatching { gymRepository.search(value) }.getOrDefault(emptyList())
            _uiState.update { it.copy(gymPicker = it.gymPicker.copy(results = results, isSearching = false)) }
        }
    }

    fun onGymSelected(gym: Gym) = _uiState.update {
        it.copy(gymPicker = it.gymPicker.copy(query = gym.name, selectedLabel = gym.label, expanded = false))
    }

    fun openGymSuggestion() = _uiState.update {
        it.copy(
            gymSuggestion = GymSuggestionState(name = it.gymPicker.query.trim()),
            gymPicker = it.gymPicker.copy(expanded = false),
        )
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
                    )
                }
                _events.send(AccountEvent.Message("Danke! Vorschlag eingereicht — sofort verwendbar."))
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

    fun onBioChange(value: String) = _uiState.update { it.copy(bio = value.take(BIO_MAX_LENGTH)) }

    fun onSearchRadiusChange(value: Int) = _uiState.update { it.copy(searchRadiusKm = value) }

    fun saveProfile() {
        val state = _uiState.value
        val city = state.resolvedCity
        if (city == null) {
            _uiState.update {
                it.copy(
                    saveError = "Bitte eine gültige österreichische Postleitzahl eingeben " +
                        "(Ort wird automatisch ermittelt).",
                )
            }
            return
        }
        if (profile.value?.photos.isNullOrEmpty()) {
            _uiState.update { it.copy(saveError = "Bitte lade mindestens ein Foto hoch, bevor du speicherst.") }
            return
        }
        val gymLabel = state.gymPicker.selectedLabel
        if (gymLabel == null) {
            _uiState.update { it.copy(saveError = "Bitte ein Gym aus der Liste auswählen.") }
            return
        }

        _uiState.update { it.copy(isSaving = true, saveError = null) }
        viewModelScope.launch {
            runCatching {
                profileRepository.updateProfile(
                    plz = state.postalCode,
                    city = city,
                    gymLabel = gymLabel,
                    bio = state.bio.trim(),
                    searchRadiusKm = state.searchRadiusKm,
                )
            }.onSuccess {
                _uiState.update { it.copy(isSaving = false) }
                _events.send(AccountEvent.Message("Profil gespeichert ✓"))
            }.onFailure { throwable ->
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        saveError = (throwable as? FlexrApiException)?.message ?: "Speichern fehlgeschlagen.",
                    )
                }
            }
        }
    }

    // ---------- Fotos ----------

    fun onPhotoPicked(uri: Uri) {
        _uiState.update { it.copy(isUploadingPhoto = true, photoError = null) }
        viewModelScope.launch {
            runCatching {
                val prepared = imageProcessor.prepare(uri)
                profileRepository.addPhoto(prepared)
            }.onSuccess {
                _uiState.update { it.copy(isUploadingPhoto = false) }
            }.onFailure { throwable ->
                _uiState.update {
                    it.copy(
                        isUploadingPhoto = false,
                        photoError = when (throwable) {
                            is PhotoTooSmallException -> throwable.message
                            is FlexrApiException -> throwable.message
                            else -> "Foto-Upload fehlgeschlagen."
                        },
                    )
                }
            }
        }
    }

    fun onPhotoRemoved(photoId: String) {
        if ((profile.value?.photos?.size ?: 0) <= 1) {
            _uiState.update {
                it.copy(
                    photoError = "Mindestens ein Foto ist erforderlich. Lade zuerst ein weiteres hoch.",
                )
            }
            return
        }
        _uiState.update { it.copy(photoError = null) }
        viewModelScope.launch {
            runCatching { profileRepository.deletePhoto(photoId) }
                .onFailure { _events.send(AccountEvent.Message(it.message ?: "Löschen fehlgeschlagen.")) }
        }
    }

    // ---------- Verifizierung ----------

    fun refreshVerificationStatus() {
        viewModelScope.launch {
            val status = runCatching { verificationRepository.status() }.getOrNull()?.status
                ?: VerificationStatus.NONE
            _uiState.update { it.copy(verificationStatus = status) }
        }
    }

    /**
     * Springt an die Stelle, an der die Prüfung tatsächlich weitergeht: fehlt
     * nur noch der Ausweis, führt der Weg direkt dorthin statt zu den Selfies.
     */
    fun startVerification() {
        viewModelScope.launch {
            val event = if (_uiState.value.verificationStatus.needsDocument) {
                AccountEvent.ContinueWithDocument
            } else {
                AccountEvent.StartVerification
            }
            _events.send(event)
        }
    }

    /** „Verstanden" auf dem Verifiziert-Hinweis: dauerhaft ausblenden. */
    fun dismissVerifiedHint() {
        _uiState.update { it.copy(verifiedHintDismissed = true) }
        viewModelScope.launch { sessionStore.setVerifiedHintDismissed() }
    }

    // ---------- Mitgliedschaft ----------

    // Zwei getrennte, nicht vorangekreuzte Erklärungen vor jedem Checkout
    // (§ 10 und § 18 Abs. 1 Z 1 FAGG) - ohne beide lehnt das Backend die
    // Anfrage mit 422 ab (`CheckoutRequest` in `backend/app/schemas.py`).
    fun openCheckoutDialog() {
        _uiState.update {
            it.copy(
                checkoutDialogVisible = true,
                checkoutImmediateStart = false,
                checkoutWithdrawalAck = false,
                checkoutError = null,
            )
        }
    }

    fun closeCheckoutDialog() {
        _uiState.update { it.copy(checkoutDialogVisible = false) }
    }

    fun onCheckoutImmediateStartChange(checked: Boolean) {
        _uiState.update { it.copy(checkoutImmediateStart = checked) }
    }

    fun onCheckoutWithdrawalAckChange(checked: Boolean) {
        _uiState.update { it.copy(checkoutWithdrawalAck = checked) }
    }

    fun confirmCheckout() {
        val current = _uiState.value
        if (!current.checkoutImmediateStart || !current.checkoutWithdrawalAck) {
            _uiState.update {
                it.copy(checkoutError = "Bitte bestätige beide Erklärungen, um fortzufahren.")
            }
            return
        }
        _uiState.update { it.copy(isStartingCheckout = true, checkoutError = null) }
        viewModelScope.launch {
            runCatching { billingRepository.checkoutUrl(immediateStart = true, withdrawalAck = true) }
                .onSuccess { url ->
                    _uiState.update { it.copy(isStartingCheckout = false, checkoutDialogVisible = false) }
                    _events.send(AccountEvent.OpenUrl(url))
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isStartingCheckout = false,
                            checkoutError = (throwable as? FlexrApiException)?.message
                                ?: "Checkout konnte nicht gestartet werden.",
                        )
                    }
                }
        }
    }

    fun openBillingPortal() {
        viewModelScope.launch {
            runCatching { billingRepository.portalUrl() }
                .onSuccess { _events.send(AccountEvent.OpenUrl(it)) }
                .onFailure {
                    _events.send(AccountEvent.Message(it.message ?: "Abo-Verwaltung konnte nicht geöffnet werden."))
                }
        }
    }

    // ---------- Benachrichtigungen ----------

    /**
     * Neue Fotoreihenfolge speichern.
     *
     * Der Server bekommt die vollstaendige Liste; scheitert der Aufruf, bleibt
     * die bisherige Reihenfolge stehen, weil die Anzeige dem Profil aus dem
     * Repository folgt und nicht der Geste.
     */
    fun onPhotosReordered(photoIds: List<String>) {
        viewModelScope.launch {
            runCatching { profileRepository.reorderPhotos(photoIds) }
                .onFailure {
                    _events.send(
                        AccountEvent.Message(
                            it.message ?: "Reihenfolge konnte nicht gespeichert werden.",
                        ),
                    )
                }
        }
    }

    fun setNotificationsEnabled(enabled: Boolean) {
        _uiState.update { it.copy(notificationsEnabled = enabled) }
        viewModelScope.launch { sessionStore.setNotificationsEnabled(enabled) }
    }

    /**
     * Einzelnen Schalter unter "Benachrichtigungen" speichern.
     *
     * Es wird immer nur das eine geänderte Feld geschickt - so überschreibt ein
     * Schalter nie die Stellung der übrigen mit einem veralteten Stand. Die
     * Anzeige folgt dem Profil aus dem Repository, deshalb gibt es hier keine
     * zweite Kopie des Zustands, die auseinanderlaufen könnte.
     */
    fun updateNotificationSetting(request: NotificationSettingsRequestDto) {
        _uiState.update { it.copy(isSavingNotifications = true) }
        viewModelScope.launch {
            runCatching { profileRepository.updateNotificationSettings(request) }
                .onFailure {
                    _events.send(
                        AccountEvent.Message(
                            it.message ?: "Einstellung konnte nicht gespeichert werden.",
                        ),
                    )
                }
            _uiState.update { it.copy(isSavingNotifications = false) }
        }
    }

    // ---------- Einwilligungen ----------

    fun refreshConsents() {
        _uiState.update { it.copy(consentsLoading = true, consentError = null) }
        viewModelScope.launch {
            runCatching { profileRepository.consents() }
                .onSuccess { consents ->
                    _uiState.update {
                        it.copy(consents = consents, consentsLoading = false, consentError = null)
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            consentsLoading = false,
                            consentError = (throwable as? FlexrApiException)?.message
                                ?: "Einwilligungen konnten nicht geladen werden.",
                        )
                    }
                }
        }
    }

    fun revokeConsent(consentType: String) {
        if (_uiState.value.revokingConsentType != null || _uiState.value.grantingConsentType != null) return
        _uiState.update { it.copy(revokingConsentType = consentType, consentError = null) }
        viewModelScope.launch {
            runCatching {
                val result = profileRepository.revokeConsent(consentType)
                result to profileRepository.consents()
            }.onSuccess { (result, consents) ->
                _uiState.update {
                    it.copy(
                        consents = consents,
                        revokingConsentType = null,
                        consentError = null,
                    )
                }
                _events.send(AccountEvent.Message(result.consequence))
            }.onFailure { throwable ->
                _uiState.update {
                    it.copy(
                        revokingConsentType = null,
                        consentError = (throwable as? FlexrApiException)?.message
                            ?: "Der Widerruf konnte nicht gespeichert werden.",
                    )
                }
            }
        }
    }

    /** Einen zuvor erklärten Widerruf rückgängig machen. */
    fun grantConsent(consentType: String) {
        if (_uiState.value.revokingConsentType != null || _uiState.value.grantingConsentType != null) return
        _uiState.update { it.copy(grantingConsentType = consentType, consentError = null) }
        viewModelScope.launch {
            runCatching {
                val result = profileRepository.grantConsent(consentType)
                result to profileRepository.consents()
            }.onSuccess { (result, consents) ->
                _uiState.update {
                    it.copy(
                        consents = consents,
                        grantingConsentType = null,
                        consentError = null,
                    )
                }
                _events.send(AccountEvent.Message(result.consequence))
            }.onFailure { throwable ->
                _uiState.update {
                    it.copy(
                        grantingConsentType = null,
                        consentError = (throwable as? FlexrApiException)?.message
                            ?: "Die erneute Einwilligung konnte nicht gespeichert werden.",
                    )
                }
            }
        }
    }

    // ---------- Blockierte Personen ----------

    fun refreshBlockedUsers() {
        _uiState.update { it.copy(blockedUsersLoading = true, blockedUsersError = null) }
        viewModelScope.launch {
            runCatching { safetyRepository.blockedUsers() }
                .onSuccess { blocked ->
                    _uiState.update {
                        it.copy(blockedUsers = blocked, blockedUsersLoading = false, blockedUsersError = null)
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            blockedUsersLoading = false,
                            blockedUsersError = (throwable as? FlexrApiException)?.message
                                ?: "Deine Blockierungen konnten nicht geladen werden.",
                        )
                    }
                }
        }
    }

    /**
     * Hebt eine Blockierung auf. Löst weder Match noch Chatverlauf auf, blendet
     * sie nur wieder ein — entspricht `DELETE /api/blocks/{id}` in safety.py.
     */
    fun unblockUser(userId: String) {
        if (_uiState.value.unblockingUserId != null) return
        _uiState.update { it.copy(unblockingUserId = userId, blockedUsersError = null) }
        viewModelScope.launch {
            runCatching { safetyRepository.unblock(userId) }
                .onSuccess {
                    _uiState.update {
                        it.copy(
                            blockedUsers = it.blockedUsers.filterNot { user -> user.userId == userId },
                            unblockingUserId = null,
                        )
                    }
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            unblockingUserId = null,
                            blockedUsersError = (throwable as? FlexrApiException)?.message
                                ?: "Aufheben fehlgeschlagen.",
                        )
                    }
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

    fun confirmDelete() {
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
                    _events.send(
                        AccountEvent.Message(
                            "Dein Konto wurde deaktiviert und wird in 30 Tagen endgültig gelöscht.",
                        ),
                    )
                    _events.send(AccountEvent.LoggedOut)
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

    companion object {
        const val BIO_MAX_LENGTH = 280
        const val MIN_RADIUS_KM = 2
        const val MAX_RADIUS_KM = 250
        private const val LOOKUP_DEBOUNCE_MS = 300L
    }
}
