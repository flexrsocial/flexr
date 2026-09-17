package flexr.social.app.push

import android.content.Context
import android.util.Log
import com.google.firebase.FirebaseApp
import dagger.hilt.android.qualifiers.ApplicationContext
import com.google.firebase.messaging.FirebaseMessaging
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.PushTokenRequestDto
import flexr.social.app.data.session.SessionStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.tasks.await
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Meldet den Gerätetoken beim Server an und wieder ab.
 *
 * **Der Token ist der Schalter.** Wer Benachrichtigungen in der App abschaltet,
 * wird abgemeldet; der Server hat dann niemanden, dem er zustellen könnte. Das
 * ist bewusst so und nicht als zusätzliches Flag am Konto gebaut — zwei Quellen
 * für dieselbe Frage laufen früher oder später auseinander.
 *
 * Läuft still: Ist Push nicht eingerichtet (keine Firebase-Konfiguration im
 * Build) oder fehlen die Play-Dienste, passiert hier nichts, und die App fällt
 * auf den WorkManager-Abgleich zurück.
 */
@Singleton
class PushTokenRegistrar @Inject constructor(
    @ApplicationContext private val context: Context,
    private val api: FlexrApi,
    private val sessionStore: SessionStore,
) {

    /**
     * Den aktuellen Token holen und anmelden. Aufzurufen nach dem Anmelden und
     * bei jedem Start — mehrfaches Anmelden desselben Tokens ist der Normalfall
     * und schreibt serverseitig nur dieselbe Zeile fort.
     */
    suspend fun anmelden() {
        // Ohne Firebase-Konfiguration im Build gibt es nichts anzumelden -
        // die App faellt dann auf den WorkManager-Abgleich zurueck.
        if (FirebaseApp.getApps(context).isEmpty()) return
        if (sessionStore.currentToken().isNullOrBlank()) return
        if (!sessionStore.notificationsEnabled.first()) {
            // Abgeschaltet: einen eventuell noch hinterlegten Token abräumen,
            // statt ihn stillschweigend weiterlaufen zu lassen.
            abmelden()
            return
        }
        val token = runCatching { FirebaseMessaging.getInstance().token.await() }
            .getOrElse {
                Log.i(TAG, "Kein FCM-Token zu bekommen: ${it.message}")
                return
            }
        registrieren(token)
    }

    /** Einen bereits bekannten Token anmelden (aus [FlexrMessagingService.onNewToken]). */
    suspend fun registrieren(token: String) {
        if (sessionStore.currentToken().isNullOrBlank()) return
        runCatching {
            api.registerPushToken(PushTokenRequestDto(platform = "android", token = token))
            sessionStore.setPushToken(token)
        }.onFailure { Log.i(TAG, "Push-Token nicht angemeldet: ${it.message}") }
    }

    /**
     * Abmelden — beim Abmelden vom Konto und beim Abschalten der
     * Benachrichtigungen.
     *
     * Der zuletzt angemeldete Token steht lokal, weil der Server ihn zum
     * Löschen braucht und `FirebaseMessaging.getToken()` beim Abmelden nicht
     * mehr unbedingt erreichbar ist.
     */
    suspend fun abmelden() {
        val token = sessionStore.pushToken() ?: return
        runCatching {
            api.unregisterPushToken(PushTokenRequestDto(platform = "android", token = token))
        }.onFailure { Log.i(TAG, "Push-Token nicht abgemeldet: ${it.message}") }
        sessionStore.setPushToken(null)
    }

    private companion object {
        const val TAG = "FlexrPush"
    }
}
