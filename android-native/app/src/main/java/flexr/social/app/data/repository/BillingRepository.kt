package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.CheckoutRequestDto
import flexr.social.app.data.remote.dto.GooglePurchaseRequestDto
import flexr.social.app.data.remote.dto.StorePurchaseResultDto
import flexr.social.app.domain.model.Membership
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Mitgliedschaft: Abo-Status und die Wege, auf denen er entsteht.
 *
 * Zwei davon gibt es, und welcher gilt, entscheidet der Server (siehe
 * `backend/app/clients.py`):
 *
 *  * **In dieser App:** Play Billing. Der einzige zulässige Kaufweg für
 *    digitale Inhalte, die in der App wirken.
 *  * **Im Browser:** Stripe. Die Checkout- und Portal-Aufrufe hier unten
 *    bedient der Server nur für Web-Clients; sie bleiben stehen, weil das
 *    Portal weiterhin erreichbar ist, wenn jemand im Browser gekauft hat.
 *
 * In beiden Fällen kennt die App nur den Status - Zahlungsdaten werden hier
 * weder eingegeben noch verarbeitet.
 */
@Singleton
class BillingRepository @Inject constructor(
    private val api: FlexrApi,
) {

    private val _membership = MutableStateFlow<Membership?>(null)
    val membership: StateFlow<Membership?> = _membership.asStateFlow()

    suspend fun refresh(): Membership {
        val status = apiCall { api.getMembershipStatus() }.toDomain()
        _membership.value = status
        return status
    }

    fun clear() {
        _membership.value = null
    }

    /**
     * Restliche Likes nachziehen, ohne `/api/billing/status` erneut zu holen.
     *
     * Sowohl der Swipe als auch das Zuruecknehmen liefern den neuen Stand in
     * ihrer eigenen Antwort mit - ein zweiter Aufruf nach jedem Like waere
     * reine Verschwendung. Die Web-App macht es an derselben Stelle genauso.
     * `null` heisst unbegrenzt und bleibt dann auch null.
     */
    fun updateLikesRemaining(remaining: Int?) {
        _membership.update { it?.copy(likesRemaining = remaining) }
    }

    /**
     * Beide Erklärungen müssen vor dem Aufruf aktiv bestätigt worden sein
     * (§ 10 und § 18 Abs. 1 Z 1 FAGG) - das Backend lehnt `false` oder ein
     * fehlendes Feld mit 422 ab.
     */
    suspend fun checkoutUrl(immediateStart: Boolean, withdrawalAck: Boolean): String =
        apiCall { api.createCheckout(CheckoutRequestDto(immediateStart, withdrawalAck)) }.checkoutUrl

    /** Self-Service-Verwaltung/Kündigung über das Stripe Billing Portal. */
    suspend fun portalUrl(): String = apiCall { api.createPortal() }.portalUrl

    /**
     * Einen Play-Kauf beim Server einreichen und den Status neu holen.
     *
     * Der Server prüft den Token bei Google und entscheidet; die App schaltet
     * nichts selbst frei. Das anschließende [refresh] ist kein Beiwerk - ohne
     * es stünde nach dem Kauf minutenlang der alte Status in der Oberfläche,
     * bis der nächste Abruf ihn zufällig mitnimmt.
     */
    suspend fun playKaufEinreichen(purchaseToken: String) {
        apiCall<StorePurchaseResultDto> {
            api.submitGooglePurchase(GooglePurchaseRequestDto(purchaseToken))
        }
        refresh()
    }
}
