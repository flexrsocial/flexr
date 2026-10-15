package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.GymSuggestRequestDto
import flexr.social.app.domain.model.Gym
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Fitnessstudios: durchsuchbare Liste (OSM-Import + freigegebene Vorschläge)
 * und die Vorschlagsfunktion für fehlende Studios.
 */
@Singleton
class GymRepository @Inject constructor(
    private val api: FlexrApi,
    private val plzRepository: PlzRepository,
) {

    /**
     * [nearPostalCode]: die schon eingegebene PLZ. Damit stehen nahe Studios
     * oben - bei Ketten mit 20+ Filialen lag das eigene sonst hinter allen
     * Wiener Filialen (Sortierung nur nach Name und PLZ).
     */
    suspend fun search(query: String, nearPostalCode: String? = null): List<Gym> =
        apiCall {
            api.searchGyms(
                query = query.trim(),
                near = nearPostalCode?.trim()?.takeIf { it.length == 4 && it.all(Char::isDigit) },
            )
        }.map { it.toDomain() }

    /**
     * Vorschlag einreichen. Der Ort wird — wie im Web — still über die
     * PLZ-Datenbank ermittelt; schlägt das fehl, bleibt er leer und der Admin
     * ergänzt ihn bei der Freigabe.
     */
    suspend fun suggest(
        name: String,
        street: String,
        houseNumber: String,
        plz: String,
    ): Gym {
        val city = runCatching { plzRepository.municipalityFor(plz) }.getOrNull()
        return apiCall {
            api.suggestGym(
                GymSuggestRequestDto(
                    name = name.trim(),
                    street = street.trim(),
                    houseNumber = houseNumber.trim(),
                    plz = plz.trim(),
                    city = city?.takeIf { it.isNotBlank() },
                ),
            )
        }.toDomain()
    }
}
