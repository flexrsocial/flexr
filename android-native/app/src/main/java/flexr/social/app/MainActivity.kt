package flexr.social.app

import android.content.Context
import android.content.Intent
import android.content.res.Configuration
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dagger.hilt.android.AndroidEntryPoint
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.locale.AppLanguage
import flexr.social.app.core.locale.AppLanguageViewModel
import flexr.social.app.core.locale.LanguageStore
import flexr.social.app.core.locale.ProvideAppLanguage
import flexr.social.app.notifications.ActivityNotificationWorker
import flexr.social.app.notifications.NewMessageWorker
import flexr.social.app.ui.FlexrApp
import flexr.social.app.ui.navigation.TopLevelDestination

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    /**
     * Sprache, mit der diese Activity aufgebaut wurde.
     *
     * Gesetzt in [attachBaseContext] und ab da unveraenderlich: Der
     * Basis-Context steht fest, sobald die Activity haengt. Ein Wechsel danach
     * kann nur noch ueber [recreate] wirken — siehe [onCreate].
     */
    private var attachedLanguage: AppLanguage = AppLanguage.DEFAULT

    /**
     * Setzt die gewaehlte Sprache am Basis-Context — dem einzigen Ort, an dem
     * sie zuverlaessig wirkt.
     *
     * Vorgeschichte: Bis zum 11.09.2026 wurde die Sprache zur Laufzeit
     * umgehaengt, erst ueber einen untergeschobenen `LocalContext`
     * (`ContextWrapper`), dann ueber ein ueberschriebenes `getResources()` auf
     * der Activity. Beide Fassungen wurden am Geraet geprueft, und in beiden
     * blieb jeder Text deutsch, obwohl der Regler umsprang. Auf Papier haetten
     * beide funktionieren muessen (`stringResource` liest
     * `LocalContext.current.resources`) — taten sie aber nicht.
     *
     * Diese Fassung raet nicht mehr, sondern nimmt den Weg, den Android selbst
     * vorsieht: Ein `createConfigurationContext` als Basis der Activity. Damit
     * liefert *jeder* Context dieser Activity die richtigen Ressourcen —
     * `stringResource`, `getString`, Dialoge, `LocalConfiguration`,
     * Systemdialoge — ohne dass irgendwo etwas ueberschrieben waere.
     *
     * Der Preis ist ein [recreate] beim Wechsel. Er kostet nichts Sichtbares:
     * ViewModels ueberleben ihn, und Navigationsstapel wie Scrollpositionen
     * liegen in `rememberSaveable` und kommen zurueck. Genau so schaltet auch
     * Android 13 selbst die App-Sprache um.
     *
     * Die Wahl kommt aus [LanguageStore] und wird synchron gelesen: Hier gibt
     * es weder Hilt noch einen Coroutine-Scope, auf die man warten koennte.
     */
    override fun attachBaseContext(newBase: Context) {
        val language = LanguageStore.storedLanguage(newBase) ?: AppLanguage.detect()
        attachedLanguage = language
        val configuration = Configuration(newBase.resources.configuration).apply {
            setLocale(language.locale)
            setLayoutDirection(language.locale)
        }
        super.attachBaseContext(newBase.createConfigurationContext(configuration))
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
            val languageViewModel: AppLanguageViewModel = hiltViewModel()
            val language by languageViewModel.language.collectAsStateWithLifecycle()
            // Sprache gewechselt: Die Ressourcen dieser Activity stehen seit
            // `attachBaseContext` fest, also muss sie neu aufgebaut werden.
            // Loest im Normalfall nie aus - der Startwert des Flusses kommt aus
            // demselben synchron gelesenen Speicher wie `attachedLanguage`.
            // Es gibt genau zwei Ausloeser: der Griff an den Regler, und der
            // erste Start nach dem Umzug vom alten DataStore
            // (LanguageStore.migrateLegacyChoice).
            LaunchedEffect(language) {
                if (language != attachedLanguage && !isFinishing) recreate()
            }
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
