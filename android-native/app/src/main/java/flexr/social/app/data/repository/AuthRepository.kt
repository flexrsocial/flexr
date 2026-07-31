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
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharedFlow
import java.time.LocalDate
import javax.inject.Inject
import javax.inject.Singleton

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

    val isLoggedIn: Flow<Boolean> = sessionStore.isLoggedIn

    /** Feuert, sobald das Backend eine Anmeldung als abgelaufen zurückweist (401). */
    val sessionExpired: SharedFlow<Unit> = sessionExpiryInterceptor.events

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
        consentWithdrawalWaiver: Boolean,
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
                    consentWithdrawalWaiver = consentWithdrawalWaiver,
                ),
            )
        }
        sessionStore.saveToken(response.accessToken)
    }

    suspend fun login(email: String, password: String) {
        val response = apiCall { api.login(LoginRequestDto(email.trim(), password)) }
        sessionStore.saveToken(response.accessToken)
    }

    /** Abmelden: Token verwerfen und den lokalen Cache leeren. */
    suspend fun logout() {
        sessionStore.clear()
        matchDao.deleteAll()
        messageDao.deleteAll()
    }
}
