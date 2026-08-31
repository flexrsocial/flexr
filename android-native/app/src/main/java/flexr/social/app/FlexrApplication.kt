package flexr.social.app

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import coil.ImageLoader
import coil.ImageLoaderFactory
import coil.disk.DiskCache
import coil.memory.MemoryCache
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class FlexrApplication : Application(), Configuration.Provider, ImageLoaderFactory {

    @Inject
    lateinit var workerFactory: HiltWorkerFactory

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .setMinimumLoggingLevel(if (BuildConfig.DEBUG) android.util.Log.DEBUG else android.util.Log.WARN)
            .build()

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    /**
     * Profilfotos sind der Inhalt dieser App — sie duerfen nicht bei jedem
     * Anzeigen neu aus dem Netz kommen. Ohne eigenen Loader nimmt Coil seine
     * Vorgaben und richtet sich nach den HTTP-Cache-Headern; fehlen die (R2
     * lieferte lange gar keine), faellt es auf heuristisches Caching zurueck
     * und laedt praktisch jedes Mal neu. Ein Empfangsloch liess die Bilder
     * dann schlicht verschwinden.
     *
     * [respectCacheHeaders] steht deshalb auf false: die Objektschluessel sind
     * UUIDs und werden nie ueberschrieben, ein einmal geladenes Bild bleibt
     * gueltig. Damit zeigt die App Fotos auch offline — passend dazu, dass
     * Matches und Chats ohnehin aus Room kommen.
     */
    override fun newImageLoader(): ImageLoader = ImageLoader.Builder(this)
        .memoryCache { MemoryCache.Builder(this).maxSizePercent(0.25).build() }
        .diskCache {
            DiskCache.Builder()
                .directory(cacheDir.resolve("bilder"))
                .maxSizeBytes(150L * 1024 * 1024)
                .build()
        }
        .respectCacheHeaders(false)
        .crossfade(true)
        .build()

    private fun createNotificationChannels() {
        val manager = getSystemService(NotificationManager::class.java)
        val messages = NotificationChannel(
            CHANNEL_MESSAGES,
            getString(R.string.notification_channel_messages),
            NotificationManager.IMPORTANCE_DEFAULT,
        ).apply {
            description = getString(R.string.notification_channel_messages_desc)
            enableLights(true)
            lightColor = android.graphics.Color.parseColor("#FF5A1F")
        }
        manager.createNotificationChannel(messages)

        // Eigener Kanal neben den Nachrichten: Matches und Erinnerungen sind
        // weniger dringend als ein Chat. Getrennt kann der Nutzer sie in den
        // Systemeinstellungen leiser stellen, ohne die Nachrichten zu verlieren.
        val activity = NotificationChannel(
            CHANNEL_ACTIVITY,
            getString(R.string.notification_channel_activity),
            NotificationManager.IMPORTANCE_DEFAULT,
        ).apply {
            description = getString(R.string.notification_channel_activity_desc)
            enableLights(true)
            lightColor = android.graphics.Color.parseColor("#FF5A1F")
        }
        manager.createNotificationChannel(activity)
    }

    companion object {
        const val CHANNEL_MESSAGES = "flexr_messages"
        const val CHANNEL_ACTIVITY = "flexr_activity"
    }
}
