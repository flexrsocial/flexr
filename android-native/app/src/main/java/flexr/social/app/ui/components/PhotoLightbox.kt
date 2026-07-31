package flexr.social.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil.compose.AsyncImage
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.domain.model.Photo

/**
 * Foto-Vollbild mit Wischgalerie.
 *
 * Nativ per [HorizontalPager] gelöst: Wischen, Fangpunkte und Vorausladen
 * kommen vom Framework — im Web war das handgeschriebene Touch-Logik.
 * Beim Schließen wird der zuletzt betrachtete Index zurückgemeldet, damit die
 * Karte dahinter dasselbe Foto zeigt.
 */
@Composable
fun PhotoLightbox(
    photos: List<Photo>,
    startIndex: Int,
    onClose: (lastIndex: Int) -> Unit,
) {
    if (photos.isEmpty()) return
    val pagerState = rememberPagerState(
        initialPage = startIndex.coerceIn(0, photos.lastIndex),
        pageCount = { photos.size },
    )

    Dialog(
        onDismissRequest = { onClose(pagerState.currentPage) },
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Box(
            Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.96f)),
        ) {
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.fillMaxSize(),
                pageSpacing = 12.dp,
            ) { page ->
                AsyncImage(
                    model = photos[page].url,
                    contentDescription = "Foto ${page + 1} von ${photos.size}",
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp, vertical = 64.dp),
                )
            }

            IconButton(
                onClick = { onClose(pagerState.currentPage) },
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(16.dp)
                    .size(42.dp)
                    .clip(CircleShape)
                    .background(Color.White.copy(alpha = 0.08f)),
            ) {
                Icon(FlexrIcons.Close, contentDescription = "Schließen", tint = Color.White)
            }

            if (photos.size > 1) {
                Row(
                    Modifier
                        .align(Alignment.BottomCenter)
                        .fillMaxWidth()
                        .padding(bottom = 26.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = "${pagerState.currentPage + 1} / ${photos.size}",
                        style = MonoStyle,
                        color = FlexrTheme.colors.chalkDim,
                        modifier = Modifier
                            .clip(CircleShape)
                            .background(Color.White.copy(alpha = 0.08f))
                            .padding(horizontal = 12.dp, vertical = 6.dp),
                    )
                }
            }
        }
    }
}
