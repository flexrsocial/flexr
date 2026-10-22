package flexr.social.app.ui.incoming

import androidx.activity.compose.BackHandler
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import flexr.social.app.R
import flexr.social.app.core.designsystem.component.EmptyState
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.component.PremiumBadge
import flexr.social.app.core.designsystem.component.ScreenHeader
import flexr.social.app.core.designsystem.component.VerifiedBadge
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.domain.model.Profile
import flexr.social.app.ui.components.ConfirmDialog
import flexr.social.app.ui.components.PhotoLightbox
import flexr.social.app.ui.components.ReportDialog
import flexr.social.app.ui.swipe.MatchOverlay
import flexr.social.app.ui.swipe.RoundActionButton
import flexr.social.app.ui.swipe.SwipeableCard
import flexr.social.app.ui.swipe.rememberSwipeCardState

/**
 * „Wer dich geliket hat" — die Namen gibt es nur mit Premium.
 *
 * Der gesperrte Zustand ist bewusst kein Fehlerbildschirm, sondern die Zahl
 * plus der Hinweis, dass dieselben Leute auch ganz normal im Deck auftauchen.
 * Wer ohne Premium hier landet, hat nichts verloren — er sieht nur nicht, wer
 * es ist.
 *
 * Der Weg zum Angebot steht hier nur, wenn der Server diesem Client einen Kauf
 * überhaupt anbietet ([premiumOffered]) — in dieser App also über Play
 * Billing, und nur mit eingetragener Produktkennung. Fehlt sie, bleibt es bei
 * der Auskunft, ohne Knopf und ohne Preis.
 */
@Composable
fun IncomingScreen(
    onBack: () -> Unit,
    onOpenPremium: () -> Unit,
    onOpenChat: (String) -> Unit,
    onShowMessage: (String) -> Unit,
    onShowStickyMessage: (String) -> Unit,
    premiumOffered: Boolean,
    viewModel: IncomingViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val likes = state.likes
    val selected = state.selected

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is IncomingEvent.Message ->
                    if (event.sticky) onShowStickyMessage(event.text) else onShowMessage(event.text)
                is IncomingEvent.OpenChat -> onOpenChat(event.matchId)
            }
        }
    }
    // Zurück schließt zuerst das geöffnete Profil, erst dann den Bildschirm.
    BackHandler(enabled = selected != null) { viewModel.closeProfile() }

    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        // Eigene Kopfzeile mit Ausstieg wie im Match-Profil: Der Bildschirm
        // liegt ueber der unteren Navigation, ohne Knopf bliebe nur die
        // Systemgeste.
        Row(
            Modifier.fillMaxWidth().padding(vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(
                onClick = { if (selected != null) viewModel.closeProfile() else onBack() },
                modifier = Modifier.size(36.dp),
            ) {
                Icon(
                    FlexrIcons.Back,
                    contentDescription = stringResource(R.string.common_back),
                    tint = FlexrTheme.colors.chalk,
                )
            }
            Spacer(Modifier.width(6.dp))
            ScreenHeader(
                eyebrow = stringResource(R.string.incoming_eyebrow),
                title = selected?.let { "${it.name}, ${it.age}" } ?: stringResource(R.string.incoming_h2),
            )
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(FlexrTheme.colors.hairline))
        Spacer(Modifier.height(16.dp))

        if (selected != null) {
            IncomingProfile(
                profile = selected,
                isSwiping = state.isSwiping,
                onLike = viewModel::like,
                onPass = viewModel::pass,
                onReport = viewModel::report,
                onBlock = viewModel::block,
            )
            return@Column
        }

        Box(Modifier.fillMaxSize()) {
            when {
                state.isLoading -> LoadingState(label = stringResource(R.string.incoming_loading))

                state.error != null -> EmptyState(
                    modifier = Modifier.align(Alignment.Center),
                    icon = FlexrIcons.Matches,
                    title = stringResource(R.string.incoming_h2),
                    description = state.error.orEmpty(),
                    action = {
                        FlexrSecondaryButton(
                            text = stringResource(R.string.swipe_retry),
                            onClick = viewModel::load,
                        )
                    },
                )

                likes == null || (likes.count == 0 && likes.profiles.isEmpty()) -> EmptyState(
                    modifier = Modifier.align(Alignment.Center),
                    icon = FlexrIcons.Matches,
                    title = stringResource(R.string.incoming_h2),
                    description = stringResource(R.string.incoming_none),
                )

                likes.premiumRequired -> Column(
                    Modifier.align(Alignment.Center).fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    EmptyState(
                        icon = FlexrIcons.Premium,
                        title = if (likes.count == 1) {
                            stringResource(R.string.incoming_locked_title_one)
                        } else {
                            stringResource(R.string.incoming_locked_title, likes.count)
                        },
                        description = stringResource(R.string.incoming_locked_sub),
                    )
                    if (premiumOffered) {
                        FlexrButton(
                            text = stringResource(R.string.premium_show_offer),
                            onClick = onOpenPremium,
                            modifier = Modifier.padding(top = 4.dp),
                        )
                    }
                }

                else -> LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                    modifier = Modifier.fillMaxSize(),
                ) {
                    items(likes.profiles, key = { it.id }) { profile ->
                        IncomingProfileRow(profile, onClick = { viewModel.openProfile(profile) })
                    }
                    item { Spacer(Modifier.height(12.dp)) }
                }
            }
        }
    }

    state.matchedWith?.let { matched ->
        MatchOverlay(
            matchedProfile = matched,
            ownAvatarUrl = state.ownAvatarUrl,
            ownName = stringResource(R.string.swipe_own_name),
            onWriteMessage = viewModel::openChatWithMatch,
            onKeepSwiping = viewModel::dismissMatchOverlay,
        )
    }
}

