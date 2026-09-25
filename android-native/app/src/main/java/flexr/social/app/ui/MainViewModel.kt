package flexr.social.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.R
import flexr.social.app.SessionGate
import flexr.social.app.core.locale.AppLanguage
import flexr.social.app.core.locale.AppStrings
import flexr.social.app.core.locale.LanguageStore
import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.core.network.VerificationGate
import flexr.social.app.data.billing.PlayBillingService
import flexr.social.app.data.repository.AuthRepository
import flexr.social.app.data.repository.BillingRepository
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.repository.ProfileRepository
import flexr.social.app.data.repository.VerificationRepository
import flexr.social.app.domain.model.Membership
import flexr.social.app.domain.model.MyProfile
import flexr.social.app.notifications.MessageNotificationScheduler
import flexr.social.app.push.PushTokenRegistrar
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/** Startzustand der App — steuert, welcher Navigationsgraph aktiv ist. */
sealed interface AppState {
    data object Loading : AppState

    data object LoggedOut : AppState

    /**
     * Konto angelegt, aber die Alters- und Identitätsprüfung ist noch nicht
     * bestanden: nur der Verifizierungsablauf. Das ist seit dem 10.09.2026 das
     * einzige Tor vor der App — die Bezahlwand (frueher `Locked`) ist mit der
     * dauerhaft kostenlosen Nutzung entfallen.
     */
    data class NeedsVerification(val profile: MyProfile) : AppState

    data class Ready(val profile: MyProfile, val membership: Membership) : AppState

    /**
     * Beim Start war der Server nicht erreichbar (kein Netz, Zeitueberschreitung,
     * 5xx) - die Sitzung selbst ist aber noch gueltig. Vorher fuehrte dieser
     * Fall auf den Login: Wer die App im Keller-Gym ohne Empfang oeffnete, sah
     * die Anmeldemaske, obwohl sein Token gueltig war - und weil sich
     * `isLoggedIn` dabei nicht aenderte, lud auch spaeteres Netz nichts nach.
     * Blieb nur, sich erneut anzumelden.
     */
    data class Unreachable(val message: String) : AppState
}

/**
 * Hält den app-weiten Sitzungszustand: abgemeldet, in Prüfung oder
 * einsatzbereit. Entspricht der `boot()`/`goToApp()`-Logik des Web-Frontends,
 * hier aber als beobachtbarer Zustand statt als imperativer Bildschirmwechsel.
 */
