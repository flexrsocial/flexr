package flexr.social.app.core.designsystem.component

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme

/**
 * Emoji-Auswahl für Bio und Chat — dieselbe Liste und dieselbe Einfügelogik wie
 * im Web-Frontend (`initEmojiPicker` in frontend/index.html).
 *
 * Bewusst eine feste Auswahl statt einer vollständigen Unicode-Tabelle: Die
 * Systemtastatur kann ohnehin alles, das Panel ist die schnelle Abkürzung zu
 * dem, was auf einer Gym-Dating-Plattform tatsächlich gebraucht wird.
 */
object EmojiCatalog {

    val emojis: List<String> = listOf(
        // Training & Sport
        "💪", "🏋️", "🏋️‍♀️", "🤸", "🏃", "🏃‍♀️", "🚴", "🚵", "🧘", "🏊", "🥊", "🤾", "⚽",
        "🏀", "🎾", "🏐", "🏈", "⚾", "🏓", "🏸", "⛷️", "🏂", "🛹", "🧗", "🧗‍♀️", "🤼",
        "⛰️", "🥾", "🚶", "🏇", "🤺", "🎳", "🪂", "🏄", "🚣", "🤽", "🥋", "🥅",
        "🏹", "⛹️", "⛹️‍♀️", "🤹", "🕺", "💃", "🦵", "🦶", "🫀", "🫁", "🦿",
        "⏱️", "⌚", "🧢", "👟", "🩳", "🧦", "🎽", "🧊", "🩹", "🧴", "🪢", "🛼",
        // Energie & Erfolg
        "🔥", "⚡", "💥", "🎯", "🏆", "🥇", "🥈", "🥉", "💯", "✨", "🌟", "⭐",
        "🙌", "👊", "🤝", "✌️", "👏", "🤞", "💫", "🚀", "🎖️", "🏅", "📈", "🔝",
        // Stimmung & Gesichter
        "😄", "😁", "😉", "😎", "🥳", "😏", "🤓", "🙃", "😊", "😜", "🤪", "😇",
        "🫶", "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "😍", "🥰", "😘", "💕",
        "🤗", "😌", "😤", "🥵", "😅", "🤩", "🫡", "🤠",
        // Essen & Trinken
        "🍗", "🥩", "🥦", "🍳", "🥤", "☕", "🍕", "🍺", "🍔", "🌮", "🍣", "🥗",
        "🍎", "🍌", "🥑", "🍫", "🧋", "🍦", "🥞", "🍝", "🍷", "🍹", "🫐", "🥜",
        "🥛", "🧀", "🍚", "🍠", "🥕", "🫑", "🌽", "🥬", "🥒", "🍇", "🍊", "🥝",
        "🍉", "🥚", "🐟", "🍤", "🫘", "🌰", "💊", "🧂", "🥥", "🍯",
        // Lifestyle & Sonstiges
        "🎵", "🎬", "🎮", "📚", "🐶", "🐱", "🐺", "🦁", "☀️", "🌙", "🌈", "🌊",
        "✈️", "🗺️", "📍", "🎉", "🤷", "🤙", "👀", "🧠", "🛠️", "🎸", "📸", "🏝️",
        "🚗", "🏍️", "⛺", "🎿", "🃏", "🎲", "🧩", "🪩",
    ).distinct()
}

/**
 * Setzt ein Emoji an der Cursorposition ein und ersetzt dabei eine eventuelle
 * Auswahl. Überschreitet das Ergebnis `maxLength`, bleibt der Text unverändert
 * — genau wie im Web.
 */
fun TextFieldValue.withEmojiInserted(emoji: String, maxLength: Int?): TextFieldValue {
    val start = selection.min.coerceIn(0, text.length)
    val end = selection.max.coerceIn(0, text.length)
    val next = text.substring(0, start) + emoji + text.substring(end)
    if (maxLength != null && next.length > maxLength) return this
    val caret = start + emoji.length
    return TextFieldValue(text = next, selection = TextRange(caret))
}

/**
 * Aufklappbares Emoji-Raster. Die Höhe ist gedeckelt, damit das Panel in einer
 * scrollenden Spalte liegen kann, ohne den Rest der Seite zu verdrängen.
 */
@Composable
fun EmojiPickerPanel(
    expanded: Boolean,
    onPick: (String) -> Unit,
    modifier: Modifier = Modifier,
    columns: Int = 8,
    height: Int = 180,
) {
    val colors = FlexrTheme.colors
    AnimatedVisibility(
        visible = expanded,
        enter = fadeIn() + expandVertically(),
        exit = fadeOut() + shrinkVertically(),
        modifier = modifier,
    ) {
        LazyVerticalGrid(
            columns = GridCells.Fixed(columns),
            modifier = Modifier
                .fillMaxWidth()
                .height(height.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(colors.surface2)
                .border(1.dp, colors.steel, RoundedCornerShape(12.dp))
                .padding(6.dp),
        ) {
            items(EmojiCatalog.emojis) { emoji ->
                Box(
                    Modifier
                        .aspectRatio(1f)
                        .clip(RoundedCornerShape(8.dp))
                        .clickable { onPick(emoji) },
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = emoji,
                        style = TextStyle(fontSize = 19.sp),
                    )
                }
            }
        }
    }
}

/** Runder Umschalter, der das Panel auf- und zuklappt. */
@Composable
fun EmojiToggleButton(
    expanded: Boolean,
    onToggle: () -> Unit,
    modifier: Modifier = Modifier,
    size: Int = 34,
) {
    val colors = FlexrTheme.colors
    Box(
        modifier
            .size(size.dp)
            .clip(RoundedCornerShape(percent = 50))
            .background(if (expanded) colors.surface3 else Color.Transparent)
            .clickable(onClick = onToggle),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = FlexrIcons.Emoji,
            contentDescription = if (expanded) "Emoji-Auswahl schließen" else "Emoji einfügen",
            tint = if (expanded) colors.plate else colors.chalkDim,
            modifier = Modifier.size((size * 0.62).dp),
        )
    }
}
