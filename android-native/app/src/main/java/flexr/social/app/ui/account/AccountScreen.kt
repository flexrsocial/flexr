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
import androidx.compose.ui.res.stringResource
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
import flexr.social.app.R
import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FieldLabel
import flexr.social.app.core.designsystem.component.FlexrDangerButton
import flexr.social.app.core.designsystem.component.FlexrLinkButton
import flexr.social.app.core.designsystem.component.FlexrPasswordField
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.component.FlexrTextField
import flexr.social.app.core.designsystem.component.LanguageSwitch
import flexr.social.app.core.designsystem.component.SectionTitle
import flexr.social.app.core.designsystem.component.VerifiedBadge
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.core.locale.AppLanguageViewModel
import flexr.social.app.core.locale.LocalAppLanguage
import flexr.social.app.data.remote.dto.ConsentDto
import flexr.social.app.data.remote.dto.NotificationSettingsRequestDto
import flexr.social.app.domain.model.BlockedUser
import flexr.social.app.domain.model.NotificationSettings
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
    // Sprachwahl: derselbe Activity-weite ViewModel wie in der Kopfzeile.
    val languageViewModel: AppLanguageViewModel = hiltViewModel()
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
            onShowMessage(context.getString(R.string.account_notification_permission))
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
                        contentDescription = stringResource(R.string.account_own_photo),
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
                    text = when {
                        !status.billingEnabled -> stringResource(R.string.account_status_beta_free)
                        status.isSubscribed -> stringResource(R.string.account_status_active)
                        else -> stringResource(
                            R.string.account_trial_days_left,
                            ServerTime.daysUntil(status.trialEndsAt),
                        )
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.chalk,
                )
                // Wer noch ein Abo aus der Zeit vor der Aussetzung hat, muss es
                // weiterhin kuendigen koennen - der Verwalten-Link bleibt dafuer
                // stehen. Ein Abschluss wird waehrend der Gratisphase gar nicht
                // erst angeboten; der Server lehnt ihn mit 409 ab.
                if (status.isSubscribed) {
                    FlexrLinkButton(
                        text = stringResource(R.string.account_manage_subscription),
                        onClick = viewModel::openBillingPortal,
                    )
                } else if (status.billingEnabled) {
                    FlexrLinkButton(
                        text = stringResource(R.string.account_subscribe),
                        onClick = viewModel::openCheckoutDialog,
                    )
                }
            }
        }

        // ---------- Profil ----------
        Spacer(Modifier.height(26.dp))
        SectionTitle(stringResource(R.string.account_section_profile))

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
            label = stringResource(R.string.field_bio),
            placeholder = stringResource(R.string.field_bio_placeholder),
            singleLine = false,
            maxLines = 5,
            minHeight = 96,
            maxLength = AccountViewModel.BIO_MAX_LENGTH,
            imeAction = ImeAction.Default,
            emojiPicker = true,
        )

        FieldLabel(stringResource(R.string.account_radius_label))
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
            Text(
                stringResource(R.string.account_radius_value, state.searchRadiusKm),
                style = MonoStyle,
                color = colors.chalk,
            )
        }
        Text(
            text = stringResource(R.string.account_radius_hint),
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )

        FieldError(state.saveError)
        Spacer(Modifier.height(16.dp))
        FlexrSecondaryButton(
            text = stringResource(R.string.account_save),
            onClick = viewModel::saveProfile,
            loading = state.isSaving,
        )

        // ---------- Fotos ----------
        Spacer(Modifier.height(28.dp))
        SectionTitle(stringResource(R.string.account_section_photos))
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
                    stringResource(R.string.photo_uploading),
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
        }
        PhotoVisibilityHint(photoStatuses = currentProfile?.photos?.map { it.status }.orEmpty())
        FieldError(state.photoError)

        // ---------- Einstellungen ----------
        Spacer(Modifier.height(28.dp))
        SectionTitle(stringResource(R.string.account_section_settings))

        // Sprachwahl auch hier, weil Einstellungen im Profil gesucht werden -
        // derselbe Regler wie oben in der Kopfzeile, gleicher Zustand.
        Row(
            Modifier.fillMaxWidth().padding(top = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f).padding(end = 12.dp)) {
                Text(
                    stringResource(R.string.lang_row_title),
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    stringResource(R.string.lang_row_hint),
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
            LanguageSwitch(
                language = LocalAppLanguage.current,
                onSelect = languageViewModel::select,
            )
        }
        Row(
            Modifier.fillMaxWidth().padding(top = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    stringResource(R.string.account_messages_switch),
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
                    stringResource(R.string.account_notifications_title),
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    stringResource(R.string.account_notifications_row),
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
                    stringResource(R.string.account_legal_title),
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    stringResource(R.string.account_legal_row),
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
                    stringResource(R.string.account_privacy_title),
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    stringResource(R.string.account_consents_row),
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
                    stringResource(R.string.account_blocks_title),
                    style = MaterialTheme.typography.bodyLarge,
                    color = colors.chalk,
                )
                Text(
                    stringResource(R.string.account_blocks_row),
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
        SectionTitle(stringResource(R.string.common_account))
        Spacer(Modifier.height(12.dp))
        FlexrSecondaryButton(text = stringResource(R.string.common_logout), onClick = onLogout)
        Spacer(Modifier.height(10.dp))
        FlexrDangerButton(
            text = stringResource(R.string.common_delete_account),
            onClick = viewModel::showDeleteDialog,
        )

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
            title = { Text(stringResource(R.string.consent_revoke_title), style = MaterialTheme.typography.headlineSmall) },
            text = {
                Text(
                    text = stringResource(R.string.consent_revoke_body),
                    style = MaterialTheme.typography.bodyMedium,
                    color = FlexrTheme.colors.chalkDim,
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    pendingSensitiveRevoke = false
                    viewModel.revokeConsent("sensitive_data")
                }) {
                    Text(stringResource(R.string.consent_revoke_confirm), color = FlexrTheme.colors.danger)
                }
            },
            dismissButton = {
                TextButton(onClick = { pendingSensitiveRevoke = false }) {
                    Text(stringResource(R.string.common_cancel), color = FlexrTheme.colors.chalkDim)
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
        title = { Text(stringResource(R.string.checkout_title), style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                CheckoutConsentRow(
                    checked = immediateStartChecked,
                    onCheckedChange = onImmediateStartChange,
                    text = stringResource(R.string.checkout_consent_immediate),
                )
                CheckoutConsentRow(
                    checked = withdrawalAckChecked,
                    onCheckedChange = onWithdrawalAckChange,
                    text = stringResource(R.string.checkout_consent_withdrawal),
                )
                FieldError(error)
            }
        },
        confirmButton = {
            TextButton(onClick = onConfirm, enabled = !isStarting) {
                Text(stringResource(R.string.checkout_continue), color = colors.plate)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss, enabled = !isStarting) {
                Text(stringResource(R.string.common_cancel), color = colors.chalkDim)
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
    val revokedSuffix = stringResource(R.string.consent_revoked_suffix)
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
            Text(stringResource(R.string.common_loading), style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)
        }
        sichtbareConsents.isEmpty() && error == null -> Text(
            stringResource(R.string.consent_none),
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )
        else -> Column {
            sichtbareConsents.forEachIndexed { index, consent ->
                Column(Modifier.fillMaxWidth().padding(vertical = 10.dp)) {
                    val label = CONSENT_LABELS[consent.consentType]
                        ?.let { stringResource(it) } ?: consent.consentType
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
                                    append(revokedSuffix)
                                }
                            }
                        },
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalk,
                    )
                    val datum = ServerTime
                        .parse(if (consent.active) consent.grantedAt else consent.revokedAt)
                        ?.let(ServerTime::formatDay)
                    val tag = datum ?: stringResource(R.string.date_unknown)
                    val grundlage = CONSENT_GRUNDLAGE[consent.consentType]?.let { stringResource(it) }
                    val details = buildString {
                        if (consent.active) {
                            append(stringResource(R.string.consent_granted_version, tag, consent.version))
                        } else {
                            append(stringResource(R.string.consent_revoked_on_day, tag))
                        }
                        grundlage?.let { append(" $it") }
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
                                text = stringResource(R.string.consent_revoke_link),
                                onClick = { onRevoke(consent.consentType) },
                                enabled = !busy,
                            )
                        } else {
                            FlexrLinkButton(
                                text = stringResource(R.string.consent_grant_link),
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
            Text(stringResource(R.string.common_loading), style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)
        }
        blockedUsers.isEmpty() && error == null -> Text(
            stringResource(R.string.blocks_empty),
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
                        contentDescription = stringResource(R.string.common_profile_photo_of, user.name),
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
                            text = seit?.let { stringResource(R.string.blocks_blocked_since, it) }
                                ?: stringResource(R.string.blocks_blocked),
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.chalkDim,
                        )
                    }
                    FlexrLinkButton(
                        text = stringResource(R.string.blocks_unblock),
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
                stringResource(R.string.blocks_note),
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
                modifier = Modifier.padding(top = 8.dp),
            )
        }
    }
    FieldError(error)
}

