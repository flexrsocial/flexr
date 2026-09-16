package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.CheckoutRequestDto
import flexr.social.app.domain.model.Membership
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Mitgliedschaft: Probemonat, Abo-Status und die Stripe-Übergänge.
 *
 * Checkout und Kündigung laufen bewusst über eine externe Browser-Sitzung
 * (Custom Tab). Zahlungsdaten werden dadurch nie in der App eingegeben oder
 * verarbeitet — die App kennt nur den Status.
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
}
