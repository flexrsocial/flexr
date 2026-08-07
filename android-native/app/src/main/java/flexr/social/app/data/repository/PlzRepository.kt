package flexr.social.app.data.repository

import flexr.social.app.core.network.FlexrApiException
import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import javax.inject.Inject
import javax.inject.Singleton

/** Fehler, wenn zu einer eingegebenen PLZ kein österreichischer Ort existiert. */
class UnknownPostalCodeException : Exception("Postleitzahl nicht gefunden. Bitte prüfen.")

/**
 * Ortsermittlung zur Postleitzahl über das eigene Backend.
 *
 * Früher fragte die App dafür openplzapi.org direkt an. Das ging zweimal
 * schief: der Dienst beantwortet Requests mit OkHttp-User-Agent mit HTTP 418,
 * womit in der App überhaupt keine PLZ mehr auflösbar war und die
 * Registrierung scheiterte — und seine seitenweise begrenzte Ortschaftsliste
 * ließ die Häufigkeits-Heuristik bei großen PLZ danebengreifen (4020 wurde zu
 * „Leonding" statt „Linz"). Das Backend liefert jetzt den amtlichen Ortsnamen.
 */
@Singleton
class PlzRepository @Inject constructor(
    private val api: FlexrApi,
) {

    private val cache = mutableMapOf<String, String>()

    suspend fun municipalityFor(postalCode: String): String {
        val plz = postalCode.trim()
        require(POSTAL_CODE_PATTERN.matches(plz)) { "Ungültige Postleitzahl." }
        cache[plz]?.let { return it }

        val city = try {
            apiCall { api.lookupPostalCode(plz) }.city
        } catch (exception: FlexrApiException) {
            if (exception.statusCode == 404) throw UnknownPostalCodeException() else throw exception
        }

        cache[plz] = city
        return city
    }

    companion object {
        val POSTAL_CODE_PATTERN = Regex("^\\d{4}$")
    }
}
