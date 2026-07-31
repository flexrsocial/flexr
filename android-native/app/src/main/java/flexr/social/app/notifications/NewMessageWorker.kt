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
import flexr.social.app.data.repository.MatchRepository
import flexr.social.app.data.session.SessionStore
import kotlinx.coroutines.flow.first

/**
 * Hintergrundabgleich für neue Nachrichten.
 *
 * Die Web-App konnte nur pollen, solange der Tab offen war. Nativ übernimmt das
 * WorkManager: die Match-Liste wird periodisch aufgefrischt und bei neuen
 * ungelesenen Nachrichten erscheint eine Systembenachrichtigung. Der lokale
 * Cache ist dadurch beim Öffnen der App bereits aktuell.
 */
@HiltWorker
class NewMessageWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted params: WorkerParameters,
    private val matchRepository: MatchRepository,
    private val sessionStore: SessionStore,
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        if (sessionStore.currentToken().isNullOrBlank()) return Result.success()
        if (!sessionStore.notificationsEnabled.first()) return Result.success()

        val matches = runCatching { matchRepository.refresh() }.getOrElse { return Result.retry() }

        val unread = matches.filter { it.unreadCount > 0 }
        if (unread.isEmpty()) {
            NotificationManagerCompat.from(applicationContext).cancel(NOTIFICATION_ID)
            return Result.success()
        }

        // Nur bei wirklich neuen Nachrichten benachrichtigen — sonst würde jeder
        // Durchlauf dieselbe ungelesene Nachricht erneut melden.
        val newestId = unread
            .mapNotNull { it.lastMessage }
            .maxByOrNull { it.createdAt }
            ?.id
            ?: return Result.success()

        if (sessionStore.lastNotifiedMessageId() == newestId) return Result.success()
        sessionStore.setLastNotifiedMessageId(newestId)

        showNotification(
            senderNames = unread.map { it.profile.name },
            totalUnread = unread.sumOf { it.unreadCount },
            preview = unread.mapNotNull { it.lastMessage }.maxByOrNull { it.createdAt }?.content,
        )
        return Result.success()
    }

    private fun showNotification(senderNames: List<String>, totalUnread: Int, preview: String?) {
        val granted = ContextCompat.checkSelfPermission(
            applicationContext, Manifest.permission.POST_NOTIFICATIONS,
        ) == PackageManager.PERMISSION_GRANTED
        if (!granted) return

        val title = if (senderNames.size == 1) {
            "Neue Nachricht von ${senderNames.first()}"
        } else {
            "$totalUnread neue Nachrichten"
        }
        val text = if (senderNames.size == 1) {
            preview.orEmpty()
        } else {
            senderNames.distinct().joinToString(", ")
        }

        val intent = Intent(applicationContext, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra(EXTRA_OPEN_CHATS, true)
        }
        val pendingIntent = PendingIntent.getActivity(
            applicationContext,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val notification = NotificationCompat.Builder(applicationContext, FlexrApplication.CHANNEL_MESSAGES)
            .setSmallIcon(R.drawable.ic_dumbbell)
            .setColor(android.graphics.Color.parseColor("#FF5A1F"))
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(pendingIntent)
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setAutoCancel(true)
            .build()

        NotificationManagerCompat.from(applicationContext).notify(NOTIFICATION_ID, notification)
    }

    companion object {
        const val WORK_NAME = "flexr_new_messages"
        const val EXTRA_OPEN_CHATS = "open_chats"
        private const val NOTIFICATION_ID = 1001
    }
}
