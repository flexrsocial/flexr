package flexr.social.app.data.session

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

private val Context.sessionDataStore: DataStore<Preferences> by preferencesDataStore(name = "flexr_session")

/**
 * Sitzungszustand der App: JWT, stabile Geräte-ID und Nutzereinstellungen.
 *
 * Ersetzt den `localStorage` der Web-App. Bewusst DataStore statt Room —
 * es sind wenige Schlüssel-Wert-Paare, keine relationalen Daten.
 * Vom Cloud-Backup ausgenommen (siehe res/xml/data_extraction_rules.xml).
 */
@Singleton
class SessionStore @Inject constructor(
    @ApplicationContext private val context: Context,
) {

    private object Keys {
        val TOKEN = stringPreferencesKey("access_token")
        val DEVICE_ID = stringPreferencesKey("device_id")
        val USER_ID = stringPreferencesKey("user_id")
        val NOTIFICATIONS_ENABLED = booleanPreferencesKey("notifications_enabled")
        val LAST_NOTIFIED_MESSAGE = stringPreferencesKey("last_notified_message_id")
        val VERIFIED_HINT_DISMISSED = booleanPreferencesKey("verified_hint_dismissed")
    }

    val token: Flow<String?> = context.sessionDataStore.data.map { it[Keys.TOKEN] }

    val isLoggedIn: Flow<Boolean> = token.map { !it.isNullOrBlank() }

    val userId: Flow<String?> = context.sessionDataStore.data.map { it[Keys.USER_ID] }

    val notificationsEnabled: Flow<Boolean> =
        context.sessionDataStore.data.map { it[Keys.NOTIFICATIONS_ENABLED] ?: true }

    /** Ob der Hinweis „Dein Profil ist verifiziert" bereits bestätigt wurde. */
    val verifiedHintDismissed: Flow<Boolean> =
        context.sessionDataStore.data.map { it[Keys.VERIFIED_HINT_DISMISSED] ?: false }

    suspend fun setVerifiedHintDismissed() {
        context.sessionDataStore.edit { it[Keys.VERIFIED_HINT_DISMISSED] = true }
    }

    suspend fun currentToken(): String? = context.sessionDataStore.data.first()[Keys.TOKEN]

    suspend fun saveToken(token: String) {
        context.sessionDataStore.edit { it[Keys.TOKEN] = token }
    }

    suspend fun saveUserId(userId: String) {
        context.sessionDataStore.edit { it[Keys.USER_ID] = userId }
    }

    suspend fun clear() {
        context.sessionDataStore.edit { prefs ->
            prefs.remove(Keys.TOKEN)
            prefs.remove(Keys.USER_ID)
            prefs.remove(Keys.LAST_NOTIFIED_MESSAGE)
            // Bestätigter Hinweis gilt pro Konto — beim Abmelden zurücksetzen.
            prefs.remove(Keys.VERIFIED_HINT_DISMISSED)
            // Die Geräte-ID bleibt bewusst erhalten: sie ist an das Gerät gebunden
            // (Mehrfachkonto-Erkennung / Ban-Evasion-Schutz im Backend) und darf
            // sich durch ein simples Ausloggen nicht ändern.
        }
    }

    suspend fun setNotificationsEnabled(enabled: Boolean) {
        context.sessionDataStore.edit { it[Keys.NOTIFICATIONS_ENABLED] = enabled }
    }

    suspend fun lastNotifiedMessageId(): String? =
        context.sessionDataStore.data.first()[Keys.LAST_NOTIFIED_MESSAGE]

    suspend fun setLastNotifiedMessageId(id: String) {
        context.sessionDataStore.edit { it[Keys.LAST_NOTIFIED_MESSAGE] = id }
    }

    /**
     * Stabile, zufällige Geräte-ID — entspricht `flexr_device_id` im Web und
     * erfüllt das vom Backend erwartete Format `^[A-Za-z0-9-]{8,64}$`.
     * Bewusst keine Hardware-Kennung (ANDROID_ID o. Ä.): die ID ist nicht
     * geräteübergreifend rückverfolgbar und wird beim Deinstallieren gelöscht.
     */
    suspend fun deviceId(): String {
        context.sessionDataStore.data.first()[Keys.DEVICE_ID]?.let { return it }
        val generated = UUID.randomUUID().toString()
        context.sessionDataStore.edit { it[Keys.DEVICE_ID] = generated }
        return generated
    }
}
