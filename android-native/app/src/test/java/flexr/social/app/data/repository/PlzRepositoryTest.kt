package flexr.social.app.data.repository

import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.data.remote.dto.PlzLookupDto
import flexr.social.app.testing.FakeFlexrApi
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class PlzRepositoryTest {

    private class FakePlzApi(private val antwort: () -> PlzLookupDto) : FakeFlexrApi() {
        var callCount = 0
        override suspend fun lookupPostalCode(plz: String): PlzLookupDto {
            callCount++
            return antwort()
        }
    }

    @Test
    fun `ort kommt vom backend`() = runTest {
        val api = FakePlzApi { PlzLookupDto(plz = "4020", city = "Linz") }
        assertEquals("Linz", PlzRepository(api).municipalityFor("4020"))
    }

    @Test
    fun `404 meldet unbekannte plz`() = runTest {
        val api = FakePlzApi { throw FlexrApiException(404, "Postleitzahl nicht gefunden. Bitte prüfen.") }
        val repository = PlzRepository(api)
        assertThrows(UnknownPostalCodeException::class.java) {
            kotlinx.coroutines.runBlocking { repository.municipalityFor("9999") }
        }
    }

    @Test
    fun `andere fehler bleiben unterscheidbar`() = runTest {
        // Netzausfall darf nicht als „PLZ gibt es nicht" beim Nutzer landen.
        val api = FakePlzApi { throw FlexrApiException(0, "Keine Internetverbindung.") }
        val repository = PlzRepository(api)
        val fehler = assertThrows(FlexrApiException::class.java) {
            kotlinx.coroutines.runBlocking { repository.municipalityFor("1010") }
        }
        assertEquals(0, fehler.statusCode)
    }

    @Test
    fun `ungueltiges format wird gar nicht erst angefragt`() = runTest {
        val api = FakePlzApi { PlzLookupDto(plz = "1010", city = "Wien") }
        val repository = PlzRepository(api)
        assertThrows(IllegalArgumentException::class.java) {
            kotlinx.coroutines.runBlocking { repository.municipalityFor("10") }
        }
        assertEquals(0, api.callCount)
    }

    @Test
    fun `wiederholte abfrage kommt aus dem cache`() = runTest {
        val api = FakePlzApi { PlzLookupDto(plz = "8010", city = "Graz") }
        val repository = PlzRepository(api)
        repository.municipalityFor("8010")
        repository.municipalityFor("8010")
        assertEquals(1, api.callCount)
    }
}
