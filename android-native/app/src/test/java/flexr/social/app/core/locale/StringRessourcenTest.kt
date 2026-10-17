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

    @Test
    fun `jeder text hat eine englische fassung`() {
        val deutsch = Regex("""<string name="([a-z_0-9]+)"(?![^>]*translatable="false")""")
            .findAll(File(dateien[0]).readText()).map { it.groupValues[1] }.toSet()
        val englisch = wert.findAll(File(dateien[1]).readText()).map { it.groupValues[1] }.toSet()
        val fehlend = deutsch - englisch
        assertTrue("Ohne englische Fassung (faellt auf Deutsch zurueck): $fehlend", fehlend.isEmpty())
    }

    /**
     * Bis 2.7.36 standen auf dem Login-Bildschirm auch bei englischer Sprache
     * "Einloggen" und "Registrieren", der Senden-Knopf im Chat hiess fuer
     * TalkBack immer "Senden", und das PLZ-Feld war immer mit "Postleitzahl"
     * beschriftet - alles direkt im Kotlin-Code statt in strings.xml.
     *
     * Geprueft werden die Stellen, an denen Text auf dem Bildschirm oder bei
     * TalkBack landet. Die Rechtstexte (LegalContent.kt) sind bewusst nur
     * deutsch: In der englischen Oberflaeche bleibt die deutsche Fassung
     * massgeblich (lang_row_hint).
     */
    @Test
    fun `keine fest eingetragenen texte in der oberflaeche`() {
        val aufruf = Regex(
            """(?:\b(?:contentDescription|text|label|title|placeholder|description|[a-z]+Label)""" +
                """\s*(?::\s*String\??\s*)?=\s*|\bText\(\s*|Message\(\s*|Fehlgeschlagen\(\s*""" +
                // Auch als Zweig oder Ersatzwert: text = if (...) "Einloggen" else "Registrieren",
                // fehler.message ?: "...", debugMessage.ifBlank { "..." }
                """|\?:\s*|\belse\s+|\bif\s*\([^)]*\)\s*|\bif(?:Blank|Empty)\s*\{\s*)"((?:[^"\\]|\\.)*)"""",
        )
        val vorlage = Regex("""\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*""")
        val wort = Regex("""\b[A-ZÄÖÜ][a-zäöüß]{2,}|[äöüÄÖÜß]|[A-Za-z]{2,} [A-Za-z]{2,}""")
        // Namen fuer den Animations-Inspektor (`animate*AsState(label = ...)`)
        // erscheinen nirgends - z. B. "SprachreglerKnopf".
        val bezeichner = Regex("""[A-Za-z][a-z0-9]*(?:[A-Z][a-z0-9]+)+""")
        val fehler = File("src/main/java").walk()
            .filter { it.extension == "kt" && it.name != "LegalContent.kt" }
            .flatMap { datei ->
                datei.readLines().withIndex()
                    .filterNot { (_, zeile) -> zeile.trimStart().let { it.startsWith("//") || it.startsWith("*") } }
                    .flatMap { (nummer, zeile) ->
                        aufruf.findAll(zeile)
                            .map { it.groupValues[1] }
                            .filterNot { text -> "@" in text || bezeichner.matches(text) }
                            .filter { text -> wort.containsMatchIn(text.replace(vorlage, "")) }
                            .map { text -> "${datei.name}:${nummer + 1} \"$text\"" }
                    }
            }
            .toList()
        assertTrue("Fest eingetragene Texte gehoeren in strings.xml: $fehler", fehler.isEmpty())
    }
}
