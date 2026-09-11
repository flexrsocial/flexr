package flexr.social.app.core.locale

import android.content.res.Configuration
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.ProvidableCompositionLocal
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext

/**
 * Die gerade gewaehlte Sprache, fuer Stellen, die sie selbst kennen muessen
 * (der Sprachregler, um seinen Zustand zu zeichnen).
 */
val LocalAppLanguage: ProvidableCompositionLocal<AppLanguage> =
    compositionLocalOf { AppLanguage.DEFAULT }

/**
 * Loest `stringResource` innerhalb von [content] in [language] auf.
 *
 * Bewusst ueber eine ausgetauschte [LocalConfiguration] und nicht ueber einen
 * Neustart der Activity: `stringResource` beobachtet [LocalConfiguration], ein
 * Sprachwechsel zeichnet die Oberflaeche also einfach neu. Die Activity bleibt
 * stehen, Navigationsstapel und Scrollpositionen ueberleben den Wechsel —
 * anders als bei `recreate()`.
 *
 * [LocalContext] wird hier bewusst NICHT ausgetauscht (anders als bis zum
 * 11.09.2026): Die eigentliche Umschaltung der Ressourcen passiert in
 * [flexr.social.app.MainActivity.applyLanguage] ueber ein ueberschriebenes
 * `getResources()` auf der Activity selbst. `LocalContext.current` bleibt
 * dadurch ueberall die echte Activity, und `stringResource` liest ueber
 * `LocalContext.current.resources` automatisch die dort hinterlegten,
 * lokalisierten Ressourcen - ganz ohne einen zweiten, fabrizierten Context.
 * Diese [Configuration] hier dient nur noch als Ausloeser fuer die
 * Rekomposition: Ihr Inhalt selbst wird von niemandem mehr gelesen.
 */
@Composable
fun ProvideAppLanguage(
    language: AppLanguage,
    content: @Composable () -> Unit,
) {
    val context = LocalContext.current
    val configuration = remember(language, context) {
        Configuration(context.resources.configuration).apply { setLocale(language.locale) }
    }
    CompositionLocalProvider(
        LocalAppLanguage provides language,
        LocalConfiguration provides configuration,
        content = content,
    )
}
