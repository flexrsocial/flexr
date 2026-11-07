package flexr.social.app.data.restore

import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.remote.dto.OkResponseDto
import flexr.social.app.data.remote.dto.RestoreKeyDeleteRequestDto
import flexr.social.app.data.remote.dto.RestoreKeyLoginRequestDto
import flexr.social.app.data.remote.dto.RestoreKeyOptionsDto
import flexr.social.app.data.remote.dto.RestoreKeyRegisterRequestDto
import flexr.social.app.data.remote.dto.RestoreKeyRegisterResponseDto
import flexr.social.app.data.remote.dto.TokenResponseDto
import flexr.social.app.testing.FakeFlexrApi
import flexr.social.app.testing.FakeSessionStore
import java.io.IOException
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Restore Key: anlegen nach dem Anmelden, still einloesen auf dem neuen Geraet,
 * verwerfen beim Abmelden (Gegenstueck: backend/tests/test_restore_keys.py).
 */
class RestoreKeyManagerTest {

    private class FakeClient(
        override val isSupported: Boolean = true,
        var createResult: String? = "registrierung",
        var getResult: () -> String? = { "assertion" },
    ) : RestoreCredentialClient {
        val created = mutableListOf<String>()
        var cleared = 0

        override suspend fun create(requestJson: String): String? {
            created += requestJson
            return createResult
        }

        override suspend fun get(requestJson: String): String? = getResult()

        override suspend fun clear() {
            cleared++
        }
    }

    private open class Api : FakeFlexrApi() {
        val registered = mutableListOf<String>()
        val deleted = mutableListOf<RestoreKeyDeleteRequestDto>()
        var loginResult: () -> TokenResponseDto = { TokenResponseDto("wiederhergestellt") }

        override suspend fun restoreKeyOptions() = RestoreKeyOptionsDto("{\"create\":1}")

        override suspend fun registerRestoreKey(body: RestoreKeyRegisterRequestDto): RestoreKeyRegisterResponseDto {
            registered += body.registrationResponseJson
            return RestoreKeyRegisterResponseDto("cred-${registered.size}")
        }

        override suspend fun deleteRestoreKey(body: RestoreKeyDeleteRequestDto): OkResponseDto {
            deleted += body
            return OkResponseDto()
        }

        override suspend fun restoreKeyLoginOptions() = RestoreKeyOptionsDto("{\"get\":1}")

        override suspend fun restoreKeyLogin(body: RestoreKeyLoginRequestDto): TokenResponseDto {
            assertEquals("assertion", body.authenticationResponseJson)
            return loginResult()
        }
    }

    private fun manager(api: Api, store: FakeSessionStore, client: FakeClient, jetzt: Long = 1_000_000L) =
        RestoreKeyManager(api, store, client).also { it.now = { jetzt } }

    // ---------- anlegen ----------

    @Test
    fun `legt nach dem Anmelden einen Schluessel an`() = runTest {
        val api = Api()
        val store = FakeSessionStore()
        val client = FakeClient()

        manager(api, store, client).ensureKey()

        assertEquals(listOf("{\"create\":1}"), client.created)
        assertEquals(listOf("registrierung"), api.registered)
        assertEquals("cred-1", store.restoreKeyId)
        assertEquals(1_000_000L, store.restoreKeySyncedAt)
    }

    @Test
    fun `frischer Schluessel wird nicht bei jedem Start neu angelegt`() = runTest {
        val api = Api()
        val store = FakeSessionStore().apply { saveRestoreKey("cred-alt", 1_000_000L) }
        val client = FakeClient()

        manager(api, store, client, jetzt = 1_000_000L + RestoreKeyManager.ROTATE_AFTER_MS - 1).ensureKey()

        assertTrue(client.created.isEmpty())
        assertEquals("cred-alt", store.restoreKeyId)
    }

    @Test
    fun `nach 30 Tagen wird der Schluessel erneuert`() = runTest {
        val api = Api()
        val store = FakeSessionStore().apply { saveRestoreKey("cred-alt", 1_000_000L) }
        val client = FakeClient()
        val jetzt = 1_000_000L + RestoreKeyManager.ROTATE_AFTER_MS

        manager(api, store, client, jetzt).ensureKey()

        assertEquals("cred-1", store.restoreKeyId)
        assertEquals(jetzt, store.restoreKeySyncedAt)
    }

    @Test
    fun `ohne Sitzung wird nichts angelegt`() = runTest {
        val client = FakeClient()
        manager(Api(), FakeSessionStore(initialToken = null), client).ensureKey()
        assertTrue(client.created.isEmpty())
    }

    @Test
    fun `kann das Geraet keinen anlegen, bleibt alles still`() = runTest {
        val api = Api()
        val store = FakeSessionStore()

        manager(api, store, FakeClient(createResult = null)).ensureKey()
        manager(api, store, FakeClient(isSupported = false)).ensureKey()

        assertTrue(api.registered.isEmpty())
        assertNull(store.restoreKeyId)
    }

    @Test
    fun `Serverfehler beim Anlegen wirft nicht`() = runTest {
        val api = object : Api() {
            override suspend fun registerRestoreKey(body: RestoreKeyRegisterRequestDto): RestoreKeyRegisterResponseDto =
                throw FlexrApiException(400, "Wiederherstellungsschlüssel ungültig.")
        }
        val store = FakeSessionStore()

        manager(api, store, FakeClient()).ensureKey()

        assertNull(store.restoreKeyId)
    }

