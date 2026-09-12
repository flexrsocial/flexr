package flexr.social.app.core.locale

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import flexr.social.app.data.repository.ProfileRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

/**
 * Gewaehlte Sprache fuer die Oberflaeche.
 *
 * Wird an zwei Stellen geholt — einmal in der [flexr.social.app.MainActivity],
 * um die ganze App in [ProvideAppLanguage] zu huellen, und einmal im
 * Kontobereich fuer den Regler. Beide sehen denselben Zustand, weil der
 * [LanguageStore] dahinter ein Singleton ist.
 */
@HiltViewModel
class AppLanguageViewModel @Inject constructor(
    private val store: LanguageStore,
    private val profileRepository: ProfileRepository,
) : ViewModel() {

    /**
     * Startwert ist [LanguageStore.current], nicht [AppLanguage.detect]: Die
     * gespeicherte Wahl steht synchron fest, und
     * [flexr.social.app.MainActivity] vergleicht diesen Wert mit der Sprache,
     * mit der sie aufgebaut wurde. Ein Startwert "Vorgabe", der sich einen
     * Wimpernschlag spaeter korrigiert, wuerde dort einen ueberfluessigen
     * Neuaufbau ausloesen.
     */
    val language: StateFlow<AppLanguage> = store.language
        .stateIn(viewModelScope, SharingStarted.Eagerly, store.current)

    /**
     * Sprache waehlen.
     *
     * Gespeichert wird sofort und ohne Server; die Oberflaeche zieht nach,
     * sobald [flexr.social.app.MainActivity] die Activity mit der neuen
     * Sprache neu aufbaut. Die Meldung ans Profil kommt hinterher und darf
     * scheitern: Der Server braucht sie nur fuer seine E-Mails, und
     * [MainViewModel] holt sie beim naechsten Start ohnehin nach.
     */
    fun select(language: AppLanguage) {
        viewModelScope.launch {
            store.setLanguage(language)
            // Nur mit geladenem Profil: Der Regler steht seit dem 12.09.2026
            // auch auf dem Startbildschirm, und dort gibt es keine Sitzung.
            // Die Meldung liefe in ein 401, und der SessionExpiryInterceptor
            // wuerde daraufhin den Token verwerfen. Verloren geht dadurch
            // nichts - die Registrierung schickt die Sprache selbst mit
            // (RegisterViewModel), und MainViewModel.syncLanguage holt sie beim
            // naechsten Login nach.
            if (profileRepository.myProfile.value != null) {
                profileRepository.reportLanguage(language.code)
            }
        }
    }
}
