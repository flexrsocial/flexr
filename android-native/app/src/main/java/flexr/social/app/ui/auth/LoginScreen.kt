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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
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
        FlexrButton(
            text = "Einloggen",
            onClick = {
                keyboard?.hide()
                viewModel.login()
            },
            enabled = state.canSubmit,
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
}
