package flexr.social.app.ui.paywall

import android.app.Activity
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.R
import flexr.social.app.core.designsystem.component.Eyebrow
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.theme.FlexrTheme
import androidx.compose.ui.platform.LocalContext
import flexr.social.app.data.billing.PlayBillingService
import flexr.social.app.ui.account.AccountEvent
import flexr.social.app.ui.account.AccountViewModel
import flexr.social.app.ui.account.CheckoutDialog

/**
 * FLEXR Premium — das freiwillige Zusatzpaket.
 *
 * War bis zum 10.09.2026 die Bezahlwand, auf der man nach Ablauf des
 * Probemonats zwangsweise landete. Die Nutzung von FLEXR kostet seither
 * dauerhaft nichts; dieser Bildschirm erklaert nur, was Premium zusaetzlich
 * kann, und wird aus dem Kontobereich heraus aufgerufen — nie erzwungen.
 *
 * Gekauft wird über **Google Play** — der einzige zulässige Weg für digitale
 * Inhalte, die in dieser App wirken (Play-Payments-Policy). Zahlungsdaten
 * nimmt die App zu keinem Zeitpunkt entgegen; sie reicht nur den Kauf-Token
 * beim Server ein, der ihn bei Google prüft.
 *
 * Preis und Währung schreibt der Play Store, nicht wir: Google rechnet sie je
 * nach Land des Kontos. Solange sie noch nicht geladen sind, steht der Preis
 * aus den Ressourcen da - er stimmt für Österreich, ist aber nur der
 * Platzhalter.
 */
