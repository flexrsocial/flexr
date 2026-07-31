package flexr.social.app.ui.swipe

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.AnimationVector2D
import androidx.compose.animation.core.VectorConverter
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import flexr.social.app.core.designsystem.component.StatChip
import flexr.social.app.core.designsystem.component.VerifiedBadge
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.domain.model.Profile
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import kotlin.math.abs

/**
 * Zustand einer Swipe-Karte. Ausgelagert, damit auch die Aktionsknöpfe unter
 * dem Deck dieselbe Wegflug-Animation auslösen wie eine echte Wischgeste.
 */
class SwipeCardState internal constructor(
    internal val offset: Animatable<Offset, AnimationVector2D>,
) {
    internal var gripSign by mutableFloatStateOf(1f)
    internal var containerWidth by mutableFloatStateOf(1080f)

    val horizontalOffset: Float get() = offset.value.x

    /** Wegflug nach links (Pass) oder rechts (Like). */
    suspend fun flyOut(like: Boolean, velocity: Float = 0f) {
        val speed = abs(velocity).coerceAtMost(4000f)
        val direction = if (like) 1f else -1f
        val duration = (420 - speed / 20).toInt().coerceAtLeast(260)
        offset.animateTo(
            targetValue = Offset(
                x = direction * (containerWidth * 1.6f + speed * 0.1f),
                y = -160f,
            ),
            animationSpec = tween(duration),
        )
    }

    suspend fun settleBack() {
        offset.animateTo(Offset.Zero, spring(dampingRatio = 0.55f, stiffness = 420f))
    }

    suspend fun reset() = offset.snapTo(Offset.Zero)
}

@Composable
fun rememberSwipeCardState(key: Any?): SwipeCardState {
    val animatable = remember(key) { Animatable(Offset.Zero, Offset.VectorConverter) }
    return remember(key) { SwipeCardState(animatable) }
}

/**
 * Profilkarte mit Wischgeste.
 *
 * Verhalten wie in der Web-App: Die Rotation richtet sich nach Auslenkung UND
 * Griffpunkt (oben angefasst kippt die Karte anders als unten, wie ein Blatt
 * Papier). Ausgelöst wird ab einer Schwelle ODER bei genug Schwung.
 */
@Composable
fun SwipeableCard(
    profile: Profile,
    state: SwipeCardState,
    onSwiped: (like: Boolean) -> Unit,
    onOpenPhotos: (startIndex: Int) -> Unit,
    onReport: () -> Unit,
    onBlock: () -> Unit,
    /** Angezeigtes Foto — ausgelagert, damit die Vollbildansicht ihren Stand zurückgibt. */
    photoIndex: Int,
    onPhotoIndexChange: (Int) -> Unit,
    modifier: Modifier = Modifier,
    onUnmatch: (() -> Unit)? = null,
    /** Wischgeste aktiv. Im Match-Profil wird nicht gewischt, nur betrachtet. */
    draggable: Boolean = true,
    /** Melde-/Block-Knöpfe, Fotogalerie und Stempel. */
    interactive: Boolean = true,
) {
    val scope = rememberCoroutineScope()
    val density = LocalDensity.current
    val threshold = with(density) { SWIPE_THRESHOLD_DP.dp.toPx() }
    val dragX = state.offset.value.x
    val progress = (abs(dragX) / threshold).coerceIn(0f, 1f)

    Box(
        modifier = modifier
            .fillMaxSize()
            .graphicsLayer {
                state.containerWidth = size.width
                translationX = state.offset.value.x
                translationY = state.offset.value.y * 0.55f
                rotationZ = (state.offset.value.x / 12f)
                    .coerceIn(-MAX_ROTATION, MAX_ROTATION) * state.gripSign
                alpha = 1f - (progress * 0.15f)
            }
            .clip(RoundedCornerShape(20.dp))
            .background(Brush.verticalGradient(listOf(Color(0xFF202020), Color(0xFF191919))))
            .border(1.5.dp, FlexrTheme.colors.plate.copy(alpha = 0.3f), RoundedCornerShape(20.dp))
            .then(
                if (draggable) {
                    Modifier.pointerInput(profile.id) {
                        val velocityTracker = androidx.compose.ui.input.pointer.util.VelocityTracker()
                        detectDragGestures(
                            onDragStart = { position ->
                                velocityTracker.resetTracking()
                                state.gripSign = if (position.y < size.height / 2f) 1f else -1f
                            },
                            onDrag = { change, dragAmount ->
                                change.consume()
                                velocityTracker.addPosition(change.uptimeMillis, change.position)
                                scope.launch { state.offset.snapTo(state.offset.value + dragAmount) }
                            },
                            onDragCancel = { scope.launch { state.settleBack() } },
                            onDragEnd = {
                                val velocityX = velocityTracker.calculateVelocity().x
                                val flung = abs(velocityX) > FLING_VELOCITY && abs(state.offset.value.x) > 40f
                                if (abs(state.offset.value.x) > threshold || flung) {
                                    val like = if (flung) velocityX > 0 else state.offset.value.x > 0
                                    scope.launch {
                                        state.flyOut(like, velocityX)
                                        onSwiped(like)
                                    }
                                } else {
                                    scope.launch { state.settleBack() }
                                }
                            },
                        )
                    }
                } else {
                    Modifier
                }
            ),
    ) {
        CardContent(
            profile = profile,
            interactive = interactive,
            onOpenPhotos = onOpenPhotos,
            onReport = onReport,
            onBlock = onBlock,
            onUnmatch = onUnmatch,
            photoIndex = photoIndex,
            onPhotoIndexChange = onPhotoIndexChange,
        )

        if (draggable) {
            SwipeStamp(
                text = "Match",
                color = FlexrTheme.colors.lime,
                rotation = -10f,
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(16.dp)
                    .alpha(if (dragX > 0) progress else 0f),
            )
            SwipeStamp(
                text = "Nope",
                color = FlexrTheme.colors.danger,
                rotation = 10f,
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(16.dp)
                    .alpha(if (dragX < 0) progress else 0f),
            )
        }
    }
}

