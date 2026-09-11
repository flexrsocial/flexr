package flexr.social.app

import android.content.Intent
import android.content.res.Configuration
import android.content.res.Resources
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dagger.hilt.android.AndroidEntryPoint
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.locale.AppLanguage
import flexr.social.app.core.locale.AppLanguageViewModel
import flexr.social.app.core.locale.ProvideAppLanguage
import flexr.social.app.notifications.ActivityNotificationWorker
import flexr.social.app.notifications.NewMessageWorker
import flexr.social.app.ui.FlexrApp
import flexr.social.app.ui.navigation.TopLevelDestination

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    /**
     * Ressourcen der gerade gewaehlten Sprache - `null`, solange noch keine
     * angewendet wurde (siehe [applyLanguage]).
     *
     * [getResources] liefert diese anstelle der echten Ressourcen der
     * Activity, sobald sie gesetzt sind. Bewusst ein Feld auf der ECHTEN
     * Activity statt eines zweiten, per `ContextWrapper` fabrizierten Context
     * als `LocalContext`, wie es hier bis zum 11.09.2026 stand: Ein
     * `ContextWrapper` um die Activity ist selbst *keine* Activity mehr - ein
     * direktes `context as Activity` (Berechtigungsabfragen, CameraX, Custom
     * Tabs) waere daran mit einer `ClassCastException` gescheitert, obwohl die
     * echte Activity ueber `baseContext` weiter erreichbar gewesen waere.
     * Gemeldet wurde ausserdem, dass `stringResource` trotz gewaehlter
     * Sprache weiter Deutsch auflöste; ob das an genau diesem Wrapper lag,
     * liess sich mangels Testgeraet nicht abschliessend nachweisen, aber der
     * Verdacht lag nahe. Mit diesem Feld bleibt `LocalContext.current`
     * UEBERALL die echte Activity; nur [getResources] liefert je nach Sprache
     * etwas anderes - dieselbe Technik, mit der Apps schon vor Jetpack
     * Compose die Sprache zur Laufzeit umgeschaltet haben.
     */
    private var localizedResources: Resources? = null

    override fun getResources(): Resources = localizedResources ?: super.getResources()

    /**
     * Baut die lokalisierten Ressourcen fuer [language] und haelt sie in
     * [localizedResources] bereit.
     *
     * Zwei bewusste Entscheidungen gegen die naheliegenderen Varianten:
     *
     * - Die Ausgangskonfiguration kommt aus `super.getResources()`, nicht aus
     *   `resources` (das waere wegen der Ueberschreibung unten dasselbe Feld,
     *   das gerade erst gesetzt wird) und nicht aus `applicationContext` (das
     *   kennt Fenstergroesse und Mehrfenster-/Faltzustand dieser Activity
     *   nicht, nur die Vorgabe des Geraets).
     * - `createConfigurationContext` wird auf `applicationContext` aufgerufen,
     *   nicht auf `this`: Es ist unklar, ob die Systemimplementierung dabei
     *   intern `getResources()` der aufrufenden Instanz konsultiert - waere
     *   das so, entstuende mit `this` eine Ringabhaengigkeit auf das Feld
     *   unten. `applicationContext` ist dafuer eine andere Instanz, an der
     *   nichts ueberschrieben ist.
     */
    private fun applyLanguage(language: AppLanguage) {
        val configuration = Configuration(super.getResources().configuration).apply {
            setLocale(language.locale)
        }
        localizedResources = applicationContext.createConfigurationContext(configuration).resources
    }

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
            // Die Sprachwahl huellt alles ein, was Texte zeigt: darin loest
            // `stringResource` gegen die gewaehlte Sprache auf. Bewusst kein
            // `recreate()` beim Wechsel - so bleiben Navigationsstapel und
            // Scrollpositionen stehen.
            val languageViewModel: AppLanguageViewModel = hiltViewModel()
            val language by languageViewModel.language.collectAsStateWithLifecycle()
            // Synchron VOR dem ersten Zeichnen anwenden (derselbe `remember`-
            // Kniff wie in ProvideAppLanguage fuer die Configuration): Damit
            // sieht `stringResource` schon im ersten Frame nach jedem Wechsel
            // die richtige Sprache, nicht erst nach einer weiteren Rekomposition.
            remember(language) { applyLanguage(language) }
            ProvideAppLanguage(language) {
                FlexrTheme {
                    FlexrApp(
                        intentData = intent?.data,
                        notificationTarget = notificationTarget,
                        onNotificationTargetHandled = { notificationTarget = null },
                    )
                }
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
