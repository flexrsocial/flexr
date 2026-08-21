package flexr.social.app.core.designsystem.component

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import flexr.social.app.core.designsystem.theme.FlexrTheme

/**
 * Primäre Aktion der Marke: Orange-Verlauf, Versalien in Oswald, gesperrt —
 * die Compose-Entsprechung der `.btn`-Regel aus der Web-App.
 */
@Composable
fun FlexrButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    loading: Boolean = false,
    icon: ImageVector? = null,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val pressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(if (pressed) 0.98f else 1f, label = "buttonScale")
    val colors = FlexrTheme.colors
    val isEnabled = enabled && !loading
    // Gesperrt heisst: es fehlt noch etwas. Waehrend einer laufenden Aktion ist
    // der Knopf ebenfalls nicht tippbar, sieht aber weiter nach Aktion aus.
    val isBlocked = !enabled && !loading

    Box(
        modifier = modifier
            .fillMaxWidth()
            .scale(scale)
            .clip(RoundedCornerShape(12.dp))
            // Der gesperrte Zustand lag frueher auf alpha 0.4. Ein oranger
            // Verlauf auf #121212 verschwindet dabei fast vollstaendig - erst
            // beim Registrierungsknopf gemeldet, dann beim Login. Statt zu
            // verblassen wechselt der Knopf jetzt die Farbe: voll deckende
            // Stahlflaeche mit lesbarer Schrift, unverwechselbar "noch nicht".
            .background(
                if (isBlocked) {
                    SolidColor(colors.surface3)
                } else {
                    Brush.linearGradient(
                        listOf(colors.plateBright, colors.plate, Color(0xFFEF4C15)),
                    )
                },
            )
            .then(
                if (isBlocked) {
                    Modifier.border(1.dp, colors.steel, RoundedCornerShape(12.dp))
                } else {
                    Modifier
                },
            ),
    ) {
        val contentColor = if (isBlocked) colors.chalkDim else colors.plateInk

        TextButton(
            onClick = onClick,
            enabled = isEnabled,
            interactionSource = interactionSource,
            shape = RoundedCornerShape(12.dp),
            contentPadding = PaddingValues(horizontal = 18.dp, vertical = 14.dp),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(9.dp, Alignment.CenterHorizontally),
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (loading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(17.dp),
                        color = contentColor,
                        strokeWidth = 2.dp,
                    )
                } else if (icon != null) {
                    Icon(icon, contentDescription = null, tint = contentColor, modifier = Modifier.size(17.dp))
                }
                Text(
                    text = text.uppercase(),
                    style = MaterialTheme.typography.labelLarge,
                    color = contentColor,
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}

/** Zurückhaltende Aktion: transparenter Grund mit Stahlrahmen (`.btn.secondary`). */
@Composable
fun FlexrSecondaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    loading: Boolean = false,
    icon: ImageVector? = null,
) {
    val colors = FlexrTheme.colors
    OutlinedButton(
        onClick = onClick,
        enabled = enabled && !loading,
        modifier = modifier.fillMaxWidth().height(50.dp),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp, colors.steel),
        colors = androidx.compose.material3.ButtonDefaults.outlinedButtonColors(
            containerColor = Color.White.copy(alpha = 0.03f),
            contentColor = colors.chalk,
        ),
    ) {
        if (loading) {
            CircularProgressIndicator(Modifier.size(17.dp), color = colors.chalk, strokeWidth = 2.dp)
        } else if (icon != null) {
            Icon(icon, contentDescription = null, modifier = Modifier.size(17.dp))
        }
        if (loading || icon != null) Box(Modifier.size(9.dp))
        Text(text.uppercase(), style = MaterialTheme.typography.labelLarge)
    }
}

/** Zerstörende Aktion als Geisterknopf (`.btn.danger-ghost`). */
@Composable
fun FlexrDangerButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    loading: Boolean = false,
    solid: Boolean = false,
) {
    val colors = FlexrTheme.colors
    OutlinedButton(
        onClick = onClick,
        enabled = enabled && !loading,
        modifier = modifier.fillMaxWidth().height(50.dp),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp, colors.danger.copy(alpha = if (solid) 1f else 0.45f)),
        colors = androidx.compose.material3.ButtonDefaults.outlinedButtonColors(
            containerColor = if (solid) colors.danger else colors.danger.copy(alpha = 0.08f),
            contentColor = if (solid) Color.White else colors.danger,
        ),
    ) {
        if (loading) {
            CircularProgressIndicator(
                Modifier.size(17.dp),
                color = if (solid) Color.White else colors.danger,
                strokeWidth = 2.dp,
            )
            Box(Modifier.size(9.dp))
        }
        Text(text.uppercase(), style = MaterialTheme.typography.labelLarge)
    }
}

/**
 * Textlink-Optik für Nebenaktionen (`.link-btn` / `.membership-link`) - bewusst
 * kein `TextButton`: dessen erzwungene Mindestbreite zentriert den Text sonst
 * in unsichtbarem Leerraum statt ihn linksbündig mit dem Text darüber zu halten.
 */
@Composable
fun FlexrLinkButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    color: Color = FlexrTheme.colors.plate,
) {
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        color = if (enabled) color else FlexrTheme.colors.chalkDim,
        textDecoration = androidx.compose.ui.text.style.TextDecoration.Underline,
        modifier = modifier
            .clip(RoundedCornerShape(4.dp))
            .clickable(enabled = enabled, onClick = onClick)
            .padding(vertical = 8.dp),
    )
}
