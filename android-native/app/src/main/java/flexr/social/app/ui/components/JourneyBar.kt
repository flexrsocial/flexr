package flexr.social.app.ui.components

import androidx.annotation.StringRes
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import flexr.social.app.R
import flexr.social.app.core.designsystem.theme.FlexrTheme

/**
 * Der Weg bis zum ersten Swipe - dieselben fuenf Abschnitte wie in der
 * Web-App (renderJourney in frontend/app/index.html).
 *
 * Vorher zeigte die Registrierung gar keinen Fortschritt und die Pruefschirme
 * drei unbeschriftete Striche; wie viel nach dem Formular noch kommt, erfuhr
 * man erst unterwegs.
 */
enum class JourneyStep(@StringRes val label: Int) {
    PROFILE(R.string.journey_profile),
    MAIL(R.string.journey_mail),
    SELFIE(R.string.journey_selfie),
    ID(R.string.journey_id),
    REVIEW(R.string.journey_review),
}

/**
 * @param progress nur fuer den aktiven Abschnitt: fuellt ihn anteilig
 *   (Registrierungsformular). Ohne Wert ist der aktive Abschnitt ganz hell.
 * @param note Zeile darunter, schon uebersetzt.
 */
@Composable
fun JourneyBar(
    current: JourneyStep,
    modifier: Modifier = Modifier,
    progress: Float? = null,
    note: String? = null,
) {
    val colors = FlexrTheme.colors
    val steps = JourneyStep.entries
    val beschreibung = stringResource(R.string.journey_a11y, current.ordinal + 1, steps.size)
    val anteil by animateFloatAsState(progress ?: 1f, label = "journeyProgress")
    Column(modifier.fillMaxWidth().semantics { contentDescription = beschreibung }) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            steps.forEach { step ->
                val erledigt = step.ordinal < current.ordinal
                val aktiv = step == current
                Column(Modifier.weight(1f)) {
                    Box(
                        Modifier
                            .fillMaxWidth()
                            .height(4.dp)
                            .clip(RoundedCornerShape(2.dp))
                            .background(colors.steel),
                    ) {
                        val fuellung = when {
                            erledigt -> 1f
                            aktiv -> anteil
                            else -> 0f
                        }
                        if (fuellung > 0f) {
                            Box(
                                Modifier
                                    .fillMaxHeight()
                                    .fillMaxWidth(fuellung)
                                    .background(if (aktiv && progress == null) colors.chalk else colors.plate),
                            )
                        }
                    }
                    Spacer(Modifier.height(6.dp))
                    Text(
                        text = stringResource(step.label).uppercase(),
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp, letterSpacing = 0.8.sp),
                        color = when {
                            erledigt -> colors.plate
                            aktiv -> colors.chalk
                            else -> colors.chalkDim
                        },
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
        }
        if (note != null) {
            Spacer(Modifier.height(8.dp))
            Text(note, style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)
        }
    }
}
