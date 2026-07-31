package flexr.social.app.core.designsystem.component

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import flexr.social.app.core.designsystem.theme.FlexrTheme

/** Feldbeschriftung im FLEXR-Stil: klein, gesperrt, Versalien, gedämpft. */
@Composable
fun FieldLabel(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text.uppercase(),
        style = MaterialTheme.typography.bodySmall.copy(fontSize = 12.sp, letterSpacing = 0.04.em),
        color = FlexrTheme.colors.chalkDim,
        modifier = modifier.padding(top = 16.dp, bottom = 6.dp),
    )
}

/**
 * Standard-Eingabefeld der App. Die Beschriftung steht — wie im Web — über
 * dem Feld statt als schwebendes Material-Label; das hält lange deutsche
 * Beschriftungen lesbar.
 */
@Composable
fun FlexrTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    placeholder: String? = null,
    keyboardType: KeyboardType = KeyboardType.Text,
    imeAction: ImeAction = ImeAction.Next,
    singleLine: Boolean = true,
    maxLines: Int = 1,
    enabled: Boolean = true,
    isError: Boolean = false,
    supportingText: String? = null,
    trailingIcon: ImageVector? = null,
    onTrailingIconClick: (() -> Unit)? = null,
    maxLength: Int? = null,
    minHeight: Int = 0,
    onImeAction: (() -> Unit)? = null,
) {
    val colors = FlexrTheme.colors
    Column(modifier.fillMaxWidth()) {
        FieldLabel(label)
        OutlinedTextField(
            value = value,
            onValueChange = { new -> onValueChange(maxLength?.let { new.take(it) } ?: new) },
            modifier = Modifier
                .fillMaxWidth()
                .then(if (minHeight > 0) Modifier.heightIn(min = minHeight.dp) else Modifier),
            enabled = enabled,
            isError = isError,
            singleLine = singleLine,
            maxLines = maxLines,
            textStyle = MaterialTheme.typography.bodyLarge,
            placeholder = placeholder?.let {
                { Text(it, style = MaterialTheme.typography.bodyLarge, color = colors.chalkDim) }
            },
            trailingIcon = trailingIcon?.let {
                {
                    IconButton(onClick = { onTrailingIconClick?.invoke() }) {
                        Icon(it, contentDescription = null, tint = colors.chalkDim, modifier = Modifier.size(20.dp))
                    }
                }
            },
            keyboardOptions = KeyboardOptions(keyboardType = keyboardType, imeAction = imeAction),
            keyboardActions = androidx.compose.foundation.text.KeyboardActions(
                onDone = { onImeAction?.invoke() },
                onGo = { onImeAction?.invoke() },
                onSend = { onImeAction?.invoke() },
            ),
            shape = MaterialTheme.shapes.small,
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                disabledContainerColor = MaterialTheme.colorScheme.surface,
                errorContainerColor = MaterialTheme.colorScheme.surface,
                focusedBorderColor = colors.plate,
                unfocusedBorderColor = colors.steel,
                cursorColor = colors.plate,
                focusedTextColor = colors.chalk,
                unfocusedTextColor = colors.chalk,
            ),
        )
        Row(Modifier.fillMaxWidth()) {
            if (supportingText != null) {
                Text(
                    text = supportingText,
                    style = MaterialTheme.typography.bodySmall,
                    color = if (isError) colors.danger else colors.chalkDim,
                    modifier = Modifier.padding(top = 6.dp).weight(1f),
                )
            }
            if (maxLength != null) {
                Text(
                    text = "${value.length}/$maxLength",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.chalkDim,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }
    }
}

/** Passwortfeld mit Sichtbarkeitsschalter. */
@Composable
fun FlexrPasswordField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    placeholder: String? = null,
    imeAction: ImeAction = ImeAction.Done,
    isError: Boolean = false,
    supportingText: String? = null,
    onImeAction: (() -> Unit)? = null,
) {
    var visible by remember { mutableStateOf(false) }
    val colors = FlexrTheme.colors

    Column(modifier.fillMaxWidth()) {
        FieldLabel(label)
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            modifier = Modifier.fillMaxWidth(),
            isError = isError,
            singleLine = true,
            textStyle = MaterialTheme.typography.bodyLarge,
            placeholder = placeholder?.let {
                { Text(it, style = MaterialTheme.typography.bodyLarge, color = colors.chalkDim) }
            },
            visualTransformation = if (visible) VisualTransformation.None else PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = imeAction),
            keyboardActions = androidx.compose.foundation.text.KeyboardActions(
                onDone = { onImeAction?.invoke() },
                onGo = { onImeAction?.invoke() },
            ),
            trailingIcon = {
                IconButton(onClick = { visible = !visible }) {
                    Icon(
                        imageVector = if (visible) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                        contentDescription = if (visible) "Passwort verbergen" else "Passwort anzeigen",
                        tint = colors.chalkDim,
                        modifier = Modifier.size(20.dp),
                    )
                }
            },
            shape = MaterialTheme.shapes.small,
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                errorContainerColor = MaterialTheme.colorScheme.surface,
                focusedBorderColor = colors.plate,
                unfocusedBorderColor = colors.steel,
                cursorColor = colors.plate,
                focusedTextColor = colors.chalk,
                unfocusedTextColor = colors.chalk,
            ),
        )
        if (supportingText != null) {
            Text(
                text = supportingText,
                style = MaterialTheme.typography.bodySmall,
                color = if (isError) colors.danger else colors.chalkDim,
                modifier = Modifier.padding(top = 6.dp),
            )
        }
    }
}

/** Fehlerzeile unter einer Eingabegruppe (`.field-err`). */
@Composable
fun FieldError(message: String?, modifier: Modifier = Modifier) {
    if (message.isNullOrBlank()) return
    Text(
        text = message,
        style = MaterialTheme.typography.bodySmall,
        color = FlexrTheme.colors.danger,
        modifier = modifier.fillMaxWidth().padding(top = 8.dp),
    )
}