@HiltViewModel
class MainViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val profileRepository: ProfileRepository,
    private val languageStore: LanguageStore,
    private val billingRepository: BillingRepository,
    private val playBilling: PlayBillingService,
    private val verificationRepository: VerificationRepository,
    private val notificationScheduler: MessageNotificationScheduler,
    private val pushTokenRegistrar: PushTokenRegistrar,
    matchRepository: MatchRepository,
    private val strings: AppStrings,
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

        // 403 "verification_required" mitten in der Sitzung: Die Freischaltung
        // wurde entzogen (neue Prüfung angefordert oder Prüfung endgültig
        // abgelehnt). Sitzung neu bestimmen — loadSession() schaltet dann
        // anhand von isAccountActivated auf NeedsVerification. Ohne das blieb
        // der Nutzer auf dem Deck stehen und sah nur "Zugriff nicht möglich".
        VerificationGate.events
            .onEach { if (_appState.value is AppState.Ready) loadSession() }
            .launchIn(viewModelScope)

        // Die Mitgliedschaft aendert sich auch ohne neuen Anmeldevorgang: nach
        // jedem Like sinkt das Restkontingent, nach einem zurueckgenommenen
        // Swipe steigt es wieder. Ohne diese Beobachtung zeigte die Pille im
        // Kopf den Stand vom App-Start, bis jemand sich neu anmeldet.
        billingRepository.membership
            .filterNotNull()
            .onEach { aktuell ->
                _appState.update { zustand ->
                    if (zustand is AppState.Ready) zustand.copy(membership = aktuell) else zustand
                }
            }
            .launchIn(viewModelScope)
    }

    /**
     * Sprache zwischen Geraet und Profil abgleichen.
     *
     * Wer auf diesem Geraet schon einmal ausdruecklich gewaehlt hat, hat das
     * letzte Wort — die Wahl geht ans Profil. Wer noch nie gewaehlt hat
     * (frische Installation, neues Geraet), uebernimmt, was am Profil steht:
     * Sonst bekaeme jemand, der auf Englisch gestellt hat, auf dem naechsten
     * Geraet wieder Deutsch, obwohl der Server seine Mails laengst auf
     * Englisch schickt.
     */
    private suspend fun syncLanguage(profileLanguage: String) {
        val gewaehlt = languageStore.chosen.first()
        if (gewaehlt != null) {
            profileRepository.reportLanguage(gewaehlt.code)
        } else {
            AppLanguage.fromCode(profileLanguage)
                ?.takeIf { it != AppLanguage.detect() }
                ?.let { languageStore.setLanguage(it) }
        }
    }

    /** Nach Login/Registrierung: Profil und Mitgliedschaft laden. */
    fun loadSession() {
        viewModelScope.launch {
            runCatching {
                val profile = profileRepository.refresh()
                val membership = billingRepository.refresh()
                profile to membership
            }.onSuccess { (profile, membership) ->
                syncLanguage(profile.language)
                _appState.value = when {
                    // Ohne bestandene Prüfung gibt es kein Deck, keine Matches
                    // und keinen Chat. Das ist die einzige Huerde - bezahlen
                    // muss fuer die Nutzung niemand.
                    !profile.isAccountActivated -> {
                        notificationScheduler.cancel()
                        AppState.NeedsVerification(profile)
                    }

                    else -> {
                        notificationScheduler.schedule()
                        AppState.Ready(profile, membership)
                    }
                }
                SessionGate.isReady = true

                // Laufende Play-Kaeufe beim Server nachreichen. Das ist der
                // Weg zurueck aus jeder Stoerung: Wer beim Kauf gerade keine
                // Verbindung hatte, das Geraet gewechselt oder die App neu
                // installiert hat, bekommt sein Premium dadurch von selbst
                // wieder - ohne einen Knopf "Kauf wiederherstellen", den er
                // erst suchen muesste. Laeuft still; wer nichts gekauft hat,
                // merkt davon nichts.
                launch { runCatching { playBilling.bestehendeKaeufeAbgleichen() } }

                // Geraet fuer echte Push-Zustellung anmelden. Bei jedem Start,
                // nicht nur nach dem Anmelden: Firebase vergibt den Token neu,
                // wenn die App neu installiert oder ihre Daten geloescht
                // werden - ohne Nachmelden schickte der Server danach an eine
                // Adresse, die es nicht mehr gibt. Laeuft still; ohne
                // Firebase-Konfiguration passiert nichts.
                launch { runCatching { pushTokenRegistrar.anmelden() } }
            }.onFailure { throwable ->
                val fehler = throwable as? FlexrApiException
                when {
                    // Token ungueltig: Der Interceptor hat bereits abgemeldet,
                    // isLoggedIn wechselt und fuehrt von selbst auf den Login.
                    fehler?.isUnauthorized == true -> {
                        if (_appState.value !is AppState.Ready) markLoggedOut()
                    }
                    // Beim Start oder aus dem Offline-Schirm heraus: angemeldet
                    // bleiben und einen Neuversuch anbieten. Eine laufende
                    // Sitzung (Ready, Pruefung) bleibt bei einem kurzen
                    // Aussetzer dagegen einfach stehen.
                    _appState.value is AppState.Loading || _appState.value is AppState.Unreachable -> {
                        _appState.value = AppState.Unreachable(
                            fehler?.message ?: strings.get(R.string.error_connection),
                        )
                    }
                }
                SessionGate.isReady = true
            }
        }
    }

    /** Nach Rückkehr aus dem Stripe-Checkout: Premium-Status neu holen. */
    fun refreshMembership() = loadSession()

    /**
     * Aktivierungslink aus der Bestätigungsmail (App Link auf
     * https://flexr.social/mail-bestaetigen).
     *
     * Der Token wird eingelöst und danach die Sitzung neu bestimmt - der
     * Verifizierungs-Schirm zeigt sonst weiter "Bestätige deine E-Mail", obwohl
     * die Adresse längst bestätigt ist.
     */
    fun confirmEmailToken(token: String, onResult: (String) -> Unit) {
        viewModelScope.launch {
            runCatching { verificationRepository.confirmEmail(token) }
                .onSuccess { name ->
                    onResult(strings.get(R.string.mail_confirmed, name))
                    loadSession()
                }
                .onFailure { throwable ->
                    onResult(
                        (throwable as? FlexrApiException)?.message
                            ?: strings.get(R.string.mail_confirm_failed),
                    )
                }
        }
    }

    fun logout() {
        viewModelScope.launch {
            notificationScheduler.cancel()
            // Vor dem Abmelden: Danach ist der Sitzungstoken weg, und der
            // Server wuerde die Abmeldung des Geraets nicht mehr annehmen -
            // er bekaeme weiter Nachrichten fuer ein Konto geschickt, das auf
            // diesem Geraet niemand mehr benutzt.
            runCatching { pushTokenRegistrar.abmelden() }
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
