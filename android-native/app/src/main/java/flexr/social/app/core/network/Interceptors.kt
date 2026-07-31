package flexr.social.app.core.network

import flexr.social.app.data.session.SessionStore
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Hängt Bearer-Token und Geräte-ID an jeden Request — dieselben Header wie im
 * Web (`Authorization`, `X-Device-Id`). Presigned-Uploads in den Objekt-Storage
 * werden ausgenommen: dort würde ein fremder Authorization-Header die
 * S3-Signatur ungültig machen.
 */
@Singleton
class AuthHeaderInterceptor @Inject constructor(
    private val sessionStore: SessionStore,
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val isOwnBackend = request.url.encodedPath.startsWith("/api/")
        if (!isOwnBackend) return chain.proceed(request)

        val builder = request.newBuilder()
        runBlocking {
            sessionStore.currentToken()?.let { builder.header("Authorization", "Bearer $it") }
            builder.header("X-Device-Id", sessionStore.deviceId())
        }
        return chain.proceed(builder.build())
    }
}

/**
 * Meldet abgelaufene Sitzungen zentral: bei 401 wird der Token verworfen und
 * die App über [events] zurück auf den Login geführt. Entspricht dem
 * 401-Zweig der `api()`-Funktion im Web-Frontend.
 */
@Singleton
class SessionExpiryInterceptor @Inject constructor(
    private val sessionStore: SessionStore,
) : Interceptor {

    private val _events = MutableSharedFlow<Unit>(
        replay = 0,
        extraBufferCapacity = 1,
        onBufferOverflow = BufferOverflow.DROP_OLDEST,
    )
    val events: SharedFlow<Unit> = _events

    override fun intercept(chain: Interceptor.Chain): Response {
        val response = chain.proceed(chain.request())
        val isOwnBackend = chain.request().url.encodedPath.startsWith("/api/")
        val isLoginAttempt = chain.request().url.encodedPath.startsWith("/api/auth/")
        if (response.code == 401 && isOwnBackend && !isLoginAttempt) {
            runBlocking { sessionStore.clear() }
            _events.tryEmit(Unit)
        }
        return response
    }
}
