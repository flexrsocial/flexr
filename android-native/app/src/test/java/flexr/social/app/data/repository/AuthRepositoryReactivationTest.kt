package flexr.social.app.data.repository

import flexr.social.app.core.network.SessionExpiryInterceptor
import flexr.social.app.data.remote.dto.LoginRequestDto
import flexr.social.app.data.remote.dto.TokenResponseDto
import flexr.social.app.testing.FakeFlexrApi
import flexr.social.app.testing.FakeMatchDao
import flexr.social.app.testing.FakeMessageDao
import flexr.social.app.testing.FakeSessionStore
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * Entspricht routers/auth.reactivate: dieselben Zugangsdaten wie beim Login,
 * bei Erfolg wird das Token wie nach einem normalen Login gespeichert.
 */
class AuthRepositoryReactivationTest {

    private fun repository(api: FakeFlexrApi, sessionStore: FakeSessionStore) = AuthRepository(
        api = api,
        sessionStore = sessionStore,
        matchDao = FakeMatchDao(),
        messageDao = FakeMessageDao(),
        sessionExpiryInterceptor = SessionExpiryInterceptor(sessionStore),
    )

    @Test
    fun `reactivate speichert das neue Token`() = runTest {
        var receivedBody: LoginRequestDto? = null
        val api = object : FakeFlexrApi() {
            override suspend fun reactivate(body: LoginRequestDto): TokenResponseDto {
                receivedBody = body
                return TokenResponseDto(accessToken = "reaktiviertes-token")
            }
        }
        val sessionStore = FakeSessionStore(initialToken = null)
        val repository = repository(api, sessionStore)

        repository.reactivate(" gelöscht@example.com ", "supersecret123")

        assertEquals("gelöscht@example.com", receivedBody?.email)
        assertEquals("supersecret123", receivedBody?.password)
        assertEquals("reaktiviertes-token", sessionStore.currentToken())
    }

    @Test
    fun `fehlgeschlagene Reaktivierung speichert kein Token`() = runTest {
        val api = object : FakeFlexrApi() {
            override suspend fun reactivate(body: LoginRequestDto): TokenResponseDto =
                error("Falsches Passwort.")
        }
        val sessionStore = FakeSessionStore(initialToken = null)
        val repository = repository(api, sessionStore)

        runCatching { repository.reactivate("gelöscht@example.com", "falsch") }

        assertNull(sessionStore.currentToken())
    }
}
