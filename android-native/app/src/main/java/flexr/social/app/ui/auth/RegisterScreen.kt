package flexr.social.app.ui.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withLink
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FieldLabel
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrPasswordField
import flexr.social.app.core.designsystem.component.FlexrTextField
import flexr.social.app.core.designsystem.component.ScreenHeader
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.domain.model.Gender
import flexr.social.app.ui.components.GymPicker
import flexr.social.app.ui.components.GymSuggestionDialog
import flexr.social.app.ui.components.PhotoGridEditor
import flexr.social.app.ui.components.PhotoSlot
import flexr.social.app.ui.components.PostalCodeField
import flexr.social.app.ui.navigation.LegalDocument
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset

@Composable
fun RegisterScreen(
    onRegistered: (String?) -> Unit,
    onGoToLogin: () -> Unit,
    onOpenLegal: (LegalDocument) -> Unit,
    viewModel: RegisterViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val keyboard = LocalSoftwareKeyboardController.current
    var showDatePicker by remember { mutableStateOf(false) }

    LaunchedEffect(state.success) {
        if (state.success) onRegistered(state.successNotice)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .imePadding()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp),
    ) {
        Spacer(Modifier.height(8.dp))
        AuthTabs(selected = AuthTab.REGISTER, onSelect = { if (it == AuthTab.LOGIN) onGoToLogin() })

        Spacer(Modifier.height(24.dp))
        ScreenHeader(
            eyebrow = "Erste Wiederholung",
            title = "Dating für Leute,\ndie auch montags\nBeintag machen.",
            subtitle = "Erstell dein Profil. 1 Monat gratis testen, danach 5 €/Monat. " +
                "Jederzeit kündbar. Aktuell nur in Österreich verfügbar.",
        )

        FlexrTextField(
            value = state.email,
            onValueChange = viewModel::onEmailChange,
            label = "E-Mail",
            placeholder = "max@example.com",
            keyboardType = KeyboardType.Email,
        )
        FlexrPasswordField(
            value = state.password,
            onValueChange = viewModel::onPasswordChange,
            label = "Passwort",
            placeholder = "Mind. 8 Zeichen",
            imeAction = ImeAction.Next,
        )
        FlexrTextField(
            value = state.name,
            onValueChange = viewModel::onNameChange,
            label = "Name",
            placeholder = "Max",
            maxLength = 100,
        )

        BirthdateField(
            birthdate = state.birthdate,
            age = state.age,
            onClick = {
                keyboard?.hide()
                showDatePicker = true
            },
        )

        PostalCodeField(
            postalCode = state.postalCode,
            lookupState = state.plzLookup,
            onPostalCodeChange = viewModel::onPostalCodeChange,
        )

        GenderSelector(selected = state.gender, onSelect = viewModel::onGenderChange)

        GymPicker(
            state = state.gymPicker,
            onQueryChange = viewModel::onGymQueryChange,
            onSelect = viewModel::onGymSelected,
            onSuggestRequested = viewModel::openGymSuggestion,
        )

        FlexrTextField(
            value = state.bio,
            onValueChange = viewModel::onBioChange,
            label = "Bio",
            placeholder = "Was du suchst, dein Training, gerne mit Emojis 💪",
            singleLine = false,
            maxLines = 5,
            minHeight = 96,
            maxLength = RegisterUiState.BIO_MAX_LENGTH,
            imeAction = ImeAction.Default,
        )

        FieldLabel("Fotos (mind. 1, max. 6)")
        PhotoGridEditor(
            slots = state.photos.map { PhotoSlot(key = it.id, model = it.previewUri) },
            onPhotoPicked = viewModel::onPhotoPicked,
            onRemove = viewModel::onPhotoRemoved,
        )
        if (state.isPreparingPhoto) {
            Row(
                Modifier.fillMaxWidth().padding(top = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CircularProgressIndicator(Modifier.size(14.dp), color = FlexrTheme.colors.plate, strokeWidth = 1.5.dp)
                Spacer(Modifier.size(8.dp))
                Text(
                    "Foto wird vorbereitet …",
                    style = MaterialTheme.typography.bodySmall,
                    color = FlexrTheme.colors.chalkDim,
                )
            }
        }
        FieldError(state.photoError)

        Spacer(Modifier.height(20.dp))
        ConsentCheckbox(
            checked = state.consentSensitiveData,
            onCheckedChange = viewModel::onConsentSensitiveDataChange,
            prefix = "Ich willige ein, dass meine Angaben zu Geschlecht und gesuchtem Geschlecht " +
                "(daraus ableitbar: sexuelle Orientierung) gemäß ",
            linkText = "Datenschutzerklärung",
            suffix = " verarbeitet werden.",
            onLinkClick = { onOpenLegal(LegalDocument.DATENSCHUTZ) },
        )
        ConsentCheckbox(
            checked = state.consentWithdrawalWaiver,
            onCheckedChange = viewModel::onConsentWithdrawalWaiverChange,
            prefix = "Ich stimme zu, dass der Zugang sofort mit Registrierung beginnt, und nehme zur " +
                "Kenntnis, dass ich dadurch mein 14-tägiges Rücktrittsrecht verliere (siehe ",
            linkText = "AGB",
            suffix = ", §18 FAGG).",
            onLinkClick = { onOpenLegal(LegalDocument.AGB) },
        )

        FieldError(state.error)

        Spacer(Modifier.height(22.dp))
        FlexrButton(
            text = "Profil erstellen & Probemonat starten",
            onClick = {
                keyboard?.hide()
                viewModel.register()
            },
            enabled = state.canSubmit,
            loading = state.isSubmitting,
        )
        Spacer(Modifier.height(40.dp))
    }

    if (showDatePicker) {
        BirthdatePickerDialog(
            initial = state.birthdate,
            onConfirm = {
                viewModel.onBirthdateChange(it)
                showDatePicker = false
            },
            onDismiss = { showDatePicker = false },
        )
    }

    state.gymSuggestion?.let { suggestion ->
        GymSuggestionDialog(
            state = suggestion,
            onNameChange = { value -> viewModel.onGymSuggestionChange { it.copy(name = value) } },
            onStreetChange = { value -> viewModel.onGymSuggestionChange { it.copy(street = value) } },
            onHouseNumberChange = { value -> viewModel.onGymSuggestionChange { it.copy(houseNumber = value) } },
            onPostalCodeChange = { value -> viewModel.onGymSuggestionChange { it.copy(postalCode = value) } },
            onSubmit = viewModel::submitGymSuggestion,
            onDismiss = viewModel::closeGymSuggestion,
        )
    }
}

