package flexr.social.app.testing

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.rules.TestWatcher
import org.junit.runner.Description

/**
 * Ersetzt `Dispatchers.Main` durch einen Testdispatcher.
 *
 * ViewModels starten ihre Arbeit in `viewModelScope`, und der läuft auf
 * `Dispatchers.Main`. Ohne diese Regel wirft schon der Konstruktor
 * "Module with the Main dispatcher had failed to initialize" — auf der JVM gibt
 * es keinen Android-Hauptthread.
 *
 * Bewusst [StandardTestDispatcher] statt `UnconfinedTestDispatcher`: gestartete
 * Coroutinen laufen erst, wenn der Test sie über `runCurrent()` oder
 * `advanceUntilIdle()` dazu auffordert. Das macht die Reihenfolge im Test
 * sichtbar, statt sie zu verstecken.
 */
class MainDispatcherRule(
    val dispatcher: TestDispatcher = StandardTestDispatcher(),
) : TestWatcher() {

    override fun starting(description: Description) {
        Dispatchers.setMain(dispatcher)
    }

    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