// Ressourcen-Kennungen statt fertiger Texte: aufgeloest wird erst dort, wo
// gezeichnet wird - nur da ist die gewaehlte Sprache bekannt.
private val CONSENT_LABELS = mapOf(
    "sensitive_data" to R.string.consent_sensitive,
    "verification_media" to R.string.consent_verification,
    "terms" to R.string.consent_terms,
)

private val CONSENT_GRUNDLAGE = mapOf(
    "sensitive_data" to R.string.consent_basis_explicit,
    "verification_media" to R.string.consent_basis_explicit,
    "terms" to R.string.consent_basis_contract,
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
    val label = stringResource(
        when {
            status == VerificationStatus.SUBMITTED -> R.string.verify_badge_checking
            status.needsDocument -> R.string.verify_badge_confirm_age
            else -> R.string.verify_hint_title
        },
    )
    val description = stringResource(
        when {
            status == VerificationStatus.SUBMITTED -> R.string.verify_badge_reviewing
            status.needsDocument -> R.string.verify_badge_selfie_done
            status == VerificationStatus.REJECTED -> R.string.verify_badge_failed
            else -> R.string.verify_badge_start
        },
    )

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
                        text = stringResource(
                            if (status.needsDocument) R.string.verify_hint_document else R.string.verify_hint_start,
                        ),
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
 * Untermenü "Benachrichtigungen" - vier Anlässe, je getrennt für E-Mail und App.
 *
 * Als Dialog und nicht als weiterer Block im Konto: acht Schalter, die im
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
        title = { Text(stringResource(R.string.account_notifications_title), style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column(
                Modifier
                    .fillMaxWidth()
                    .heightIn(max = 480.dp)
                    .verticalScroll(rememberScrollState()),
            ) {
                NotificationGroupTitle(stringResource(R.string.notify_match_title))
                NotificationSwitchRow(
                    label = stringResource(R.string.notify_email),
                    hint = stringResource(R.string.notify_match_hint),
                    checked = settings.matchEmail,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyMatchEmail = it)) }
                NotificationSwitchRow(
                    label = stringResource(R.string.notify_push),
                    hint = null,
                    checked = settings.matchPush,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyMatchPush = it)) }

                NotificationGroupTitle(stringResource(R.string.notify_queue_title))
                NotificationSwitchRow(
                    label = stringResource(R.string.notify_email),
                    hint = stringResource(R.string.notify_queue_hint),
                    checked = settings.queueEmail,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyQueueEmail = it)) }
                NotificationSwitchRow(
                    label = stringResource(R.string.notify_push),
                    hint = null,
                    checked = settings.queuePush,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyQueuePush = it)) }

                NotificationGroupTitle(stringResource(R.string.notify_inactive_title))
                NotificationSwitchRow(
                    label = stringResource(R.string.notify_email),
                    hint = stringResource(R.string.notify_inactive_hint),
                    checked = settings.inactiveEmail,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyInactiveEmail = it)) }
                NotificationSwitchRow(
                    label = stringResource(R.string.notify_push),
                    hint = null,
                    checked = settings.inactivePush,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyInactivePush = it)) }

                NotificationGroupTitle(stringResource(R.string.notify_likes_title))
                NotificationSwitchRow(
                    label = stringResource(R.string.notify_email),
                    hint = stringResource(R.string.notify_likes_hint),
                    checked = settings.pendingLikesEmail,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyPendingLikesEmail = it)) }
                NotificationSwitchRow(
                    label = stringResource(R.string.notify_push),
                    hint = null,
                    checked = settings.pendingLikesPush,
                    enabled = !saving,
                ) { onChange(NotificationSettingsRequestDto(notifyPendingLikesPush = it)) }

                Spacer(Modifier.height(14.dp))
                Text(
                    stringResource(R.string.notify_legal_hint),
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalkDim,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.common_close), color = colors.plate)
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
        title = { Text(stringResource(R.string.account_legal_title), style = MaterialTheme.typography.headlineSmall) },
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
                            text = stringResource(document.titleRes),
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
                Text(stringResource(R.string.common_close), color = colors.plate)
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
        title = { Text(stringResource(R.string.common_delete_account), style = MaterialTheme.typography.headlineSmall) },
        text = {
            Column {
                Text(
                    text = stringResource(R.string.delete_body),
                    style = MaterialTheme.typography.bodyMedium,
                    color = FlexrTheme.colors.chalkDim,
                )
                FlexrPasswordField(
                    value = password,
                    onValueChange = onPasswordChange,
                    label = stringResource(R.string.delete_password_label),
                    placeholder = "••••••••",
                    isError = error != null,
                    supportingText = error,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onConfirm, enabled = !isDeleting) {
                Text(stringResource(R.string.delete_confirm), color = FlexrTheme.colors.danger)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.common_cancel), color = FlexrTheme.colors.chalkDim)
            }
        },
    )
}
