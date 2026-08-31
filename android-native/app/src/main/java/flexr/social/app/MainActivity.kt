package flexr.social.app

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import dagger.hilt.android.AndroidEntryPoint
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.notifications.ActivityNotificationWorker
import flexr.social.app.notifications.NewMessageWorker
import flexr.social.app.ui.FlexrApp
import flexr.social.app.ui.navigation.TopLevelDestination

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    /**
     * Ziel einer angetippten Benachrichtigung, bis die Navigation es verbraucht
     * hat.
     *
     * Als Compose-Zustand und nicht als schlichtes Feld: bei laufender App
     * kommt der Tipp über [onNewIntent] herein, lange nachdem `setContent`
     * gelaufen ist - ohne beobachtbaren Zustand bliebe er unbemerkt liegen.
     */
    private var notificationTarget by mutableStateOf<String?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        val splash = installSplashScreen()
        super.onCreate(savedInstanceState)
        notificationTarget = targetOf(intent)

        // Der Splash bleibt sichtbar, bis der gespeicherte Token geprüft ist —
        // so startet die App nie kurz auf dem Login-Screen, um dann umzuspringen.
        splash.setKeepOnScreenCondition { !SessionGate.isReady }

        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
            navigationBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
        )

        setContent {
            FlexrTheme {
                FlexrApp(
                    intentData = intent?.data,
                    notificationTarget = notificationTarget,
                    onNotificationTargetHandled = { notificationTarget = null },
                )
            }
        }
    }

    /**
     * Tipp auf eine Benachrichtigung, während die App bereits läuft.
     *
     * Ohne diese Überschreibung greift das Ziel nur beim Kaltstart - bei
     * laufender App holt Android die bestehende Activity nach vorn, `onCreate`
     * läuft nicht erneut, und der Tipp verpuffte.
     */
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        // setIntent, damit ein späteres intent?.data denselben Stand sieht.
        setIntent(intent)
        targetOf(intent)?.let { notificationTarget = it }
    }

    /**
     * Zielroute aus den Extras einer Benachrichtigung.
     *
     * Die Aktivitäts-Benachrichtigungen bringen ihr Ziel als Serverwert mit
     * ("matches"/"swipe"), die Nachrichten-Benachrichtigung nur ein Flag. Der
     * Serverwert wird gegen die bekannten Reiter geprüft statt blind
     * übernommen: ein unbekannter Wert aus einer neueren Serverfassung soll
     * die App einfach öffnen, nicht auf eine leere Route führen.
     *
     * Bewusst getrennt von `intent.data`: darüber läuft der Bestätigungslink
     * aus der Registrierungsmail, und der bleibt hier unangetastet.
     */
    private fun targetOf(intent: Intent?): String? {
        if (intent == null) return null
        if (intent.getBooleanExtra(NewMessageWorker.EXTRA_OPEN_CHATS, false)) {
            return TopLevelDestination.CHATS.route
        }
        val target = intent.getStringExtra(ActivityNotificationWorker.EXTRA_TARGET)
        return TopLevelDestination.entries.firstOrNull { it.route == target }?.route
    }
}

/**
 * Minimaler Übergabepunkt zwischen Splash und Compose: der Start-ViewModel
 * meldet hier, sobald der Sitzungsstatus feststeht.
 */
object SessionGate {
    @Volatile
    var isReady: Boolean = false
}
