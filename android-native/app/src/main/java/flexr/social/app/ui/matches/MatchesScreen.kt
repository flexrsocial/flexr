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
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.R
import flexr.social.app.core.designsystem.component.EmptyState
import flexr.social.app.core.designsystem.component.ScreenHeader
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive

/**
 * Abstand zwischen zwei stillen Hintergrund-Abgleichen, während Matches oder
 * Chats sichtbar sind — gleiche Kadenz wie der Web-Poll (`refreshUnreadBadge`,
 * alle 20s). Nur so lange aktiv, wie der jeweilige Bildschirm komponiert ist:
 * `LaunchedEffect` bricht automatisch ab, sobald er die Komposition verlässt.
 */
private const val LIST_POLL_INTERVAL_MS = 20_000L

/** Alle Matches — der Einstieg ins Profil und von dort in den Chat. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MatchesScreen(
    onOpenMatchProfile: (String) -> Unit,
    onOpenIncoming: () -> Unit,
    viewModel: MatchesViewModel = hiltViewModel(),
) {
    val matches by viewModel.matches.collectAsStateWithLifecycle()
    val isRefreshing by viewModel.isRefreshing.collectAsStateWithLifecycle()
    val incoming by viewModel.incoming.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        while (isActive) {
            delay(LIST_POLL_INTERVAL_MS)
            viewModel.silentRefresh()
        }
    }

    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(18.dp))
        ScreenHeader(
            eyebrow = stringResource(R.string.matches_eyebrow),
            title = stringResource(R.string.matches_title),
        )
        Spacer(Modifier.height(16.dp))

        // Die Karte zeigt die Zahl immer, die Namen nur mit Premium. Ohne
        // offene Likes bleibt sie ganz weg - eine "0" waere eine Enttaeuschung
        // ohne Anlass.
        incoming?.takeIf { it.count > 0 }?.let { offen ->
            IncomingLikesCard(
                count = offen.count,
                premiumRequired = offen.premiumRequired,
                onClick = onOpenIncoming,
            )
            Spacer(Modifier.height(12.dp))
        }

        PullToRefreshBox(
            isRefreshing = isRefreshing,
            onRefresh = viewModel::refresh,
            modifier = Modifier.fillMaxSize(),
        ) {
            if (matches.isEmpty() && !isRefreshing) {
                // Mittig wie der Leerzustand im Swipe-Deck - sonst klebt er
                // oben unter der Ueberschrift, waehrend er dort auf halber
                // Hoehe steht.
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    EmptyState(
                        icon = FlexrIcons.Matches,
                        title = stringResource(R.string.matches_empty_title),
                        description = stringResource(R.string.matches_empty_sub),
                    )
                }
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                    modifier = Modifier.fillMaxSize(),
                ) {
                    items(matches, key = { it.matchId }) { match ->
                        MatchListItem(
                            match = match,
                            onClick = { onOpenMatchProfile(match.matchId) },
                        )
                    }
                    item { Spacer(Modifier.height(12.dp)) }
                }
            }
        }
    }
}

/** Nur Matches mit laufender Unterhaltung. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatsScreen(
    ownUserId: String?,
    onOpenChat: (String) -> Unit,
    viewModel: MatchesViewModel = hiltViewModel(),
) {
    val conversations by viewModel.conversations.collectAsStateWithLifecycle()
    val isRefreshing by viewModel.isRefreshing.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        while (isActive) {
            delay(LIST_POLL_INTERVAL_MS)
            viewModel.silentRefresh()
        }
    }

    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(18.dp))
        ScreenHeader(
            eyebrow = stringResource(R.string.chats_eyebrow),
            title = stringResource(R.string.chats_title),
        )
        Spacer(Modifier.height(16.dp))

        PullToRefreshBox(
            isRefreshing = isRefreshing,
            onRefresh = viewModel::refresh,
            modifier = Modifier.fillMaxSize(),
        ) {
            if (conversations.isEmpty() && !isRefreshing) {
                // Mittig wie der Leerzustand im Swipe-Deck - sonst klebt er
                // oben unter der Ueberschrift, waehrend er dort auf halber
                // Hoehe steht.
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    EmptyState(
                        icon = FlexrIcons.Chats,
                        title = stringResource(R.string.chats_empty_title),
                        description = stringResource(R.string.chats_empty_sub),
                    )
                }
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                    modifier = Modifier.fillMaxSize(),
                ) {
                    items(conversations, key = { it.matchId }) { match ->
                        MatchListItem(
                            match = match,
                            onClick = { onOpenChat(match.matchId) },
                            ownUserId = ownUserId,
                            showLastMessage = true,
                        )
                    }
                    item { Spacer(Modifier.height(12.dp)) }
                }
            }
        }
    }
}

/**
 * „Wer dich geliket hat" als Karte ueber der Matchliste (`.incoming-card`).
 *
 * Die Zahl steht im Kreis links daneben - deshalb kommt sie im Satz daneben
 * nicht noch einmal vor.
 */
@Composable
private fun IncomingLikesCard(
    count: Int,
    premiumRequired: Boolean,
    onClick: () -> Unit,
) {
    val colors = FlexrTheme.colors
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(MaterialTheme.shapes.medium)
            .background(colors.plate.copy(alpha = 0.08f))
            .border(1.dp, colors.plateDim, MaterialTheme.shapes.medium)
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 11.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(
            Modifier
                .size(34.dp)
                .clip(CircleShape)
                .background(colors.plate),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = count.toString(),
                style = MaterialTheme.typography.titleMedium,
                color = colors.plateInk,
            )
        }
        Column(Modifier.weight(1f)) {
            Text(
                text = if (count == 1) {
                    stringResource(R.string.incoming_title_one)
                } else {
                    stringResource(R.string.incoming_title)
                },
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalk,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = if (premiumRequired) {
                    stringResource(R.string.incoming_sub_free)
                } else {
                    stringResource(R.string.incoming_sub_premium)
                },
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        Icon(
            FlexrIcons.Forward,
            contentDescription = null,
            tint = colors.chalkDim,
            modifier = Modifier.size(18.dp),
        )
    }
}