@Composable
fun PaywallScreen(
    onBack: () -> Unit,
    onOpenUrl: (String) -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: AccountViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val membership by viewModel.membership.collectAsStateWithLifecycle()
    val storePreis by viewModel.storePreis.collectAsStateWithLifecycle()
    val kontext = LocalContext.current

    // Den echten Preis holen, sobald bekannt ist, welches Produkt gemeint ist.
    LaunchedEffect(membership?.storeProductId) { viewModel.ladePremiumAngebot() }

    // Ausgang des Kaufs. Ein Abbruch bleibt bewusst stumm: Wer selbst
    // abbricht, braucht darüber keine Meldung.
    val erfolgstext = stringResource(R.string.purchase_success)
    LaunchedEffect(Unit) {
        viewModel.kaufEreignisse.collect { ereignis ->
            when (ereignis) {
                is PlayBillingService.Ereignis.Erfolgreich -> onShowMessage(erfolgstext)
                is PlayBillingService.Ereignis.Fehlgeschlagen -> onShowMessage(ereignis.meldung)
                is PlayBillingService.Ereignis.Abgebrochen -> Unit
            }
        }
    }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is AccountEvent.Message -> onShowMessage(event.text)
                is AccountEvent.OpenUrl -> onOpenUrl(event.url)
                // Ausloggen und Selbstloeschung sitzen im Kontobereich, von
                // dem aus dieser Bildschirm aufgerufen wird - hier kann keines
                // der drei Ereignisse mehr entstehen.
                AccountEvent.LoggedOut -> Unit
                AccountEvent.StartVerification -> Unit
                AccountEvent.ContinueWithDocument -> Unit
            }
        }
    }

    val colors = FlexrTheme.colors
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .navigationBarsPadding()
            .padding(horizontal = 20.dp),
    ) {
        // Kopf ohne Schlosssymbol und ohne die grosszuegigen Abstaende des
        // gemeinsamen `EmptyState`.
        //
        // Der Grund ist Platz: Mit Symbolkreis (68 dp), seinen Abstaenden und
        // den 48 dp Polsterung oben und unten reichte der Bildschirm auf einem
        // Telefon nicht bis zum Zurueck-Knopf - man musste scrollen, um aus
        // einer Seite wieder herauszukommen, die niemand erzwungen aufruft.
        // Ohne das Schloss passt alles auf einen Schirm.
        //
        // Das Schloss war ausserdem ein Ueberbleibsel der alten Bezahlwand:
        // Seit dem 10.09.2026 ist hier nichts mehr gesperrt, FLEXR kostet
        // dauerhaft nichts. Ein Vorhaengeschloss ueber einem freiwilligen
        // Zusatzpaket sagt das Gegenteil.
        Spacer(Modifier.height(24.dp))
        Text(
            text = stringResource(R.string.paywall_title).uppercase(),
            style = MaterialTheme.typography.headlineSmall,
            color = colors.chalk,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(6.dp))
        Text(
            text = stringResource(R.string.paywall_sub),
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(20.dp))

        Column(
            Modifier
                .fillMaxWidth()
                .clip(MaterialTheme.shapes.large)
                .background(MaterialTheme.colorScheme.surface)
                .border(1.dp, colors.plate.copy(alpha = 0.3f), MaterialTheme.shapes.large)
                .padding(20.dp),
        ) {
            Eyebrow(stringResource(R.string.paywall_membership))
            Row(verticalAlignment = Alignment.Bottom) {
                Text(
                    storePreis ?: stringResource(R.string.paywall_price),
                    style = MaterialTheme.typography.displayMedium,
                    color = colors.chalk,
                )
                Text(
                    stringResource(R.string.paywall_per_month),
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.chalkDim,
                    modifier = Modifier.padding(bottom = 5.dp),
                )
            }
            Spacer(Modifier.height(16.dp))
            // Die Zahlen kommen vom Server, nicht aus dem Text: Wer die
            // Grenzen in config.py aendert, aendert damit auch diese Liste.
            val m = membership
            val vorteile = listOfNotNull(
                m?.let { stringResource(R.string.premium_feature_likes, it.freeDailyLikes) }
                    ?: stringResource(R.string.paywall_feature_unlimited),
                m?.let { stringResource(R.string.premium_feature_chats, it.freeOpenChats) }
                    ?: stringResource(R.string.paywall_feature_chat),
                stringResource(R.string.premium_feature_incoming),
                stringResource(R.string.premium_feature_rewind),
                m?.let {
                    stringResource(R.string.premium_feature_radius, it.maxRadiusKm.coerceAtLeast(250), it.freeMaxRadiusKm)
                },
                stringResource(R.string.premium_feature_badge),
                stringResource(R.string.paywall_feature_cancel),
            )
            vorteile.forEach { feature ->
                Row(
                    Modifier.fillMaxWidth().padding(vertical = 6.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalAlignment = Alignment.Top,
                ) {
                    Icon(
                        Icons.Filled.Check,
                        contentDescription = null,
                        tint = colors.lime,
                        modifier = Modifier.size(18.dp),
                    )
                    Text(
                        feature,
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalkDim,
                    )
                }
            }
            Spacer(Modifier.height(12.dp))
            // Kaufen laesst sich nur, was der Server auch anbietet: Er
            // meldet mit store_purchase_available, ob dieser Client kaufen
            // darf und unter welcher Produktkennung. Fehlt beides - weil
            // Premium serverseitig aus ist oder noch kein Produkt eingetragen
            // wurde -, steht statt eines Knopfes in die Sackgasse der Hinweis.
            val angebot = membership
            if (angebot != null && angebot.storePurchaseAvailable) {
                FlexrButton(
                    text = stringResource(R.string.paywall_subscribe),
                    onClick = { (kontext as? Activity)?.let(viewModel::kaufePremium) },
                )
            } else {
                Text(
                    stringResource(R.string.premium_beta_hint),
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
        }

        Spacer(Modifier.height(14.dp))
        Text(
            text = stringResource(R.string.paywall_return_note),
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )

        // Ausloggen und Selbstloeschung standen hier, solange dieser
        // Bildschirm der einzige erreichbare war. Der Kontobereich ist jetzt
        // immer navigierbar; beides sitzt dort, wo man es sucht.
        //
        // Die Abstaende hier sind knapp gehalten, damit der Zurueck-Knopf ohne
        // Scrollen erreichbar bleibt; `navigationBarsPadding()` oben haelt ihn
        // schon von der Systemleiste frei.
        Spacer(Modifier.height(16.dp))
        FlexrSecondaryButton(text = stringResource(R.string.common_back), onClick = onBack)
        Spacer(Modifier.height(16.dp))
    }

    if (state.checkoutDialogVisible) {
        CheckoutDialog(
            immediateStartChecked = state.checkoutImmediateStart,
            withdrawalAckChecked = state.checkoutWithdrawalAck,
            error = state.checkoutError,
            isStarting = state.isStartingCheckout,
            onImmediateStartChange = viewModel::onCheckoutImmediateStartChange,
            onWithdrawalAckChange = viewModel::onCheckoutWithdrawalAckChange,
            onConfirm = viewModel::confirmCheckout,
            onDismiss = viewModel::closeCheckoutDialog,
        )
    }
}
