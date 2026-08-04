package flexr.social.app.data.session

import kotlinx.coroutines.flow.Flow

/**
 * Sitzungszustand der App: JWT, stabile Geräte-ID und Nutzereinstellungen.
 *
 * Ersetzt den `localStorage` der Web-App.
 *
 * Bewusst als Schnittstelle: die echte Umsetzung [DataStoreSessionStore] hängt
 * am Android-Context, und alles, was den Sitzungszustand braucht (Repositories,
 * darüber die ViewModels), wäre damit in reinen JVM-Tests nicht mehr
 * konstruierbar. Die Tests setzen `FakeSessionStore` ein.
 */
interface SessionStore {

    val token: Flow<String?>

    val isLoggedIn: Flow<Boolean>

    val userId: Flow<String?>

    val notificationsEnabled: Flow<Boolean>

    /** Ob der Hinweis „Dein Profil ist verifiziert" bereits bestätigt wurde. */
    val verifiedHintDismissed: Flow<Boolean>

    suspend fun setVerifiedHintDismissed()

    suspend fun currentToken(): String?

    suspend fun saveToken(token: String)

    suspend fun saveUserId(userId: String)

    suspend fun clear()

    suspend fun setNotificationsEnabled(enabled: Boolean)

    suspend fun lastNotifiedMessageId(): String?

    suspend fun setLastNotifiedMessageId(id: String)

    /**
     * Stabile, zufällige Geräte-ID — entspricht `flexr_device_id` im Web und
     * erfüllt das vom Backend erwartete Format `^[A-Za-z0-9-]{8,64}$`.
     * Bewusst keine Hardware-Kennung (ANDROID_ID o. Ä.): die ID ist nicht
     * geräteübergreifend rückverfolgbar und wird beim Deinstallieren gelöscht.
     */
    suspend fun deviceId(): String
}
