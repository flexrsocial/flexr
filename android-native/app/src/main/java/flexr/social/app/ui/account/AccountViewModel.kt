package flexr.social.app.ui.account

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.R
import flexr.social.app.core.locale.AppStrings
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.core.media.PhotoTooSmallException
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.remote.dto.ConsentDto
import flexr.social.app.data.billing.PlayBillingService
import flexr.social.app.data.remote.dto.NotificationSettingsRequestDto
import flexr.social.app.data.repository.BillingRepository
import flexr.social.app.data.repository.GymRepository
import flexr.social.app.data.repository.PlzRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.SafetyRepository
import flexr.social.app.data.repository.UnknownPostalCodeException
import flexr.social.app.data.repository.VerificationRepository
import flexr.social.app.push.PushTokenRegistrar
import flexr.social.app.data.session.SessionStore
import flexr.social.app.domain.model.BlockedUser
import flexr.social.app.domain.model.Gym
import flexr.social.app.domain.model.Membership
import flexr.social.app.domain.model.MyProfile
import flexr.social.app.domain.model.PhotoStatus
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
import java.time.Instant
import javax.inject.Inject

data class AccountUiState(
    val postalCode: String = "",
    val plzLookup: PlzLookupState = PlzLookupState.Idle,
    val gymPicker: GymPickerState = GymPickerState(),
    val gymSuggestion: GymSuggestionState? = null,
    val bio: String = "",
    val searchRadiusKm: Int = 20,
    /**
     * Groesster Umkreis, den dieses Konto einstellen darf.
     *
     * Kommt vom Server (`GET /api/billing/status`, Feld `max_radius_km`) und
     * ist damit dieselbe Zahl, die der Server auch durchsetzt - er kappt jeden
     * Wunsch darueber stillschweigend (`premium.clamp_radius`). Der Regler
     * endet deshalb genau hier: Ein Standardkonto konnte ihn bisher bis 250 km
     * ziehen, gespeichert wurden aber 50 km, und die Oberflaeche zeigte
     * anschliessend eine Zahl, nach der gar nicht gesucht wurde.
     *
     * Bis der Mitgliedsstand geladen ist, steht der volle Regler: lieber kurz
     * zu viel anbieten als einem Premium-Konto ohne Grund den halben Regler
     * wegzunehmen - durchgesetzt wird ohnehin serverseitig.
     */
    val maxSelectableRadiusKm: Int = AccountViewModel.MAX_RADIUS_KM,
    /** Solange gesetzt, ist ein Gym-Wechsel gesperrt (siehe MyProfile.activeGymLockUntil). */
    val gymChangeLockedUntil: Instant? = null,
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
    /**
     * Wird erst true, sobald [notificationsEnabled] den echten gespeicherten
     * Wert traegt statt des Default-Werts oben. Der Screen fragt die
     * Systemberechtigung erst danach einmalig an - sonst koennte er sie faelschlich
     * fuer ein Konto anfragen, das Benachrichtigungen bereits deaktiviert hatte.
     */
    val notificationsLoaded: Boolean = false,
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
    /** Offener Dialog "E-Mail-Adresse ändern" / "Passwort ändern", sonst null. */
    val credentials: CredentialsDialogState? = null,
) {
    val resolvedCity: String? get() = (plzLookup as? PlzLookupState.Resolved)?.city

    /** Gilt fuer dieses Konto ueberhaupt eine Grenze, oder steht der Regler offen? */
    val isRadiusCapped: Boolean get() = maxSelectableRadiusKm < AccountViewModel.MAX_RADIUS_KM
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
    private val playBilling: PlayBillingService,
    private val gymRepository: GymRepository,
    private val plzRepository: PlzRepository,
    private val verificationRepository: VerificationRepository,
    private val safetyRepository: SafetyRepository,
    private val imageProcessor: ImageProcessor,
    private val sessionStore: SessionStore,
    private val pushTokenRegistrar: PushTokenRegistrar,
    private val strings: AppStrings,
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
        // Die Grenze haengt am Mitgliedsstand und kann sich waehrend der
        // Sitzung aendern (Kauf, Kuendigung, Ablauf) - deshalb beobachtet statt
        // einmalig gelesen. `uebernehmeRadiusGrenze` kappt einen zu grossen
        // gespeicherten Wert gleich mit: Wer Premium kuendigt, kommt sonst mit
        // 250 km zurueck und sieht einen Regler, der nichts mehr bewirkt.
        viewModelScope.launch {
            membership.collect(::uebernehmeRadiusGrenze)
        }
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
                    notificationsLoaded = true,
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
                searchRadiusKm = profile.searchRadiusKm.coerceAtMost(state.maxSelectableRadiusKm),
                gymChangeLockedUntil = profile.activeGymLockUntil(),
            )
        }
    }

    /**
     * Neue Radius-Grenze aus dem Mitgliedsstand uebernehmen und einen darueber
     * liegenden Reglerstand darauf zurueckholen.
     *
     * Ohne geladenen Stand (`null`), ohne geltende Grenzen oder mit Premium
     * steht der volle Regler - dieselbe Bedingung, nach der der Server
     * entscheidet (`premium.max_radius_km`).
     */
    private fun uebernehmeRadiusGrenze(status: Membership?) {
        val grenze = if (status == null || !status.limitsActive || status.isPremium) {
            MAX_RADIUS_KM
        } else {
            status.maxRadiusKm.coerceAtMost(MAX_RADIUS_KM)
        }
        _uiState.update {
            it.copy(
                maxSelectableRadiusKm = grenze,
                searchRadiusKm = it.searchRadiusKm.coerceAtMost(grenze),
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
                                else strings.get(R.string.error_city_lookup),
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
                            error = throwable.message ?: strings.get(R.string.gym_suggest_failed),
                        ),
                    )
                }
            }
        }
    }

    fun onBioChange(value: String) = _uiState.update { it.copy(bio = value.take(BIO_MAX_LENGTH)) }

    fun onSearchRadiusChange(value: Int) = _uiState.update {
        // Auch hier kappen und nicht nur am Regler: Der Wertebereich der
        // Oberflaeche ist eine Anzeige, die Grenze gehoert an den Zustand.
        it.copy(searchRadiusKm = value.coerceIn(MIN_RADIUS_KM, it.maxSelectableRadiusKm))
    }

    fun saveProfile() {
        val state = _uiState.value
        val city = state.resolvedCity
        if (city == null) {
            _uiState.update {
                it.copy(
                    saveError = strings.get(R.string.account_err_postal_code),
                )
            }
            return
        }
        if ((profile.value?.photos?.size ?: 0) < ImageProcessor.MIN_PHOTOS) {
            _uiState.update {
                it.copy(
                    saveError = strings.get(
                        R.string.account_err_photo_before_save,
                        ImageProcessor.MIN_PHOTOS,
                    ),
                )
            }
            return
        }
        val gymLabel = state.gymPicker.selectedLabel
        if (gymLabel == null) {
            _uiState.update { it.copy(saveError = strings.get(R.string.account_err_gym)) }
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
            }.onSuccess { updated ->
                // Uebernimmt u.a. eine frisch gesetzte Gym-Wechsel-Karenz - ohne
                // das bliebe das Feld nach dem Speichern faelschlich entsperrt,
                // bis das Profil ein naechstes Mal komplett neu geladen wird.
                prefillFrom(updated)
                _uiState.update { it.copy(isSaving = false) }
                _events.send(AccountEvent.Message(strings.get(R.string.account_saved)))
            }.onFailure { throwable ->
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        saveError = (throwable as? FlexrApiException)?.message ?: strings.get(R.string.account_save_failed),
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
                            is PhotoTooSmallException -> strings.get(
                                R.string.photo_too_small,
                                throwable.width,
                                throwable.height,
                                ImageProcessor.MIN_EDGE_PX,
                            )
                            is FlexrApiException -> throwable.message
                            else -> strings.get(R.string.photo_upload_failed)
                        },
                    )
                }
            }
        }
    }

    fun onPhotoRemoved(photoId: String) {
        // Dieselbe Grenze wie beim Anlegen des Kontos: Der Server lehnt das
        // Loeschen sonst ohnehin ab (backend/app/routers/profiles.py), hier
        // steht die Meldung nur frueher und in der gewaehlten Sprache.
        // Abgelehnte Fotos zaehlen nicht mit und lassen sich immer entfernen -
        // ihre Datei ist ohnehin schon geloescht.
        val foto = profile.value?.photos?.firstOrNull { it.id == photoId }
        if (foto?.status != PhotoStatus.REJECTED &&
            (profile.value?.validPhotoCount ?: 0) <= ImageProcessor.MIN_PHOTOS
        ) {
            _uiState.update {
                it.copy(
                    photoError = strings.get(
                        R.string.photo_min_count,
                        ImageProcessor.MIN_PHOTOS,
                    ),
                )
            }
            return
        }
        _uiState.update { it.copy(photoError = null) }
        viewModelScope.launch {
            runCatching { profileRepository.deletePhoto(photoId) }
                .onFailure {
                    _events.send(AccountEvent.Message(it.message ?: strings.get(R.string.common_delete_failed)))
                }
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
                it.copy(checkoutError = strings.get(R.string.account_checkout_consent_missing))
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
                                ?: strings.get(R.string.account_checkout_failed),
                        )
                    }
                }
        }
    }

    // ---------- Kauf über Google Play ----------

    /** Der Preis, wie der Play Store ihn schreibt - `null`, solange er lädt. */
    val storePreis: StateFlow<String?> = playBilling.preis

    /** Ausgang des Kaufvorgangs. Google meldet ihn unter Umständen erst
     *  Minuten später, deshalb ein Fluss und kein Rückgabewert. */
    val kaufEreignisse = playBilling.ereignisse

    /**
     * Produktdaten laden, damit der echte Preis dasteht, bevor jemand tippt.
     *
     * Ohne das stünde auf dem Knopf ein Preis aus unseren Ressourcen - und der
     * stimmt nur zufällig: Google rechnet Währung, Steuer und Schreibweise je
     * nach Land des Kontos.
     */
    fun ladePremiumAngebot() {
        val produktId = membership.value?.storeProductId ?: return
        viewModelScope.launch { playBilling.produktLaden(produktId) }
    }

    /**
     * Kaufvorgang starten. Das Ergebnis kommt über [PlayBillingService.ereignisse] -
     * Google führt den Kauf in einer eigenen Oberfläche zu Ende.
     */
    fun kaufePremium(activity: android.app.Activity) {
        val produktId = membership.value?.storeProductId ?: return
        viewModelScope.launch { playBilling.kaufen(activity, produktId) }
    }

    /**
     * Kündigen läuft bei einem Play-Kauf über den Play Store, nicht über uns:
     * Google ist der Händler, wir könnten das Abo gar nicht beenden. Der Link
     * führt direkt auf die Abo-Seite dieses Produkts.
     */
    fun playAboVerwalten() {
        val produktId = membership.value?.storeProductId
        val ziel = if (produktId != null) {
            "https://play.google.com/store/account/subscriptions" +
                "?sku=$produktId&package=flexr.social.app"
        } else {
            "https://play.google.com/store/account/subscriptions"
        }
        viewModelScope.launch { _events.send(AccountEvent.OpenUrl(ziel)) }
    }

    fun openBillingPortal() {
        viewModelScope.launch {
            runCatching { billingRepository.portalUrl() }
                .onSuccess { _events.send(AccountEvent.OpenUrl(it)) }
                .onFailure {
                    _events.send(AccountEvent.Message(it.message ?: strings.get(R.string.account_portal_failed)))
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
                            it.message ?: strings.get(R.string.photo_order_failed),
                        ),
                    )
                }
        }
    }

    fun setNotificationsEnabled(enabled: Boolean) {
        _uiState.update { it.copy(notificationsEnabled = enabled) }
        viewModelScope.launch {
            sessionStore.setNotificationsEnabled(enabled)
            // Der Push-Token **ist** der Schalter: Abgeschaltet heisst
            // abgemeldet, und der Server hat dann niemanden, dem er zustellen
            // koennte. Ein zusaetzliches Flag am Konto gaebe es zwei Quellen
            // fuer dieselbe Frage - die laufen frueher oder spaeter auseinander.
            runCatching {
                if (enabled) pushTokenRegistrar.anmelden() else pushTokenRegistrar.abmelden()
            }
        }
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
                            it.message ?: strings.get(R.string.account_notification_save_failed),
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
                                ?: strings.get(R.string.consent_load_failed),
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
                            ?: strings.get(R.string.consent_revoke_failed),
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
                            ?: strings.get(R.string.consent_grant_failed),
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
                                ?: strings.get(R.string.blocks_load_failed),
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

    // ---------- Zugangsdaten ----------

    fun openCredentials(mode: CredentialsMode) =
        _uiState.update { it.copy(credentials = CredentialsDialogState(mode = mode)) }

    fun closeCredentials() = _uiState.update { it.copy(credentials = null) }

    fun onCredentialsChange(transform: (CredentialsDialogState) -> CredentialsDialogState) =
        _uiState.update { state ->
            state.copy(credentials = state.credentials?.let { transform(it).copy(error = null) })
        }

    fun saveCredentials() {
        val dialog = _uiState.value.credentials ?: return
        if (dialog.saving) return
        val fehler = when {
            dialog.currentPassword.isBlank() -> strings.get(R.string.cred_err_pw)
            dialog.mode == CredentialsMode.EMAIL &&
                !Regex("^\\S+@\\S+\\.\\S+$").matches(dialog.newEmail.trim()) ->
                strings.get(R.string.forgot_err_email)
            dialog.mode == CredentialsMode.PASSWORD && dialog.newPassword.length < 8 ->
                strings.get(R.string.reset_err_short)
            dialog.mode == CredentialsMode.PASSWORD && dialog.newPassword != dialog.newPassword2 ->
                strings.get(R.string.register_err_password_mismatch)
            else -> null
        }
        if (fehler != null) {
            _uiState.update { it.copy(credentials = dialog.copy(error = fehler)) }
            return
        }
        _uiState.update { it.copy(credentials = dialog.copy(saving = true, error = null)) }
        viewModelScope.launch {
            runCatching {
                when (dialog.mode) {
                    CredentialsMode.EMAIL -> {
                        val profil = profileRepository.changeEmail(dialog.newEmail, dialog.currentPassword)
                        strings.get(R.string.cred_email_done, profil.email)
                    }
                    CredentialsMode.PASSWORD -> {
                        profileRepository.changePassword(dialog.currentPassword, dialog.newPassword)
                        strings.get(R.string.cred_pw_done)
                    }
                }
            }.onSuccess { meldung ->
                _uiState.update { it.copy(credentials = null) }
                _events.send(AccountEvent.Message(meldung))
            }.onFailure { throwable ->
                _uiState.update { state ->
                    state.copy(
                        credentials = state.credentials?.copy(
                            saving = false,
                            error = (throwable as? FlexrApiException)?.message
                                ?: strings.get(R.string.reset_err_save),
                        ),
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
            _uiState.update { it.copy(deleteError = strings.get(R.string.delete_password_missing)) }
            return
        }
        _uiState.update { it.copy(isDeleting = true, deleteError = null) }
        viewModelScope.launch {
            runCatching { profileRepository.deleteAccount(password) }
                .onSuccess {
                    _uiState.update { it.copy(isDeleting = false, deleteDialogVisible = false) }
                    _events.send(
                        AccountEvent.Message(
                            strings.get(R.string.delete_done),
                        ),
                    )
                    _events.send(AccountEvent.LoggedOut)
                }
                .onFailure { throwable ->
                    _uiState.update {
                        it.copy(
                            isDeleting = false,
                            deleteError = (throwable as? FlexrApiException)?.message
                                ?: strings.get(R.string.common_delete_failed),
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

enum class CredentialsMode { EMAIL, PASSWORD }

data class CredentialsDialogState(
    val mode: CredentialsMode,
    val newEmail: String = "",
    val currentPassword: String = "",
    val newPassword: String = "",
    val newPassword2: String = "",
    val saving: Boolean = false,
    val error: String? = null,
)
