package flexr.social.app.ui.matches

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import flexr.social.app.core.designsystem.component.VerifiedBadge
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.domain.model.MatchSummary

/**
 * Listeneintrag für Matches und Chats (`.match-item`).
 *
 * Online-Zustand als oranger Ring um den Avatar, ungelesene Nachrichten als
 * leuchtender Rahmen plus Zähler — dieselbe Bildsprache wie im Web.
 */
@Composable
fun MatchListItem(
    match: MatchSummary,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    ownUserId: String? = null,
    showLastMessage: Boolean = false,
) {
    val colors = FlexrTheme.colors
    val unread = match.unreadCount > 0
    val profile = match.profile

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(MaterialTheme.shapes.medium)
            .background(Brush.verticalGradient(listOf(Color(0xFF1F1F1F), Color(0xFF1A1A1A))))
            .border(
                width = if (unread) 1.5.dp else 1.dp,
                color = if (unread) colors.plateDim else colors.hairline,
                shape = MaterialTheme.shapes.medium,
            )
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(13.dp),
    ) {
        Box(Modifier.size(54.dp)) {
            AsyncImage(
                model = profile.primaryPhoto?.avatarUrl,
                contentDescription = "Profilfoto von ${profile.name}",
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxSize()
                    .clip(CircleShape)
                    .background(colors.surface2),
            )
            if (match.isOnline) {
                Box(
                    Modifier
                        .fillMaxSize()
                        .clip(CircleShape)
                        .border(2.dp, colors.plateDim, CircleShape),
                )
            }
        }

        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "${profile.name}, ${profile.age}",
                    style = MaterialTheme.typography.titleMedium,
                    color = colors.chalk,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                if (profile.isVerified) {
                    Spacer(Modifier.width(6.dp))
                    VerifiedBadge(size = 14)
                }
            }
            val secondary = if (showLastMessage) {
                match.lastMessage?.let { message ->
                    val prefix = if (message.senderId == ownUserId) "Du: " else ""
                    prefix + message.content
                }.orEmpty()
            } else {
                buildString {
                    append(profile.city)
                    profile.distanceKm?.let { append(" · $it km") }
                    if (match.isOnline) append(" · gerade online")
                }
            }
            Text(
                text = secondary,
                style = MaterialTheme.typography.bodySmall,
                color = if (unread) colors.chalk else colors.chalkDim,
                fontWeight = if (unread) FontWeight.Medium else FontWeight.Normal,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 3.dp),
            )
        }

        if (unread) {
            Box(
                Modifier
                    .size(22.dp)
                    .clip(CircleShape)
                    .background(colors.plate),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = if (match.unreadCount > 9) "9+" else "${match.unreadCount}",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.plateInk,
                )
            }
        } else {
            Icon(
                Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = null,
                tint = colors.chalkDim.copy(alpha = 0.6f),
                modifier = Modifier.size(18.dp),
            )
        }
    }
}
