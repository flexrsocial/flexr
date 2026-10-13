package flexr.social.app.ui.account

import flexr.social.app.ui.account.AccountViewModel.Companion.MAX_RADIUS_KM
import flexr.social.app.ui.account.AccountViewModel.Companion.MIN_RADIUS_KM
import flexr.social.app.ui.account.AccountViewModel.Companion.radiusAusStellung
import flexr.social.app.ui.account.AccountViewModel.Companion.stellungAusRadius
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Seit 2.7.23 reicht der Regler bis 580 km und laeuft quadratisch (siehe
 * AccountViewModel.radiusAusStellung). Linear laegen 50 km bei 8 % der
 * Schiene - die kleinen Umkreise waeren mit dem Finger kaum zu treffen.
 */
class RadiusSkalaTest {

    @Test
    fun `Enden des Reglers sind Minimum und Maximum`() {
        assertEquals(MIN_RADIUS_KM, radiusAusStellung(0f, MAX_RADIUS_KM))
        assertEquals(MAX_RADIUS_KM, radiusAusStellung(1f, MAX_RADIUS_KM))
        assertEquals(580, MAX_RADIUS_KM)
    }

    @Test
    fun `kleine Umkreise bekommen einen brauchbaren Teil der Schiene`() {
        val bei50 = stellungAusRadius(50, MAX_RADIUS_KM)
        val bei20 = stellungAusRadius(20, MAX_RADIUS_KM)
        assertTrue("50 km bei $bei50", bei50 in 0.28f..0.30f)
        assertTrue("20 km bei $bei20", bei20 in 0.17f..0.19f)
    }

    @Test
    fun `jeder Wert uebersteht den Weg ueber die Stellung`() {
        // Der Regler zeigt den gespeicherten Wert an; ein Zurueckrechnen darf
        // ihn nicht verschieben, sonst aendert schon das Oeffnen des Kontos
        // den Umkreis.
        for (km in MIN_RADIUS_KM..MAX_RADIUS_KM) {
            assertEquals(km, radiusAusStellung(stellungAusRadius(km, MAX_RADIUS_KM), MAX_RADIUS_KM))
        }
        // Auch mit der Grenze des kostenlosen Kontos (Regler endet bei 50 km).
        for (km in MIN_RADIUS_KM..50) {
            assertEquals(km, radiusAusStellung(stellungAusRadius(km, 50), 50))
        }
    }

    @Test
    fun `ausserhalb liegende Werte werden gekappt`() {
        assertEquals(1f, stellungAusRadius(900, MAX_RADIUS_KM))
        assertEquals(0f, stellungAusRadius(0, MAX_RADIUS_KM))
        assertEquals(MAX_RADIUS_KM, radiusAusStellung(1.5f, MAX_RADIUS_KM))
        assertEquals(1f, stellungAusRadius(MIN_RADIUS_KM, MIN_RADIUS_KM))
    }
}
