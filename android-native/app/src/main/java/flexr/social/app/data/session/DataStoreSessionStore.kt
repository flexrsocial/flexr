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
 * [SessionStore] auf Basis von DataStore. Bewusst DataStore statt Room —
 * es sind wenige Schlüssel-Wert-Paare, keine relationalen Daten.
 * Vom Cloud-Backup ausgenommen (siehe res/xml/data_extraction_rules.xml).
 */
@Singleton
class DataStoreSessionStore @Inject constructor(
    @ApplicationContext private val context: Context,
) : SessionStore {

    private object Keys {
        val TOKEN = stringPreferencesKey("access_token")
        val DEVICE_ID = stringPreferencesKey("device_id")
        val USER_ID = stringPreferencesKey("user_id")
        val NOTIFICATIONS_ENABLED = booleanPreferencesKey("notifications_enabled")
        val LAST_NOTIFIED_MESSAGE = stringPreferencesKey("last_notified_message_id")
        val VERIFIED_HINT_DISMISSED = booleanPreferencesKey("verified_hint_dismissed")
    }

    override val token: Flow<String?> = context.sessionDataStore.data.map { it[Keys.TOKEN] }

    override val isLoggedIn: Flow<Boolean> = token.map { !it.isNullOrBlank() }

    override val userId: Flow<String?> = context.sessionDataStore.data.map { it[Keys.USER_ID] }

    override val notificationsEnabled: Flow<Boolean> =
        context.sessionDataStore.data.map { it[Keys.NOTIFICATIONS_ENABLED] ?: true }

    override val verifiedHintDismissed: Flow<Boolean> =
        context.sessionDataStore.data.map { it[Keys.VERIFIED_HINT_DISMISSED] ?: false }

    override suspend fun setVerifiedHintDismissed() {
        context.sessionDataStore.edit { it[Keys.VERIFIED_HINT_DISMISSED] = true }
    }

    override suspend fun currentToken(): String? = context.sessionDataStore.data.first()[Keys.TOKEN]

    override suspend fun saveToken(token: String) {
        context.sessionDataStore.edit { it[Keys.TOKEN] = token }
    }

    override suspend fun saveUserId(userId: String) {
        context.sessionDataStore.edit { it[Keys.USER_ID] = userId }
    }

    override suspend fun clear() {
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

    override suspend fun setNotificationsEnabled(enabled: Boolean) {
        context.sessionDataStore.edit { it[Keys.NOTIFICATIONS_ENABLED] = enabled }
    }

    override suspend fun lastNotifiedMessageId(): String? =
        context.sessionDataStore.data.first()[Keys.LAST_NOTIFIED_MESSAGE]

    override suspend fun setLastNotifiedMessageId(id: String) {
        context.sessionDataStore.edit { it[Keys.LAST_NOTIFIED_MESSAGE] = id }
    }

    override suspend fun deviceId(): String {
        context.sessionDataStore.data.first()[Keys.DEVICE_ID]?.let { return it }
        val generated = UUID.randomUUID().toString()
        context.sessionDataStore.edit { it[Keys.DEVICE_ID] = generated }
        return generated
    }
}
