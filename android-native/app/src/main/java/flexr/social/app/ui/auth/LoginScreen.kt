package flexr.social.app.ui.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.R
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrPasswordField
import flexr.social.app.core.designsystem.component.FlexrTextField
import flexr.social.app.core.designsystem.component.ScreenHeader
import flexr.social.app.core.designsystem.theme.FlexrTheme

@Composable
fun LoginScreen(
    onLoggedIn: () -> Unit,
    onGoToRegister: () -> Unit,
    viewModel: LoginViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val keyboard = LocalSoftwareKeyboardController.current

    LaunchedEffect(state.success) {
        if (state.success) onLoggedIn()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .imePadding()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp),
        verticalArrangement = Arrangement.Top,
    ) {
        Spacer(Modifier.height(8.dp))
        AuthTabs(selected = AuthTab.LOGIN, onSelect = { if (it == AuthTab.REGISTER) onGoToRegister() })

        Spacer(Modifier.height(24.dp))
        ScreenHeader(
            eyebrow = stringResource(R.string.login_eyebrow),
            title = stringResource(R.string.login_title),
            subtitle = stringResource(R.string.login_subtitle),
        )

        FlexrTextField(
            value = state.email,
            onValueChange = viewModel::onEmailChange,
            label = stringResource(R.string.field_email),
            placeholder = "max@example.com",
            keyboardType = KeyboardType.Email,
            imeAction = ImeAction.Next,
        )

        FlexrPasswordField(
            value = state.password,
            onValueChange = viewModel::onPasswordChange,
            label = stringResource(R.string.field_password),
            placeholder = "••••••••",
            imeAction = ImeAction.Go,
            onImeAction = {
                keyboard?.hide()
                viewModel.login()
            },
        )

        FieldError(state.error)

        Spacer(Modifier.height(22.dp))
        // Wie bei der Registrierung bewusst immer tippbar: Ein gesperrter Knopf
        // sagt nicht, was fehlt. viewModel.login() nennt den Grund beim Tippen.
        FlexrButton(
            text = stringResource(R.string.login_submit),
            onClick = {
                keyboard?.hide()
                viewModel.login()
            },
            loading = state.isSubmitting,
        )

        TextButton(
            onClick = viewModel::openForgot,
            modifier = Modifier.fillMaxWidth().padding(top = 6.dp),
        ) {
            Text(
                stringResource(R.string.login_forgot),
                color = FlexrTheme.colors.chalkDim,
                style = MaterialTheme.typography.bodySmall,
                textDecoration = TextDecoration.Underline,
            )
        }

        Spacer(Modifier.height(16.dp))
        Text(
            text = stringResource(R.string.login_register_hint),
            style = MaterialTheme.typography.bodySmall,
            color = FlexrTheme.colors.chalkDim,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(40.dp))
    }

    if (state.forgotOpen) {
        ForgotPasswordDialog(
            email = state.forgotEmail,
            sending = state.forgotSending,
            sent = state.forgotSent,
            error = state.forgotError,
            onEmailChange = viewModel::onForgotEmailChange,
            onSend = viewModel::sendForgot,
            onDismiss = viewModel::dismissForgot,
        )
    }

    val reactivateMessage = state.reactivateMessage
    if (reactivateMessage != null) {
        ReactivateAccountDialog(
            message = reactivateMessage,
            error = state.reactivateError,
            isReactivating = state.isReactivating,
            onConfirm = viewModel::reactivate,
            onDismiss = viewModel::dismissReactivateDialog,
        )
    }
}

/**
 * Konto innerhalb der 30-Tage-Karenz nach Selbstlöschung: Statt der
 * Sackgasse aus routers/auth.login (403, code=account_deleted) bietet der
 * Login hier die Reaktivierung an (POST /api/auth/reactivate, dieselben
 * Zugangsdaten wie eben eingegeben).
 */
@Composable
private fun ReactivateAccountDialog(
    message: String,
    error: String?,
    isReactivating: Boolean,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text(stringResource(R.string.login_reactivate_title), style = MaterialTheme.typography.headlineSmall) },
        text = {
            Text(
                text = (error ?: message),
                style = MaterialTheme.typography.bodyMedium,
                color = if (error != null) FlexrTheme.colors.danger else FlexrTheme.colors.chalkDim,
            )
        },
        confirmButton = {
            TextButton(onClick = onConfirm, enabled = !isReactivating) {
                Text(stringResource(R.string.login_reactivate_confirm))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.common_cancel), color = FlexrTheme.colors.chalkDim)
            }
        },
    )
}

/**
 * "Passwort vergessen?": Link per Mail anfordern. Das neue Passwort legt man
 * im Browser fest (der Link zeigt auf flexr.social/app/?reset=...) und meldet
 * sich danach hier wieder an.
 */
@Composable
private fun ForgotPasswordDialog(
    email: String,
    sending: Boolean,
    sent: Boolean,
    error: String?,
    onEmailChange: (String) -> Unit,
    onSend: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text(stringResource(R.string.forgot_title), style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column {
                Text(
                    text = stringResource(if (sent) R.string.forgot_done else R.string.forgot_sub),
                    style = MaterialTheme.typography.bodyMedium,
                    color = FlexrTheme.colors.chalkDim,
                )
                if (!sent) {
                    Spacer(Modifier.height(12.dp))
                    FlexrTextField(
                        value = email,
                        onValueChange = onEmailChange,
                        label = stringResource(R.string.field_email),
                        placeholder = "max@example.com",
                        keyboardType = KeyboardType.Email,
                        imeAction = ImeAction.Send,
                        onImeAction = onSend,
                    )
                    FieldError(error)
                }
            }
        },
        confirmButton = {
            if (sent) {
                TextButton(onClick = onDismiss) { Text(stringResource(R.string.common_close)) }
            } else {
                TextButton(onClick = onSend, enabled = !sending) { Text(stringResource(R.string.forgot_send)) }
            }
        },
        dismissButton = {
            if (!sent) {
                TextButton(onClick = onDismiss) {
                    Text(stringResource(R.string.common_cancel), color = FlexrTheme.colors.chalkDim)
                }
            }
        },
    )
}
