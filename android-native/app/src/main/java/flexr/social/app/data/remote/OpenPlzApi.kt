package flexr.social.app.data.remote

import flexr.social.app.data.remote.dto.OpenPlzLocalityDto
import retrofit2.http.GET
import retrofit2.http.Query

/**
 * Öffentliche PLZ-Datenbank (openplzapi.org) für die Ortsermittlung —
 * dieselbe Quelle, die das Web-Frontend nutzt. Damit ist ganz Österreich
 * abgedeckt, ohne eine gepflegte Städteliste in der App.
 */
interface OpenPlzApi {

    @GET("at/Localities")
    suspend fun localities(@Query("postalCode") postalCode: String): List<OpenPlzLocalityDto>
}