    @Test
    fun `nach dem Passwortwechsel wird sofort ein neuer angelegt`() = runTest {
        val api = Api()
        val store = FakeSessionStore().apply { saveRestoreKey("cred-alt", 1_000_000L) }

        manager(api, store, FakeClient()).renew()

        assertEquals("cred-1", store.restoreKeyId)
    }

    // ---------- einloesen ----------

    @Test
    fun `erster Start auf dem neuen Geraet meldet still an`() = runTest {
        val store = FakeSessionStore(initialToken = null)

        val angemeldet = manager(Api(), store, FakeClient()).restoreSession()

        assertTrue(angemeldet)
        assertEquals("wiederhergestellt", store.currentToken())
        assertTrue(store.restoreAttempted)
    }

    @Test
    fun `ohne mitgewanderten Schluessel bleibt es bei der Anmeldemaske`() = runTest {
        val store = FakeSessionStore(initialToken = null)

        assertFalse(manager(Api(), store, FakeClient(getResult = { null })).restoreSession())
        assertNull(store.currentToken())
        // nicht bei jedem Start erneut fragen
        assertTrue(store.restoreAttempted)
    }

    @Test
    fun `nach einem Versuch wird nicht erneut gefragt`() = runTest {
        val store = FakeSessionStore(initialToken = null).apply { setRestoreAttempted() }
        val api = object : Api() {
            override suspend fun restoreKeyLoginOptions(): RestoreKeyOptionsDto = error("nicht erwartet")
        }
        assertFalse(manager(api, store, FakeClient()).restoreSession())
    }

    @Test
    fun `mit Sitzung wird nichts eingeloest`() = runTest {
        val store = FakeSessionStore(initialToken = "schon-da")
        assertFalse(manager(Api(), store, FakeClient()).restoreSession())
        assertEquals("schon-da", store.currentToken())
        assertFalse(store.restoreAttempted)
    }

    @Test
    fun `verworfener Schluessel wird auch auf dem Geraet geloescht`() = runTest {
        val api = Api().apply {
            loginResult = { throw FlexrApiException(401, "Automatische Anmeldung nicht möglich.", code = "restore_key_invalid") }
        }
        val store = FakeSessionStore(initialToken = null)
        val client = FakeClient()

        assertFalse(manager(api, store, client).restoreSession())

        assertNull(store.currentToken())
        assertEquals(1, client.cleared)
        assertTrue(store.restoreAttempted)
    }

    @Test
    fun `ohne Netz wird es beim naechsten Start erneut versucht`() = runTest {
        val api = object : Api() {
            override suspend fun restoreKeyLoginOptions(): RestoreKeyOptionsDto = throw IOException("offline")
        }
        val store = FakeSessionStore(initialToken = null)

        assertFalse(manager(api, store, FakeClient()).restoreSession())
        assertFalse(store.restoreAttempted)
    }

    @Test
    fun `voruebergehend gestoerte Play-Dienste - naechster Start versucht es erneut`() = runTest {
        val store = FakeSessionStore(initialToken = null)
        val client = FakeClient(getResult = { throw RestoreUnavailableException(RuntimeException("busy")) })

        assertFalse(manager(Api(), store, client).restoreSession())
        assertFalse(store.restoreAttempted)
    }

    @Test
    fun `haengt der Credential Manager, haelt der Start nicht ewig an`() = runTest {
        val store = FakeSessionStore(initialToken = null)
        val client = object : RestoreCredentialClient {
            override val isSupported = true
            override suspend fun create(requestJson: String): String? = null
            override suspend fun get(requestJson: String): String? {
                delay(RestoreKeyManager.RESTORE_TIMEOUT_MS * 2)
                return "assertion"
            }
            override suspend fun clear() = Unit
        }

        assertFalse(RestoreKeyManager(Api(), store, client).restoreSession())
        assertNull(store.currentToken())
        assertFalse(store.restoreAttempted)
    }

    // ---------- verwerfen ----------

    @Test
    fun `Abmelden verwirft den Schluessel beim Server und auf dem Geraet`() = runTest {
        val api = Api()
        val store = FakeSessionStore().apply { saveRestoreKey("cred-7", 1L) }
        val client = FakeClient()

        manager(api, store, client).forget()

        assertEquals(listOf(RestoreKeyDeleteRequestDto("cred-7")), api.deleted)
        assertEquals(1, client.cleared)
        assertNull(store.restoreKeyId)
        assertNull(store.restoreKeySyncedAt)
    }

    @Test
    fun `abgelaufene Sitzung - nur auf dem Geraet loeschen`() = runTest {
        val api = Api()
        val store = FakeSessionStore(initialToken = null).apply { saveRestoreKey("cred-7", 1L) }
        val client = FakeClient()

        manager(api, store, client).forget()

        assertTrue(api.deleted.isEmpty())
        assertEquals(1, client.cleared)
        assertNull(store.restoreKeyId)
    }

    @Test
    fun `Server nicht erreichbar - Geraet wird trotzdem bereinigt`() = runTest {
        val api = object : Api() {
            override suspend fun deleteRestoreKey(body: RestoreKeyDeleteRequestDto): OkResponseDto =
                throw IOException("offline")
        }
        val store = FakeSessionStore().apply { saveRestoreKey("cred-7", 1L) }
        val client = FakeClient()

        manager(api, store, client).forget()

        assertEquals(1, client.cleared)
        assertNull(store.restoreKeyId)
    }

    @Test
    fun `Abmelden leert die Restore-Markierung, nicht aber den Versuchsmerker`() = runTest {
        val store = FakeSessionStore().apply {
            saveRestoreKey("cred-7", 1L)
            setRestoreAttempted()
        }
        store.clear()
        assertNull(store.restoreKeyId)
        assertTrue(store.restoreAttempted)
    }
}
