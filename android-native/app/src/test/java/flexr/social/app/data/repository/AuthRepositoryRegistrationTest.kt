package flexr.social.app.data.repository

import app.cash.turbine.test
import flexr.social.app.core.network.SessionExpiryInterceptor
import flexr.social.app.testing.FakeMatchDao
import flexr.social.app.testing.FakeMessageDao
import flexr.social.app.testing.FakeFlexrApi
import flexr.social.app.testing.FakeSessionStore
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Während der Registrierung liegt das Token schon vor, die Profilfotos aber
 * noch nicht.
 *
 * Wer in diesem Moment als „angemeldet" gilt, wird vom MainViewModel sofort auf
 * den Verifizierungsschirm geschickt - und der Server lehnt den Start dann mit
 * „Lade zuerst mindestens ein Profilfoto hoch" ab, obwohl der Upload eine
 * Sekunde später durch ist. Genau dieses Fenster hält der Test zu.
 */
class AuthRepositoryRegistrationTest {

    private fun repository(sessionStore: FakeSessionStore) = AuthRepository(
        api = FakeFlexrApi(),
        sessionStore = sessionStore,
        matchDao = FakeMatchDao(),
        messageDao = FakeMessageDao(),
        sessionExpiryInterceptor = SessionExpiryInterceptor(sessionStore),
    )

    @Test
    fun `angemeldet erst wenn die Registrierung samt Fotos durch ist`() = runTest {
        val sessionStore = FakeSessionStore(initialToken = null)
        val repository = repository(sessionStore)

        repository.isLoggedIn.test {
            assertFalse(awaitItem())

            // register() speichert das Token - der Upload läuft aber noch.
            repository.beginRegistration()
            sessionStore.saveToken("frisches-token")
            expectNoEvents()

            repository.finishRegistration()
            assertTrue(awaitItem())
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun `ein gespeichertes Token gilt ohne laufende Registrierung sofort`() = runTest {
        val repository = repository(FakeSessionStore(initialToken = "altes-token"))

        repository.isLoggedIn.test {
            assertTrue(awaitItem())
            cancelAndIgnoreRemainingEvents()
        }
    }
}
