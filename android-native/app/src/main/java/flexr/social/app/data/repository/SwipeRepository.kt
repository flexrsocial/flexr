package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.SwipeRequestDto
import flexr.social.app.domain.model.Profile
import flexr.social.app.domain.model.SwipeOutcome
import javax.inject.Inject
import javax.inject.Singleton

/** Swipe-Deck und Like/Pass. Entspricht backend/app/routers/swipes.py. */
@Singleton
class SwipeRepository @Inject constructor(
    private val api: FlexrApi,
) {

    /**
     * Kandidaten im gewählten Umkreis, bereits serverseitig nach Entfernung
     * sortiert und auf Profile mit mindestens einem freigegebenen Foto gefiltert.
     */
    suspend fun loadDeck(): List<Profile> = apiCall { api.getDeck() }.map { it.toDomain() }

    suspend fun like(userId: String): SwipeOutcome = swipe(userId, "like")

    suspend fun pass(userId: String): SwipeOutcome = swipe(userId, "pass")

    private suspend fun swipe(userId: String, action: String): SwipeOutcome {
        val result = apiCall { api.swipe(SwipeRequestDto(userId, action)) }
        return SwipeOutcome(matched = result.matched)
    }
}
