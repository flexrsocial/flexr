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
import androidx.compose.material.icons.filled.Person
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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import flexr.social.app.R
import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.designsystem.component.PremiumBadge
import flexr.social.app.core.designsystem.component.VerifiedBadge
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.core.locale.LocalAppLanguage
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
    /** Gesetzt: statt des Pfeils ein Knopf "Hallo sagen", der direkt in den Chat fuehrt. */
    onSayHi: (() -> Unit)? = null,
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
                contentDescription = stringResource(R.string.common_profile_photo_of, profile.name),
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxSize()
                    .clip(CircleShape)
                    .background(colors.surface2),
            )
            if (profile.primaryPhoto == null) {
                // Kein freigegebenes Foto mehr: Umriss wie im Web statt einer
                // leeren grauen Scheibe.
                Icon(
                    Icons.Filled.Person,
                    contentDescription = null,
                    tint = colors.chalkDim.copy(alpha = 0.45f),
                    modifier = Modifier.align(Alignment.Center).size(34.dp),
                )
            }
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
                Row(Modifier.weight(1f), verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "${profile.name}, ${profile.age}",
                        style = MaterialTheme.typography.titleMedium,
                        color = colors.chalk,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f, fill = false),
                    )
                    if (profile.isVerified) {
                        Spacer(Modifier.width(6.dp))
                        VerifiedBadge(size = 14)
                    }
                    if (profile.isPremium) {
                        Spacer(Modifier.width(6.dp))
                        PremiumBadge(size = 14)
                    }
                }
                // Chatliste: Zeitpunkt der letzten Nachricht rechts neben dem
                // Namen, wie in der Web-App und in Messengern ueblich.
                val gesendet = match.lastMessage?.createdAt
                if (showLastMessage && gesendet != null) {
                    val zeit = if (ServerTime.daysAgo(gesendet) == 1L) {
                        stringResource(R.string.chat_yesterday)
                    } else {
                        ServerTime.formatChatListTime(gesendet, LocalAppLanguage.current.locale)
                    }
                    Spacer(Modifier.width(10.dp))
                    Text(
                        text = zeit,
                        style = MonoStyle,
                        color = if (unread) colors.plate else colors.chalkDim,
                        fontWeight = if (unread) FontWeight.SemiBold else FontWeight.Medium,
                        maxLines = 1,
                    )
                }
            }
            val onlineLabel = stringResource(R.string.matches_online_now)
            val secondary = if (showLastMessage) {
                // lastMessage kann trotz inChats fehlen: nach "Chatverlauf
                // leeren" ist der Chat weiterhin gelistet, aber (für einen
                // selbst) leer.
                match.lastMessage?.let { message ->
                    val prefix = if (message.senderId == ownUserId) {
                        stringResource(R.string.chats_you_prefix)
                    } else {
                        ""
                    }
                    prefix + message.content
                } ?: stringResource(R.string.chats_cleared)
            } else {
                buildString {
                    append(profile.city)
                    profile.distanceKm?.let { append(" · $it km") }
                    if (match.isOnline) append(" · ").append(onlineLabel)
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
        } else if (onSayHi != null) {
            Row(
                Modifier
                    .clip(CircleShape)
                    .background(colors.plate.copy(alpha = 0.08f))
                    .border(1.dp, colors.plate.copy(alpha = 0.42f), CircleShape)
                    .clickable(onClick = onSayHi)
                    .padding(horizontal = 12.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    FlexrIcons.Chats,
                    contentDescription = null,
                    tint = colors.plate,
                    modifier = Modifier.size(14.dp),
                )
                Spacer(Modifier.width(6.dp))
                Text(
                    text = stringResource(R.string.matches_say_hi),
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.SemiBold,
                    color = colors.plate,
                    maxLines = 1,
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
