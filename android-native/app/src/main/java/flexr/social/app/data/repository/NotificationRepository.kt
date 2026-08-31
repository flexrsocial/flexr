package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.MarkDeliveredRequestDto
import flexr.social.app.domain.model.PushNotification
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Abholfach für die vom Server bereitgelegten App-Benachrichtigungen.
 *
 * FLEXR nutzt kein FCM/APNs — neues Match, wartende Profile und die
 * Inaktivitäts-Erinnerung kommen über denselben Hintergrundabgleich, mit dem
 * [flexr.social.app.notifications.NewMessageWorker] schon neue Nachrichten
 * meldet. Ob ein Anlass überhaupt im Fach landet, entscheidet der Server
 * anhand der Schalter unter "Benachrichtigungen"; die App zeigt nur an, was
 * ihr gereicht wird.
 */
@Singleton
class NotificationRepository @Inject constructor(
    private val api: FlexrApi,
) {

    suspend fun pending(): List<PushNotification> =
        apiCall { api.pendingNotifications() }.map { it.toDomain() }

    /**
     * Quittiert erst nach dem Anzeigen, nicht beim Abholen: bricht der
     * Hintergrundlauf dazwischen ab, kommt die Nachricht im nächsten Durchgang
     * erneut — besser doppelt als verschluckt.
     */
    suspend fun markDelivered(ids: List<String>) {
        if (ids.isEmpty()) return
        apiCall { api.markNotificationsDelivered(MarkDeliveredRequestDto(ids)) }
    }
}