/** Karte im Hintergrund des Stapels — wächst mit, während die obere weggezogen wird. */
@Composable
fun BackgroundCard(profile: Profile, progress: Float, modifier: Modifier = Modifier) {
    val scale = 0.92f + 0.08f * progress
    Box(
        modifier = modifier
            .fillMaxSize()
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                translationY = 14f * (1f - progress)
            }
            .clip(RoundedCornerShape(20.dp))
            .background(Brush.verticalGradient(listOf(Color(0xFF202020), Color(0xFF191919))))
            .border(1.dp, FlexrTheme.colors.hairline, RoundedCornerShape(20.dp)),
    ) {
        CardContent(
            profile = profile,
            interactive = false,
            onOpenPhotos = {},
            onReport = {},
            onBlock = {},
            onUnmatch = null,
            photoIndex = 0,
            onPhotoIndexChange = {},
        )
    }
}



@Composable
private fun CardContent(
    profile: Profile,
    interactive: Boolean,
    onOpenPhotos: (Int) -> Unit,
    onReport: () -> Unit,
    onBlock: () -> Unit,
    onUnmatch: (() -> Unit)?,
    photoIndex: Int,
    onPhotoIndexChange: (Int) -> Unit,
) {
    val colors = FlexrTheme.colors
    val photos = profile.photos

    Column(Modifier.fillMaxSize()) {
        Box(
            Modifier
                .fillMaxWidth()
                .weight(0.58f)
                .pointerInput(profile.id, interactive) {
                    if (interactive && photos.isNotEmpty()) {
                        detectTapGestures { onOpenPhotos(photoIndex) }
                    }
                },
        ) {
            AsyncImage(
                model = photos.getOrNull(photoIndex)?.url,
                contentDescription = "Profilfoto von ${profile.name}",
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize().background(colors.surface2),
            )
            // Abdunkelung oben und unten, damit Text auf jedem Foto lesbar bleibt
            Box(
                Modifier.fillMaxSize().background(
                    Brush.verticalGradient(
                        0f to Color.Black.copy(alpha = 0.38f),
                        0.16f to Color.Transparent,
                        0.42f to Color.Transparent,
                        1f to Color.Black.copy(alpha = 0.88f),
                    ),
                ),
            )

            if (photos.size > 1) {
                // Die Striche sind die Foto-Auswahl: ein Tipp auf einen Strich
                // (bzw. den Bereich darunter) schaltet direkt auf dieses Foto —
                // ohne Umweg über die Vollbildansicht. Der Trefferbereich ist
                // bewusst 44dp hoch, die Striche selbst wären zu schmal.
                Box(
                    Modifier
                        .align(Alignment.TopCenter)
                        .fillMaxWidth()
                        .height(44.dp)
                        .pointerInput(profile.id, photos.size, interactive) {
                            if (!interactive) return@pointerInput
                            detectTapGestures { offset ->
                                val segment = size.width.toFloat() / photos.size
                                onPhotoIndexChange(
                                    (offset.x / segment).toInt().coerceIn(0, photos.lastIndex),
                                )
                            }
                        },
                ) {
                    Row(
                        Modifier.fillMaxWidth().padding(10.dp),
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        photos.forEachIndexed { index, _ ->
                            Box(
                                Modifier
                                    .weight(1f)
                                    .height(3.dp)
                                    .clip(RoundedCornerShape(2.dp))
                                    .background(
                                        if (index == photoIndex) colors.plate
                                        else Color.White.copy(alpha = 0.28f),
                                    ),
                            )
                        }
                    }
                }
            }

            if (interactive) {
                Row(
                    Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = 22.dp, end = 10.dp),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    onUnmatch?.let {
                        CardActionButton(FlexrIcons.Unmatch, "Match auflösen", it)
                    }
                    CardActionButton(FlexrIcons.Report, "Melden", onReport)
                    CardActionButton(FlexrIcons.Block, "Blockieren", onBlock)
                }
            }

            Column(
                Modifier
                    .align(Alignment.BottomStart)
                    .padding(start = 16.dp, end = 16.dp, bottom = 12.dp),
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "${profile.name}, ${profile.age}",
                        style = MaterialTheme.typography.titleLarge.copy(fontSize = androidx.compose.ui.unit.TextUnit(26f, androidx.compose.ui.unit.TextUnitType.Sp)),
                        color = Color.White,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    if (profile.isVerified) {
                        Spacer(Modifier.size(6.dp))
                        VerifiedBadge()
                    }
                }
                Text(
                    text = buildString {
                        append(profile.city)
                        if (profile.gymName.isNotBlank()) append(" · ").append(profile.gymName)
                        profile.distanceKm?.let { append(" · ").append("$it km") }
                    }.uppercase(),
                    style = MonoStyle,
                    color = colors.chalkDim,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }

        Column(
            Modifier
                .fillMaxWidth()
                .weight(0.42f)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 14.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatChip(
                    text = profile.gym.ifBlank { "Kein Gym angegeben" },
                    icon = FlexrIcons.Gym,
                )
                if (profile.isOnline) {
                    StatChip(text = "Online", accent = true, pulsingDot = true)
                }
            }
            Spacer(Modifier.height(12.dp))
            Text(
                text = profile.bio?.takeIf { it.isNotBlank() } ?: "Keine Bio angegeben.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
        }
    }
}

