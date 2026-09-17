package flexr.social.app.push

import android.Manifest
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import dagger.hilt.android.AndroidEntryPoint
import flexr.social.app.FlexrApplication
import flexr.social.app.MainActivity
import flexr.social.app.R
import flexr.social.app.notifications.NewMessageWorker
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Nimmt echte Push-Nachrichten entgegen.
 *
 * **Warum es diesen Dienst gibt.** Bis zum 17.09.2026 holten sich die Apps ihre
 * Benachrichtigungen selbst ab — auf Android per WorkManager. Das hat eine
 * Decke, die keine Einstellung verschiebt: 15 Minuten ist das kürzeste zulässige
 * Intervall, im Doze-Modus schiebt Android den Lauf in die nächste
 * Wartungsphase, und nach einem erzwungenen Beenden läuft gar nichts mehr.
 * Gemeldet wurde genau das — eine Chatnachricht kam erst an, als die App eine
 * Stunde später von Hand gestartet wurde.
 *
 * Über FCM schickt der Server, und das Gerät wacht dafür auf (der Server setzt
 * dazu `priority: high`, siehe `backend/app/push.py`).
 *
 * Der WorkManager-Abgleich bleibt **zusätzlich** bestehen: Er ist der Fallback,
 * wenn Push nicht eingerichtet ist, die Play-Dienste fehlen oder eine
 * Zustellung verlorengeht.
 */
@AndroidEntryPoint
class FlexrMessagingService : FirebaseMessagingService() {

    @Inject
    lateinit var tokenRegistrar: PushTokenRegistrar

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    /**
     * Firebase vergibt den Token neu, wenn die App neu installiert wird, Daten
     * gelöscht werden oder der Token altert. Ohne dieses Nachmelden wäre das
     * Gerät danach still — der Server schickte an eine Adresse, die es nicht
     * mehr gibt.
     */
    override fun onNewToken(token: String) {
        scope.launch { tokenRegistrar.registrieren(token) }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val granted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.POST_NOTIFICATIONS,
        ) == PackageManager.PERMISSION_GRANTED
        if (!granted) return

        // Titel und Text kommen fertig vom Server. Bewusst dort und nicht hier
        // zusammengesetzt: Der Server kennt die Profilsprache des Empfängers,
        // und er zensiert den Text, bevor er ihn auf einen gesperrten
        // Bildschirm schickt (siehe routers/messages.py).
        val titel = message.notification?.title ?: message.data["title"] ?: return
        val text = message.notification?.body ?: message.data["body"].orEmpty()

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            if (message.data["target"] == "chats") {
                putExtra(NewMessageWorker.EXTRA_OPEN_CHATS, true)
            }
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val notification = NotificationCompat.Builder(this, FlexrApplication.CHANNEL_MESSAGES)
            .setSmallIcon(R.drawable.ic_dumbbell)
            .setColor(android.graphics.Color.parseColor("#FF5A1F"))
            .setContentTitle(titel)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(pendingIntent)
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setAutoCancel(true)
            .build()

        // Dieselbe ID wie der WorkManager-Abgleich: Holt der später dieselbe
        // Nachricht noch einmal ab, ersetzt er diese Benachrichtigung, statt
        // eine zweite danebenzustellen.
        NotificationManagerCompat.from(this).notify(NOTIFICATION_ID, notification)
    }

    private companion object {
        const val NOTIFICATION_ID = 1001
    }
}
