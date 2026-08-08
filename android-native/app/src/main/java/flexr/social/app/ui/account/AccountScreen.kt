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
import flexr.social.app.core.designsystem.component.VerifiedBlue
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
        // Der Verifiziert-Hinweis verschwindet, sobald er bestätigt wurde;
        // alle anderen Zustände sind Handlungsaufforderungen und bleiben stehen.
        if (!isVerified || !state.verifiedHintDismissed) {
            Spacer(Modifier.height(14.dp))
            VerificationHint(
                isVerified = isVerified,
                status = state.verificationStatus,
                onDismiss = viewModel::dismissVerifiedHint,
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
            text = "Ausgangspunkt ist die Adresse deines Gyms — nicht dein Wohnort und " +
                "nicht dein aktueller Standort. Im eingestellten Umkreis siehst du auch " +
                "Leute aus anderen Studios in der Nähe.",
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

        // ---------- Benachrichtigungen ----------
        Spacer(Modifier.height(28.dp))
        SectionTitle("Benachrichtigungen")
        Row(
            Modifier.fillMaxWidth().padding(top = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    "Neue Nachrichten",
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    "Benachrichtigung, wenn dir ein Match schreibt.",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
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

        // ---------- Konto ----------
        Spacer(Modifier.height(28.dp))
        SectionTitle("Konto")
        Spacer(Modifier.height(12.dp))
        FlexrSecondaryButton(text = "Ausloggen", onClick = onLogout)
        Spacer(Modifier.height(10.dp))
        FlexrDangerButton(text = "Konto löschen", onClick = viewModel::showDeleteDialog)

        // ---------- Rechtliches ----------
        Spacer(Modifier.height(28.dp))
        SectionTitle("Rechtliches")
        Column(Modifier.fillMaxWidth().padding(top = 6.dp)) {
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

        Spacer(Modifier.height(40.dp))
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
 * Der Bestätigungs-Hinweis lässt sich mit „Verstanden" dauerhaft wegklicken;
 * steht die Verifizierung noch aus, führt „Zur Verifizierung" direkt in den
 * Ablauf. Beide Aktionen sind sichtbare Schaltflächen statt einer unsichtbar
 * anklickbaren Fläche.
 */
@Composable
private fun VerificationHint(
    isVerified: Boolean,
    status: VerificationStatus,
    onDismiss: () -> Unit,
    onStartVerification: () -> Unit,
) {
    val colors = FlexrTheme.colors
    val tint = when {
        isVerified -> VerifiedBlue
        status == VerificationStatus.SUBMITTED -> colors.chalkDim
        else -> colors.plate
    }
    val label = when {
        isVerified -> "Verifiziert"
        status == VerificationStatus.SUBMITTED -> "Prüfung läuft …"
        status.needsDocument -> "Alter bestätigen"
        else -> "Verifizierung"
    }
    val description = when {
        isVerified ->
            "Dein Profil ist verifiziert — andere sehen den blauen Haken neben deinem Namen."
        status == VerificationStatus.SUBMITTED ->
            "Deine Verifizierung wird geprüft. Nach der Freigabe bekommst du den blauen Haken."
        status.needsDocument ->
            "Es fehlt noch die Aufnahme deines amtlichen Lichtbildausweises."
        status == VerificationStatus.REJECTED ->
            "Deine Verifizierung konnte nicht abgeschlossen werden. Bei Fragen: " +
                "flexr.social@proton.me"
        else ->
            "Zeig mit 3 Live-Selfies und einem Lichtbildausweis, dass du wirklich du bist — " +
                "und hol dir den blauen Haken."
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
            if (isVerified) {
                VerifiedBadge(size = 15)
                Spacer(Modifier.width(8.dp))
            } else if (status != VerificationStatus.SUBMITTED) {
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
            isVerified -> Row(
                Modifier.fillMaxWidth().padding(top = 4.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismiss) {
                    Text("Verstanden", color = tint, style = MaterialTheme.typography.labelLarge)
                }
            }

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
                    text = "Dein Konto wird sofort deaktiviert und ist für andere nicht mehr " +
                        "sichtbar. Alle Daten inklusive Fotos werden nach 30 Tagen endgültig " +
                        "und unwiderruflich gelöscht (siehe Datenschutzerklärung).",
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
