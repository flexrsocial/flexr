package flexr.social.app.data.billing

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.AcknowledgePurchaseParams
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import dagger.hilt.android.qualifiers.ApplicationContext
import flexr.social.app.data.repository.BillingRepository
import flexr.social.app.di.ApplicationScope
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume

/**
 * FLEXR Premium über Google Play kaufen.
 *
 * Für digitale Inhalte, die in dieser App wirken, ist Play Billing der einzige
 * zulässige Kaufweg (Play-Payments-Policy) — Stripe bleibt dem Browser. Was
 * beide gemeinsam haben: **Die App schaltet nichts frei.** Sie reicht nur den
 * Kauf-Token beim Server ein; ob daraus Premium wird, entscheidet der Server
 * nach Rückfrage bei Google (siehe `backend/app/store_billing.py`). Ein
 * manipulierter Client kann sich hier nichts erschleichen.
 *
 * Drei Wege führen zu einem Token, und alle drei münden in [einreichen]:
 *
 *  1. Der Kauf selbst ([kaufen] → [PurchasesUpdatedListener]).
 *  2. [bestehendeKaeufeAbgleichen] beim Start. Das ist kein Beiwerk, sondern
 *     der Weg zurück aus jeder Störung: Wer beim Kauf gerade keine Verbindung
 *     hatte oder das Gerät gewechselt hat, bekommt sein Premium dadurch von
 *     selbst wieder — ohne einen Knopf „Kauf wiederherstellen", den er erst
 *     suchen müsste.
 *  3. Ein noch offener Kauf, der später bestätigt wird (Lastschrift,
 *     Gutschein) — Google meldet ihn dann nachträglich an denselben Listener.
 *
 * Bestätigt (`acknowledge`) wird serverseitig, sobald die Berechtigung
 * wirklich gutgeschrieben ist. Ohne Bestätigung storniert Google den Kauf nach
 * drei Tagen und erstattet das Geld — der Kunde hätte bezahlt und stünde
 * trotzdem ohne Premium da.
 */
