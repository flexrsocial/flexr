package flexr.social.app.core.common

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.view.WindowManager
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.platform.LocalContext

/**
 * Schützt den aktuellen Bildschirm vor Screenshots und der Vorschau im
 * App-Umschalter.
 *
 * Ohne dieses Flag legt Android beim Wechsel in den Hintergrund ein Abbild des
 * Bildschirms im System-Cache ab — bei der Ausweisaufnahme wäre das ein Foto
 * des Lichtbildausweises auf der Geräteplatte, außerhalb unserer Kontrolle und
 * außerhalb der Löschzusage aus der Datenschutzerklärung. Dasselbe gilt für die
 * Verifizierungs-Selfies.
 *
 * Wird beim Verlassen des Bildschirms wieder aufgehoben: Der Rest der App soll
 * sich normal verhalten (Screenshots von Profil oder Chat sind zulässig).
 */
@Composable
fun SecureScreen() {
    val context = LocalContext.current
    DisposableEffect(context) {
        val window = context.findActivity()?.window
        window?.setFlags(
            WindowManager.LayoutParams.FLAG_SECURE,
            WindowManager.LayoutParams.FLAG_SECURE,
        )
        onDispose { window?.clearFlags(WindowManager.LayoutParams.FLAG_SECURE) }
    }
}

/** Die Activity hinter einem Compose-Context (ggf. durch ContextWrapper verpackt). */
private tailrec fun Context.findActivity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.findActivity()
    else -> null
}
