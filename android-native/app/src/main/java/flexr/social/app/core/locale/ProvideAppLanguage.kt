package flexr.social.app.core.locale

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.ProvidableCompositionLocal
import androidx.compose.runtime.compositionLocalOf

/**
 * Die gerade gewaehlte Sprache, fuer Stellen, die sie selbst kennen muessen
 * (der Sprachregler, um seinen Zustand zu zeichnen).
 */
val LocalAppLanguage: ProvidableCompositionLocal<AppLanguage> =
    compositionLocalOf { AppLanguage.DEFAULT }

/**
 * Stellt [LocalAppLanguage] bereit.
 *
 * Hier wird an den Ressourcen **nichts** mehr gedreht. Bis zum 11.09.2026
 * tauschte diese Funktion `LocalContext` bzw. `LocalConfiguration` aus, um
 * `stringResource` zur Laufzeit umzubiegen; am Geraet blieben die Texte
 * trotzdem deutsch. Die Umschaltung sitzt jetzt dort, wo Android sie vorsieht:
 * am Basis-Context der Activity ([flexr.social.app.MainActivity.attachBaseContext]).
 * Damit loest `stringResource` von sich aus richtig auf — `LocalContext` ist
 * ueberall die echte, richtig lokalisierte Activity, und `LocalConfiguration`
 * traegt deren Sprache ohne Zutun.
 *
 * Bleibt genau eine Aufgabe: Der Regler muss wissen, welches Segment leuchtet.
 */
@Composable
fun ProvideAppLanguage(
    language: AppLanguage,
    content: @Composable () -> Unit,
) {
    CompositionLocalProvider(
        LocalAppLanguage provides language,
        content = content,
    )
}
