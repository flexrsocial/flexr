package flexr.social.app.ui.matches

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.R
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.ui.components.ConfirmDialog
import flexr.social.app.ui.components.PhotoLightbox
import flexr.social.app.ui.components.ReportDialog
import flexr.social.app.ui.swipe.SwipeableCard
import flexr.social.app.ui.swipe.rememberSwipeCardState

/**
 * Profil eines Matches — der Zwischenschritt vor dem Chat.
 *
 * Zeigt dieselbe Karte wie das Deck, aber ohne Wischgeste; stattdessen gibt es
 * „Match auflösen", „Melden" und „Blockieren" direkt auf der Karte.
 */
@Composable
fun MatchProfileScreen(
    onBack: () -> Unit,
    onOpenChat: (String) -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: MatchProfileViewModel = hiltViewModel(),
) {
    val match by viewModel.match.collectAsStateWithLifecycle()
    var lightboxStartIndex by remember { mutableStateOf<Int?>(null) }
    var photoIndex by remember { mutableIntStateOf(0) }
    var showReportDialog by remember { mutableStateOf(false) }
    var showBlockDialog by remember { mutableStateOf(false) }
    var showUnmatchDialog by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is MatchProfileEvent.Message -> onShowMessage(event.text)
                MatchProfileEvent.Closed -> onBack()
            }
        }
    }

    val current = match
    Column(
        Modifier
            .fillMaxSize()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp),
    ) {
        Row(
            Modifier.fillMaxWidth().padding(vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack, modifier = Modifier.size(36.dp)) {
                Icon(
                    FlexrIcons.Back,
                    contentDescription = stringResource(R.string.common_back),
                    tint = FlexrTheme.colors.chalk,
                )
            }
            Spacer(Modifier.width(6.dp))
            Text(
                text = current?.profile?.let { "${it.name}, ${it.age}" } ?: stringResource(R.string.common_profile),
                style = MaterialTheme.typography.titleMedium,
                color = FlexrTheme.colors.chalk,
            )
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(FlexrTheme.colors.hairline))
        Spacer(Modifier.height(16.dp))

        if (current == null) {
            LoadingState()
            return@Column
        }

        Box(Modifier.fillMaxWidth().weight(1f)) {
            SwipeableCard(
                profile = current.profile,
                state = rememberSwipeCardState(current.profile.id),
                onSwiped = {},
                onOpenPhotos = { index -> lightboxStartIndex = index },
                onReport = { showReportDialog = true },
                onBlock = { showBlockDialog = true },
                // Auf dem Profil wird nicht gewischt — nur betrachtet.
                // Melden, Blockieren, Auflösen und die Fotogalerie bleiben aktiv.
                onUnmatch = { showUnmatchDialog = true },
                draggable = false,
                photoIndex = photoIndex,
                onPhotoIndexChange = { photoIndex = it },
            )
        }

        Spacer(Modifier.height(16.dp))
        FlexrButton(
            text = stringResource(R.string.common_write_message),
            onClick = { onOpenChat(current.matchId) },
            icon = FlexrIcons.Chats,
        )
        Spacer(Modifier.height(16.dp))
    }

    lightboxStartIndex?.let { startIndex ->
        current?.let {
            PhotoLightbox(
                photos = it.profile.photos,
                startIndex = startIndex,
                onClose = { lastIndex ->
                    photoIndex = lastIndex
                    lightboxStartIndex = null
                },
            )
        }
    }

    if (showReportDialog && current != null) {
        ReportDialog(
            userName = current.profile.name,
            onSubmit = {
                showReportDialog = false
                viewModel.report(it)
            },
            onDismiss = { showReportDialog = false },
        )
    }
    if (showBlockDialog && current != null) {
        ConfirmDialog(
            title = stringResource(R.string.block_dialog_title, current.profile.name),
            text = stringResource(R.string.match_profile_block_body),
            confirmLabel = stringResource(R.string.common_block),
            onConfirm = {
                showBlockDialog = false
                viewModel.block()
            },
            onDismiss = { showBlockDialog = false },
        )
    }
    if (showUnmatchDialog && current != null) {
        ConfirmDialog(
            title = stringResource(R.string.match_profile_unmatch_title, current.profile.name),
            text = stringResource(R.string.match_profile_unmatch_body),
            confirmLabel = stringResource(R.string.match_profile_unmatch_confirm),
            onConfirm = {
                showUnmatchDialog = false
                viewModel.unmatch()
            },
            onDismiss = { showUnmatchDialog = false },
        )
    }
}
