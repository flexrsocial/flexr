package flexr.social.app.core.designsystem.icon

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Block
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.EmojiEmotions
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.HeartBroken
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.OutlinedFlag
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Place
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.unit.dp

/**
 * Marken-Symbol: die FLEXR-Hantel — dieselbe Geometrie wie das Launcher-Icon,
 * abgeleitet aus dem im Play Store hinterlegten Icon (zwei schmale äußere
 * Scheiben, zwei breite innere, durchgehender Steg). Als [ImageVector] ist es
 * überall scharf und lässt sich wie jedes Material-Icon einfärben.
 *
 * In der Oberfläche etwas leichter gestrichen als auf dem Launcher-Icon, damit
 * es bei 22dp in der Navigation nicht zuläuft.
 */
val FlexrDumbbell: ImageVector by lazy {
    ImageVector.Builder(
        name = "FlexrDumbbell",
        defaultWidth = 24.dp,
        defaultHeight = 24.dp,
        viewportWidth = 24f,
        viewportHeight = 24f,
    ).apply {
        val stroke = SolidColor(Color.White)
        fun bar(x: Float, top: Float, bottom: Float, width: Float) {
            path(
                stroke = stroke,
                strokeLineWidth = width,
                strokeLineCap = StrokeCap.Round,
                strokeLineJoin = StrokeJoin.Round,
            ) {
                moveTo(x, top)
                lineTo(x, bottom)
            }
        }
        bar(4.2f, 7.2f, 16.8f, 1.9f)    // äußere Scheibe links
        bar(8.2f, 4.6f, 19.4f, 2.6f)    // innere Scheibe links
        bar(15.8f, 4.6f, 19.4f, 2.6f)   // innere Scheibe rechts
        bar(19.8f, 7.2f, 16.8f, 1.9f)   // äußere Scheibe rechts
        path(
            stroke = stroke,
            strokeLineWidth = 2f,
            strokeLineCap = StrokeCap.Round,
        ) {
            moveTo(3.4f, 12f)
            lineTo(20.6f, 12f)
        }
    }.build()
}

/**
 * Symbolsatz der App an einer Stelle gebündelt. Wo Material Design bereits ein
 * passendes, den Nutzern vertrautes Symbol liefert, wird es verwendet — das ist
 * auf Android die richtige Wahl gegenüber nachgebauten Web-Icons.
 */
object FlexrIcons {
    val Swipe = FlexrDumbbell
    val Gym = FlexrDumbbell
    val Matches = Icons.Filled.Favorite
    val Chats = Icons.Filled.Chat
    val Account = Icons.Filled.Person
    val Like = Icons.Filled.Favorite
    val Pass = Icons.Filled.Close
    val Unmatch = Icons.Filled.HeartBroken
    val Report = Icons.Filled.OutlinedFlag
    val Block = Icons.Filled.Block
    val Back = Icons.AutoMirrored.Filled.ArrowBack
    val Send = Icons.AutoMirrored.Filled.Send
    val More = Icons.Filled.MoreVert
    val Camera = Icons.Filled.CameraAlt
    val Locked = Icons.Filled.Lock
    val Place = Icons.Filled.Place
    val Close = Icons.Filled.Close
    val Emoji = Icons.Filled.EmojiEmotions
}

/** Merkt sich das Hantel-Icon über Rekompositionen hinweg. */
@Composable
fun rememberDumbbellIcon(): ImageVector = remember { FlexrDumbbell }
