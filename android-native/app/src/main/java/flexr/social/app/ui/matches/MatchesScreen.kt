package flexr.social.app.ui.matches

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.core.designsystem.component.EmptyState
import flexr.social.app.core.designsystem.component.ScreenHeader
import flexr.social.app.core.designsystem.icon.FlexrIcons
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
    viewModel: MatchesViewModel = hiltViewModel(),
) {
    val matches by viewModel.matches.collectAsStateWithLifecycle()
    val isRefreshing by viewModel.isRefreshing.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        while (isActive) {
            delay(LIST_POLL_INTERVAL_MS)
            viewModel.silentRefresh()
        }
    }

    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(18.dp))
        ScreenHeader(eyebrow = "Trefferquote", title = "Deine Matches")
        Spacer(Modifier.height(16.dp))

        PullToRefreshBox(
            isRefreshing = isRefreshing,
            onRefresh = viewModel::refresh,
            modifier = Modifier.fillMaxSize(),
        ) {
            if (matches.isEmpty() && !isRefreshing) {
                Box(Modifier.fillMaxSize()) {
                    EmptyState(
                        icon = FlexrIcons.Matches,
                        title = "Noch keine Matches",
                        description = "Weiter swipen — dein nächster Trainingspartner wartet schon.",
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
        ScreenHeader(eyebrow = "Im Gespräch", title = "Deine Chats")
        Spacer(Modifier.height(16.dp))

        PullToRefreshBox(
            isRefreshing = isRefreshing,
            onRefresh = viewModel::refresh,
            modifier = Modifier.fillMaxSize(),
        ) {
            if (conversations.isEmpty() && !isRefreshing) {
                Box(Modifier.fillMaxSize()) {
                    EmptyState(
                        icon = FlexrIcons.Chats,
                        title = "Noch keine Chats",
                        description = "Schreib einem deiner Matches die erste Nachricht.",
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
