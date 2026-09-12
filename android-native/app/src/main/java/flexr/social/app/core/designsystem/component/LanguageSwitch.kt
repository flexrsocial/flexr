package flexr.social.app.core.designsystem.component

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import flexr.social.app.R
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.locale.AppLanguage

private val SEGMENT_WIDTH = 40.dp
private val SEGMENT_HEIGHT = 26.dp

/**
 * Zwei Segmente mit gleitendem Knopf — dieselbe Optik wie der Sprachregler der
 * Web-App (`.lang-switch` in frontend/app/index.html).
 *
 * Er steht an zwei Stellen: in der Kopfzeile des ausgeloggten Graphen, wo ihn
 * ein noch nicht angemeldeter Nutzer sofort sieht, und im Kontobereich unter
 * „Profil", wo man Einstellungen sucht. Angemeldet ist er nur noch dort — in
 * der Kopfzeile steht dann der Mitgliedschafts-Status.
 */
@Composable
fun LanguageSwitch(
    language: AppLanguage,
    onSelect: (AppLanguage) -> Unit,
    modifier: Modifier = Modifier,
) {
    val knobOffset by animateDpAsState(
        targetValue = if (language == AppLanguage.ENGLISH) SEGMENT_WIDTH else 0.dp,
        label = "SprachreglerKnopf",
    )
    val label = stringResource(R.string.lang_switch_label)
    Box(
        modifier
            .semantics { contentDescription = label }
            .clip(RoundedCornerShape(percent = 50))
            .background(FlexrTheme.colors.surface2)
            .border(1.dp, FlexrTheme.colors.steel, RoundedCornerShape(percent = 50))
            .padding(2.dp),
    ) {
        Box(
            Modifier
                .offset(x = knobOffset)
                .width(SEGMENT_WIDTH)
                .height(SEGMENT_HEIGHT)
                .clip(RoundedCornerShape(percent = 50))
                .background(FlexrTheme.colors.plate),
        )
        Row {
            AppLanguage.entries.forEach { entry ->
                val selected = entry == language
                Box(
                    modifier = Modifier
                        .width(SEGMENT_WIDTH)
                        .height(SEGMENT_HEIGHT)
                        .clip(RoundedCornerShape(percent = 50))
                        .clickable(role = Role.Tab) { onSelect(entry) },
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = entry.code.uppercase(),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = if (selected) FlexrTheme.colors.plateInk else FlexrTheme.colors.chalkDim,
                    )
                }
            }
        }
    }
}

@Preview
@Composable
private fun LanguageSwitchPreview() {
    FlexrTheme {
        Box(Modifier.padding(16.dp)) {
            LanguageSwitch(language = AppLanguage.GERMAN, onSelect = {})
        }
    }
}
