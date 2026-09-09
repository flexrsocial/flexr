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
 * Bewusst ueber ausgetauschte CompositionLocals und nicht ueber einen Neustart
 * der Activity: `stringResource` liest [LocalContext] und beobachtet
 * [LocalConfiguration], ein Sprachwechsel zeichnet die Oberflaeche also einfach
 * neu. Die Activity bleibt stehen, Navigationsstapel und Scrollpositionen
 * ueberleben den Wechsel — anders als bei `recreate()`.
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
    val localizedContext = remember(configuration) {
        context.createConfigurationContext(configuration)
    }
    CompositionLocalProvider(
        LocalAppLanguage provides language,
        LocalContext provides localizedContext,
        LocalConfiguration provides configuration,
        content = content,
    )
}
