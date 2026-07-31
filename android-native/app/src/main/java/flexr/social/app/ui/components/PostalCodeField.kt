package flexr.social.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import flexr.social.app.core.designsystem.component.FieldLabel
import flexr.social.app.core.designsystem.theme.FlexrTheme

/** Ergebnis der Ortsermittlung zu einer Postleitzahl. */
sealed interface PlzLookupState {
    data object Idle : PlzLookupState
    data object Loading : PlzLookupState
    data class Resolved(val city: String) : PlzLookupState
    data class Failed(val message: String) : PlzLookupState
}

/**
 * Kombiniertes PLZ-/Ortsfeld: links vier Ziffern, rechts der automatisch
 * ermittelte Gemeindename. Es gibt bewusst keine Städteauswahl — die PLZ
 * bestimmt den Ort, damit ganz Österreich abgedeckt ist.
 */
@Composable
fun PostalCodeField(
    postalCode: String,
    lookupState: PlzLookupState,
    onPostalCodeChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    label: String = "Postleitzahl",
    imeAction: ImeAction = ImeAction.Next,
) {
    val colors = FlexrTheme.colors
    val interactionSource = remember { MutableInteractionSource() }
    val focused by interactionSource.collectIsFocusedAsState()

    Column(modifier.fillMaxWidth()) {
        FieldLabel(label)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(MaterialTheme.shapes.small)
                .background(MaterialTheme.colorScheme.surface)
                .border(
                    width = if (focused) 2.dp else 1.dp,
                    color = if (focused) colors.plate else colors.steel,
                    shape = MaterialTheme.shapes.small,
                )
                .padding(horizontal = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            BasicTextField(
                value = postalCode,
                onValueChange = { input -> onPostalCodeChange(input.filter(Char::isDigit).take(4)) },
                modifier = Modifier.width(56.dp).padding(vertical = 14.dp),
                textStyle = MaterialTheme.typography.bodyLarge.copy(color = colors.chalk),
                cursorBrush = SolidColor(colors.plate),
                singleLine = true,
                interactionSource = interactionSource,
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.NumberPassword,
                    imeAction = imeAction,
                ),
                decorationBox = { inner ->
                    if (postalCode.isEmpty()) {
                        Text(
                            "1010",
                            style = MaterialTheme.typography.bodyLarge,
                            color = colors.chalkDim,
                        )
                    }
                    inner()
                },
            )
            Box(
                Modifier
                    .padding(start = 8.dp)
                    .width(1.dp)
                    .height(22.dp)
                    .background(colors.steel),
            )
            Spacer(Modifier.width(10.dp))
            when (lookupState) {
                PlzLookupState.Idle -> PlzHint("— PLZ eingeben —", resolved = false)
                PlzLookupState.Loading -> Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(
                        Modifier.size(13.dp),
                        color = colors.plate,
                        strokeWidth = 1.5.dp,
                    )
                    Spacer(Modifier.width(8.dp))
                    PlzHint("Lädt …", resolved = false)
                }
                is PlzLookupState.Resolved -> PlzHint(lookupState.city, resolved = true)
                is PlzLookupState.Failed -> PlzHint("— unbekannte PLZ —", resolved = false)
            }
        }
        if (lookupState is PlzLookupState.Failed) {
            Text(
                text = lookupState.message,
                style = MaterialTheme.typography.bodySmall,
                color = colors.danger,
                modifier = Modifier.padding(top = 6.dp),
            )
        }
    }
}

@Composable
private fun PlzHint(text: String, resolved: Boolean) {
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        color = if (resolved) FlexrTheme.colors.chalk else FlexrTheme.colors.chalkDim,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis,
    )
}
