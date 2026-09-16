package flexr.social.app.ui.incoming

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
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
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

/**
 * „Wer dich geliket hat" — die Namen gibt es nur mit Premium.
 *
 * Der gesperrte Zustand ist bewusst kein Fehlerbildschirm, sondern die Zahl
 * plus der Hinweis, dass dieselben Leute auch ganz normal im Deck auftauchen.
 * Wer ohne Premium hier landet, hat nichts verloren — er sieht nur nicht, wer
 * es ist.
 */
@Composable
fun IncomingScreen(
    onBack: () -> Unit,
    onOpenPremium: () -> Unit,
    viewModel: IncomingViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val likes = state.likes

    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        // Eigene Kopfzeile mit Ausstieg wie im Match-Profil: Der Bildschirm
        // liegt ueber der unteren Navigation, ohne Knopf bliebe nur die
        // Systemgeste.
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
            ScreenHeader(
                eyebrow = stringResource(R.string.incoming_eyebrow),
                title = stringResource(R.string.incoming_h2),
            )
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(FlexrTheme.colors.hairline))
        Spacer(Modifier.height(16.dp))

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
                    FlexrButton(
                        text = stringResource(R.string.premium_show_offer),
                        onClick = onOpenPremium,
                        modifier = Modifier.padding(top = 4.dp),
                    )
                }

                else -> LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                    modifier = Modifier.fillMaxSize(),
                ) {
                    items(likes.profiles, key = { it.id }) { profile ->
                        IncomingProfileRow(profile)
                    }
                    item { Spacer(Modifier.height(12.dp)) }
                }
            }
        }
    }
}

/**
 * Eine Zeile der Liste — dieselbe Form wie [flexr.social.app.ui.matches.MatchListItem],
 * damit die Ansicht nicht wie ein fremder Teil der App wirkt.
 *
 * Bewusst ohne Tippziel: Von hier aus gibt es (noch) nichts zu öffnen. Ein Chat
 * setzt ein Match voraus, und zurückliken passiert im Deck — die Leute stehen
 * dort ohnehin alle drin.
 */
@Composable
private fun IncomingProfileRow(profile: Profile) {
    val colors = FlexrTheme.colors
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(MaterialTheme.shapes.medium)
            .background(Brush.verticalGradient(listOf(Color(0xFF1F1F1F), Color(0xFF1A1A1A))))
            .border(1.dp, colors.hairline, MaterialTheme.shapes.medium)
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
    }
}
