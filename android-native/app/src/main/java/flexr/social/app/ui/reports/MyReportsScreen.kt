package flexr.social.app.ui.reports

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.designsystem.component.EmptyState
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.domain.model.MyReport
import flexr.social.app.domain.model.ReportOutcome

/**
 * „Meine Meldungen" — der Stand jeder abgegebenen Meldung.
 *
 * Art. 16 Abs. 5 DSA verlangt, dass der Melder die Entscheidung über seine
 * Meldung erfährt. Eine stille Bearbeitung reicht dafür nicht: Hier steht zu
 * jeder Meldung das Aktenzeichen, ob sie noch läuft und, sobald entschieden
 * wurde, die Begründung im Wortlaut.
 */
@Composable
fun MyReportsScreen(
    onBack: () -> Unit,
    viewModel: MyReportsViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = FlexrTheme.colors

    Column(Modifier.fillMaxSize().navigationBarsPadding().padding(horizontal = 20.dp)) {
        Row(
            Modifier.fillMaxWidth().padding(vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack, modifier = Modifier.size(36.dp)) {
                Icon(FlexrIcons.Back, contentDescription = "Zurück", tint = colors.chalk)
            }
            Spacer(Modifier.width(6.dp))
            Text(
                text = "Meine Meldungen",
                style = MaterialTheme.typography.headlineSmall,
                color = colors.chalk,
            )
        }

        when {
            state.isLoading -> LoadingState()

            state.error != null -> EmptyState(
                icon = FlexrIcons.Report,
                title = "Konnte nicht geladen werden",
                description = state.error.orEmpty(),
            )

            state.reports.isEmpty() -> EmptyState(
                icon = FlexrIcons.Report,
                title = "Keine Meldungen",
                description = "Hier siehst du, was aus deinen Meldungen geworden ist — " +
                    "sobald du eine abgegeben hast.",
            )

            else -> LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = PaddingValues(top = 6.dp, bottom = 24.dp),
            ) {
                items(state.reports, key = { it.reference }) { report ->
                    ReportCard(report)
                }
            }
        }
    }
}

@Composable
private fun ReportCard(report: MyReport) {
    val colors = FlexrTheme.colors
    Column(
        Modifier
            .fillMaxWidth()
            .clip(MaterialTheme.shapes.medium)
            .background(colors.surface2)
            .border(1.dp, colors.hairline, MaterialTheme.shapes.medium)
            .padding(horizontal = 14.dp, vertical = 12.dp),
    ) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = report.reference,
                style = MonoStyle,
                color = colors.plate,
                modifier = Modifier.weight(1f),
            )
            StatusPill(report.outcome)
        }
        report.createdAt?.let {
            Spacer(Modifier.height(3.dp))
            Text(
                text = "Gemeldet am ${ServerTime.formatDateTime(it)}",
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
            )
        }

        Spacer(Modifier.height(9.dp))
        Text(
            text = report.reason,
            style = MaterialTheme.typography.bodyMedium,
            color = colors.chalk,
        )

        if (report.outcome == ReportOutcome.OPEN) {
            Spacer(Modifier.height(9.dp))
            Text(
                text = "Wir prüfen deine Meldung innerhalb von 72 Stunden — bei Gefahr " +
                    "für eine Person sofort.",
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
            )
        } else if (!report.decisionNote.isNullOrBlank()) {
            Spacer(Modifier.height(9.dp))
            Text(
                text = "Unsere Entscheidung",
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(2.dp))
            Text(
                text = report.decisionNote,
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalk,
            )
            report.decidedAt?.let {
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Entschieden am ${ServerTime.formatDateTime(it)}. Bist du damit " +
                        "nicht einverstanden, schreib uns an flexr.social@proton.me.",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
        }
    }
}

@Composable
private fun StatusPill(outcome: ReportOutcome) {
    val colors = FlexrTheme.colors
    val (label, tint) = when (outcome) {
        ReportOutcome.OPEN -> "in Prüfung" to colors.chalkDim
        ReportOutcome.NO_ACTION -> "kein Verstoß" to colors.chalkDim
        ReportOutcome.ACTION_TAKEN -> "eingeschritten" to colors.plate
    }
    Text(
        text = label,
        style = MaterialTheme.typography.bodySmall,
        color = tint,
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .border(1.dp, colors.hairline, RoundedCornerShape(20.dp))
            .padding(horizontal = 9.dp, vertical = 3.dp),
    )
}
