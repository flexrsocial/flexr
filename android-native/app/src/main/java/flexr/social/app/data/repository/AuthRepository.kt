package flexr.social.app.data.repository

import flexr.social.app.core.network.SessionExpiryInterceptor
import flexr.social.app.core.network.apiCall
import flexr.social.app.data.local.MatchDao
import flexr.social.app.data.local.MessageDao
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.LoginRequestDto
import flexr.social.app.data.remote.dto.RegisterRequestDto
import flexr.social.app.data.session.SessionStore
import flexr.social.app.domain.model.Gender
import java.time.LocalDate
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged

/**
 * Registrierung, Anmeldung und Sitzungsende.
 *
 * Entspricht backend/app/routers/auth.py. Das Feld „interessiert an" gibt es
 * bewusst nicht: das Backend leitet es gegengeschlechtlich aus dem Geschlecht
 * ab (Produktentscheidung), die App bildet das genauso ab.
 */
@Singleton
class AuthRepository @Inject constructor(
    private val api: FlexrApi,
    private val sessionStore: SessionStore,
    private val matchDao: MatchDao,
    private val messageDao: MessageDao,
    sessionExpiryInterceptor: SessionExpiryInterceptor,
) {

    /**
     * Läuft gerade eine Registrierung samt Erstupload der Profilfotos?
     *
     * Das Token wird schon von `register()` gespeichert, die Fotos gehen aber
     * erst danach raus - dazwischen ist das Konto zwar angemeldet, hat aber
     * noch kein Foto. Wer in diesem Moment auf den Verifizierungsschirm
     * geschickt wird, bekommt vom Server ein 400 („Lade zuerst mindestens ein
     * Profilfoto hoch"), obwohl gleich alles da ist.
     */
    private val registrationInFlight = MutableStateFlow(false)

    /**
     * Angemeldet **und** einsatzbereit. Während der Registrierung bleibt das
     * bewusst `false`, bis die Fotos oben sind - siehe [registrationInFlight].
     */
    val isLoggedIn: Flow<Boolean> =
        combine(sessionStore.isLoggedIn, registrationInFlight) { loggedIn, inFlight ->
            loggedIn && !inFlight
        }.distinctUntilChanged()

    /** Feuert, sobald das Backend eine Anmeldung als abgelaufen zurückweist (401). */
    val sessionExpired: SharedFlow<Unit> = sessionExpiryInterceptor.events

    /** Klammer um Registrierung + Erstupload. Immer mit `try`/`finally` benutzen. */
    fun beginRegistration() { registrationInFlight.value = true }

    fun finishRegistration() { registrationInFlight.value = false }

    suspend fun register(
        email: String,
        password: String,
        name: String,
        birthdate: LocalDate,
        plz: String,
        city: String,
        gender: Gender,
        gymLabel: String,
        bio: String?,
        consentSensitiveData: Boolean,
        /**
         * Sprache, in der gerade registriert wird ("de" oder "en").
         *
         * Kommt als Parameter statt aus dem `core.locale.LanguageStore`:
         * Dieses Repository
         * soll ohne Android-Context auskommen, damit es sich in den
         * Einheitstests ohne Rahmenwerk bauen laesst.
         */
        language: String,
    ) {
        val response = apiCall {
            api.register(
                RegisterRequestDto(
                    email = email.trim(),
                    password = password,
                    name = name.trim(),
                    birthdate = birthdate.toString(),
                    plz = plz.trim(),
                    city = city.trim(),
                    gender = gender.apiValue,
                    gym = gymLabel,
                    bio = bio?.trim()?.takeIf { it.isNotEmpty() },
                    consentSensitiveData = consentSensitiveData,
                    // Die Sprache, in der gerade registriert wird. Der Server
                    // merkt sie am Profil und schreibt seine Mails danach -
                    // sie entstehen zum Teil ohne die App (Tagesjob,
                    // Stripe-Webhook, Moderation) und koennen die Einstellung
                    // nirgends sonst nachlesen.
                    language = language,
                ),
            )
        }
        sessionStore.saveToken(response.accessToken)
    }

    suspend fun login(email: String, password: String) {
        val response = apiCall { api.login(LoginRequestDto(email.trim(), password)) }
        sessionStore.saveToken(response.accessToken)
    }

    /**
     * Macht eine Selbstlöschung innerhalb der 30-Tage-Karenzzeit rückgängig und
     * meldet gleich an. Nimmt dieselben Zugangsdaten wie [login] entgegen.
     */
    suspend fun reactivate(email: String, password: String) {
        val response = apiCall { api.reactivate(LoginRequestDto(email.trim(), password)) }
        sessionStore.saveToken(response.accessToken)
    }

    /** Abmelden: Token verwerfen und den lokalen Cache leeren. */
    suspend fun logout() {
        sessionStore.clear()
        matchDao.deleteAll()
        messageDao.deleteAll()
    }
}
