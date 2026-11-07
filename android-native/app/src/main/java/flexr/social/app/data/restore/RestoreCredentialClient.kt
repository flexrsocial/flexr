package flexr.social.app.data.restore

import android.content.Context
import android.os.Build
import android.util.Log
import androidx.credentials.ClearCredentialStateRequest
import androidx.credentials.CreateRestoreCredentialRequest
import androidx.credentials.CreateRestoreCredentialResponse
import androidx.credentials.CredentialManager
import androidx.credentials.GetCredentialRequest
import androidx.credentials.GetRestoreCredentialOption
import androidx.credentials.RestoreCredential
import androidx.credentials.exceptions.ClearCredentialException
import androidx.credentials.exceptions.CreateCredentialException
import androidx.credentials.exceptions.GetCredentialException
import androidx.credentials.exceptions.NoCredentialException
import androidx.credentials.exceptions.restorecredential.E2eeUnavailableException
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Schmale Hülle um den Credential Manager - nur die drei Aufrufe für den
 * Restore Key. Als Schnittstelle, damit [RestoreKeyManager] ohne Android in
 * reinen JVM-Tests läuft.
 */
interface RestoreCredentialClient {

    /** Restore Credentials gibt es ab Android 9 (API 28) mit Play-Diensten 24.22. */
    val isSupported: Boolean

    /**
     * Legt den Restore Key an und liefert die Registrierungsantwort
     * (WebAuthn-JSON) - oder `null`, wenn das Gerät keinen anlegen kann.
     */
    suspend fun create(requestJson: String): String?

    /**
     * Holt den mitgewanderten Restore Key und lässt die Challenge signieren.
     * `null`, wenn auf dem Gerät keiner liegt.
     *
     * @throws RestoreUnavailableException bei einer vorübergehenden Störung -
     *   dann soll es beim nächsten Start noch einmal versucht werden.
     */
    suspend fun get(requestJson: String): String?

    /** Löscht den Restore Key auf dem Gerät. */
    suspend fun clear()
}

/** Vorübergehend nicht abrufbar (etwa Play-Dienste beschäftigt). */
class RestoreUnavailableException(cause: Throwable) : Exception(cause)

@Singleton
class CredentialManagerRestoreClient @Inject constructor(
    @param:ApplicationContext private val context: Context,
) : RestoreCredentialClient {

    private val credentialManager by lazy { CredentialManager.create(context) }

    override val isSupported: Boolean
        get() = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P

    override suspend fun create(requestJson: String): String? {
        if (!isSupported) return null
        return try {
            createWith(requestJson, cloudBackup = true)
        } catch (e: E2eeUnavailableException) {
            // Kein Google-Backup oder keine Displaysperre: dann wenigstens
            // lokal, damit der Schlüssel bei der Übertragung per Kabel oder
            // WLAN von Gerät zu Gerät mitwandert (Vorgabe von Google).
            try {
                createWith(requestJson, cloudBackup = false)
            } catch (e: CreateCredentialException) {
                Log.i(TAG, "Restore Key nicht angelegt: ${e.type}")
                null
            }
        } catch (e: CreateCredentialException) {
            Log.i(TAG, "Restore Key nicht angelegt: ${e.type}")
            null
        }
    }

    private suspend fun createWith(requestJson: String, cloudBackup: Boolean): String {
        val response = credentialManager.createCredential(
            context,
            CreateRestoreCredentialRequest(requestJson, cloudBackup),
        )
        return (response as CreateRestoreCredentialResponse).responseJson
    }

    override suspend fun get(requestJson: String): String? {
        if (!isSupported) return null
        return try {
            // Bewusst als einzige Option: Zusammen mit anderen wirft der
            // Credential Manager IllegalArgumentException.
            val response = credentialManager.getCredential(
                context,
                GetCredentialRequest(listOf(GetRestoreCredentialOption(requestJson))),
            )
            (response.credential as? RestoreCredential)?.authenticationResponseJson
        } catch (e: NoCredentialException) {
            null
        } catch (e: GetCredentialException) {
            // Fehlender Anbieter (keine Play-Dienste, zu alt) ist endgültig,
            // alles andere ein Fall für den nächsten Start.
            if (e is androidx.credentials.exceptions.GetCredentialProviderConfigurationException ||
                e is androidx.credentials.exceptions.GetCredentialUnsupportedException
            ) {
                null
            } else {
                throw RestoreUnavailableException(e)
            }
        }
    }

    override suspend fun clear() {
        if (!isSupported) return
        try {
            credentialManager.clearCredentialState(
                ClearCredentialStateRequest(ClearCredentialStateRequest.TYPE_CLEAR_RESTORE_CREDENTIAL),
            )
        } catch (e: ClearCredentialException) {
            Log.i(TAG, "Restore Key nicht geloescht: ${e.type}")
        }
    }

    private companion object {
        const val TAG = "RestoreKey"
    }
}
