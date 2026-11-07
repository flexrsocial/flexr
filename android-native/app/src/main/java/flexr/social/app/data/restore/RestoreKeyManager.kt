package flexr.social.app.data.restore

import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.RestoreKeyDeleteRequestDto
import flexr.social.app.data.remote.dto.RestoreKeyLoginRequestDto
import flexr.social.app.data.remote.dto.RestoreKeyRegisterRequestDto
import flexr.social.app.data.session.SessionStore
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.withTimeoutOrNull
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Anmeldung nach dem Gerätewechsel per Restore Key (Credential Manager,
 * "Restore Credentials"). Google Play verlangt ab April 2027, dass ein
 * eingeloggter Nutzer nach der Übertragung auf ein neues Gerät - per Kabel,
 * WLAN oder Cloud-Backup - ohne erneute Anmeldung eingeloggt ist.
 *
 * Drei Stationen, Gegenstück auf dem Server ist backend/app/restore_keys.py:
 *
 * 1. [ensureKey] - nach jeder erfolgreichen Sitzungsbestimmung (Login,
 *    Registrierung, App-Start mit Sitzung): Fehlt der Schlüssel oder ist er
 *    älter als [ROTATE_AFTER_MS], wird still ein neuer angelegt. Der Server
 *    verwirft Schlüssel nach 90 Tagen; wer FLEXR regelmäßig öffnet, hat
 *    deshalb immer einen gültigen.
 * 2. [restoreSession] - beim ersten Start ohne Token: mitgewanderten
 *    Schlüssel holen, Challenge signieren lassen, gegen ein Token tauschen.
 *    Die App-Daten selbst wandern bewusst nicht mit
 *    (res/xml/data_extraction_rules.xml); der Schlüssel tut es unabhängig
 *    davon über die Play-Dienste.
 * 3. [forget] - Abmelden und Kontolöschung: Schlüssel beim Server und auf dem
 *    Gerät verwerfen, sonst wäre man beim nächsten Start still wieder drin.
 *
 * Nichts davon darf den Nutzer stören: Jeder Fehler endet still, im
 * schlimmsten Fall sieht er die Anmeldemaske wie bisher.
 */
@Singleton
class RestoreKeyManager @Inject constructor(
    private val api: FlexrApi,
    private val sessionStore: SessionStore,
    private val client: RestoreCredentialClient,
) {

    /** Uhr für die Tests austauschbar. */
    internal var now: () -> Long = System::currentTimeMillis

    private val ensureLock = Mutex()

    /**
     * Restore Key anlegen, falls keiner da oder er fällig ist. Läuft
     * höchstens einmal gleichzeitig (loadSession kann mehrfach feuern).
     */
    suspend fun ensureKey() {
        if (!client.isSupported) return
        if (!ensureLock.tryLock()) return
        try {
            if (sessionStore.currentToken().isNullOrBlank()) return
            val syncedAt = sessionStore.restoreKeySyncedAt()
            val fresh = syncedAt != null &&
                sessionStore.restoreKeyCredentialId() != null &&
                now() - syncedAt in 0 until ROTATE_AFTER_MS
            if (fresh) return

            val options = apiCall { api.restoreKeyOptions() }
            val registration = client.create(options.requestJson) ?: return
            val stored = apiCall {
                api.registerRestoreKey(RestoreKeyRegisterRequestDto(registration))
            }
            sessionStore.saveRestoreKey(stored.credentialId, now())
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            // Kein Netz, Server lehnt ab, Credential Manager streikt: beim
            // nächsten Start wieder. Niemand soll davon etwas merken.
        } finally {
            ensureLock.unlock()
        }
    }

    /** Nach einem Passwortwechsel in der App: Der Server hat alle Schlüssel verworfen. */
    suspend fun renew() {
        sessionStore.clearRestoreKey()
        ensureKey()
    }

    /**
     * Stille Anmeldung auf dem neuen Gerät. Nur ohne Token und nur, solange es
     * auf diesem Gerät noch nicht versucht wurde - nach einem Abmelden fragt
     * die App nicht bei jedem Start erneut.
     *
     * @return `true`, wenn danach ein Token gespeichert ist.
     */
    suspend fun restoreSession(): Boolean {
        if (!client.isSupported) return false
        if (!sessionStore.currentToken().isNullOrBlank()) return false
        if (sessionStore.restoreAttempted()) return false

        val outcome = withTimeoutOrNull(RESTORE_TIMEOUT_MS) { attemptRestore() } ?: Outcome.RETRY
        if (outcome != Outcome.RETRY) sessionStore.setRestoreAttempted()
        return outcome == Outcome.SIGNED_IN
    }

    private enum class Outcome { SIGNED_IN, NOTHING_TO_RESTORE, RETRY }

    private suspend fun attemptRestore(): Outcome {
        return try {
            val options = apiCall { api.restoreKeyLoginOptions() }
            val assertion = client.get(options.requestJson) ?: return Outcome.NOTHING_TO_RESTORE
            val token = try {
                apiCall { api.restoreKeyLogin(RestoreKeyLoginRequestDto(assertion)) }
            } catch (e: FlexrApiException) {
                if (e.statusCode in 400..499) {
                    // Schlüssel verworfen (Abmelden, Passwortwechsel,
                    // Kontolöschung) oder Konto gesperrt: Den toten Schlüssel
                    // nicht weiter mitschleppen.
                    client.clear()
                    return Outcome.NOTHING_TO_RESTORE
                }
                throw e
            }
            sessionStore.saveToken(token.accessToken)
            Outcome.SIGNED_IN
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            Outcome.RETRY
        }
    }

    /**
     * Abmelden oder Kontolöschung. Muss laufen, solange das Token noch da ist
     * - danach nähme der Server den Auftrag nicht mehr an. Bei abgelaufener
     * Sitzung (401) ist es schon weg; dann bleibt der Schlüssel beim Server
     * liegen, bis er nach 90 Tagen verfällt, und wird hier nur auf dem Gerät
     * gelöscht.
     */
    suspend fun forget() {
        val credentialId = sessionStore.restoreKeyCredentialId()
        if (!sessionStore.currentToken().isNullOrBlank()) {
            runCatching {
                apiCall { api.deleteRestoreKey(RestoreKeyDeleteRequestDto(credentialId)) }
            }
        }
        runCatching { client.clear() }
        sessionStore.clearRestoreKey()
    }

    companion object {
        /** Schlüssel nach so langer Zeit erneuern (Server verwirft nach 90 Tagen). */
        const val ROTATE_AFTER_MS = 30L * 24 * 60 * 60 * 1000

        /** Länger hält der erste Start den Startbildschirm nicht auf. */
        const val RESTORE_TIMEOUT_MS = 10_000L
    }
}
