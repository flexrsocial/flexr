package flexr.social.app.notifications

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Plant den periodischen Nachrichtenabgleich. 15 Minuten ist das kleinste von
 * WorkManager zugelassene Intervall; der Abgleich läuft nur bei Netz und wird
 * beim Abmelden wieder abgeräumt.
 */
@Singleton
class MessageNotificationScheduler @Inject constructor(
    @ApplicationContext private val context: Context,
) {

    fun schedule() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val messages = PeriodicWorkRequestBuilder<NewMessageWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 5, TimeUnit.MINUTES)
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            NewMessageWorker.WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            messages,
        )

        // Getrennter Auftrag mit größerem Abstand: Matches und Erinnerungen
        // vertragen eine Stunde Verzögerung, ein Chat nicht. Das spart Akku
        // und Anfragen gegenüber dem 15-Minuten-Takt der Nachrichten.
        val activity = PeriodicWorkRequestBuilder<ActivityNotificationWorker>(1, TimeUnit.HOURS)
            .setConstraints(constraints)
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 15, TimeUnit.MINUTES)
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            ActivityNotificationWorker.WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            activity,
        )
    }

    fun cancel() {
        WorkManager.getInstance(context).cancelUniqueWork(NewMessageWorker.WORK_NAME)
        WorkManager.getInstance(context).cancelUniqueWork(ActivityNotificationWorker.WORK_NAME)
    }
}
