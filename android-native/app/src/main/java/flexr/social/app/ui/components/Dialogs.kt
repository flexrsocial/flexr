package flexr.social.app.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.text.input.ImeAction
import flexr.social.app.core.designsystem.component.FlexrTextField
import flexr.social.app.core.designsystem.theme.FlexrTheme

/** Bestätigungsdialog für Aktionen mit Folgen (Blockieren, Löschen, Auflösen). */
@Composable
fun ConfirmDialog(
    title: String,
    text: String,
    confirmLabel: String,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
    destructive: Boolean = true,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text(title, style = MaterialTheme.typography.headlineSmall) },
        text = {
            Text(text, style = MaterialTheme.typography.bodyMedium, color = FlexrTheme.colors.chalkDim)
        },
        confirmButton = {
            TextButton(onClick = onConfirm) {
                Text(
                    confirmLabel,
                    color = if (destructive) FlexrTheme.colors.danger else FlexrTheme.colors.plate,
                )
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Abbrechen", color = FlexrTheme.colors.chalkDim)
            }
        },
    )
}

/**
 * Meldedialog mit Freitextbegründung. Im Web war das ein `prompt()` des
 * Browsers — nativ ein richtiger Dialog mit Längenprüfung (3–500 Zeichen,
 * wie das Backend sie erwartet).
 */
@Composable
fun ReportDialog(
    userName: String,
    onSubmit: (String) -> Unit,
    onDismiss: () -> Unit,
) {
    var reason by remember { mutableStateOf("") }
    val isValid = reason.trim().length >= 3

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text("$userName melden", style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column {
                Text(
                    text = "Was ist vorgefallen? Deine Meldung wird von uns geprüft.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = FlexrTheme.colors.chalkDim,
                )
                FlexrTextField(
                    value = reason,
                    onValueChange = { reason = it },
                    label = "Grund",
                    placeholder = "Kurze Beschreibung",
                    singleLine = false,
                    maxLines = 4,
                    minHeight = 84,
                    maxLength = 500,
                    imeAction = ImeAction.Done,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = { onSubmit(reason.trim()) }, enabled = isValid) {
                Text("Melden", color = if (isValid) FlexrTheme.colors.danger else FlexrTheme.colors.chalkDim)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Abbrechen", color = FlexrTheme.colors.chalkDim)
            }
        },
    )
}
