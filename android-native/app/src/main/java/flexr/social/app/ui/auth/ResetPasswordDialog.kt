package flexr.social.app.ui.auth

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.DialogProperties
import flexr.social.app.R
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FlexrPasswordField
import flexr.social.app.core.designsystem.theme.FlexrTheme

/**
 * "Neues Passwort festlegen" nach dem Tipp auf den Reset-Link in der Mail
 * (seit 2.7.38, Link `https://flexr.social/app/open/?reset=...`; vorher ging
 * das nur im Browser). Länge und Wiederholung prüft der Dialog wie
 * Registrierung und Konto, alles Weitere der Server - dessen Meldung (etwa
 * "Link abgelaufen") erscheint hier über [onSave].
 */
@Composable
fun ResetPasswordDialog(
    onSave: (newPassword: String, onError: (String) -> Unit) -> Unit,
    onDismiss: () -> Unit,
) {
    var passwort by rememberSaveable { mutableStateOf("") }
    var wiederholung by rememberSaveable { mutableStateOf("") }
    var fehler by rememberSaveable { mutableStateOf<String?>(null) }
    var speichert by remember { mutableStateOf(false) }
    val zuKurz = stringResource(R.string.reset_err_short)
    val ungleich = stringResource(R.string.register_err_password_mismatch)

    fun speichern() {
        if (speichert) return
        fehler = when {
            passwort.length < 8 -> zuKurz
            passwort != wiederholung -> ungleich
            else -> null
        }
        if (fehler != null) return
        speichert = true
        onSave(passwort) { meldung ->
            speichert = false
            fehler = meldung
        }
    }

    AlertDialog(
        onDismissRequest = { if (!speichert) onDismiss() },
        // Ein Tipp neben den Dialog schliesst ihn nicht: Mit offener Tastatur
        // rueckt er nach oben, ein knapp verfehltes zweites Feld haette sonst
        // alles Eingetippte verworfen (im Emulator so passiert).
        properties = DialogProperties(dismissOnClickOutside = false),
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text(stringResource(R.string.reset_title), style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column {
                Text(
                    text = stringResource(R.string.reset_sub),
                    style = MaterialTheme.typography.bodyMedium,
                    color = FlexrTheme.colors.chalkDim,
                )
                Spacer(Modifier.height(12.dp))
                FlexrPasswordField(
                    value = passwort,
                    onValueChange = {
                        passwort = it
                        fehler = null
                    },
                    label = stringResource(R.string.reset_new_pw),
                    placeholder = stringResource(R.string.register_password_placeholder),
                    imeAction = ImeAction.Next,
                )
                Spacer(Modifier.height(12.dp))
                FlexrPasswordField(
                    value = wiederholung,
                    onValueChange = {
                        wiederholung = it
                        fehler = null
                    },
                    label = stringResource(R.string.register_password_repeat),
                    imeAction = ImeAction.Done,
                    onImeAction = { speichern() },
                )
                FieldError(fehler)
            }
        },
        confirmButton = {
            TextButton(onClick = { speichern() }, enabled = !speichert) {
                Text(stringResource(R.string.reset_save))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss, enabled = !speichert) {
                Text(stringResource(R.string.common_cancel), color = FlexrTheme.colors.chalkDim)
            }
        },
    )
}