@Singleton
class PlayBillingService @Inject constructor(
    @ApplicationContext private val context: Context,
    private val repository: BillingRepository,
    @ApplicationScope private val scope: CoroutineScope,
) {

    /** Was der Kaufversuch ergeben hat — für die Oberfläche. */
    sealed interface Ereignis {
        data object Erfolgreich : Ereignis
        data object Abgebrochen : Ereignis
        data class Fehlgeschlagen(val meldung: String) : Ereignis
    }

    private val _ereignisse = MutableSharedFlow<Ereignis>(
        replay = 0,
        extraBufferCapacity = 1,
        onBufferOverflow = BufferOverflow.DROP_OLDEST,
    )
    val ereignisse: SharedFlow<Ereignis> = _ereignisse

    /** Der Preis, wie der Play Store ihn in der Sprache des Geräts schreibt. */
    private val _preis = MutableStateFlow<String?>(null)
    val preis: StateFlow<String?> = _preis.asStateFlow()

    private var produkt: ProductDetails? = null

    private val client: BillingClient = BillingClient.newBuilder(context)
        .setListener(::onPurchasesUpdated)
        // Ohne diese Angabe verweigert die Bibliothek beim Start den Dienst.
        // FLEXR verkauft nur ein Abo, aber der Parameter ist trotzdem Pflicht.
        // Seit Billing Library 7 genuegt ein leerer PendingPurchasesParams-
        // Builder nicht mehr: build() wirft dann "Pending purchases for
        // one-time products must be supported." - ungefangen, weil das hier
        // ein Property-Initializer ist, also bei jedem App-Start, sobald Hilt
        // diesen Singleton konstruiert. enableOneTimeProducts() ist deshalb
        // Pflicht, obwohl FLEXR gar keine Einmalkaeufe anbietet (Fund vom
        // 18.09.2026, Absturzbericht aus Downloads/ geholt).
        .enablePendingPurchases(
            PendingPurchasesParams.newBuilder()
                .enableOneTimeProducts()
                .build(),
        )
        // Verbindung bricht bei Updates des Play Stores regelmässig ab; ohne
        // das hier müsste jede Aufrufstelle den Wiederaufbau selbst regeln.
        .enableAutoServiceReconnection()
        .build()

    private fun onPurchasesUpdated(ergebnis: BillingResult, kaeufe: List<Purchase>?) {
        when (ergebnis.responseCode) {
            BillingClient.BillingResponseCode.OK -> {
                kaeufe.orEmpty().forEach { kauf -> scope.launch { einreichen(kauf, meldend = true) } }
            }
            BillingClient.BillingResponseCode.USER_CANCELED ->
                _ereignisse.tryEmit(Ereignis.Abgebrochen)
            // Der Kauf lief schon - kein Fehler, sondern der haeufigste Fall
            // nach einem Neuinstallieren. Der Abgleich holt ihn ohnehin.
            BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED ->
                scope.launch { bestehendeKaeufeAbgleichen() }
            else -> _ereignisse.tryEmit(
                Ereignis.Fehlgeschlagen(ergebnis.debugMessage.ifBlank { "Fehler ${ergebnis.responseCode}" })
            )
        }
    }

    private suspend fun verbinden(): Boolean {
        if (client.isReady) return true
        return suspendCancellableCoroutine { fortsetzung ->
            client.startConnection(object : BillingClientStateListener {
                override fun onBillingSetupFinished(ergebnis: BillingResult) {
                    if (fortsetzung.isActive) {
                        fortsetzung.resume(
                            ergebnis.responseCode == BillingClient.BillingResponseCode.OK
                        )
                    }
                }

                override fun onBillingServiceDisconnected() {
                    // enableAutoServiceReconnection() kuemmert sich darum. Hier
                    // nichts zu tun: Wer gerade wartet, bekommt sein Ergebnis
                    // ueber onBillingSetupFinished.
                }
            })
        }
    }

    /**
     * Produktdaten laden. Danach steht [preis] — der Text kommt vom Store, nicht
     * von uns: Google rechnet Währung, Steuer und Schreibweise je nach Land.
     */
    suspend fun produktLaden(produktId: String): ProductDetails? {
        produkt?.let { if (it.productId == produktId) return it }
        if (!verbinden()) return null

        val anfrage = QueryProductDetailsParams.newBuilder()
            .setProductList(
                listOf(
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(produktId)
                        .setProductType(BillingClient.ProductType.SUBS)
                        .build()
                )
            )
            .build()

        val gefunden = suspendCancellableCoroutine { fortsetzung ->
            client.queryProductDetailsAsync(anfrage) { _, ergebnis ->
                if (fortsetzung.isActive) {
                    fortsetzung.resume(ergebnis.productDetailsList.firstOrNull())
                }
            }
        }

        produkt = gefunden
        _preis.value = gefunden?.let { details ->
            details.subscriptionOfferDetails
                ?.firstOrNull()
                ?.pricingPhases
                ?.pricingPhaseList
                ?.lastOrNull()      // die Dauerphase, nicht ein Einstiegsangebot
                ?.formattedPrice
        }
        return gefunden
    }

    /**
     * Den Kaufvorgang starten. Das Ergebnis kommt über [ereignisse], nicht als
     * Rückgabewert — Google führt den Kauf in einer eigenen Oberfläche zu Ende,
     * unter Umständen erst nach Minuten.
     */
    suspend fun kaufen(activity: Activity, produktId: String) {
        val details = produktLaden(produktId)
        if (details == null) {
            _ereignisse.tryEmit(Ereignis.Fehlgeschlagen("Das Angebot ist gerade nicht abrufbar."))
            return
        }
        val angebot = details.subscriptionOfferDetails?.firstOrNull()
        if (angebot == null) {
            _ereignisse.tryEmit(Ereignis.Fehlgeschlagen("Zu diesem Abo gibt es gerade kein Angebot."))
            return
        }

        val ergebnis = client.launchBillingFlow(
            activity,
            BillingFlowParams.newBuilder()
                .setProductDetailsParamsList(
                    listOf(
                        BillingFlowParams.ProductDetailsParams.newBuilder()
                            .setProductDetails(details)
                            .setOfferToken(angebot.offerToken)
                            .build()
                    )
                )
                .build(),
        )
        if (ergebnis.responseCode != BillingClient.BillingResponseCode.OK) {
            _ereignisse.tryEmit(
                Ereignis.Fehlgeschlagen(
                    ergebnis.debugMessage.ifBlank { "Der Kauf konnte nicht gestartet werden." }
                )
            )
        }
    }

    /**
     * Laufende Käufe beim Start einreichen.
     *
     * Läuft still: Wer nichts gekauft hat, soll davon nichts merken, und ein
     * Netzfehler beim Start ist kein Grund für eine Meldung.
     */
    suspend fun bestehendeKaeufeAbgleichen() {
        if (!verbinden()) return
        val kaeufe = suspendCancellableCoroutine { fortsetzung ->
            client.queryPurchasesAsync(
                QueryPurchasesParams.newBuilder()
                    .setProductType(BillingClient.ProductType.SUBS)
                    .build()
            ) { _, liste -> if (fortsetzung.isActive) fortsetzung.resume(liste) }
        }
        kaeufe.forEach { einreichen(it, meldend = false) }
    }

    /**
     * Den Kauf-Token beim Server einreichen — der einzige Ort, an dem aus einem
     * Kauf eine Berechtigung wird.
     */
    private suspend fun einreichen(kauf: Purchase, meldend: Boolean) {
        // PENDING heisst: Google wartet noch auf das Geld (Lastschrift,
        // Gutschein). Einreichen waere verfrueht - Google meldet den Kauf
        // erneut, sobald er durch ist.
        if (kauf.purchaseState != Purchase.PurchaseState.PURCHASED) return

        val erfolg = runCatching { repository.playKaufEinreichen(kauf.purchaseToken) }
        erfolg.onSuccess {
            // Doppelte Sicherung gegen die Drei-Tage-Stornierung von Google:
            // Der Server bestaetigt bereits selbst, aber nur, wenn er den Kauf
            // annehmen konnte. Faellt das aus, faengt es der Client hier ab.
            if (!kauf.isAcknowledged) {
                client.acknowledgePurchase(
                    AcknowledgePurchaseParams.newBuilder()
                        .setPurchaseToken(kauf.purchaseToken)
                        .build()
                ) { /* Ergebnis egal: Der Server ist ohnehin die massgebliche Stelle. */ }
            }
            if (meldend) _ereignisse.tryEmit(Ereignis.Erfolgreich)
        }
        erfolg.onFailure { fehler ->
            if (meldend) {
                _ereignisse.tryEmit(
                    Ereignis.Fehlgeschlagen(
                        fehler.message ?: "Der Kauf konnte nicht bestätigt werden."
                    )
                )
            }
        }
    }
}
