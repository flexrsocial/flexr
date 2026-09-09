package flexr.social.app.core.locale

import android.content.Context
import android.content.res.Configuration
import androidx.annotation.StringRes
import dagger.hilt.android.qualifiers.ApplicationContext
import flexr.social.app.di.ApplicationScope
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

/**
 * Texte fuer alles, was ausserhalb von Compose entsteht: ViewModels, die
 * Fehlermeldungen in ihren Zustand schreiben, und die Benachrichtigungs-Worker.
 *
 * In Compose wird weiterhin `stringResource` benutzt — dort sorgt
 * [ProvideAppLanguage] dafuer, dass die Ressourcen in der gewaehlten Sprache
 * aufgeloest werden. Beides greift auf dieselben `strings.xml` zu.
 *
 * Bewusst eine Schnittstelle: die Umsetzung haengt am Android-Context und
 * machte jedes ViewModel darueber in reinen JVM-Tests unkonstruierbar — dort
 * kommt `FakeAppStrings` zum Einsatz, wie schon bei `SessionStore`.
 */
interface AppStrings {

    fun get(@StringRes id: Int): String

    fun get(@StringRes id: Int, vararg args: Any): String
}

/**
 * [AppStrings] auf Basis der Android-Ressourcen.
 *
 * Der Startwert ist [AppLanguage.detect] und damit schon die richtige
 * Vermutung; sobald der gespeicherte Wert aus dem DataStore da ist, zieht der
 * Zustand nach. Das spart einen blockierenden Lesevorgang beim Start.
 */
@Singleton
class ResourceAppStrings @Inject constructor(
    @ApplicationContext private val context: Context,
    languageStore: LanguageStore,
    @ApplicationScope scope: CoroutineScope,
) : AppStrings {

    private val language: StateFlow<AppLanguage> = languageStore.language
        .stateIn(scope, SharingStarted.Eagerly, AppLanguage.detect())

    /**
     * Ein Context mit der gewaehlten Sprache. Wird bei jedem Zugriff neu
     * gebaut — das ist nur ein Resources-Wrapper und billiger, als einen
     * zwischengespeicherten Stand nach einem Sprachwechsel aufzuraeumen.
     */
    private fun localized(): Context {
        val locale: Locale = language.value.locale
        val configuration = Configuration(context.resources.configuration).apply {
            setLocale(locale)
        }
        return context.createConfigurationContext(configuration)
    }

    override fun get(@StringRes id: Int): String = localized().getString(id)

    override fun get(@StringRes id: Int, vararg args: Any): String =
        localized().getString(id, *args)
}
