package flexr.social.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FlexrTextField
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.domain.model.Gym

/** Zustand des Gym-Suchfeldes. */
data class GymPickerState(
    val query: String = "",
    val results: List<Gym> = emptyList(),
    val isSearching: Boolean = false,
    val expanded: Boolean = false,
    /** Vollständiges Label des gewählten Gyms — genau dieser Wert wird gespeichert. */
    val selectedLabel: String? = null,
)

/**
 * Gym-Auswahl mit Live-Suche über die Gym-Datenbank (Name, Ort oder PLZ) und
 * Vorschlagsfunktion für fehlende Studios. Gespeichert wird immer das volle
 * Label „Name — Straße 1, 1100 Wien"; nur das erkennt das Backend als gültig.
 */
@Composable
fun GymPicker(
    state: GymPickerState,
    onQueryChange: (String) -> Unit,
    onSelect: (Gym) -> Unit,
    onSuggestRequested: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = FlexrTheme.colors

    Column(modifier.fillMaxWidth()) {
        FlexrTextField(
            value = state.query,
            onValueChange = onQueryChange,
            label = "Gym",
            placeholder = "Gym suchen (Name, Ort oder PLZ) …",
            imeAction = ImeAction.Search,
            trailingIcon = Icons.Filled.Search,
        )

        if (state.expanded) {
            Column(
                Modifier
                    .fillMaxWidth()
                    .padding(top = 6.dp)
                    .clip(MaterialTheme.shapes.medium)
                    .background(colors.surface2)
                    .border(1.dp, colors.steel, MaterialTheme.shapes.medium),
            ) {
                if (state.isSearching) {
                    Row(
                        Modifier.fillMaxWidth().padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        CircularProgressIndicator(Modifier.size(14.dp), color = colors.plate, strokeWidth = 1.5.dp)
                        Spacer(Modifier.size(10.dp))
                        Text("Suche …", style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)
                    }
                }
                LazyColumn(Modifier.heightIn(max = 260.dp)) {
                    items(state.results, key = { it.id }) { gym ->
                        GymResultRow(gym = gym, onClick = { onSelect(gym) })
                    }
                    item {
                        Row(
                            Modifier
                                .fillMaxWidth()
                                .clickable(onClick = onSuggestRequested)
                                .padding(horizontal = 14.dp, vertical = 13.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Icon(
                                Icons.Filled.Add,
                                contentDescription = null,
                                tint = colors.plate,
                                modifier = Modifier.size(16.dp),
                            )
                            Text(
                                text = "Gym nicht dabei? Jetzt vorschlagen",
                                style = MaterialTheme.typography.bodyMedium,
                                color = colors.plate,
                            )
                        }
                    }
                }
            }
        }

        state.selectedLabel?.let { label ->
            Text(
                text = label,
                style = MonoStyle,
                color = colors.lime,
                modifier = Modifier
                    .padding(top = 8.dp)
                    .clip(MaterialTheme.shapes.extraSmall)
                    .background(colors.lime.copy(alpha = 0.07f))
                    .padding(horizontal = 10.dp, vertical = 7.dp),
            )
        }
    }
}

@Composable
private fun GymResultRow(gym: Gym, onClick: () -> Unit) {
    val colors = FlexrTheme.colors
    Column(
        Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 11.dp),
    ) {
        Text(
            text = gym.name,
            style = MaterialTheme.typography.bodyMedium,
            color = colors.chalk,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        if (gym.addressLine.isNotBlank()) {
            Text(
                text = gym.addressLine,
                style = MonoStyle,
                color = colors.chalkDim,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

/** Eingaben des Vorschlagsdialogs. */
data class GymSuggestionState(
    val name: String = "",
    val street: String = "",
    val houseNumber: String = "",
    val postalCode: String = "",
    val isSubmitting: Boolean = false,
    val error: String? = null,
) {
    val isValid: Boolean
        get() = name.trim().length >= 2 &&
            street.trim().length >= 2 &&
            houseNumber.isNotBlank() &&
            Regex("^\\d{4}$").matches(postalCode)
}

/**
 * Dialog „Gym vorschlagen". Der Vorschlag ist sofort für das eigene Profil
 * verwendbar und erscheint nach Freigabe für alle in der Auswahl.
 */
@Composable
fun GymSuggestionDialog(
    state: GymSuggestionState,
    onNameChange: (String) -> Unit,
    onStreetChange: (String) -> Unit,
    onHouseNumberChange: (String) -> Unit,
    onPostalCodeChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text("Gym vorschlagen", style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column {
                Text(
                    text = "Dein Gym fehlt in der Liste? Reich es mit Adresse ein — du kannst es " +
                        "sofort für dein Profil verwenden, nach Prüfung erscheint es für alle.",
                    style = MaterialTheme.typography.bodySmall,
                    color = FlexrTheme.colors.chalkDim,
                )
                FlexrTextField(
                    value = state.name,
                    onValueChange = onNameChange,
                    label = "Name des Gyms",
                    placeholder = "z. B. Eisenschmiede",
                    maxLength = 120,
                )
                FlexrTextField(
                    value = state.street,
                    onValueChange = onStreetChange,
                    label = "Straße",
                    placeholder = "z. B. Hauptstraße",
                    maxLength = 120,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Box(Modifier.weight(1f)) {
                        FlexrTextField(
                            value = state.houseNumber,
                            onValueChange = onHouseNumberChange,
                            label = "Hausnummer",
                            placeholder = "12",
                            maxLength = 20,
                        )
                    }
                    Box(Modifier.weight(1f)) {
                        FlexrTextField(
                            value = state.postalCode,
                            onValueChange = { onPostalCodeChange(it.filter(Char::isDigit).take(4)) },
                            label = "Postleitzahl",
                            placeholder = "1010",
                            keyboardType = KeyboardType.NumberPassword,
                            imeAction = ImeAction.Done,
                        )
                    }
                }
                FieldError(state.error)
            }
        },
        confirmButton = {
            TextButton(onClick = onSubmit, enabled = state.isValid && !state.isSubmitting) {
                Text("Vorschlag einreichen", color = FlexrTheme.colors.plate)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Abbrechen", color = FlexrTheme.colors.chalkDim)
            }
        },
    )
}
