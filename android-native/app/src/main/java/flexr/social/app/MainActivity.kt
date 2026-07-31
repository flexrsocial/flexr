package flexr.social.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import dagger.hilt.android.AndroidEntryPoint
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.ui.FlexrApp

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        val splash = installSplashScreen()
        super.onCreate(savedInstanceState)

        // Der Splash bleibt sichtbar, bis der gespeicherte Token geprüft ist —
        // so startet die App nie kurz auf dem Login-Screen, um dann umzuspringen.
        splash.setKeepOnScreenCondition { !SessionGate.isReady }

        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
            navigationBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
        )

        setContent {
            FlexrTheme {
                FlexrApp(intentData = intent?.data)
            }
        }
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
