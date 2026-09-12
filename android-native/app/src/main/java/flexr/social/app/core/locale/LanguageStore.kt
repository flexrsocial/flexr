package flexr.social.app.core.locale

import android.content.Context
import android.content.SharedPreferences
import androidx.core.content.edit
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import flexr.social.app.di.ApplicationScope
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

/**
 * Bis zum 11.09.2026 lag die Sprachwahl hier in einem DataStore. Sie liegt
 * jetzt in [SharedPreferences] — aus einem einzigen Grund: Sie muss
 * **synchron** lesbar sein.
 *
 * [flexr.social.app.MainActivity.attachBaseContext] setzt die Sprache am
 * Basis-Context der Activity, und dieser Aufruf kann nicht warten: Er
 * entscheidet, welche Ressourcen die Activity ihr ganzes Leben lang liefert,
 * und laeuft ab, bevor Hilt, Compose oder irgendein Coroutine-Scope existiert.
 * DataStore kann das grundsaetzlich nicht bedienen (nur `suspend`), und
 * `runBlocking` auf dem Hauptfaden waere genau das, wovor DataStore warnt.
 * [SharedPreferences] ist fuer diesen Fall gebaut.
 *
 * Die Wahl gehoert weiterhin dem Geraet, nicht dem Konto — beim Abmelden
 * ([flexr.social.app.data.session.SessionStore.clear]) bleibt sie stehen.
 */
private const val PREFERENCES_NAME = "flexr_language"
private const val LANGUAGE_KEY = "app_language"

/**
 * Der alte DataStore. Er existiert nur noch, um die Wahl eines Nutzers, der
 * schon eine aeltere Fassung installiert hatte, einmalig herueberzuholen
 * (siehe [LanguageStore.migrateLegacyChoice]).
 */
private val Context.legacyLanguageDataStore: DataStore<Preferences> by
    preferencesDataStore(name = "flexr_settings")

private val legacyLanguageKey = stringPreferencesKey("app_language")

/**
 * Gewaehlte Sprache, dauerhaft gespeichert.
 *
 * Solange nichts gewaehlt wurde, liefert [language] das Ergebnis von
 * [AppLanguage.detect]; ein Wechsel der Systemsprache oder ein Umzug wirkt
 * damit weiterhin, bis der Nutzer den Regler einmal selbst bedient.
 */
@Singleton
class LanguageStore @Inject constructor(
    @ApplicationContext private val context: Context,
    @ApplicationScope scope: CoroutineScope,
) {

    private val preferences = preferences(context)

    private val state = MutableStateFlow(storedLanguage(context))

    /**
     * Die ausdrueckliche Wahl — `null`, solange der Regler nie bedient wurde.
     *
     * [language] verschweigt den Unterschied bewusst (es liefert dann die
     * Vorgabe aus [AppLanguage.detect]). Beim Abgleich mit dem Profil zaehlt er
     * aber: Eine Wahl auf diesem Geraet schlaegt das Profil, eine blosse
     * Vorgabe nicht.
     */
    val chosen: StateFlow<AppLanguage?> = state.asStateFlow()

    val language: Flow<AppLanguage> = state.map { it ?: AppLanguage.detect() }

    /**
     * Derselbe Wert wie die erste Ausgabe von [language], nur ohne Warten.
     *
     * Sammler benutzen ihn als Startwert ihres `stateIn`, damit niemand fuer
     * einen Frame auf der Vorgabe steht, obwohl die Wahl laengst feststeht —
     * genau dieser Zwischenstand haette in [flexr.social.app.MainActivity]
     * sonst einen ueberfluessigen Neuaufbau ausgeloest.
     */
    val current: AppLanguage get() = state.value ?: AppLanguage.detect()

    init {
        scope.launch { migrateLegacyChoice() }
    }

    suspend fun setLanguage(language: AppLanguage) = store(language)

    private fun store(language: AppLanguage) {
        preferences.edit { putString(LANGUAGE_KEY, language.code) }
        state.value = language
    }

    /**
     * Wahl aus dem alten DataStore uebernehmen, einmalig.
     *
     * Laeuft nur, wenn hier noch nichts steht. Das Ergebnis kommt zu spaet fuer
     * [flexr.social.app.MainActivity.attachBaseContext] dieses einen Starts —
     * die Activity merkt den Unterschied aber selbst und baut sich neu auf.
     */
    private suspend fun migrateLegacyChoice() {
        if (state.value != null) return
        val code = runCatching { context.legacyLanguageDataStore.data.first()[legacyLanguageKey] }
            .getOrNull()
        AppLanguage.fromCode(code)?.let(::store)
    }

    companion object {

        /**
         * Die gespeicherte Wahl, synchron — fuer `attachBaseContext`, das
         * weder `suspend` sein noch auf Hilt warten kann.
         */
        fun storedLanguage(context: Context): AppLanguage? =
            AppLanguage.fromCode(preferences(context).getString(LANGUAGE_KEY, null))

        private fun preferences(context: Context): SharedPreferences =
            (context.applicationContext ?: context)
                .getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE)
    }
}
