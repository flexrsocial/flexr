package flexr.social.app.core.review

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import com.google.android.play.core.review.ReviewManagerFactory
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.tasks.await

/**
 * Bittet über die Play In-App Review API um eine Bewertung (seit 2.7.43).
 *
 * Anlass (07.11.2026): Der Store-Eintrag hatte keine einzige Bewertung. Gefragt
 * wird in einem positiven Moment, der den Ablauf nicht stört: direkt nachdem
 * jemand seine [MESSAGES_BEFORE_ASKING]. Nachricht erfolgreich abgeschickt hat
 * - wer so weit ist, hat ein Match und schreibt.
 *
 * Ob der Dialog wirklich erscheint, entscheidet Google Play (Kontingent pro
 * Nutzer, nie bei Debug-Builds außerhalb von Internal App Sharing). Damit wir
 * nicht bei jeder Nachricht anfragen, höchstens [MAX_ASKS]-mal und frühestens
 * [DAYS_BETWEEN_ASKS] Tage nach dem letzten Versuch. Bewusst SharedPreferences
 * statt SessionStore: Der Zähler gehört zum Gerät, nicht zur Sitzung, und soll
 * ein Ab- und Anmelden überleben.
 */
@Singleton
class ReviewPrompter @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val prefs = context.getSharedPreferences("review_prompt", Context.MODE_PRIVATE)

    /** Zählt eine gesendete Nachricht. `true`, wenn jetzt gefragt werden soll. */
    fun registerSentMessage(now: Long = System.currentTimeMillis()): Boolean {
        val sent = prefs.getInt(KEY_SENT, 0) + 1
        prefs.edit().putInt(KEY_SENT, sent).apply()
        if (sent < MESSAGES_BEFORE_ASKING) return false
        val asks = prefs.getInt(KEY_ASKS, 0)
        if (asks >= MAX_ASKS) return false
        val last = prefs.getLong(KEY_LAST_ASK, 0L)
        if (last != 0L && now - last < DAYS_BETWEEN_ASKS * DAY_MS) return false
        prefs.edit().putInt(KEY_ASKS, asks + 1).putLong(KEY_LAST_ASK, now).apply()
        return true
    }

    /** Startet den Play-Dialog. Fehler (kein Play Store, offline) bleiben still. */
    suspend fun launch(activity: Activity) {
        runCatching {
            val manager = ReviewManagerFactory.create(activity)
            val info = manager.requestReviewFlow().await()
            manager.launchReviewFlow(activity, info).await()
        }
    }

    companion object {
        const val MESSAGES_BEFORE_ASKING = 3
        const val MAX_ASKS = 3
        const val DAYS_BETWEEN_ASKS = 60L
        private const val DAY_MS = 24L * 60 * 60 * 1000
        private const val KEY_SENT = "sent_messages"
        private const val KEY_ASKS = "asks"
        private const val KEY_LAST_ASK = "last_ask"
    }
}

/** Die Activity hinter einem Compose-Context (LocalContext). */
fun Context.findActivity(): Activity? {
    var current: Context? = this
    while (current is ContextWrapper) {
        if (current is Activity) return current
        current = current.baseContext
    }
    return null
}
