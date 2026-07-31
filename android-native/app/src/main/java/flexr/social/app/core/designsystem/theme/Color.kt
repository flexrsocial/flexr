package flexr.social.app.core.designsystem.theme

import androidx.compose.ui.graphics.Color

/**
 * Markenpalette, 1:1 übernommen aus den CSS-Custom-Properties der Web-App
 * (`:root` in frontend/index.html). Die Namen bleiben bewusst gleich, damit
 * beide Oberflächen nachweislich dieselbe Farbwelt verwenden.
 */
internal object FlexrPalette {
    val Ink = Color(0xFF121212)          // --ink
    val Surface = Color(0xFF1C1C1C)      // --surface
    val Surface2 = Color(0xFF242424)     // --surface-2
    val Surface3 = Color(0xFF2C2C2C)     // --surface-3
    val Steel = Color(0xFF3A3A3A)        // --steel
    val Hairline = Color(0x12FFFFFF)     // --hairline: rgba(255,255,255,.07)

    val Chalk = Color(0xFFEDE9E2)        // --chalk
    val ChalkDim = Color(0xFFA8A49B)     // --chalk-dim

    val Plate = Color(0xFFFF5A1F)        // --plate
    val PlateBright = Color(0xFFFF7A45)  // --plate-bright
    val PlateDim = Color(0xFFC94515)     // --plate-dim
    val PlateGlow = Color(0x59FF5A1F)    // --plate-glow: rgba(255,90,31,.35)
    val PlateInk = Color(0xFF191008)     // Schrift auf orangem Grund

    val Lime = Color(0xFFC7FF4A)         // --lime
    val Danger = Color(0xFFE34848)       // --danger

    /** Logo-Rot des Wortzeichens — bewusst getrennt vom UI-Orange (siehe brand/README). */
    val BrandRed = Color(0xFFE8412B)
}
