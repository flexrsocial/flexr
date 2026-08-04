package flexr.social.app.ui.swipe

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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.core.designsystem.component.EmptyState
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.component.ScreenHeader
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.ui.components.ConfirmDialog
import flexr.social.app.ui.components.PhotoLightbox
import flexr.social.app.ui.components.ReportDialog
import kotlin.math.abs

@Composable
fun SwipeScreen(
    onOpenChat: (String) -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: SwipeViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()

    var lightboxStartIndex by remember { mutableStateOf<Int?>(null) }
    var showReportDialog by remember { mutableStateOf(false) }
    var showBlockDialog by remember { mutableStateOf(false) }

    // Keine Standortabfrage mehr: die Umkreissuche geht von der Adresse des
    // eingetragenen Gyms aus, die Geräteposition wird dafür nicht gebraucht.

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is SwipeEvent.Message -> onShowMessage(event.text)
                is SwipeEvent.OpenChat -> onOpenChat(event.matchId)
            }
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp),
    ) {
        Spacer(Modifier.height(18.dp))
        ScreenHeader(eyebrow = "Heutige Sätze", title = "Wer trainiert wo du bist")
        Text(
            // Die Umkreissuche geht von der Adresse des eingetragenen Gyms aus,
            // nicht mehr vom Wohnort und nicht von der Geräteposition.
            text = "Umkreis ${state.searchRadiusKm} km · Standort laut PLZ-Gym".uppercase(),
            style = MonoStyle,
            color = FlexrTheme.colors.chalkDim,
            modifier = Modifier.padding(top = 8.dp),
        )

        Spacer(Modifier.height(16.dp))

        Box(Modifier.fillMaxWidth().weight(1f)) {
            when {
                state.isLoading -> LoadingState(label = "Lade Profile …")

                state.error != null -> EmptyState(
                    icon = FlexrIcons.Swipe,
                    title = "Nicht geladen",
                    description = state.error.orEmpty(),
                    action = {
                        flexr.social.app.core.designsystem.component.FlexrSecondaryButton(
                            text = "Erneut versuchen",
                            onClick = viewModel::loadDeck,
                        )
                    },
                )

                state.isExhausted -> EmptyState(
                    icon = FlexrIcons.Swipe,
                    title = "Alle Sätze absolviert",
                    description = "Keine neuen Profile in deiner Nähe. Schau später nochmal vorbei.",
                    action = {
                        flexr.social.app.core.designsystem.component.FlexrSecondaryButton(
                            text = "Neu laden",
                            onClick = viewModel::loadDeck,
                        )
                    },
                )

                else -> {
                    val current = state.current
                    val cardState = rememberSwipeCardState(current?.id)
                    // Beim Kartenwechsel wieder auf das erste Foto.
                    var photoIndex by remember(current?.id) { mutableIntStateOf(0) }

                    state.next?.let { next ->
                        BackgroundCard(
                            profile = next,
                            progress = (abs(cardState.horizontalOffset) / 300f).coerceIn(0f, 1f),
                        )
                    }
                    current?.let { profile ->
                        SwipeableCard(
                            profile = profile,
                            state = cardState,
                            onSwiped = { like -> if (like) viewModel.like() else viewModel.pass() },
                            onOpenPhotos = { index -> lightboxStartIndex = index },
                            onReport = { showReportDialog = true },
                            onBlock = { showBlockDialog = true },
                            photoIndex = photoIndex,
                            onPhotoIndexChange = { photoIndex = it },
                        )
                    }

                    // Nach dem Schließen zeigt die Karte das zuletzt betrachtete Foto.
                    lightboxStartIndex?.let { startIndex ->
                        current?.let { profile ->
                            PhotoLightbox(
                                photos = profile.photos,
                                startIndex = startIndex,
                                onClose = { lastIndex ->
                                    photoIndex = lastIndex
                                    lightboxStartIndex = null
                                },
                            )
                        }
                    }

                    if (current != null) {
                        Row(
                            Modifier
                                .align(Alignment.BottomCenter)
                                .padding(bottom = 14.dp),
                            horizontalArrangement = Arrangement.spacedBy(26.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            RoundActionButton(
                                icon = FlexrIcons.Pass,
                                description = "Ablehnen",
                                tint = FlexrTheme.colors.danger,
                                onClick = { scope.commitSwipe(cardState, false) { viewModel.pass() } },
                            )
                            RoundActionButton(
                                icon = FlexrIcons.Like,
                                description = "Gefällt mir",
                                tint = Color.White,
                                large = true,
                                onClick = { scope.commitSwipe(cardState, true) { viewModel.like() } },
                            )
                        }
                    }
                }
            }
        }
    }

    val current = state.current

    if (showReportDialog && current != null) {
        ReportDialog(
            userName = current.name,
            onSubmit = { reason ->
                showReportDialog = false
                viewModel.report(current.id, reason)
            },
            onDismiss = { showReportDialog = false },
        )
    }

    if (showBlockDialog && current != null) {
        ConfirmDialog(
            title = "${current.name} blockieren?",
            text = "Ihr seht euch danach nicht mehr — weder im Deck noch in den Matches.",
            confirmLabel = "Blockieren",
            onConfirm = {
                showBlockDialog = false
                viewModel.block(current.id, current.name)
            },
            onDismiss = { showBlockDialog = false },
        )
    }

    state.matchedWith?.let { matched ->
        MatchOverlay(
            matchedProfile = matched,
            ownAvatarUrl = state.ownAvatarUrl,
            ownName = "Du",
            onWriteMessage = viewModel::openChatWithMatch,
            onKeepSwiping = viewModel::dismissMatchOverlay,
        )
    }
}

/** Runder Aktionsknopf unter dem Deck (`.round-btn`). */
@Composable
private fun RoundActionButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    description: String,
    tint: Color,
    onClick: () -> Unit,
    large: Boolean = false,
) {
    val colors = FlexrTheme.colors
    val size = if (large) 64.dp else 56.dp
    Box(
        Modifier
            .size(size)
            .clip(CircleShape)
            .then(
                if (large) {
                    Modifier.background(
                        Brush.linearGradient(
                            listOf(colors.plateBright, colors.plate, Color(0xFFEF4C15)),
                        ),
                    )
                } else {
                    Modifier
                        .background(
                            Brush.verticalGradient(listOf(Color(0xFF222222), Color(0xFF1B1B1B))),
                        )
                        .border(1.dp, colors.steel, CircleShape)
                },
            )
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            icon,
            contentDescription = description,
            tint = tint,
            modifier = Modifier.size(if (large) 28.dp else 24.dp),
        )
    }
}
