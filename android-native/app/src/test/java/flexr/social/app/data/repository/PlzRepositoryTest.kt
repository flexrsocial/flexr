package flexr.social.app.data.repository

import flexr.social.app.data.remote.OpenPlzApi
import flexr.social.app.data.remote.dto.OpenPlzLocalityDto
import flexr.social.app.data.remote.dto.OpenPlzMunicipalityDto
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class PlzRepositoryTest {

    private class FakeOpenPlzApi(
        private val response: List<OpenPlzLocalityDto>,
    ) : OpenPlzApi {
        var callCount = 0
        override suspend fun localities(postalCode: String): List<OpenPlzLocalityDto> {
            callCount++
            return response
        }
    }

    private fun locality(name: String, municipality: String?) = OpenPlzLocalityDto(
        name = name,
        municipality = municipality?.let { OpenPlzMunicipalityDto(it) },
    )

    @Test
    fun `haeufigste gemeinde gewinnt`() = runTest {
        // Wien 1100 liefert mehrere Ortschaften, aber dieselbe Gemeinde —
        // gespeichert wird die Gemeinde, weil darauf die Umkreissuche aufsetzt.
        val api = FakeOpenPlzApi(
            listOf(
                locality("Wien, Favoriten", "Wien"),
                locality("Wien, Innere Stadt", "Wien"),
                locality("Irgendwo", "Andere Gemeinde"),
            ),
        )
        assertEquals("Wien", PlzRepository(api).municipalityFor("1100"))
    }

    @Test
    fun `ohne gemeindenamen greift der ortsname`() = runTest {
        val api = FakeOpenPlzApi(listOf(locality("Grafendorf bei Hartberg", null)))
        assertEquals("Grafendorf bei Hartberg", PlzRepository(api).municipalityFor("8232"))
    }

    @Test
    fun `leere antwort meldet unbekannte plz`() = runTest {
        val repository = PlzRepository(FakeOpenPlzApi(emptyList()))
        assertThrows(UnknownPostalCodeException::class.java) {
            kotlinx.coroutines.runBlocking { repository.municipalityFor("9999") }
        }
    }

    @Test
    fun `ungueltiges format wird gar nicht erst angefragt`() = runTest {
        val api = FakeOpenPlzApi(emptyList())
        val repository = PlzRepository(api)
        assertThrows(IllegalArgumentException::class.java) {
            kotlinx.coroutines.runBlocking { repository.municipalityFor("10") }
        }
        assertEquals(0, api.callCount)
    }

    @Test
    fun `wiederholte abfrage kommt aus dem cache`() = runTest {
        val api = FakeOpenPlzApi(listOf(locality("Graz", "Graz")))
        val repository = PlzRepository(api)
        repository.municipalityFor("8010")
        repository.municipalityFor("8010")
        assertEquals(1, api.callCount)
    }
}
