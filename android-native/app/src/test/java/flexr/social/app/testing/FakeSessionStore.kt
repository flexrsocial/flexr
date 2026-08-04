package flexr.social.app.testing

import flexr.social.app.data.session.SessionStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map

/**
 * [SessionStore] im Arbeitsspeicher — dieselbe Semantik wie die
 * DataStore-Fassung, aber ohne Android-Context.
 */
class FakeSessionStore(
    initialToken: String? = "test-token",
) : SessionStore {

    private val tokenState = MutableStateFlow(initialToken)
    private val userIdState = MutableStateFlow<String?>(null)
    private val notificationsState = MutableStateFlow(true)
    private val verifiedHintState = MutableStateFlow(false)
    private var lastNotifiedId: String? = null

    override val token: Flow<String?> = tokenState
    override val isLoggedIn: Flow<Boolean> = tokenState.map { !it.isNullOrBlank() }
    override val userId: Flow<String?> = userIdState
    override val notificationsEnabled: Flow<Boolean> = notificationsState
    override val verifiedHintDismissed: Flow<Boolean> = verifiedHintState

    override suspend fun setVerifiedHintDismissed() {
        verifiedHintState.value = true
    }

    override suspend fun currentToken(): String? = tokenState.value

    override suspend fun saveToken(token: String) {
        tokenState.value = token
    }

    override suspend fun saveUserId(userId: String) {
        userIdState.value = userId
    }

    override suspend fun clear() {
        tokenState.value = null
        userIdState.value = null
        lastNotifiedId = null
        // Geräte-ID bleibt erhalten — wie in der echten Umsetzung.
        verifiedHintState.value = false
    }

    override suspend fun setNotificationsEnabled(enabled: Boolean) {
        notificationsState.value = enabled
    }

    override suspend fun lastNotifiedMessageId(): String? = lastNotifiedId

    override suspend fun setLastNotifiedMessageId(id: String) {
        lastNotifiedId = id
    }

    override suspend fun deviceId(): String = "test-device-id"
}
