package flexr.social.app.core.common

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.Instant
import java.time.LocalDate

class ServerTimeTest {

    @Test
    fun `zeitstempel ohne zeitzone wird als UTC gelesen`() {
        // Das Backend liefert datetime.utcnow() ohne Offset. Würde die App den
        // Wert als Lokalzeit lesen, wäre eine stundengenaue Chat-Sperre um den
        // lokalen Offset verschoben.
        val parsed = ServerTime.parse("2026-07-26T20:30:00")
        assertEquals(Instant.parse("2026-07-26T20:30:00Z"), parsed)
    }

    @Test
    fun `zeitstempel mit offset behaelt seinen offset`() {
        val parsed = ServerTime.parse("2026-07-26T22:30:00+02:00")
        assertEquals(Instant.parse("2026-07-26T20:30:00Z"), parsed)
    }

    @Test
    fun `mikrosekunden werden akzeptiert`() {
        val parsed = ServerTime.parse("2026-07-26T20:30:00.123456")
        assertEquals(Instant.parse("2026-07-26T20:30:00.123456Z"), parsed)
    }

    @Test
    fun `leerer wert ergibt null`() {
        assertNull(ServerTime.parse(null))
        assertNull(ServerTime.parse(""))
    }

    @Test
    fun `alter wird wie im backend berechnet`() {
        val today = LocalDate.of(2026, 7, 26)
        // Geburtstag war heute
        assertEquals(30, ServerTime.ageFrom(LocalDate.of(1996, 7, 26), today))
        // Geburtstag ist morgen: noch ein Jahr jünger
        assertEquals(29, ServerTime.ageFrom(LocalDate.of(1996, 7, 27), today))
        assertEquals(30, ServerTime.ageFrom(LocalDate.of(1996, 7, 25), today))
    }

    @Test
    fun `resttage werden aufgerundet und nie negativ`() {
        val now = Instant.parse("2026-07-26T12:00:00Z")
        assertEquals(1, ServerTime.daysUntil(Instant.parse("2026-07-27T00:00:00Z"), now))
        assertEquals(2, ServerTime.daysUntil(Instant.parse("2026-07-28T06:00:00Z"), now))
        assertEquals(0, ServerTime.daysUntil(Instant.parse("2026-07-25T12:00:00Z"), now))
    }
}
