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
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
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
            eyebrow = "Willkommen zurück",
            title = "Zurück ins\nGym-Date.",
            subtitle = "Melde dich mit deinen Zugangsdaten an.",
        )

        FlexrTextField(
            value = state.email,
            onValueChange = viewModel::onEmailChange,
            label = "E-Mail",
            placeholder = "max@example.com",
            keyboardType = KeyboardType.Email,
            imeAction = ImeAction.Next,
        )

        FlexrPasswordField(
            value = state.password,
            onValueChange = viewModel::onPasswordChange,
            label = "Passwort",
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
            text = "Einloggen",
            onClick = {
                keyboard?.hide()
                viewModel.login()
            },
            loading = state.isSubmitting,
        )

        Spacer(Modifier.height(28.dp))
        Text(
            text = "Neu hier? Erstell dein Profil und teste FLEXR einen Monat gratis.",
            style = MaterialTheme.typography.bodySmall,
            color = FlexrTheme.colors.chalkDim,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(40.dp))
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
        title = { Text("Konto reaktivieren?", style = MaterialTheme.typography.headlineSmall) },
        text = {
            Text(
                text = (error ?: message),
                style = MaterialTheme.typography.bodyMedium,
                color = if (error != null) FlexrTheme.colors.danger else FlexrTheme.colors.chalkDim,
            )
        },
        confirmButton = {
            TextButton(onClick = onConfirm, enabled = !isReactivating) {
                Text("Jetzt reaktivieren")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Abbrechen", color = FlexrTheme.colors.chalkDim)
            }
        },
    )
}
