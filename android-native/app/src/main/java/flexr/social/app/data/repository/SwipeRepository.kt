package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.SwipeRequestDto
import flexr.social.app.domain.model.IncomingLikes
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
        return SwipeOutcome(matched = result.matched, likesRemaining = result.likesRemaining)
    }

    /**
     * Wer mich geliket hat - eine Premium-Funktion.
     *
     * Ohne Premium wirft der Server bewusst keinen Fehler, sondern liefert die
     * Anzahl ohne Profile. Die Oberflaeche unterscheidet die beiden Faelle an
     * [IncomingLikes.premiumRequired].
     */
    suspend fun incomingLikes(): IncomingLikes = apiCall { api.incomingLikes() }.toDomain()

    /**
     * Letzten Swipe zuruecknehmen - eine Premium-Funktion.
     *
     * Ohne Premium kommt 403 mit `code = premium_required`, bei einem bereits
     * entstandenen Match 409. Beides reicht der Aufrufer als Meldung durch,
     * statt es hier zu verschlucken: Der Unterschied ist fuer den Nutzer
     * erheblich ("brauchst Premium" gegen "daraus ist schon ein Match
     * geworden").
     */
    suspend fun rewindLastSwipe(): RewindOutcome {
        val result = apiCall { api.rewindLastSwipe() }
        return RewindOutcome(toUserId = result.toUserId, likesRemaining = result.likesRemaining)
    }
}

/** Ergebnis eines zurueckgenommenen Swipes. */
data class RewindOutcome(
    val toUserId: String,
    val likesRemaining: Int?,
)