/** Geburtsdatum: nicht tippen, sondern auswählen — der native Kalenderdialog. */
@Composable
private fun BirthdateField(birthdate: LocalDate?, age: Int?, onClick: () -> Unit) {
    val colors = FlexrTheme.colors
    Column(Modifier.fillMaxWidth()) {
        FieldLabel("Geburtsdatum")
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surface, MaterialTheme.shapes.small)
                .border(1.dp, colors.steel, MaterialTheme.shapes.small)
                .clickable(onClick = onClick)
                .padding(horizontal = 14.dp, vertical = 15.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(
                text = birthdate?.let(ServerTime::formatBirthdate) ?: "tt.mm.jjjj",
                style = MaterialTheme.typography.bodyLarge,
                color = if (birthdate != null) colors.chalk else colors.chalkDim,
            )
            if (age != null) {
                Text("$age Jahre", style = MaterialTheme.typography.bodyMedium, color = colors.chalkDim)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BirthdatePickerDialog(
    initial: LocalDate?,
    onConfirm: (LocalDate) -> Unit,
    onDismiss: () -> Unit,
) {
    val today = LocalDate.now()
    val latestAllowed = today.minusYears(RegisterUiState.MIN_AGE.toLong())
    val earliestAllowed = today.minusYears(RegisterUiState.MAX_AGE.toLong())

    val pickerState = rememberDatePickerState(
        initialSelectedDateMillis = (initial ?: latestAllowed)
            .atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli(),
        // Nur volljährige Geburtsdaten sind wählbar — das Backend prüft ebenso.
        selectableDates = object : androidx.compose.material3.SelectableDates {
            override fun isSelectableYear(year: Int) =
                year in earliestAllowed.year..latestAllowed.year

            override fun isSelectableDate(utcTimeMillis: Long): Boolean {
                val date = Instant.ofEpochMilli(utcTimeMillis).atZone(ZoneOffset.UTC).toLocalDate()
                return !date.isAfter(latestAllowed) && !date.isBefore(earliestAllowed)
            }
        },
    )

    DatePickerDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(
                onClick = {
                    pickerState.selectedDateMillis?.let { millis ->
                        onConfirm(Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).toLocalDate())
                    }
                },
            ) { Text("Übernehmen", color = FlexrTheme.colors.plate) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Abbrechen", color = FlexrTheme.colors.chalkDim)
            }
        },
    ) {
        DatePicker(state = pickerState, title = { Text("Geburtsdatum", Modifier.padding(24.dp)) })
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun GenderSelector(selected: Gender?, onSelect: (Gender) -> Unit) {
    val colors = FlexrTheme.colors
    Column(Modifier.fillMaxWidth()) {
        FieldLabel("Geschlecht")
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            Gender.entries.forEachIndexed { index, gender ->
                SegmentedButton(
                    selected = selected == gender,
                    onClick = { onSelect(gender) },
                    shape = SegmentedButtonDefaults.itemShape(index, Gender.entries.size),
                    colors = SegmentedButtonDefaults.colors(
                        activeContainerColor = colors.plate.copy(alpha = 0.16f),
                        activeContentColor = colors.plate,
                        activeBorderColor = colors.plate,
                        inactiveContainerColor = MaterialTheme.colorScheme.surface,
                        inactiveContentColor = colors.chalkDim,
                        inactiveBorderColor = colors.steel,
                    ),
                ) {
                    Text(gender.label, style = MaterialTheme.typography.bodyLarge)
                }
            }
        }
    }
}

/** Einwilligung mit eingebettetem Link auf den jeweiligen Rechtstext. */
@Composable
private fun ConsentCheckbox(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    prefix: String,
    linkText: String,
    suffix: String,
    onLinkClick: () -> Unit,
) {
    val colors = FlexrTheme.colors
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
        verticalAlignment = Alignment.Top,
    ) {
        Checkbox(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = CheckboxDefaults.colors(
                checkedColor = colors.plate,
                checkmarkColor = colors.plateInk,
                uncheckedColor = colors.steel,
            ),
        )
        Box(Modifier.padding(top = 12.dp)) {
            Text(
                text = buildAnnotatedString {
                    append(prefix)
                    withLink(
                        LinkAnnotation.Clickable(
                            tag = linkText,
                            styles = TextLinkStyles(
                                style = SpanStyle(
                                    color = colors.plate,
                                    textDecoration = TextDecoration.Underline,
                                ),
                            ),
                            linkInteractionListener = { onLinkClick() },
                        ),
                    ) { append(linkText) }
                    append(suffix)
                },
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
            )
        }
    }
}
