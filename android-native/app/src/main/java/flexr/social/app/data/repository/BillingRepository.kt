package flexr.social.app.data.repository

import flexr.social.app.core.network.apiCall
import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.domain.model.Membership
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
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

    suspend fun checkoutUrl(): String = apiCall { api.createCheckout() }.checkoutUrl

    /** Self-Service-Verwaltung/Kündigung über das Stripe Billing Portal. */
    suspend fun portalUrl(): String = apiCall { api.createPortal() }.portalUrl
}
