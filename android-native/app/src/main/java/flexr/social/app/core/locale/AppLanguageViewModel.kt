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

    val language: StateFlow<AppLanguage> = store.language
        .stateIn(viewModelScope, SharingStarted.Eagerly, AppLanguage.detect())

    /**
     * Sprache waehlen.
     *
     * Die Oberflaeche stellt sofort um — das laeuft ohne Server. Die Meldung
     * ans Profil kommt hinterher und darf scheitern: Der Server braucht sie
     * nur fuer seine E-Mails, und [MainViewModel] holt sie beim naechsten
     * Start ohnehin nach.
     */
    fun select(language: AppLanguage) {
        viewModelScope.launch {
            store.setLanguage(language)
            profileRepository.reportLanguage(language.code)
        }
    }
}
