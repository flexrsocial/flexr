package flexr.social.app.core.designsystem.component

import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.input.TextFieldValue
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Einfügeregeln des Emoji-Pickers — dieselben wie im Web-Frontend:
 * an der Cursorposition, ersetzt eine Auswahl, respektiert das Längenlimit.
 */
class EmojiInsertTest {

    @Test
    fun `fuegt an der cursorposition ein`() {
        val vorher = TextFieldValue("Training macht Spass", TextRange(8))
        val nachher = vorher.withEmojiInserted("💪", maxLength = 280)
        assertEquals("Training💪 macht Spass", nachher.text)
    }

    @Test
    fun `setzt den cursor hinter das eingefuegte emoji`() {
        val vorher = TextFieldValue("ab", TextRange(1))
        val nachher = vorher.withEmojiInserted("🔥", maxLength = null)
        assertEquals("a🔥b", nachher.text)
        assertEquals(1 + "🔥".length, nachher.selection.start)
        assertTrue(nachher.selection.collapsed)
    }

    @Test
    fun `haengt bei leerem feld einfach an`() {
        val nachher = TextFieldValue("").withEmojiInserted("🏋️", maxLength = 280)
        assertEquals("🏋️", nachher.text)
    }

    @Test
    fun `ersetzt eine markierte auswahl`() {
        val vorher = TextFieldValue("Hallo Welt", TextRange(6, 10))
        val nachher = vorher.withEmojiInserted("🌊", maxLength = 280)
        assertEquals("Hallo 🌊", nachher.text)
    }

    @Test
    fun `laesst den text unveraendert wenn das limit ueberschritten wuerde`() {
        val voll = "x".repeat(280)
        val vorher = TextFieldValue(voll, TextRange(280))
        val nachher = vorher.withEmojiInserted("💯", maxLength = 280)
        assertEquals(voll, nachher.text)
        assertEquals(280, nachher.text.length)
    }

    @Test
    fun `ohne limit wird immer eingefuegt`() {
        val lang = "y".repeat(5000)
        val nachher = TextFieldValue(lang, TextRange(0)).withEmojiInserted("✨", maxLength = null)
        assertTrue(nachher.text.startsWith("✨"))
    }

    @Test
    fun `cursor hinter dem textende wird abgefangen`() {
        // Kann auftreten, wenn der Text von aussen gekuerzt wurde, die alte
        // Auswahl aber noch steht.
        val vorher = TextFieldValue("kurz", TextRange(99))
        val nachher = vorher.withEmojiInserted("🎯", maxLength = 280)
        assertEquals("kurz🎯", nachher.text)
    }

    @Test
    fun `katalog ist frei von doppelten eintraegen und nicht leer`() {
        val liste = EmojiCatalog.emojis
        assertTrue(liste.size > 150)
        assertEquals(liste.size, liste.toSet().size)
        assertTrue(liste.contains("💪"))
    }
}
