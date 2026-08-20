package flexr.social.app.ui.account

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FieldLabel
import flexr.social.app.core.designsystem.component.FlexrDangerButton
import flexr.social.app.core.designsystem.component.FlexrLinkButton
import flexr.social.app.core.designsystem.component.FlexrPasswordField
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.component.FlexrTextField
import flexr.social.app.core.designsystem.component.SectionTitle
import flexr.social.app.core.designsystem.component.VerifiedBadge
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.ui.components.GymPicker
import flexr.social.app.ui.components.GymSuggestionDialog
import flexr.social.app.ui.components.PhotoGridEditor
import flexr.social.app.ui.components.PhotoSlot
import flexr.social.app.ui.components.PhotoVisibilityHint
import flexr.social.app.ui.components.PostalCodeField
import flexr.social.app.ui.navigation.LegalDocument

@Composable
fun AccountScreen(
    onLogout: () -> Unit,
    onOpenVerification: () -> Unit,
    onOpenDocumentStep: () -> Unit,
    onOpenLegal: (LegalDocument) -> Unit,
    onOpenUrl: (String) -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: AccountViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val profile by viewModel.profile.collectAsStateWithLifecycle()
    val membership by viewModel.membership.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is AccountEvent.Message -> onShowMessage(event.text)
                is AccountEvent.OpenUrl -> onOpenUrl(event.url)
                AccountEvent.LoggedOut -> onLogout()
                AccountEvent.StartVerification -> onOpenVerification()
                AccountEvent.ContinueWithDocument -> onOpenDocumentStep()
            }
        }
    }

    val colors = FlexrTheme.colors
    val currentProfile = profile
    val context = LocalContext.current
    var legalDialogVisible by remember { mutableStateOf(false) }
    val notificationPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (!granted) {
            viewModel.setNotificationsEnabled(false)
            onShowMessage("Ohne Berechtigung können keine Benachrichtigungen angezeigt werden.")
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
    ) {
        Spacer(Modifier.height(18.dp))

        // ---------- Kopf: Avatar, Name, Verifizierung ----------
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
            Box(
                Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(colors.surface2)
                    .border(2.dp, colors.plateDim, CircleShape),
                contentAlignment = Alignment.Center,
            ) {
                val avatar = currentProfile?.photos?.firstOrNull()?.avatarUrl
                if (avatar != null) {
                    AsyncImage(
                        model = avatar,
                        contentDescription = "Dein Profilfoto",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize().clip(CircleShape),
                    )
                } else {
                    Text(
                        text = currentProfile?.name?.take(1)?.uppercase() ?: "?",
                        style = MaterialTheme.typography.headlineMedium,
                        color = colors.chalkDim,
                    )
                }
            }
            Spacer(Modifier.width(14.dp))
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = currentProfile?.let { "${it.name}, ${it.profile.age}" } ?: "—",
                        style = MaterialTheme.typography.titleLarge,
                        color = colors.chalk,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    if (currentProfile?.profile?.isVerified == true) {
                        Spacer(Modifier.width(6.dp))
                        VerifiedBadge()
                    }
                }
                Text(
                    text = listOfNotNull(
                        currentProfile?.profile?.city,
                        currentProfile?.profile?.gymName?.takeIf { it.isNotBlank() },
                    ).joinToString(" · "),
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }

        val isVerified = currentProfile?.profile?.isVerified == true ||
            state.verificationStatus == VerificationStatus.APPROVED
        // Der blaue Haken im Profilkopf reicht als positives Feedback. Das
        // Hinweisfeld bleibt nur sichtbar, solange tatsächlich etwas zu tun ist.
        if (!isVerified) {
            Spacer(Modifier.height(14.dp))
            VerificationHint(
                status = state.verificationStatus,
                onStartVerification = viewModel::startVerification,
            )
        }

        // ---------- Mitgliedschaft ----------
        Spacer(Modifier.height(18.dp))
        membership?.let { status ->
            Column(
                Modifier
                    .fillMaxWidth()
                    .clip(MaterialTheme.shapes.medium)
                    .background(MaterialTheme.colorScheme.surface)
                    .border(1.dp, colors.hairline, MaterialTheme.shapes.medium)
                    .padding(14.dp),
            ) {
                Text(
                    text = if (status.isSubscribed) {
                        "Dein Abo ist aktiv (5 €/Monat)."
                    } else {
                        "Noch ${ServerTime.daysUntil(status.trialEndsAt)} Tag(e) gratis Probemonat."
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.chalk,
                )
                if (status.isSubscribed) {
                    FlexrLinkButton(
                        text = "Abo verwalten / kündigen",
                        onClick = viewModel::openBillingPortal,
                    )
                } else {
                    FlexrLinkButton(text = "Jetzt abonnieren", onClick = viewModel::startCheckout)
                }
            }
        }

        // ---------- Profil ----------
        Spacer(Modifier.height(26.dp))
        SectionTitle("Profil")

        PostalCodeField(
            postalCode = state.postalCode,
            lookupState = state.plzLookup,
            onPostalCodeChange = viewModel::onPostalCodeChange,
        )

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
            maxLength = AccountViewModel.BIO_MAX_LENGTH,
            imeAction = ImeAction.Default,
            emojiPicker = true,
        )

        FieldLabel("Suchumkreis")
        Row(verticalAlignment = Alignment.CenterVertically) {
            Slider(
                value = state.searchRadiusKm.toFloat(),
                onValueChange = { viewModel.onSearchRadiusChange(it.toInt()) },
                valueRange = AccountViewModel.MIN_RADIUS_KM.toFloat()..AccountViewModel.MAX_RADIUS_KM.toFloat(),
                modifier = Modifier.weight(1f),
                colors = SliderDefaults.colors(
                    thumbColor = colors.plate,
                    activeTrackColor = colors.plate,
                    inactiveTrackColor = colors.steel,
                ),
            )
            Spacer(Modifier.width(12.dp))
            Text("${state.searchRadiusKm} km", style = MonoStyle, color = colors.chalk)
        }
        Text(
            text = "Radius rund um dein Gym. Dein Gerätestandort wird nicht verwendet.",
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )

        FieldError(state.saveError)
        Spacer(Modifier.height(16.dp))
        FlexrSecondaryButton(
            text = "Profil speichern",
            onClick = viewModel::saveProfile,
            loading = state.isSaving,
        )

        // ---------- Fotos ----------
        Spacer(Modifier.height(28.dp))
        SectionTitle("Fotos")
        Spacer(Modifier.height(8.dp))
        PhotoGridEditor(
            slots = currentProfile?.photos?.map {
                PhotoSlot(key = it.id, model = it.url, status = it.status)
            }.orEmpty(),
            onPhotoPicked = viewModel::onPhotoPicked,
            onRemove = viewModel::onPhotoRemoved,
            showStatus = true,
        )
        if (state.isUploadingPhoto) {
            Row(
                Modifier.fillMaxWidth().padding(top = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CircularProgressIndicator(Modifier.size(14.dp), color = colors.plate, strokeWidth = 1.5.dp)
                Spacer(Modifier.width(8.dp))
                Text(
                    "Foto wird hochgeladen …",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
        }
        PhotoVisibilityHint(photoStatuses = currentProfile?.photos?.map { it.status }.orEmpty())
        FieldError(state.photoError)

        // ---------- Einstellungen ----------
        Spacer(Modifier.height(28.dp))
        SectionTitle("Einstellungen")
        Row(
            Modifier.fillMaxWidth().padding(top = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    "Nachrichten erhalten",
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
            }
            Switch(
                checked = state.notificationsEnabled,
                onCheckedChange = { enabled ->
                    // Ab Android 13 braucht das Anzeigen von Benachrichtigungen
                    // eine Laufzeitberechtigung — hier im Moment des Einschaltens
                    // erfragt, wo der Zweck offensichtlich ist.
                    if (enabled &&
                        Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                        ContextCompat.checkSelfPermission(
                            context,
                            Manifest.permission.POST_NOTIFICATIONS,
                        ) != PackageManager.PERMISSION_GRANTED
                    ) {
                        notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                    }
                    viewModel.setNotificationsEnabled(enabled)
                },
                colors = SwitchDefaults.colors(
                    checkedThumbColor = colors.plateInk,
                    checkedTrackColor = colors.plate,
                    uncheckedTrackColor = colors.surface3,
                    uncheckedBorderColor = colors.steel,
                ),
            )
        }

        Row(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .clickable { legalDialogVisible = true }
                .padding(vertical = 15.dp, horizontal = 2.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    "Hilfe & Rechtliches",
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    "FAQ, Sicherheit, Datenschutz und Bedingungen",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
            Icon(
                Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = null,
                tint = colors.chalkDim,
                modifier = Modifier.size(18.dp),
            )
        }

        // ---------- Konto ----------
        Spacer(Modifier.height(28.dp))
        SectionTitle("Konto")
        Spacer(Modifier.height(12.dp))
        FlexrSecondaryButton(text = "Ausloggen", onClick = onLogout)
        Spacer(Modifier.height(10.dp))
        FlexrDangerButton(text = "Konto löschen", onClick = viewModel::showDeleteDialog)

        Spacer(Modifier.height(40.dp))
    }

    if (legalDialogVisible) {
        LegalAndHelpDialog(
            onOpenLegal = { document ->
                legalDialogVisible = false
                onOpenLegal(document)
            },
            onDismiss = { legalDialogVisible = false },
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

    if (state.deleteDialogVisible) {
        DeleteAccountDialog(
            password = state.deletePassword,
            error = state.deleteError,
            isDeleting = state.isDeleting,
            onPasswordChange = viewModel::onDeletePasswordChange,
            onConfirm = viewModel::confirmDelete,
            onDismiss = viewModel::hideDeleteDialog,
        )
    }
}

/**
 * Hinweisfeld zum Verifizierungsstand.
 *
 * Solange die Verifizierung offen ist, führt die sichtbare Aktion direkt in
 * den passenden Schritt. Nach erfolgreicher Prüfung reicht der blaue Haken im
 * Profilkopf und das Feld entfällt.
 */
@Composable
private fun VerificationHint(
    status: VerificationStatus,
    onStartVerification: () -> Unit,
) {
    val colors = FlexrTheme.colors
    val tint = if (status == VerificationStatus.SUBMITTED) colors.chalkDim else colors.plate
    val label = when {
        status == VerificationStatus.SUBMITTED -> "Prüfung läuft …"
        status.needsDocument -> "Alter bestätigen"
        else -> "Verifizierung"
    }
    val description = when {
        status == VerificationStatus.SUBMITTED ->
            "Wir prüfen deine Angaben."
        status.needsDocument ->
            "Selfie erledigt. Jetzt noch den Ausweis aufnehmen."
        status == VerificationStatus.REJECTED ->
            "Nicht abgeschlossen. Hilfe bekommst du unter flexr.social@proton.me."
        else ->
            "Einmalig Selfie und Lichtbildausweis prüfen lassen."
    }

    Column(
        Modifier
            .fillMaxWidth()
            .clip(MaterialTheme.shapes.medium)
            .background(tint.copy(alpha = 0.07f))
            .border(1.dp, tint.copy(alpha = 0.35f), MaterialTheme.shapes.medium)
            .padding(14.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (status != VerificationStatus.SUBMITTED) {
                Icon(
                    Icons.Filled.Warning,
                    contentDescription = null,
                    tint = tint,
                    modifier = Modifier.size(15.dp),
                )
                Spacer(Modifier.width(8.dp))
            }
            Text(label, style = MaterialTheme.typography.titleSmall, color = tint)
        }
        Spacer(Modifier.height(6.dp))
        Text(description, style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)

        when {
            // Kein Startknopf, wenn nichts zu starten ist: in Prüfung oder
            // endgültig abgelehnt.
            status != VerificationStatus.SUBMITTED &&
                status != VerificationStatus.REJECTED -> Row(
                Modifier.fillMaxWidth().padding(top = 4.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onStartVerification) {
                    Text(
                        text = if (status.needsDocument) "Ausweis aufnehmen" else "Zur Verifizierung",
                        color = tint,
                        style = MaterialTheme.typography.labelLarge,
                    )
                }
            }
        }
    }
}

/**
 * Die lange Liste der Rechtstexte liegt hinter einem einzigen verständlichen
 * Einstieg. So bleibt die Profilseite ruhig, ohne notwendige Links zu verlieren.
 */
@Composable
private fun LegalAndHelpDialog(
    onOpenLegal: (LegalDocument) -> Unit,
    onDismiss: () -> Unit,
) {
    val colors = FlexrTheme.colors
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text("Hilfe & Rechtliches", style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column(
                Modifier
                    .fillMaxWidth()
                    .heightIn(max = 480.dp)
                    .verticalScroll(rememberScrollState()),
            ) {
                LegalDocument.entries.forEach { document ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .clickable { onOpenLegal(document) }
                            .padding(vertical = 13.dp, horizontal = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = document.title,
                            style = MaterialTheme.typography.bodyLarge,
                            color = colors.chalk,
                            modifier = Modifier.weight(1f),
                        )
                        Icon(
                            Icons.AutoMirrored.Filled.KeyboardArrowRight,
                            contentDescription = null,
                            tint = colors.chalkDim,
                            modifier = Modifier.size(18.dp),
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Schließen", color = colors.plate)
            }
        },
    )
}

/**
 * Auch von der Paywall aus erreichbar - nach Ablauf des Probemonats ist der
 * Konto-Screen nicht mehr navigierbar, die Selbstloeschung muss aber
 * erreichbar bleiben (Punkt 5 der Datenschutzerklaerung). Deshalb internal
 * statt private.
 */
@Composable
internal fun DeleteAccountDialog(
    password: String,
    error: String?,
    isDeleting: Boolean,
    onPasswordChange: (String) -> Unit,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text("Konto löschen", style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column {
                Text(
                    text = "Dein Konto wird sofort deaktiviert. Deine Daten und Fotos werden " +
                        "nach 30 Tagen endgültig gelöscht.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = FlexrTheme.colors.chalkDim,
                )
                FlexrPasswordField(
                    value = password,
                    onValueChange = onPasswordChange,
                    label = "Zur Bestätigung dein Passwort",
                    placeholder = "••••••••",
                    isError = error != null,
                    supportingText = error,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onConfirm, enabled = !isDeleting) {
                Text("Endgültig löschen", color = FlexrTheme.colors.danger)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Abbrechen", color = FlexrTheme.colors.chalkDim)
            }
        },
    )
}
