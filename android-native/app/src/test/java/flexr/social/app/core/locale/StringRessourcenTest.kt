package flexr.social.app.core.locale

import java.io.File
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Android schneidet Leerzeichen am Anfang und Ende eines String-Werts ab,
 * solange er nicht in Anfuehrungszeichen steht. Bis 2.7.30 stand deshalb in
 * der Chatliste "Du:Hey!" und in der Einwilligung bei der Registrierung
 * "... gemäßDatenschutzerklärungverarbeitet werden." - die Teile werden im
 * Code zusammengesetzt und verliessen sich auf diese Leerzeichen.
 */
class StringRessourcenTest {

    private val dateien = listOf("src/main/res/values/strings.xml", "src/main/res/values-en/strings.xml")
    private val wert = Regex("""<string name="([a-z_0-9]+)"[^>]*>(.*?)</string>""", RegexOption.DOT_MATCHES_ALL)

    @Test
    fun `leerzeichen am rand stehen in anfuehrungszeichen`() {
        val fehler = dateien.flatMap { pfad ->
            wert.findAll(File(pfad).readText()).mapNotNull { m ->
                val text = m.groupValues[2]
                val gequotet = text.startsWith("\"") && text.endsWith("\"")
                if (!gequotet && (text.startsWith(" ") || text.endsWith(" "))) {
                    "$pfad: ${m.groupValues[1]}"
                } else {
                    null
                }
            }.toList()
        }
        assertTrue("Leerzeichen gehen verloren: $fehler", fehler.isEmpty())
    }
}
