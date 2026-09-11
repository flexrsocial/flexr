package flexr.social.app.core.locale

import android.content.Context
import android.content.ContextWrapper
import android.content.res.AssetManager
import android.content.res.Configuration
import android.content.res.Resources
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
 * Ein Context, der die Ressourcen einer anderen Sprache liefert, sonst aber
 * derselbe bleibt.
 *
 * Der naheliegende Weg waere `context.createConfigurationContext(config)`
 * gewesen, und genau so stand es hier bis zum 11.09.2026. Der Rueckgabewert
 * davon ist aber ein **frischer Context ohne Bezug zur Activity**: Seine
 * `baseContext`-Kette endet im Anwendungs-Context. Alles, was sich aus
 * `LocalContext` die Activity zurueckholt - und das tun sowohl Teile von
 * Compose als auch CameraX, die Custom Tabs und jeder `context as Activity` -
 * findet dort keine mehr und scheitert.
 *
 * Deshalb hier ein [ContextWrapper] um den **urspruenglichen** Context: Die
 * Kette zur Activity bleibt unangetastet, `getSystemService`, Theme und
 * Fenster kommen unveraendert von ihr. Ausgetauscht werden nur Ressourcen und
 * Assets - und genau die liest `stringResource`.
 */
private class LokalisierterContext(
    basis: Context,
    private val ressourcen: Resources,
) : ContextWrapper(basis) {
    override fun getResources(): Resources = ressourcen
    override fun getAssets(): AssetManager = ressourcen.assets
}

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
    val localizedContext = remember(configuration, context) {
        // createConfigurationContext liefert die uebersetzten Ressourcen; nur
        // die werden uebernommen, der Context selbst bleibt der der Activity.
        LokalisierterContext(context, context.createConfigurationContext(configuration).resources)
    }
    CompositionLocalProvider(
        LocalAppLanguage provides language,
        LocalContext provides localizedContext,
        LocalConfiguration provides configuration,
        content = content,
    )
}
