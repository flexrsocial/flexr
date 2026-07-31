package flexr.social.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.SessionGate
import flexr.social.app.data.repository.AuthRepository
import flexr.social.app.data.repository.BillingRepository
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.domain.model.Membership
import flexr.social.app.domain.model.MyProfile
import flexr.social.app.notifications.MessageNotificationScheduler
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

/** Startzustand der App — steuert, welcher Navigationsgraph aktiv ist. */
sealed interface AppState {
    data object Loading : AppState

    data object LoggedOut : AppState

    /** Angemeldet, aber Probemonat abgelaufen und kein Abo: nur die Paywall. */
    data class Locked(val membership: Membership) : AppState

    data class Ready(val profile: MyProfile, val membership: Membership) : AppState
}

/**
 * Hält den app-weiten Sitzungszustand: angemeldet, zahlungspflichtig gesperrt
 * oder einsatzbereit. Entspricht der `boot()`/`goToApp()`-Logik des Web-Frontends,
 * hier aber als beobachtbarer Zustand statt als imperativer Bildschirmwechsel.
 */
@HiltViewModel
class MainViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val profileRepository: ProfileRepository,
    private val billingRepository: BillingRepository,
    private val notificationScheduler: MessageNotificationScheduler,
    matchRepository: MatchRepository,
) : ViewModel() {

    private val _appState = MutableStateFlow<AppState>(AppState.Loading)
    val appState: StateFlow<AppState> = _appState.asStateFlow()

    val unreadCount: StateFlow<Int> = matchRepository.unreadTotal
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), 0)

    init {
        authRepository.isLoggedIn
            .distinctUntilChanged()
            .onEach { loggedIn -> if (loggedIn) loadSession() else markLoggedOut() }
            .launchIn(viewModelScope)

        // 401 vom Backend: Sitzung ist weg, zurück auf den Login.
        authRepository.sessionExpired
            .onEach { logout() }
            .launchIn(viewModelScope)
    }

    /** Nach Login/Registrierung: Profil und Mitgliedschaft laden. */
    fun loadSession() {
        viewModelScope.launch {
            runCatching {
                val profile = profileRepository.refresh()
                val membership = billingRepository.refresh()
                profile to membership
            }.onSuccess { (profile, membership) ->
                _appState.value = if (membership.isActive) {
                    notificationScheduler.schedule()
                    AppState.Ready(profile, membership)
                } else {
                    notificationScheduler.cancel()
                    AppState.Locked(membership)
                }
                SessionGate.isReady = true
            }.onFailure {
                // Token ungültig oder Server nicht erreichbar — der
                // Interceptor hat bei 401 bereits abgemeldet.
                if (_appState.value is AppState.Loading) markLoggedOut()
                SessionGate.isReady = true
            }
        }
    }

    /** Nach Rückkehr aus dem Stripe-Checkout: Abo-Status neu holen. */
    fun refreshMembership() = loadSession()

    fun logout() {
        viewModelScope.launch {
            notificationScheduler.cancel()
            authRepository.logout()
            profileRepository.clear()
            billingRepository.clear()
            markLoggedOut()
        }
    }

    private fun markLoggedOut() {
        _appState.value = AppState.LoggedOut
        SessionGate.isReady = true
    }
}
