package flexr.social.app.ui.swipe

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
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
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil.compose.AsyncImage
import flexr.social.app.core.designsystem.component.Eyebrow
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.domain.model.Profile

/**
 * „Match!"-Overlay nach beidseitigem Like. Die beiden Avatare fahren beim
 * Erscheinen zusammen — dieselbe Choreografie wie im Web, hier aber mit
 * Compose-Animationen statt CSS-Keyframes.
 */
@Composable
fun MatchOverlay(
    matchedProfile: Profile,
    ownAvatarUrl: String?,
    ownName: String,
    onWriteMessage: () -> Unit,
    onKeepSwiping: () -> Unit,
) {
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(matchedProfile.id) { visible = true }

    val scale by animateFloatAsState(
        targetValue = if (visible) 1f else 0.7f,
        animationSpec = spring(dampingRatio = 0.6f, stiffness = 320f),
        label = "matchScale",
    )

    Dialog(
        onDismissRequest = onKeepSwiping,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Box(
            Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.88f))
                .padding(28.dp),
            contentAlignment = Alignment.Center,
        ) {
            Column(
                modifier = Modifier
                    .widthIn(max = 380.dp)
                    .graphicsLayer {
                        scaleX = scale
                        scaleY = scale
                    },
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Eyebrow("Beide interessiert")
                Text(
                    text = "Match!",
                    style = MaterialTheme.typography.displayLarge,
                    color = FlexrTheme.colors.plate,
                )
                Spacer(Modifier.height(24.dp))

                Row(
                    horizontalArrangement = Arrangement.spacedBy((-18).dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    MatchAvatar(url = ownAvatarUrl, name = ownName)
                    MatchAvatar(
                        url = matchedProfile.primaryPhoto?.avatarUrl,
                        name = matchedProfile.name,
                    )
                }

                Spacer(Modifier.height(20.dp))
                Text(
                    text = "Du und ${matchedProfile.name} habt euch gegenseitig geliked.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = FlexrTheme.colors.chalkDim,
                    textAlign = TextAlign.Center,
                )

                Spacer(Modifier.height(26.dp))
                FlexrButton(
                    text = "Nachricht schreiben",
                    onClick = onWriteMessage,
                    icon = FlexrIcons.Chats,
                )
                Spacer(Modifier.height(10.dp))
                FlexrSecondaryButton(text = "Weiter swipen", onClick = onKeepSwiping)
            }
        }
    }
}

@Composable
private fun MatchAvatar(url: String?, name: String) {
    val colors = FlexrTheme.colors
    Box(
        Modifier
            .size(104.dp)
            .clip(CircleShape)
            .background(colors.surface2)
            .border(3.dp, colors.plate, CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        if (url != null) {
            AsyncImage(
                model = url,
                contentDescription = name,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize().clip(CircleShape),
            )
        } else {
            Text(
                text = name.take(1).uppercase(),
                style = MaterialTheme.typography.displayMedium,
                color = colors.chalkDim,
            )
        }
    }
}