/**
 * Das angetippte Profil: dieselbe Karte wie im Match-Profil (waagrecht gewischt
 * blättert das Foto, Melden und Blockieren auf der Karte), darunter X und Herz
 * wie im Deck. Die Knöpfe stehen unter der Karte statt darauf - so verdecken
 * sie keine Bio.
 */
@Composable
private fun IncomingProfile(
    profile: Profile,
    isSwiping: Boolean,
    onLike: () -> Unit,
    onPass: () -> Unit,
    onReport: (String) -> Unit,
    onBlock: () -> Unit,
) {
    var photoIndex by remember(profile.id) { mutableIntStateOf(0) }
    var lightboxStartIndex by remember(profile.id) { mutableStateOf<Int?>(null) }
    var showReportDialog by remember(profile.id) { mutableStateOf(false) }
    var showBlockDialog by remember(profile.id) { mutableStateOf(false) }

    Column(Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxWidth().weight(1f)) {
            SwipeableCard(
                profile = profile,
                state = rememberSwipeCardState(profile.id),
                onSwiped = {},
                onOpenPhotos = { index -> lightboxStartIndex = index },
                onReport = { showReportDialog = true },
                onBlock = { showBlockDialog = true },
                draggable = false,
                photoIndex = photoIndex,
                onPhotoIndexChange = { photoIndex = it },
            )
        }
        Row(
            Modifier.fillMaxWidth().padding(vertical = 14.dp),
            horizontalArrangement = Arrangement.spacedBy(22.dp, Alignment.CenterHorizontally),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            RoundActionButton(
                icon = FlexrIcons.Pass,
                description = stringResource(R.string.swipe_pass),
                tint = FlexrTheme.colors.danger,
                enabled = !isSwiping,
                onClick = onPass,
            )
            RoundActionButton(
                icon = FlexrIcons.Like,
                description = stringResource(R.string.swipe_like),
                tint = Color.White,
                large = true,
                enabled = !isSwiping,
                onClick = onLike,
            )
        }
    }

    lightboxStartIndex?.let { startIndex ->
        PhotoLightbox(
            photos = profile.photos,
            startIndex = startIndex,
            onClose = { lastIndex ->
                photoIndex = lastIndex
                lightboxStartIndex = null
            },
        )
    }
    if (showReportDialog) {
        ReportDialog(
            userName = profile.name,
            onSubmit = { reason ->
                showReportDialog = false
                onReport(reason)
            },
            onDismiss = { showReportDialog = false },
        )
    }
    if (showBlockDialog) {
        ConfirmDialog(
            title = stringResource(R.string.block_dialog_title, profile.name),
            text = stringResource(R.string.swipe_block_body),
            confirmLabel = stringResource(R.string.common_block),
            onConfirm = {
                showBlockDialog = false
                onBlock()
            },
            onDismiss = { showBlockDialog = false },
        )
    }
}

/**
 * Eine Zeile der Liste — dieselbe Form wie [flexr.social.app.ui.matches.MatchListItem],
 * damit die Ansicht nicht wie ein fremder Teil der App wirkt. Ein Tipp öffnet
 * das Profil mit X und Herz (bis 2.7.38 ohne Tippziel).
 */
@Composable
private fun IncomingProfileRow(profile: Profile, onClick: () -> Unit) {
    val colors = FlexrTheme.colors
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(MaterialTheme.shapes.medium)
            .background(Brush.verticalGradient(listOf(Color(0xFF1F1F1F), Color(0xFF1A1A1A))))
            .border(1.dp, colors.hairline, MaterialTheme.shapes.medium)
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(13.dp),
    ) {
        AsyncImage(
            model = profile.primaryPhoto?.avatarUrl,
            contentDescription = stringResource(R.string.common_profile_photo_of, profile.name),
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .size(54.dp)
                .clip(CircleShape)
                .background(colors.surface2),
        )
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
                if (profile.isPremium) {
                    Spacer(Modifier.width(6.dp))
                    PremiumBadge(size = 14)
                }
            }
            Text(
                text = listOfNotNull(
                    profile.city.takeIf { it.isNotBlank() },
                    profile.gymName.takeIf { it.isNotBlank() },
                ).joinToString(" · "),
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 3.dp),
            )
        }
        Icon(
            Icons.AutoMirrored.Filled.KeyboardArrowRight,
            contentDescription = null,
            tint = colors.chalkDim.copy(alpha = 0.6f),
            modifier = Modifier.size(18.dp),
        )
    }
}
