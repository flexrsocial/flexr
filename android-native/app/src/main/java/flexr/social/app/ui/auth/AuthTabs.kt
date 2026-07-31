package flexr.social.app.ui.auth

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import flexr.social.app.core.designsystem.theme.FlexrTheme

enum class AuthTab { LOGIN, REGISTER }

/** Umschalter zwischen Anmeldung und Registrierung (`.auth-tabs` im Web). */
@Composable
fun AuthTabs(
    selected: AuthTab,
    onSelect: (AuthTab) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = FlexrTheme.colors
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Color.White.copy(alpha = 0.03f))
            .padding(4.dp),
    ) {
        AuthTab.entries.forEach { tab ->
            val isSelected = tab == selected
            val background by animateColorAsState(
                if (isSelected) colors.surface3 else Color.Transparent,
                label = "tabBackground",
            )
            val contentColor by animateColorAsState(
                if (isSelected) colors.plate else colors.chalkDim,
                label = "tabContent",
            )
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(9.dp))
                    .background(background)
                    .clickable(enabled = !isSelected) { onSelect(tab) }
                    .padding(vertical = 11.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = if (tab == AuthTab.LOGIN) "Einloggen" else "Registrieren",
                    style = MaterialTheme.typography.labelLarge,
                    color = contentColor,
                )
            }
        }
    }
}
