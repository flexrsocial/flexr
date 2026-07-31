package flexr.social.app.core.designsystem.theme

import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

/**
 * Zusatzfarben, die Material 3 nicht kennt, die die Marke aber braucht
 * (Kreide-Sekundärtext, Lime-Chips, Hairline-Trennlinien, Verlauf-Töne).
 */
data class FlexrExtendedColors(
    val chalk: Color,
    val chalkDim: Color,
    val hairline: Color,
    val steel: Color,
    val surface2: Color,
    val surface3: Color,
    val plate: Color,
    val plateBright: Color,
    val plateDim: Color,
    val plateGlow: Color,
    val plateInk: Color,
    val lime: Color,
    val danger: Color,
)

val LocalFlexrColors = staticCompositionLocalOf {
    FlexrExtendedColors(
        chalk = FlexrPalette.Chalk,
        chalkDim = FlexrPalette.ChalkDim,
        hairline = FlexrPalette.Hairline,
        steel = FlexrPalette.Steel,
        surface2 = FlexrPalette.Surface2,
        surface3 = FlexrPalette.Surface3,
        plate = FlexrPalette.Plate,
        plateBright = FlexrPalette.PlateBright,
        plateDim = FlexrPalette.PlateDim,
        plateGlow = FlexrPalette.PlateGlow,
        plateInk = FlexrPalette.PlateInk,
        lime = FlexrPalette.Lime,
        danger = FlexrPalette.Danger,
    )
}

/**
 * FLEXR ist bewusst durchgehend dunkel — genau wie die Web-App. Ein heller
 * Modus würde die Fotokarten und den Orange-Akzent brechen, deshalb wird
 * `isSystemInDarkTheme()` hier nicht ausgewertet, sondern nur dokumentiert.
 */
private val FlexrColorScheme = darkColorScheme(
    primary = FlexrPalette.Plate,
    onPrimary = FlexrPalette.PlateInk,
    primaryContainer = FlexrPalette.PlateDim,
    onPrimaryContainer = FlexrPalette.Chalk,
    secondary = FlexrPalette.Lime,
    onSecondary = FlexrPalette.Ink,
    secondaryContainer = FlexrPalette.Surface3,
    onSecondaryContainer = FlexrPalette.Lime,
    tertiary = FlexrPalette.PlateBright,
    onTertiary = FlexrPalette.PlateInk,
    background = FlexrPalette.Ink,
    onBackground = FlexrPalette.Chalk,
    surface = FlexrPalette.Surface,
    onSurface = FlexrPalette.Chalk,
    surfaceVariant = FlexrPalette.Surface2,
    onSurfaceVariant = FlexrPalette.ChalkDim,
    surfaceContainer = FlexrPalette.Surface2,
    surfaceContainerHigh = FlexrPalette.Surface3,
    surfaceContainerHighest = FlexrPalette.Surface3,
    outline = FlexrPalette.Steel,
    outlineVariant = FlexrPalette.Hairline,
    error = FlexrPalette.Danger,
    onError = Color.White,
    errorContainer = Color(0x1FE34848),
    onErrorContainer = FlexrPalette.Danger,
    scrim = Color(0x99000000),
)

val FlexrShapes = Shapes(
    extraSmall = RoundedCornerShape(7.dp),
    small = RoundedCornerShape(10.dp),
    medium = RoundedCornerShape(14.dp),
    large = RoundedCornerShape(20.dp),
    extraLarge = RoundedCornerShape(26.dp),
)

/**
 * Hintergrund der App-Fläche: entspricht dem mehrschichtigen Verlauf aus
 * `.app` im Web (zwei radiale Orange-Schleier über der Grundfarbe).
 */
@Composable
fun FlexrBackground(content: @Composable () -> Unit) {
    val glow = Brush.radialGradient(
        colors = listOf(Color(0x1FFF5A1F), Color.Transparent),
        center = Offset(120f, -40f),
        radius = 900f,
    )
    Box(
        Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .background(glow),
    ) { content() }
}

@Composable
fun FlexrTheme(
    @Suppress("UNUSED_PARAMETER") darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    CompositionLocalProvider(LocalFlexrColors provides LocalFlexrColors.current) {
        MaterialTheme(
            colorScheme = FlexrColorScheme,
            typography = FlexrTypography,
            shapes = FlexrShapes,
            content = content,
        )
    }
}

/** Kurzzugriff auf die Markenzusatzfarben: `FlexrTheme.colors.chalkDim`. */
object FlexrTheme {
    val colors: FlexrExtendedColors
        @Composable get() = LocalFlexrColors.current
}
