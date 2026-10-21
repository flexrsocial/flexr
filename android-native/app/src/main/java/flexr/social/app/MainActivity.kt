package flexr.social.app

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.content.pm.ActivityInfo
import android.content.res.Configuration
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.core.view.WindowCompat
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
import flexr.social.app.push.FlexrMessagingService
import flexr.social.app.ui.FlexrApp
import flexr.social.app.ui.navigation.TopLevelDestination
import flexr.social.app.ui.navigation.appLinkTarget

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

    /**
     * Link, mit dem die App geöffnet wurde (Bestätigungs- oder Reset-Link).
     * Als Zustand, weil die Activity `singleTop` ist: Läuft die App schon,
     * kommt der Link über [onNewIntent] - vorher las `setContent` nur
     * `intent?.data` vom Kaltstart, ein Link bei laufender App verpuffte.
     */
    private var linkData by mutableStateOf<Uri?>(null)

    /**
     * Zählt jeden ankommenden Link. Derselbe Link ein zweites Mal (Dialog
     * versehentlich geschlossen, erneut in der Mail getippt) ist für Compose
     * sonst kein neuer Wert - der Effekt in FlexrApp liefe nicht noch einmal.
     */
    private var linkCount by mutableIntStateOf(0)

    override fun onCreate(savedInstanceState: Bundle?) {
        val splash = installSplashScreen()
        super.onCreate(savedInstanceState)
        notificationTarget = targetOf(intent)
        linkData = intent?.data
        if (linkData != null) linkCount++

        // Der Splash bleibt sichtbar, bis der gespeicherte Token geprüft ist —
        // so startet die App nie kurz auf dem Login-Screen, um dann umzuspringen.
        splash.setKeepOnScreenCondition { !SessionGate.isReady }

        lockPortraitOnPhones()
        drawBehindSystemBars()

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
                        intentData = linkData,
                        intentId = linkCount,
                        notificationTarget = notificationTarget,
                        onNotificationTargetHandled = { notificationTarget = null },
                    )
                }
            }
        }
    }

    /**
     * Hochformat nur auf Handys.
     *
     * Bis 2.7.34 stand `screenOrientation="portrait"` im Manifest. Android 16
     * ignoriert solche Sperren auf großen Displays (kleinste Breite ab 600 dp:
     * Tablets, aufgeklappte Foldables), und die Play Console meldete sie als
     * Hindernis für große Displays. Auf Handys gilt die Sperre weiter (Deck und
     * Kamera sind für das Hochformat gebaut), auf großen Displays dreht die App
     * frei.
     *
     * Reicht in onCreate: Ändert sich die kleinste Breite (Foldable auf- oder
     * zugeklappt), baut Android die Activity neu auf, weil `smallestScreenSize`
     * nicht in `configChanges` steht.
     */
    @SuppressLint("SourceLockedOrientationActivity")
    private fun lockPortraitOnPhones() {
        requestedOrientation = if (resources.configuration.smallestScreenWidthDp < LARGE_SCREEN_MIN_DP) {
            ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        } else {
            ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        }
    }

    /**
     * Inhalt hinter Status- und Navigationsleiste, ohne die mit Android 15
     * eingestellten Fenster-APIs.
     *
     * Bis 2.7.34 lief das über `enableEdgeToEdge()` aus androidx.activity. Die
     * Bibliothek setzt für Android 8 bis 14 die Leistenfarben über
     * `Window.setStatusBarColor`/`setNavigationBarColor` und den Ausschnitt-Modus
     * `LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES`. Alle drei sind seit Android 15
     * eingestellt. Die Play Console liest diese Aufrufe aus dem Bundle und
     * meldete für 2.7.34 „veraltete APIs für die randlose Anzeige“. Auch
     * androidx.activity 1.13.0 enthält sie noch, ein Update hilft also nicht.
     *
     * Dasselbe Ergebnis ohne diese Aufrufe:
     * - Ab Android 15 ist die randlose Anzeige ohnehin erzwungen.
     * - Bis Android 14 legt `setDecorFitsSystemWindows(false)` den Inhalt hinter
     *   die Leisten. Durchsichtig macht sie das Theme (`Theme.Flexr`).
     * - Kein Kontrastschleier hinter den Leisten und helle Symbole, wie vorher
     *   mit `SystemBarStyle.dark(TRANSPARENT)`.
     * - Der Ausschnitt-Modus bleibt beim Standard. Im Hochformat liegt die
     *   Kamera-Aussparung in der Statusleiste, der Inhalt reicht also wie bisher
     *   bis ganz oben. Im Querformat (nur große Displays) hält bis Android 14
     *   das System den Rand frei, ab Android 15 die Wurzel in [FlexrApp].
     */
    private fun drawBehindSystemBars() {
        WindowCompat.setDecorFitsSystemWindows(window, false)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            window.isStatusBarContrastEnforced = false
            window.isNavigationBarContrastEnforced = false
        }
        WindowCompat.getInsetsController(window, window.decorView).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
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
        intent.data?.let {
            linkData = it
            linkCount++
        }
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
     * **Drei Quellen, nicht zwei.** War die App beendet, hat kein eigener Code
     * die Benachrichtigung gezeichnet: Das Firebase-SDK zeigt sie dann selbst
     * an und legt die Datennutzlast des Servers als Extras in den
     * Start-Intent - `target` heisst dort genau so wie in der Nutzlast
     * ([FlexrMessagingService.DATA_TARGET]). Ohne diese dritte Quelle landete
     * ein Tipp aus dem gemeldeten Fall - Telefon gesperrt, App beendet -
     * stumm auf dem Startbildschirm der App statt im Chat.
     *
     * Vierte Quelle seit 2.7.38: ein Mail-Link `https://flexr.social/app/open/<reiter>`
     * in `intent.data` ([appLinkTarget]). Der Bestätigungslink aus der
     * Registrierungsmail (`/mail-bestaetigen`) läuft ebenfalls über
     * `intent.data`, ist aber kein Reiter und bleibt FlexrApp überlassen.
     */
    private fun targetOf(intent: Intent?): String? {
        if (intent == null) return null
        if (intent.getBooleanExtra(NewMessageWorker.EXTRA_OPEN_CHATS, false)) {
            return TopLevelDestination.CHATS.route
        }
        val target = intent.getStringExtra(ActivityNotificationWorker.EXTRA_TARGET)
            ?: intent.getStringExtra(FlexrMessagingService.DATA_TARGET)
        TopLevelDestination.entries.firstOrNull { it.route == target }?.let { return it.route }
        return intent.data?.takeIf { it.host == "flexr.social" }?.let { appLinkTarget(it.path) }
    }

    private companion object {
        /** Ab dieser kleinsten Breite ignoriert Android 16 Ausrichtungssperren. */
        const val LARGE_SCREEN_MIN_DP = 600
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
