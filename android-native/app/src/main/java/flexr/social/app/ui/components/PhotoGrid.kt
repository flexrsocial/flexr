package flexr.social.app.ui.components

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.layout.boundsInWindow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.zIndex
import androidx.compose.ui.graphics.graphicsLayer
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
    /**
     * Neue Reihenfolge nach dem Verschieben (vollstaendige Liste der Schluessel).
     * null schaltet das Sortieren ab - etwa im Onboarding, wo die Fotos noch
     * gar keine Server-IDs haben.
     */
    onReorder: ((List<String>) -> Unit)? = null,
) {
    val picker = rememberLauncherForActivityResult(
        ActivityResultContracts.PickVisualMedia(),
    ) { uri -> uri?.let(onPhotoPicked) }

    // Sortieren per langem Druck: ein kurzer Tipper bleibt fuer "Entfernen"
    // und die Bildauswahl reserviert. Reihenfolge lohnt erst ab zwei Fotos.
    val reorderable = onReorder != null && slots.size > 1
    // Fensterkoordinaten je Feld, beim Layout eingesammelt - daraus wird
    // bestimmt, ueber welchem Feld der Finger gerade steht.
    val bounds = remember { mutableMapOf<Int, Rect>() }
    var draggingIndex by remember { mutableStateOf<Int?>(null) }
    var dragOffset by remember { mutableStateOf(Offset.Zero) }
    var targetIndex by remember { mutableStateOf<Int?>(null) }

    val rows = (maxPhotos + 2) / 3
    Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        repeat(rows) { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                repeat(3) { column ->
                    val index = row * 3 + column
                    Box(
                        Modifier
                            .weight(1f)
                            // Das gezogene Feld nach vorn holen, sonst
                            // verschwindet es unter den Nachbarfeldern.
                            .zIndex(if (draggingIndex == index) 1f else 0f),
                    ) {
                        if (index < maxPhotos) {
                            val slot = slots.getOrNull(index)
                            if (slot != null) {
                                val isDragged = draggingIndex == index
                                FilledPhotoSlot(
                                    slot = slot,
                                    showStatus = showStatus,
                                    onRemove = { onRemove(slot.key) },
                                    position = if (reorderable) index + 1 else null,
                                    isDragged = isDragged,
                                    isDropTarget = targetIndex == index && !isDragged,
                                    modifier = Modifier
                                        .onGloballyPositioned { bounds[index] = it.boundsInWindow() }
                                        .graphicsLayer {
                                            if (isDragged) {
                                                translationX = dragOffset.x
                                                translationY = dragOffset.y
                                            }
                                        }
                                        .then(
                                            if (!reorderable) Modifier else Modifier.pointerInput(slots) {
                                                detectDragGesturesAfterLongPress(
                                                    onDragStart = {
                                                        draggingIndex = index
                                                        dragOffset = Offset.Zero
                                                        targetIndex = null
                                                    },
                                                    onDrag = { change, amount ->
                                                        change.consume()
                                                        dragOffset += amount
                                                        val start = bounds[index] ?: return@detectDragGesturesAfterLongPress
                                                        // Mittelpunkt des mitgezogenen Feldes gegen
                                                        // die uebrigen Felder pruefen.
                                                        val center = start.center + dragOffset
                                                        targetIndex = bounds.entries
                                                            .firstOrNull { (i, rect) ->
                                                                i != index && i < slots.size && rect.contains(center)
                                                            }?.key
                                                    },
                                                    onDragEnd = {
                                                        val from = index
                                                        val to = targetIndex
                                                        draggingIndex = null
                                                        dragOffset = Offset.Zero
                                                        targetIndex = null
                                                        // Verschieben, nicht tauschen - die
                                                        // dazwischenliegenden Fotos ruecken nach.
                                                        if (to != null && to != from) {
                                                            val keys = slots.map { it.key }.toMutableList()
                                                            keys.add(to, keys.removeAt(from))
                                                            onReorder?.invoke(keys)
                                                        }
                                                    },
                                                    onDragCancel = {
                                                        draggingIndex = null
                                                        dragOffset = Offset.Zero
                                                        targetIndex = null
                                                    },
                                                )
                                            },
                                        ),
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
private fun FilledPhotoSlot(
    slot: PhotoSlot,
    showStatus: Boolean,
    onRemove: () -> Unit,
    modifier: Modifier = Modifier,
    /** 1-basierte Position; null blendet die Nummer aus (nicht sortierbar). */
    position: Int? = null,
    isDragged: Boolean = false,
    isDropTarget: Boolean = false,
) {
    val colors = FlexrTheme.colors
    val borderColor = when {
        // Das Ziel des Zugs sticht hervor, solange der Finger darueber steht.
        isDropTarget -> colors.plate
        !showStatus || slot.status == PhotoStatus.APPROVED -> Color.Transparent
        slot.status == PhotoStatus.REJECTED -> colors.danger.copy(alpha = 0.5f)
        else -> colors.plateDim
    }

    Box(
        modifier
            .fillMaxWidth()
            .aspectRatio(3f / 4f)
            // Das gezogene Feld wird leicht angehoben, damit sichtbar ist,
            // was gerade am Finger haengt.
            .alpha(if (isDragged) 0.7f else 1f)
            .clip(RoundedCornerShape(11.dp))
            .border(if (isDropTarget) 2.dp else 1.5.dp, borderColor, RoundedCornerShape(11.dp)),
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
        // Position 1 ist das Hauptfoto (Swipe-Karte, Avatar, Chat-Kopf) - die
        // Nummer macht sichtbar, was das Verschieben bewirkt.
        if (position != null) {
            Text(
                text = position.toString(),
                style = MonoStyle.copy(
                    fontSize = androidx.compose.ui.unit.TextUnit(9f, androidx.compose.ui.unit.TextUnitType.Sp),
                ),
                color = if (position == 1) colors.plateInk else colors.chalkDim,
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .padding(4.dp)
                    .clip(RoundedCornerShape(5.dp))
                    .background(
                        if (position == 1) colors.plate else Color.Black.copy(alpha = 0.62f),
                    )
                    .padding(horizontal = 5.dp, vertical = 1.dp),
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
