package flexr.social.app.core.designsystem.component

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import flexr.social.app.core.designsystem.theme.EyebrowStyle
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle

/** Kleine Mono-Vorzeile über einer Überschrift (`.eyebrow`). */
@Composable
fun Eyebrow(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text.uppercase(),
        style = EyebrowStyle,
        color = FlexrTheme.colors.plate,
        modifier = modifier.padding(bottom = 6.dp),
    )
}

/** Standard-Kopf eines Bildschirms: Vorzeile plus Überschrift. */
@Composable
fun ScreenHeader(
    eyebrow: String,
    title: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
) {
    Column(modifier.fillMaxWidth()) {
        Eyebrow(eyebrow)
        Text(
            text = title,
            style = MaterialTheme.typography.headlineMedium,
            color = FlexrTheme.colors.chalk,
        )
        if (subtitle != null) {
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodyMedium,
                color = FlexrTheme.colors.chalkDim,
                modifier = Modifier.padding(top = 10.dp),
            )
        }
    }
}

/** Leerzustand mit gestricheltem Symbolkreis (`.empty`). */
@Composable
fun EmptyState(
    icon: ImageVector,
    title: String,
    description: String,
    modifier: Modifier = Modifier,
    action: (@Composable () -> Unit)? = null,
) {
    Column(
        modifier = modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 48.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Box(
            Modifier
                .size(68.dp)
                .clip(CircleShape)
                .background(Color.White.copy(alpha = 0.015f))
                .border(1.5.dp, FlexrTheme.colors.steel, CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = FlexrTheme.colors.chalkDim.copy(alpha = 0.8f),
                modifier = Modifier.size(28.dp),
            )
        }
        Spacer(Modifier.height(12.dp))
        Text(
            text = title.uppercase(),
            style = MaterialTheme.typography.headlineSmall,
            color = FlexrTheme.colors.chalk,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = description,
            style = MaterialTheme.typography.bodySmall,
            color = FlexrTheme.colors.chalkDim,
            textAlign = TextAlign.Center,
            modifier = Modifier.widthIn(max = 260.dp),
        )
        if (action != null) {
            Spacer(Modifier.height(20.dp))
            action()
        }
    }
}

/** Ganzflächiger Ladezustand. */
@Composable
fun LoadingState(modifier: Modifier = Modifier, label: String? = null) {
    Column(
        modifier = modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        CircularProgressIndicator(color = FlexrTheme.colors.plate, strokeWidth = 2.5.dp)
        if (label != null) {
            Spacer(Modifier.height(14.dp))
            Text(label, style = MaterialTheme.typography.bodySmall, color = FlexrTheme.colors.chalkDim)
        }
    }
}

/** Statusanzeige im Kopfbereich: Testmonat / Abo aktiv / abgelaufen. */
@Composable
fun StatusPill(text: String, expired: Boolean = false, modifier: Modifier = Modifier) {
    val colors = FlexrTheme.colors
    val contentColor = if (expired) colors.danger else colors.lime
    val borderColor = if (expired) colors.danger.copy(alpha = 0.4f) else colors.lime.copy(alpha = 0.3f)
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(20.dp))
            .background(Color.White.copy(alpha = 0.02f))
            .border(1.dp, borderColor, RoundedCornerShape(20.dp))
            .padding(horizontal = 10.dp, vertical = 5.dp),
    ) {
        Text(text, style = MonoStyle, color = contentColor)
    }
}

/** Blauer Haken für verifizierte Profile. */
@Composable
fun VerifiedBadge(modifier: Modifier = Modifier, size: Int = 16) {
    Box(
        modifier = modifier
            .size(size.dp)
            .clip(CircleShape)
            .background(VerifiedBlue),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            Icons.Filled.Check,
            contentDescription = "Verifiziertes Profil",
            tint = Color.White,
            modifier = Modifier.size((size * 0.7).dp),
        )
    }
}

val VerifiedBlue = Color(0xFF2D9CDB)

/** Merkmal-Chip auf einer Profilkarte (`.stat-chip`). */
@Composable
fun StatChip(
    text: String,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null,
    accent: Boolean = false,
    pulsingDot: Boolean = false,
) {
    val colors = FlexrTheme.colors
    val tint = if (accent) colors.plate else colors.lime
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(7.dp))
            .background(tint.copy(alpha = 0.08f))
            .border(1.dp, tint.copy(alpha = if (accent) 0.35f else 0.24f), RoundedCornerShape(7.dp))
            .padding(horizontal = 10.dp, vertical = 5.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (pulsingDot) {
            val transition = rememberInfiniteTransition(label = "onlinePulse")
            val alpha by transition.animateFloat(
                initialValue = 1f,
                targetValue = 0.45f,
                animationSpec = infiniteRepeatable(tween(1000), RepeatMode.Reverse),
                label = "onlineAlpha",
            )
            Box(Modifier.size(7.dp).clip(CircleShape).background(tint).alpha(alpha))
        } else if (icon != null) {
            Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(13.dp))
        }
        Text(text, style = MonoStyle, color = tint, maxLines = 1)
    }
}

/** Feine Trennlinie im Markenstil (`--hairline`). */
@Composable
fun HairlineDivider(modifier: Modifier = Modifier) {
    Box(
        modifier
            .fillMaxWidth()
            .height(1.dp)
            .background(FlexrTheme.colors.hairline),
    )
}

/** Abschnittsüberschrift im Konto-Bereich. */
@Composable
fun SectionTitle(text: String, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.fillMaxWidth().padding(bottom = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = text.uppercase(),
            style = MaterialTheme.typography.headlineSmall,
            color = FlexrTheme.colors.chalk,
        )
        Spacer(Modifier.width(12.dp))
        Box(
            Modifier
                .weight(1f)
                .height(1.dp)
                .background(FlexrTheme.colors.hairline),
        )
    }
}

/** Kartenfläche für Gruppen im Konto-Bereich. */
@Composable
fun FlexrCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Box(
        modifier
            .fillMaxWidth()
            .clip(MaterialTheme.shapes.medium)
            .background(MaterialTheme.colorScheme.surface)
            .border(BorderStroke(1.dp, FlexrTheme.colors.hairline), MaterialTheme.shapes.medium)
            .padding(16.dp),
    ) { content() }
}
