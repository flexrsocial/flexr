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
        val request = PeriodicWorkRequestBuilder<NewMessageWorker>(15, TimeUnit.MINUTES)
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build(),
            )
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 5, TimeUnit.MINUTES)
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            NewMessageWorker.WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            request,
        )
    }

    fun cancel() {
        WorkManager.getInstance(context).cancelUniqueWork(NewMessageWorker.WORK_NAME)
    }
}
