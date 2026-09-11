package flexr.social.app.core.locale

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.languageDataStore: DataStore<Preferences> by
    preferencesDataStore(name = "flexr_settings")

/**
 * Gewaehlte Sprache, dauerhaft gespeichert.
 *
 * Bewusst ein eigener DataStore neben dem Sitzungsspeicher: die Sprachwahl
 * gehoert dem Geraet, nicht dem Konto — beim Abmelden ([SessionStore.clear])
 * soll sie stehen bleiben.
 *
 * Solange nichts gewaehlt wurde, liefert [language] das Ergebnis von
 * [AppLanguage.detect]; ein Wechsel der Systemsprache oder ein Umzug wirkt
 * damit weiterhin, bis der Nutzer den Regler einmal selbst bedient.
 */
@Singleton
class LanguageStore @Inject constructor(
    @ApplicationContext private val context: Context,
) {

    private val key = stringPreferencesKey("app_language")

    val language: Flow<AppLanguage> = context.languageDataStore.data
        .map { AppLanguage.fromCode(it[key]) ?: AppLanguage.detect() }

    /**
     * Die ausdrueckliche Wahl — `null`, solange der Regler nie bedient wurde.
     *
     * [language] verschweigt den Unterschied bewusst (es liefert dann die
     * Vorgabe aus [AppLanguage.detect]). Beim Abgleich mit dem Profil zaehlt er
     * aber: Eine Wahl auf diesem Geraet schlaegt das Profil, eine blosse
     * Vorgabe nicht.
     */
    val chosen: Flow<AppLanguage?> = context.languageDataStore.data
        .map { AppLanguage.fromCode(it[key]) }

    suspend fun setLanguage(language: AppLanguage) {
        context.languageDataStore.edit { it[key] = language.code }
    }
}
