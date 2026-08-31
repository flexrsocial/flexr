package flexr.social.app.notifications

import android.Manifest
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import flexr.social.app.FlexrApplication
import flexr.social.app.MainActivity
import flexr.social.app.R
import flexr.social.app.data.repository.NotificationRepository
import flexr.social.app.data.session.SessionStore
import flexr.social.app.domain.model.PushNotification
import kotlinx.coroutines.flow.first

/**
 * Holt die vom Server bereitgelegten Benachrichtigungen ab und zeigt sie an:
 * neues Match, wartende Profile im Suchradius und die Erinnerung nach sieben
 * Tagen ohne Nutzung.
 *
 * Kein FCM — aus demselben Grund wie bei [NewMessageWorker]: FLEXR braucht
 * dafür keinen Google-Dienst, und die Auslieferung über WorkManager reicht für
 * Anlässe, die keine Sekundengenauigkeit verlangen.
 *
 * Welche Anlässe überhaupt ankommen, entscheidet der Server anhand der
 * notify_*_push-Schalter. Die App fragt das nicht noch einmal ab: eine zweite
 * Regel hier würde bei jeder Änderung auseinanderlaufen und wäre erst nach dem
 * nächsten App-Update wirksam.
 */
@HiltWorker
class ActivityNotificationWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted params: WorkerParameters,
    private val notificationRepository: NotificationRepository,
    private val sessionStore: SessionStore,
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        if (sessionStore.currentToken().isNullOrBlank()) return Result.success()
        // Derselbe App-weite Schalter, mit dem auch der Nachrichtenabgleich
        // stillgelegt wird - er steht über den serverseitigen Einstellungen.
        if (!sessionStore.notificationsEnabled.first()) return Result.success()

        val offen = runCatching { notificationRepository.pending() }
            .getOrElse { return Result.retry() }
        if (offen.isEmpty()) return Result.success()

        val angezeigt = offen.filter { show(it) }
        // Nur Quittiertes gilt als zugestellt: fehlt die Systemberechtigung,
        // bleibt der Eintrag liegen und wird nachgeholt, sobald der Nutzer sie
        // erteilt - statt ungesehen zu verfallen.
        runCatching { notificationRepository.markDelivered(angezeigt.map { it.id }) }
            .getOrElse { return Result.retry() }
        return Result.success()
    }

    private fun show(notification: PushNotification): Boolean {
        val granted = ContextCompat.checkSelfPermission(
            applicationContext, Manifest.permission.POST_NOTIFICATIONS,
        ) == PackageManager.PERMISSION_GRANTED
        if (!granted) return false

        val intent = Intent(applicationContext, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra(EXTRA_TARGET, notification.target)
        }
        val pendingIntent = PendingIntent.getActivity(
            applicationContext,
            // Eigener Request-Code je Anlass, sonst überschreibt der zweite
            // PendingIntent das Ziel des ersten (FLAG_UPDATE_CURRENT).
            notification.id.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val system = NotificationCompat.Builder(applicationContext, FlexrApplication.CHANNEL_ACTIVITY)
            .setSmallIcon(R.drawable.ic_dumbbell)
            .setColor(android.graphics.Color.parseColor("#FF5A1F"))
            .setContentTitle(notification.title)
            .setContentText(notification.body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(notification.body))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        // Stabile ID aus der Server-ID: derselbe Anlass ersetzt seine eigene
        // Meldung, verdrängt aber keine fremde.
        NotificationManagerCompat.from(applicationContext)
            .notify(NOTIFICATION_ID_BASE + (notification.id.hashCode() and 0xFFFF), system)
        return true
    }

    companion object {
        const val WORK_NAME = "flexr_activity_notifications"
        const val EXTRA_TARGET = "notification_target"
        private const val NOTIFICATION_ID_BASE = 2000
    }
}
