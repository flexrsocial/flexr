package flexr.social.app.ui.paywall

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
import flexr.social.app.core.designsystem.component.EmptyState
import flexr.social.app.core.designsystem.component.Eyebrow
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrDangerButton
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.ui.account.AccountEvent
import flexr.social.app.ui.account.AccountViewModel
import flexr.social.app.ui.account.CheckoutDialog
import flexr.social.app.ui.account.DeleteAccountDialog

/**
 * Paywall nach Ablauf des Probemonats.
 *
 * Der Checkout läuft in einer externen Browser-Sitzung über Stripe — die App
 * nimmt zu keinem Zeitpunkt Zahlungsdaten entgegen.
 */
@Composable
fun PaywallScreen(
    onLogout: () -> Unit,
    onOpenUrl: (String) -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: AccountViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is AccountEvent.Message -> onShowMessage(event.text)
                is AccountEvent.OpenUrl -> onOpenUrl(event.url)
                AccountEvent.LoggedOut -> onLogout()
                // Auf der Paywall gibt es keinen Verifizierungsablauf - beide
                // Ereignisse können hier gar nicht ausgelöst werden.
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
        Spacer(Modifier.height(24.dp))
        EmptyState(
            icon = FlexrIcons.Locked,
            title = stringResource(R.string.paywall_title),
            description = stringResource(R.string.paywall_sub),
        )

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
                    stringResource(R.string.paywall_price),
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
            listOf(
                R.string.paywall_feature_unlimited,
                R.string.paywall_feature_chat,
                R.string.paywall_feature_cancel,
            ).forEach { feature ->
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
                        stringResource(feature),
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalkDim,
                    )
                }
            }
            Spacer(Modifier.height(12.dp))
            FlexrButton(text = stringResource(R.string.paywall_subscribe), onClick = viewModel::openCheckoutDialog)
        }

        Spacer(Modifier.height(14.dp))
        Text(
            text = stringResource(R.string.paywall_return_note),
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(Modifier.height(24.dp))
        FlexrSecondaryButton(text = stringResource(R.string.common_logout), onClick = onLogout)
        // Nach Ablauf des Probemonats ist der Konto-Screen nicht mehr
        // navigierbar. Ohne diesen Knopf waere die Selbstloeschung damit
        // unerreichbar - Punkt 5 der Datenschutzerklaerung sagt sie aber zu.
        Spacer(Modifier.height(10.dp))
        FlexrDangerButton(text = stringResource(R.string.common_delete_account), onClick = viewModel::showDeleteDialog)
        Spacer(Modifier.height(40.dp))
    }

    if (state.deleteDialogVisible) {
        DeleteAccountDialog(
            password = state.deletePassword,
            error = state.deleteError,
            isDeleting = state.isDeleting,
            onPasswordChange = viewModel::onDeletePasswordChange,
            onConfirm = viewModel::confirmDelete,
            onDismiss = viewModel::hideDeleteDialog,
        )
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
