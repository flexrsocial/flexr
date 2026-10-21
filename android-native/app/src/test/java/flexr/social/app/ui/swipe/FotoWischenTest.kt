package flexr.social.app.ui.swipe

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Seit 2.7.36 blaettert im Match-Profil ein waagrechtes Wischen auf dem Foto
 * durch die Fotos (vorher nur ueber die Vollbildansicht oder die Striche).
 */
class FotoWischenTest {

    private val schwelle = 100f

    @Test
    fun `nach links kommt das naechste Foto, nach rechts das vorige`() {
        assertEquals(2, photoIndexAfterSwipe(current = 1, count = 4, dragX = -150f, threshold = schwelle))
        assertEquals(0, photoIndexAfterSwipe(current = 1, count = 4, dragX = 150f, threshold = schwelle))
    }

    @Test
    fun `kurze Bewegung unter der Schwelle wechselt nicht`() {
        assertEquals(1, photoIndexAfterSwipe(current = 1, count = 4, dragX = -99f, threshold = schwelle))
        assertEquals(1, photoIndexAfterSwipe(current = 1, count = 4, dragX = 99f, threshold = schwelle))
        assertEquals(2, photoIndexAfterSwipe(current = 1, count = 4, dragX = -100f, threshold = schwelle))
    }

    @Test
    fun `am ersten und letzten Foto bleibt es stehen`() {
        assertEquals(0, photoIndexAfterSwipe(current = 0, count = 3, dragX = 300f, threshold = schwelle))
        assertEquals(2, photoIndexAfterSwipe(current = 2, count = 3, dragX = -300f, threshold = schwelle))
    }

    @Test
    fun `mit einem Foto passiert nichts`() {
        assertEquals(0, photoIndexAfterSwipe(current = 0, count = 1, dragX = -300f, threshold = schwelle))
    }
}
