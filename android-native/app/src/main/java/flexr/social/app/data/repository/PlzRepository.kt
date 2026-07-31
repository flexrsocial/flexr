package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.OpenPlzApi
import javax.inject.Inject
import javax.inject.Named
import javax.inject.Singleton

/** Fehler, wenn zu einer eingegebenen PLZ kein österreichischer Ort existiert. */
class UnknownPostalCodeException : Exception("Postleitzahl nicht gefunden. Bitte prüfen.")

/**
 * Ortsermittlung zur Postleitzahl über die OpenPLZ-API.
 *
 * Gespeichert wird der GEMEINDE-Name (z. B. „Wien", „Graz"), nicht die einzelne
 * Ortschaft („Wien, Favoriten") — die Gemeinde ist die sinnvolle Ebene für die
 * Umkreissuche. Heuristik wie im Web: der häufigste Gemeindename unter allen
 * Treffern der PLZ.
 */
@Singleton
class PlzRepository @Inject constructor(
    @Named("openPlz") private val api: OpenPlzApi,
) {

    private val cache = mutableMapOf<String, String>()

    suspend fun municipalityFor(postalCode: String): String {
        val plz = postalCode.trim()
        require(POSTAL_CODE_PATTERN.matches(plz)) { "Ungültige Postleitzahl." }
        cache[plz]?.let { return it }

        val localities = apiCall { api.localities(plz) }
        if (localities.isEmpty()) throw UnknownPostalCodeException()

        val municipality = localities
            .mapNotNull { it.municipality?.name }
            .groupingBy { it }
            .eachCount()
            .maxByOrNull { it.value }
            ?.key
            ?: localities.firstNotNullOfOrNull { it.name }
            ?: throw UnknownPostalCodeException()

        cache[plz] = municipality
        return municipality
    }

    companion object {
        val POSTAL_CODE_PATTERN = Regex("^\\d{4}$")
    }
}
