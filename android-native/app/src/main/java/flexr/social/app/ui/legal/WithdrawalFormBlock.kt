package flexr.social.app.ui.legal

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.R
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrTextField
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.domain.model.WithdrawalAck

/**
 * Eingebettete Online-Rücktrittsfunktion (§ 13a FAGG) innerhalb der
 * [LegalDocument.WIDERRUF]-Ansicht - ersetzt den Custom Tab auf
 * flexr.social/widerruf.html. Bis zum Absenden ein Formular, danach die
 * Bestätigung mit dem aufgezeichneten Wortlaut.
 */
@Composable
internal fun WithdrawalFormBlock(viewModel: WithdrawalViewModel = hiltViewModel()) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val result = state.result

    if (result != null) {
        WithdrawalResultBox(result)
        return
    }

    val colors = FlexrTheme.colors
    Column(Modifier.padding(bottom = 8.dp)) {
        FlexrTextField(
            value = state.name,
            onValueChange = viewModel::onNameChange,
            label = stringResource(R.string.withdrawal_name_label),
            placeholder = stringResource(R.string.withdrawal_name_placeholder),
            imeAction = ImeAction.Next,
        )
        FlexrTextField(
            value = state.email,
            onValueChange = viewModel::onEmailChange,
            label = stringResource(R.string.withdrawal_email_label),
            placeholder = "du@example.com",
            keyboardType = KeyboardType.Email,
            imeAction = ImeAction.Next,
            supportingText = stringResource(R.string.withdrawal_email_hint),
        )
        FlexrTextField(
            value = state.contractReference,
            onValueChange = viewModel::onContractReferenceChange,
            label = stringResource(R.string.withdrawal_contract_label),
            placeholder = stringResource(R.string.withdrawal_contract_placeholder),
            imeAction = ImeAction.Next,
            supportingText = stringResource(R.string.withdrawal_contract_hint),
        )
        FlexrTextField(
            value = state.message,
            onValueChange = viewModel::onMessageChange,
            label = stringResource(R.string.withdrawal_message_label),
            placeholder = stringResource(R.string.withdrawal_message_placeholder),
            singleLine = false,
            maxLines = 4,
            minHeight = 84,
            maxLength = 1000,
            imeAction = ImeAction.Default,
        )

        Row(
            Modifier
                .fillMaxWidth()
                .padding(top = 16.dp)
                .clip(RoundedCornerShape(10.dp))
                .clickable { viewModel.onConfirmedChange(!state.confirmed) },
            verticalAlignment = Alignment.Top,
        ) {
            Checkbox(
                checked = state.confirmed,
                onCheckedChange = viewModel::onConfirmedChange,
                colors = CheckboxDefaults.colors(
                    checkedColor = colors.plate,
                    checkmarkColor = colors.plateInk,
                    uncheckedColor = colors.steel,
                ),
            )
            Text(
                text = stringResource(R.string.withdrawal_confirm_label),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
                modifier = Modifier.padding(top = 12.dp, end = 4.dp),
            )
        }

        FieldError(state.error)

        Spacer(Modifier.height(16.dp))
        FlexrButton(
            text = stringResource(R.string.withdrawal_submit),
            onClick = viewModel::submit,
            enabled = state.canSubmit,
            loading = state.isSubmitting,
        )
    }
}

@Composable
private fun WithdrawalResultBox(result: WithdrawalAck) {
    val colors = FlexrTheme.colors
    Column(
        Modifier
            .fillMaxWidth()
            .padding(bottom = 8.dp)
            .clip(MaterialTheme.shapes.medium)
            .background(colors.surface2)
            .padding(16.dp),
    ) {
        Text(
            text = stringResource(
                if (result.confirmationSent) {
                    R.string.withdrawal_result_title
                } else {
                    R.string.withdrawal_result_title_no_mail
                },
            ),
            style = MaterialTheme.typography.titleSmall,
            color = colors.chalk,
        )
        Spacer(Modifier.height(8.dp))
        Text(result.message, style = MaterialTheme.typography.bodyMedium, color = colors.chalkDim)
        Spacer(Modifier.height(14.dp))
        Text(
            stringResource(R.string.withdrawal_result_wording_label),
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalk,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            result.declarationText,
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )
        Spacer(Modifier.height(14.dp))
        Text(
            stringResource(R.string.withdrawal_result_hint),
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )
    }
}
