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
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
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
import flexr.social.app.data.remote.dto.ConsentDto
import flexr.social.app.domain.model.BlockedUser
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.ui.components.GymPicker
import flexr.social.app.ui.components.GymSuggestionDialog
import flexr.social.app.data.remote.dto.NotificationSettingsRequestDto
import flexr.social.app.domain.model.NotificationSettings
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
    var notificationDialogVisible by remember { mutableStateOf(false) }
    var pendingSensitiveRevoke by remember { mutableStateOf(false) }
    var consentsExpanded by remember { mutableStateOf(false) }
    var blockedUsersExpanded by remember { mutableStateOf(false) }
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
                    FlexrLinkButton(text = "Jetzt abonnieren", onClick = viewModel::openCheckoutDialog)
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
            // Langer Druck auf ein Foto sortiert es um; Position 1 ist das
            // Hauptfoto (Swipe-Karte, Avatar, Chat-Kopf).
            onReorder = viewModel::onPhotosReordered,
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
                .clickable { notificationDialogVisible = true }
                .padding(vertical = 15.dp, horizontal = 2.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    "Benachrichtigungen",
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    "Matches, neue Profile und Erinnerungen",
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
                    "Sicherheit, Datenschutz und Bedingungen",
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

        // ---------- Datenschutz & Sicherheit ----------
        // Der Widerruf einer Einwilligung (Art. 7 Abs. 3 DSGVO) darf nicht
        // schwerer sein als die Erteilung - die war ebenfalls ein Klick bei der
        // Registrierung. Bislang ging das nur über die Web-App, das gleicht
        // diese Lücke nativ an. Gleiche Zeilen-Optik wie "Hilfe & Rechtliches"
        // darüber - nur klappt der Pfeil hier die Liste direkt auf, statt einen
        // Dialog zu öffnen.
        Row(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .clickable { consentsExpanded = !consentsExpanded }
                .padding(vertical = 15.dp, horizontal = 2.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    "Datenschutz & Sicherheit",
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    "Einwilligungen einsehen und widerrufen",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
            Icon(
                Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = null,
                tint = colors.chalkDim,
                modifier = Modifier
                    .size(18.dp)
                    .rotate(if (consentsExpanded) 90f else 0f),
            )
        }
        if (consentsExpanded) {
            ConsentSection(
                consents = state.consents,
                loading = state.consentsLoading,
                error = state.consentError,
                revokingType = state.revokingConsentType,
                grantingType = state.grantingConsentType,
                onRevoke = { consentType ->
                    if (consentType == "sensitive_data") {
                        pendingSensitiveRevoke = true
                    } else {
                        viewModel.revokeConsent(consentType)
                    }
                },
                onGrant = viewModel::grantConsent,
            )
        }

        // ---------- Blockierte Personen ----------
        // Blockieren war bis hierher eine Einbahnstraße: das Backend kann eine
        // Blockierung längst zurücknehmen (DELETE /api/blocks/{id}), nur zeigte
        // kein Client das an. Entspricht der Web-Fassung unter "Datenschutz &
        // Sicherheit" (frontend/app/index.html, "loadMyBlocks").
        Row(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .clickable { blockedUsersExpanded = !blockedUsersExpanded }
                .padding(vertical = 15.dp, horizontal = 2.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    "Blockierte Personen",
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    "Blockierungen verwalten und aufheben",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
            Icon(
                Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = null,
                tint = colors.chalkDim,
                modifier = Modifier
                    .size(18.dp)
                    .rotate(if (blockedUsersExpanded) 90f else 0f),
            )
        }
        if (blockedUsersExpanded) {
            BlockedUsersSection(
                blockedUsers = state.blockedUsers,
                loading = state.blockedUsersLoading,
                error = state.blockedUsersError,
                unblockingUserId = state.unblockingUserId,
                onUnblock = viewModel::unblockUser,
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

    if (notificationDialogVisible) {
        NotificationSettingsDialog(
            settings = currentProfile?.notifications ?: NotificationSettings(),
            saving = state.isSavingNotifications,
            onChange = viewModel::updateNotificationSetting,
            onDismiss = { notificationDialogVisible = false },
        )
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

    if (pendingSensitiveRevoke) {
        AlertDialog(
            onDismissRequest = { pendingSensitiveRevoke = false },
            containerColor = MaterialTheme.colorScheme.surface,
            title = { Text("Einwilligung widerrufen?", style = MaterialTheme.typography.headlineSmall) },
            text = {
                Text(
                    text = "Geschlecht und gesuchtes Geschlecht sind die Grundlage des " +
                        "Matchings.\n\nOhne diese Einwilligung schlagen wir dir keine Profile " +
                        "mehr vor und du erscheinst in keinem Deck. Dein Konto bleibt bestehen." +
                        "\n\nWillst du ganz weg, lösche stattdessen dein Konto.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = FlexrTheme.colors.chalkDim,
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    pendingSensitiveRevoke = false
                    viewModel.revokeConsent("sensitive_data")
                }) {
                    Text("Widerruf erklären", color = FlexrTheme.colors.danger)
                }
            },
            dismissButton = {
                TextButton(onClick = { pendingSensitiveRevoke = false }) {
                    Text("Abbrechen", color = FlexrTheme.colors.chalkDim)
                }
            },
        )
    }

    if (state.checkoutDialogVisible) {
        CheckoutDialog(
            immediateStartChecked = state.checkoutImmediateStart,
            withdrawalAckChecked = state.checkoutWithdrawalAck,
            error = state.checkoutError,
            isStarting = state.isStartingCheckout,
            onImmediateStartChange = viewModel::onCheckoutImmediateStartChange,
            onWithdrawalAckChange = viewModel::onCheckoutWithdrawalAckChange,
            onConfirm = viewModel::confirmCheckout,
            onDismiss = viewModel::closeCheckoutDialog,
        )
    }
}

/**
 * Zwei getrennte, nicht vorangekreuzte Erklärungen vor jedem Wechsel zu
 * Stripe (§ 10 und § 18 Abs. 1 Z 1 FAGG) - ohne beide sendet das Backend
 * `422 field required` zurück (`backend/app/schemas.py:CheckoutRequest`).
 * Wortlaut identisch mit der Web-App (`frontend/app/index.html`,
 * `immediateStartOverlay`). Nicht `private`: `PaywallScreen` nutzt denselben
 * Dialog für denselben Checkout-Weg (siehe `DeleteAccountDialog` darunter).
 */
@Composable
internal fun CheckoutDialog(
    immediateStartChecked: Boolean,
    withdrawalAckChecked: Boolean,
    error: String?,
    isStarting: Boolean,
    onImmediateStartChange: (Boolean) -> Unit,
    onWithdrawalAckChange: (Boolean) -> Unit,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    val colors = FlexrTheme.colors
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text("Vor der Zahlung", style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                CheckoutConsentRow(
                    checked = immediateStartChecked,
                    onCheckedChange = onImmediateStartChange,
                    text = "Ich stimme ausdrücklich zu, dass FLEXR bereits vor Ablauf der " +
                        "14-tägigen Rücktrittsfrist mit der Erbringung der kostenpflichtigen " +
                        "Dienstleistung beginnt.",
                )
                CheckoutConsentRow(
                    checked = withdrawalAckChecked,
                    onCheckedChange = onWithdrawalAckChange,
                    text = "Ich bestätige, dass ich zur Kenntnis genommen habe, dass mein " +
                        "Rücktrittsrecht nach vollständiger Vertragserfüllung durch FLEXR " +
                        "erlischt, wenn die gesetzlichen Voraussetzungen dafür erfüllt sind.",
                )
                FieldError(error)
            }
        },
        confirmButton = {
            TextButton(onClick = onConfirm, enabled = !isStarting) {
                Text("Weiter zur Zahlung", color = colors.plate)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss, enabled = !isStarting) {
                Text("Abbrechen", color = colors.chalkDim)
            }
        },
    )
}

/** Eine der beiden Checkout-Erklärungen - gleiches Muster wie `ConsentCheckbox` in RegisterScreen.kt. */
@Composable
private fun CheckoutConsentRow(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    text: String,
) {
    val colors = FlexrTheme.colors
    Row(
        Modifier
            .fillMaxWidth()
            .clickable { onCheckedChange(!checked) }
            .padding(vertical = 6.dp),
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
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = colors.chalk,
            modifier = Modifier.padding(top = 12.dp, end = 4.dp),
        )
    }
}

/**
 * Liste der DSGVO-Einwilligungen mit Sofort-Widerruf (Art. 7 Abs. 3 DSGVO) -
 * angehakt wurde mit einem Klick, also geht auch der Widerruf mit einem Klick.
 * Texte und Rechtsgrundlagen sind bewusst identisch mit der Web-App gehalten
 * (`frontend/app/index.html`, `CONSENT_TEXT`/`CONSENT_GRUNDLAGE`).
 */
@Composable
private fun ConsentSection(
    consents: List<ConsentDto>,
    loading: Boolean,
    error: String?,
    revokingType: String?,
    grantingType: String?,
    onRevoke: (String) -> Unit,
    onGrant: (String) -> Unit,
) {
    val colors = FlexrTheme.colors
    val busy = revokingType != null || grantingType != null
    // "Sofortiger Leistungsbeginn" gehört gar nicht erst in diese Liste: nicht
    // widerrufbar (siehe CONSENT_REVOCABLE unten) und stand hier trotzdem als
    // eigener Eintrag samt "— widerrufen"-Zeile, obwohl der Klick daneben
    // ohnehin nichts ausgelöst hätte.
    //
    // Der Server liefert die volle Historie (neueste zuerst) - fuer den
    // Nachweis nach Art. 7 Abs. 1 DSGVO noetig, bleibt also in der DB.
    // Angezeigt wird pro Art aber nur die neueste Zeile: eine wachsende Liste
    // aus "widerrufen"/"erteilt"-Karten derselben Sache (z. B. Geschlecht)
    // las sich wie ein Protokoll statt wie eine Einstellung.
    val sichtbareConsents = remember(consents) {
        val gesehen = mutableSetOf<String>()
        consents
            .filterNot { it.consentType == "immediate_start" }
            .filter { gesehen.add(it.consentType) }
    }
    when {
        loading && sichtbareConsents.isEmpty() -> Row(verticalAlignment = Alignment.CenterVertically) {
            CircularProgressIndicator(Modifier.size(14.dp), color = colors.plate, strokeWidth = 1.5.dp)
            Spacer(Modifier.width(8.dp))
            Text("Lade …", style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)
        }
        sichtbareConsents.isEmpty() && error == null -> Text(
            "Keine Einträge.",
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )
        else -> Column {
            sichtbareConsents.forEachIndexed { index, consent ->
                Column(Modifier.fillMaxWidth().padding(vertical = 10.dp)) {
                    val label = CONSENT_LABELS[consent.consentType] ?: consent.consentType
                    // EIN Text statt Row(Text, Text): "— widerrufen" als Row-
                    // Geschwister neben einem langen Label (z. B. "Verarbeitung
                    // von Geschlecht und gesuchtem Geschlecht") bekam kaum noch
                    // Restbreite, weil Row seine Kinder ohne weight() nicht
                    // umbricht - der Suffix landete dadurch einzeln Buchstabe
                    // für Buchstabe untereinander am rechten Rand. Ein
                    // AnnotatedString wickelt als EIN Absatz normal um.
                    Text(
                        buildAnnotatedString {
                            append(label)
                            if (!consent.active) {
                                withStyle(SpanStyle(color = colors.chalkDim)) {
                                    append("  — widerrufen")
                                }
                            }
                        },
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalk,
                    )
                    val datum = ServerTime
                        .parse(if (consent.active) consent.grantedAt else consent.revokedAt)
                        ?.let(ServerTime::formatDay)
                    val details = buildString {
                        if (consent.active) {
                            append("Erteilt am ${datum ?: "—"}, Fassung ${consent.version}.")
                        } else {
                            append("Widerrufen am ${datum ?: "—"}.")
                        }
                        CONSENT_GRUNDLAGE[consent.consentType]?.let { append(" $it") }
                    }
                    Text(
                        details,
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.chalkDim,
                        modifier = Modifier.padding(top = 2.dp),
                    )
                    if (consent.consentType in CONSENT_REVOCABLE) {
                        if (consent.active) {
                            FlexrLinkButton(
                                text = "Einwilligung widerrufen",
                                onClick = { onRevoke(consent.consentType) },
                                enabled = !busy,
                            )
                        } else {
                            FlexrLinkButton(
                                text = "Einwilligung erneut erteilen",
                                onClick = { onGrant(consent.consentType) },
                                enabled = !busy,
                            )
                        }
                    }
                }
                if (index != sichtbareConsents.lastIndex) {
                    HorizontalDivider(color = colors.hairline)
                }
            }
        }
    }
    FieldError(error)
}

/**
 * Verwaltungsliste blockierter Personen mit Aufheben-Knopf. Entspricht der
 * Web-Fassung (`frontend/app/index.html`, "loadMyBlocks"/"unblockUser").
 * Bewusst nur Name, Alter, Vorschaubild und Blockierdatum — kein Bio/Gym/
 * Entfernung, siehe `backend/app/schemas.py::BlockedUserOut`.
 */
@Composable
private fun BlockedUsersSection(
    blockedUsers: List<BlockedUser>,
    loading: Boolean,
    error: String?,
    unblockingUserId: String?,
    onUnblock: (String) -> Unit,
) {
    val colors = FlexrTheme.colors
    when {
        loading && blockedUsers.isEmpty() -> Row(verticalAlignment = Alignment.CenterVertically) {
            CircularProgressIndicator(Modifier.size(14.dp), color = colors.plate, strokeWidth = 1.5.dp)
            Spacer(Modifier.width(8.dp))
            Text("Lade …", style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)
        }
        blockedUsers.isEmpty() && error == null -> Text(
            "Du hast niemanden blockiert. Blockieren geht über das Verbots-Symbol in "
                + "jedem Profil und in jedem Chat.",
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )
        else -> Column {
            blockedUsers.forEachIndexed { index, user ->
                Row(
                    Modifier.fillMaxWidth().padding(vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    AsyncImage(
                        model = user.photoUrl,
                        contentDescription = "Profilfoto von ${user.name}",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier
                            .size(44.dp)
                            .clip(CircleShape)
                            .background(colors.surface2),
                    )
                    Column(Modifier.weight(1f)) {
                        Text(
                            text = user.name + (user.age?.let { ", $it" } ?: ""),
                            style = MaterialTheme.typography.bodyMedium,
                            color = colors.chalk,
                        )
                        val seit = user.blockedAt?.let(ServerTime::formatDay)
                        Text(
                            text = "Blockiert" + (seit?.let { " · seit $it" } ?: ""),
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.chalkDim,
                        )
                    }
                    FlexrLinkButton(
                        text = "Aufheben",
                        onClick = { onUnblock(user.userId) },
                        enabled = unblockingUserId == null,
                    )
                }
                if (index != blockedUsers.lastIndex) {
                    HorizontalDivider(color = colors.hairline)
                }
            }
            // Blockieren löst ein Match nicht auf, es blendet es nur aus - nach
            // dem Aufheben sind Match und Chatverlauf wieder da (dieselbe
            // Klarstellung wie in der Web-Fassung, siehe HANDOFF.md 23.08.).
            Text(
                "Eine Blockierung blendet ein bestehendes Match nur aus, sie löst es nicht "
                    + "auf. Hebst du sie auf, seht ihr einander wieder im Deck — und ein "
                    + "früheres Match ist samt Chatverlauf wieder da.",
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
                modifier = Modifier.padding(top = 8.dp),
            )
        }
    }
    FieldError(error)
}

private val CONSENT_LABELS = mapOf(
    "sensitive_data" to "Verarbeitung von Geschlecht und gesuchtem Geschlecht",
    "verification_media" to "Aufnahmen für die Alters- und Identitätsprüfung",
    "terms" to "Angenommene AGB-Fassung",
)

private val CONSENT_GRUNDLAGE = mapOf(
    "sensitive_data" to "Ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a DSGVO.",
    "verification_media" to "Ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a DSGVO.",
    "terms" to "Vertragsschluss, keine Einwilligung — daher nicht widerrufbar.",
)

// "Sofortiger Leistungsbeginn" erscheint hier gar nicht erst (siehe
// sichtbareConsents oben in ConsentSection): die massgebliche § 10/§ 18
// Abs. 1 Z 1 FAGG-Erklaerung liegt unveraenderlich im CheckoutConsent-
// Datensatz und wirkt fort, solange der Vertrag laeuft - ein Widerruf hier
// haette nichts bewirkt, zeigte aber einen Eintrag samt Knopf, der das
// Gegenteil suggerierte.
private val CONSENT_REVOCABLE = setOf("sensitive_data", "verification_media")

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
/**
 * Untermenü "Benachrichtigungen" - drei Anlässe, je getrennt für E-Mail und App.
 *
 * Als Dialog und nicht als weiterer Block im Konto: sechs Schalter, die im
 * Alltag niemand anfasst, hätten Profil und Fotos nach unten gedrückt.
 *
 * Die Schalter stehen unter dem App-weiten "Nachrichten erhalten" im Konto -
 * ist das aus, zeigt die App gar nichts an, unabhängig von dieser Auswahl.
 */
@Composable
private fun NotificationSettingsDialog(
    settings: NotificationSettings,
    saving: Boolean,
    onChange: (NotificationSettingsRequestDto) -> Unit,
    onDismiss: () -> Unit,
) {
    val colors = FlexrTheme.colors
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = MaterialTheme.colorScheme.surface,
        title = { Text("Benachrichtigungen", style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column(
                Modifier
                    .fillMaxWidth()
                    .heightIn(max = 480.dp)
                    .verticalScroll(rememberScrollState()),
            ) {
                NotificationGroupTitle("Neues Match")
                NotificationSwitchRow(
                    label = "E-Mail",
                    hint = "Wenn jemand dich zurückgeliked hat.",
                    checked = settings.matchEmail,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyMatchEmail = it)) }
                NotificationSwitchRow(
                    label = "App-Benachrichtigung",
                    hint = null,
                    checked = settings.matchPush,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyMatchPush = it)) }

                NotificationGroupTitle("Neue Profile im Umkreis")
                NotificationSwitchRow(
                    label = "E-Mail",
                    hint = "Ab drei wartenden Profilen, höchstens einmal am Tag.",
                    checked = settings.queueEmail,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyQueueEmail = it)) }
                NotificationSwitchRow(
                    label = "App-Benachrichtigung",
                    hint = null,
                    checked = settings.queuePush,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyQueuePush = it)) }

                NotificationGroupTitle("Erinnerung bei Inaktivität")
                NotificationSwitchRow(
                    label = "E-Mail",
                    hint = "Wenn du sieben Tage nicht in FLEXR warst.",
                    checked = settings.inactiveEmail,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyInactiveEmail = it)) }
                NotificationSwitchRow(
                    label = "App-Benachrichtigung",
                    hint = null,
                    checked = settings.inactivePush,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyInactivePush = it)) }

                Spacer(Modifier.height(14.dp))
                Text(
                    "Rechtlich nötige Nachrichten — etwa zu Abo, Rücktritt oder " +
                        "Moderationsentscheidungen — lassen sich hier nicht abschalten.",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Schließen", color = colors.plate)
            }
        },
    )
}

@Composable
private fun NotificationGroupTitle(text: String) {
    Spacer(Modifier.height(14.dp))
    Text(
        text = text,
        style = MaterialTheme.typography.labelMedium,
        color = FlexrTheme.colors.chalkDim,
    )
}

@Composable
private fun NotificationSwitchRow(
    label: String,
    hint: String?,
    checked: Boolean,
    enabled: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    val colors = FlexrTheme.colors
    Row(
        Modifier.fillMaxWidth().padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.bodyLarge, color = colors.chalk)
            if (hint != null) {
                Text(hint, style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)
            }
        }
        Switch(
            checked = checked,
            enabled = enabled,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = colors.plateInk,
                checkedTrackColor = colors.plate,
                uncheckedTrackColor = colors.surface3,
                uncheckedBorderColor = colors.steel,
            ),
        )
    }
}

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
                        "nach 30 Tagen endgültig gelöscht. Du bekommst dazu eine Bestätigungsmail. " +
                        "Innerhalb der 30 Tage kannst du dich mit deinem bisherigen Passwort " +
                        "erneut einloggen, um die Löschung rückgängig zu machen.",
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
