package flexr.social.app.core.designsystem.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import flexr.social.app.R

/**
 * Schriftfamilien der Marke. Es sind dieselben drei Schnitte wie im Web
 * (Oswald für Überschriften, Work Sans für Fließtext, JetBrains Mono für
 * technische Labels) — hier als mitgelieferte Variable Fonts statt als
 * Google-Fonts-Webrequest, damit die App offline und ohne Netzabhängigkeit
 * korrekt aussieht.
 */
@OptIn(ExperimentalTextApi::class)
private fun variableFont(resId: Int, weight: FontWeight) = Font(
    resId = resId,
    weight = weight,
    variationSettings = FontVariation.Settings(FontVariation.weight(weight.weight)),
)

val Oswald = FontFamily(
    variableFont(R.font.oswald_variable, FontWeight.Medium),
    variableFont(R.font.oswald_variable, FontWeight.SemiBold),
    variableFont(R.font.oswald_variable, FontWeight.Bold),
)

val WorkSans = FontFamily(
    variableFont(R.font.work_sans_variable, FontWeight.Normal),
    variableFont(R.font.work_sans_variable, FontWeight.Medium),
    variableFont(R.font.work_sans_variable, FontWeight.SemiBold),
)

val JetBrainsMono = FontFamily(
    variableFont(R.font.jetbrains_mono_variable, FontWeight.Medium),
    variableFont(R.font.jetbrains_mono_variable, FontWeight.Bold),
)

/**
 * Display-/Headline-Stile entsprechen den `h1,h2,h3,.display`-Regeln der
 * Web-App: Oswald, Versalien, leichte Sperrung.
 */
val FlexrTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = Oswald,
        fontWeight = FontWeight.Bold,
        fontSize = 40.sp,
        lineHeight = 44.sp,
        letterSpacing = 0.02.em,
    ),
    displayMedium = TextStyle(
        fontFamily = Oswald,
        fontWeight = FontWeight.Bold,
        fontSize = 30.sp,
        lineHeight = 33.sp,
        letterSpacing = 0.02.em,
    ),
    headlineLarge = TextStyle(
        fontFamily = Oswald,
        fontWeight = FontWeight.SemiBold,
        fontSize = 26.sp,
        lineHeight = 30.sp,
        letterSpacing = 0.02.em,
    ),
    headlineMedium = TextStyle(
        fontFamily = Oswald,
        fontWeight = FontWeight.SemiBold,
        fontSize = 22.sp,
        lineHeight = 26.sp,
        letterSpacing = 0.02.em,
    ),
    headlineSmall = TextStyle(
        fontFamily = Oswald,
        fontWeight = FontWeight.SemiBold,
        fontSize = 17.sp,
        lineHeight = 21.sp,
        letterSpacing = 0.04.em,
    ),
    titleLarge = TextStyle(
        fontFamily = Oswald,
        fontWeight = FontWeight.Medium,
        fontSize = 20.sp,
        lineHeight = 25.sp,
    ),
    titleMedium = TextStyle(
        fontFamily = Oswald,
        fontWeight = FontWeight.Medium,
        fontSize = 16.sp,
        lineHeight = 21.sp,
        letterSpacing = 0.01.em,
    ),
    titleSmall = TextStyle(
        fontFamily = WorkSans,
        fontWeight = FontWeight.SemiBold,
        fontSize = 14.sp,
        lineHeight = 19.sp,
    ),
    bodyLarge = TextStyle(
        fontFamily = WorkSans,
        fontWeight = FontWeight.Normal,
        fontSize = 15.sp,
        lineHeight = 22.sp,
    ),
    bodyMedium = TextStyle(
        fontFamily = WorkSans,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 21.sp,
    ),
    bodySmall = TextStyle(
        fontFamily = WorkSans,
        fontWeight = FontWeight.Normal,
        fontSize = 13.sp,
        lineHeight = 20.sp,
    ),
    labelLarge = TextStyle(
        fontFamily = Oswald,
        fontWeight = FontWeight.SemiBold,
        fontSize = 15.sp,
        lineHeight = 18.sp,
        letterSpacing = 0.06.em,
    ),
    labelMedium = TextStyle(
        fontFamily = JetBrainsMono,
        fontWeight = FontWeight.Medium,
        fontSize = 11.sp,
        lineHeight = 14.sp,
        letterSpacing = 0.06.em,
    ),
    labelSmall = TextStyle(
        fontFamily = JetBrainsMono,
        fontWeight = FontWeight.Medium,
        fontSize = 10.sp,
        lineHeight = 13.sp,
        letterSpacing = 0.08.em,
    ),
)

/** `.eyebrow` aus dem Web: Mono, gesperrt, Versalien, Akzentfarbe. */
val EyebrowStyle = TextStyle(
    fontFamily = JetBrainsMono,
    fontWeight = FontWeight.Medium,
    fontSize = 11.sp,
    lineHeight = 14.sp,
    letterSpacing = 0.12.em,
)

/** `.mono` — technische Werte (Entfernung, Radius, Zeitstempel). */
val MonoStyle = TextStyle(
    fontFamily = JetBrainsMono,
    fontWeight = FontWeight.Medium,
    fontSize = 11.sp,
    lineHeight = 15.sp,
    letterSpacing = 0.02.em,
)

/** Wortmarke im Header: leicht verbreitert, wie `.brand` im Web. */
val BrandStyle = TextStyle(
    fontFamily = Oswald,
    fontWeight = FontWeight.Bold,
    fontSize = 22.sp,
    letterSpacing = 0.06.em,
)