@Composable
private fun CardActionButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    description: String,
    onClick: () -> Unit,
) {
    Box(
        Modifier
            .size(30.dp)
            .clip(CircleShape)
            .background(Color.Black.copy(alpha = 0.5f))
            .border(1.dp, Color.White.copy(alpha = 0.22f), CircleShape)
            .pointerInput(description) { detectTapGestures { onClick() } },
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            icon,
            contentDescription = description,
            tint = Color.White.copy(alpha = 0.85f),
            modifier = Modifier.size(15.dp),
        )
    }
}

/** MATCH-/NOPE-Stempel, der beim Ziehen sichtbar wird. */
@Composable
private fun SwipeStamp(
    text: String,
    color: Color,
    rotation: Float,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier
            .graphicsLayer { rotationZ = rotation }
            .clip(RoundedCornerShape(10.dp))
            .background(Color.Black.copy(alpha = 0.35f))
            .border(3.dp, color, RoundedCornerShape(10.dp))
            .padding(horizontal = 14.dp, vertical = 6.dp),
    ) {
        Text(
            text = text.uppercase(),
            style = MaterialTheme.typography.headlineMedium,
            color = color,
        )
    }
}

private const val SWIPE_THRESHOLD_DP = 96
private const val MAX_ROTATION = 15f
private const val FLING_VELOCITY = 900f

/** Hilfsfunktion für die Aktionsknöpfe: Karte wegfliegen lassen, dann melden. */
fun CoroutineScope.commitSwipe(state: SwipeCardState, like: Boolean, onSwiped: (Boolean) -> Unit) {
    launch {
        state.flyOut(like)
        onSwiped(like)
    }
}
