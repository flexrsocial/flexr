package flexr.social.app.ui.swipe

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Bis 2.7.38 stand beim selben Gym „0 km" auf der Karte. Der Server rundet die
 * Entfernung zwischen den Gyms auf ganze Kilometer, 0 heisst unter 500 m.
 */
class EntfernungTest {

    @Test
    fun `null Kilometer heisst unter einem Kilometer`() {
        assertEquals("< 1 km", distanceLabel(0))
    }

    @Test
    fun `ab einem Kilometer die Zahl`() {
        assertEquals("1 km", distanceLabel(1))
        assertEquals("142 km", distanceLabel(142))
    }
}
