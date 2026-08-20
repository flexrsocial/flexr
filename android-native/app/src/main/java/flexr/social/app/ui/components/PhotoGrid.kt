package flexr.social.app.ui.components

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.domain.model.PhotoStatus

/** Ein Feld im Fotoraster — entweder belegt oder leer. */
data class PhotoSlot(
    val key: String,
    /** Coil-Modell: Uri, URL-String oder ByteArray. */
    val model: Any,
    val status: PhotoStatus? = null,
)

/**
 * Fotoraster mit sechs Feldern (`.photo-grid` im Web).
 *
 * Belegte Felder zeigen das Bild plus — beim eigenen Profil — den
 * Moderationsstatus; leere Felder öffnen den Android-Fotoauswahldialog.
 * Der nutzt den systemeigenen Photo Picker: keine Speicher-Berechtigung nötig,
 * und die App sieht ausschließlich die gewählten Bilder.
 */
@Composable
fun PhotoGridEditor(
    slots: List<PhotoSlot>,
    onPhotoPicked: (android.net.Uri) -> Unit,
    onRemove: (String) -> Unit,
    modifier: Modifier = Modifier,
    maxPhotos: Int = ImageProcessor.MAX_PHOTOS,
    showStatus: Boolean = false,
) {
    val picker = rememberLauncherForActivityResult(
        ActivityResultContracts.PickVisualMedia(),
    ) { uri -> uri?.let(onPhotoPicked) }

    val rows = (maxPhotos + 2) / 3
    Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        repeat(rows) { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                repeat(3) { column ->
                    val index = row * 3 + column
                    Box(Modifier.weight(1f)) {
                        if (index < maxPhotos) {
                            val slot = slots.getOrNull(index)
                            if (slot != null) {
                                FilledPhotoSlot(
                                    slot = slot,
                                    showStatus = showStatus,
                                    onRemove = { onRemove(slot.key) },
                                )
                            } else {
                                EmptyPhotoSlot(
                                    onClick = {
                                        picker.launch(
                                            PickVisualMediaRequest(
                                                ActivityResultContracts.PickVisualMedia.ImageOnly,
                                            ),
                                        )
                                    },
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FilledPhotoSlot(slot: PhotoSlot, showStatus: Boolean, onRemove: () -> Unit) {
    val colors = FlexrTheme.colors
    val borderColor = when {
        !showStatus || slot.status == PhotoStatus.APPROVED -> Color.Transparent
        slot.status == PhotoStatus.REJECTED -> colors.danger.copy(alpha = 0.5f)
        else -> colors.plateDim
    }

    Box(
        Modifier
            .fillMaxWidth()
            .aspectRatio(3f / 4f)
            .clip(RoundedCornerShape(11.dp))
            .border(1.5.dp, borderColor, RoundedCornerShape(11.dp)),
    ) {
        AsyncImage(
            model = slot.model,
            contentDescription = "Profilfoto",
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize(),
        )
        Box(
            Modifier
                .align(Alignment.TopEnd)
                .padding(4.dp)
                .size(22.dp)
                .clip(CircleShape)
                .background(Color.Black.copy(alpha = 0.6f))
                .clickable(onClick = onRemove),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                Icons.Filled.Close,
                contentDescription = "Foto entfernen",
                tint = Color.White,
                modifier = Modifier.size(13.dp),
            )
        }
        if (showStatus && slot.status != null && slot.status != PhotoStatus.APPROVED) {
            Text(
                text = if (slot.status == PhotoStatus.REJECTED) "Abgelehnt" else "In Prüfung",
                style = MonoStyle.copy(fontSize = androidx.compose.ui.unit.TextUnit(9f, androidx.compose.ui.unit.TextUnitType.Sp)),
                color = if (slot.status == PhotoStatus.REJECTED) colors.danger else colors.plate,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(4.dp)
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(6.dp))
                    .background(Color.Black.copy(alpha = 0.62f))
                    .padding(vertical = 2.dp),
            )
        }
    }
}

@Composable
private fun EmptyPhotoSlot(onClick: () -> Unit) {
    val colors = FlexrTheme.colors
    Box(
        Modifier
            .fillMaxWidth()
            .aspectRatio(3f / 4f)
            .clip(RoundedCornerShape(11.dp))
            .background(Color.White.copy(alpha = 0.015f))
            .border(1.5.dp, colors.steel, RoundedCornerShape(11.dp))
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            Icons.Filled.Add,
            contentDescription = "Foto hinzufügen",
            tint = colors.chalkDim,
            modifier = Modifier.size(26.dp),
        )
    }
}

/** Sichtbarkeitshinweis unter dem Fotoraster (`.photo-hint`). */
@Composable
fun PhotoVisibilityHint(
    photoStatuses: List<PhotoStatus>,
    modifier: Modifier = Modifier,
) {
    val colors = FlexrTheme.colors
    val (text, warn) = when {
        photoStatuses.isEmpty() ->
            "Mindestens ein Foto ist nötig, damit dein Profil sichtbar ist." to true
        photoStatuses.any { it == PhotoStatus.APPROVED } ->
            "Dein Profil ist sichtbar. Neue Fotos werden kurz geprüft." to false
        photoStatuses.any { it == PhotoStatus.PENDING } ->
            "Dein Foto wird geprüft." to true
        else ->
            "Foto abgelehnt. Bitte lade ein anderes hoch." to true
    }

    Text(
        text = text,
        style = MaterialTheme.typography.bodySmall,
        color = if (warn) colors.plate else colors.chalkDim,
        modifier = modifier.fillMaxWidth().padding(top = 8.dp),
    )
}
