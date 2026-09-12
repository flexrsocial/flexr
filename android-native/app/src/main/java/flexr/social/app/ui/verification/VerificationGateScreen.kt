package flexr.social.app.ui.verification

import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.R
import flexr.social.app.core.designsystem.component.Eyebrow
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrCard
import flexr.social.app.core.designsystem.component.FlexrDangerButton
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.component.SectionTitle
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.domain.model.VerificationStep
import flexr.social.app.ui.account.DeleteAccountDialog
import flexr.social.app.ui.components.PhotoGridEditor

/**
 * Einziger erreichbarer Bildschirm, solange ein Konto die Alters- und
 * Identitätsprüfung nicht bestanden hat.
 *
 * Ausloggen und Kontolöschung bleiben zugänglich — ohne sie wäre ein
 * abgelehntes Konto eine Sackgasse.
 */
@Composable
fun VerificationGateScreen(
    onStartSelfies: () -> Unit,
    onStartDocument: () -> Unit,
    onActivated: () -> Unit,
    onLogout: () -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: VerificationGateViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    // Beide Texte landen in Rueckrufen ausserhalb der Komposition - dort ist
    // `stringResource` nicht aufrufbar, also hier einmal aufloesen.
    val context = LocalContext.current
    val reviewRunningMessage = stringResource(R.string.vgate_review_running)

    // Zustand nach der Rückkehr von Selfie- oder Ausweisschritt auffrischen.
    LifecycleEventEffect(Lifecycle.Event.ON_RESUME) { viewModel.load() }

    // Freischaltung erkannt — egal ob über "Status aktualisieren" oder über das
    // Auffrischen beim Zurückkehren in die App. Der Verifizierungsgraph ist ein
    // eigener Navigationsgraph; nur ein neu geladener Sitzungszustand führt
    // hier heraus.
    LaunchedEffect(state.isActivated) {
        if (state.isActivated) onActivated()
    }

    if (state.deleteDialogVisible) {
        DeleteAccountDialog(
            password = state.deletePassword,
            error = state.deleteError,
            isDeleting = state.isDeleting,
            onPasswordChange = viewModel::onDeletePasswordChange,
            onConfirm = {
                viewModel.confirmDelete { message ->
                    onShowMessage(message)
                    onLogout()
                }
            },
            onDismiss = viewModel::hideDeleteDialog,
        )
    }

    if (state.isLoading) {
        LoadingState(label = stringResource(R.string.vgate_loading))
        return
    }

    Column(
        Modifier
            .fillMaxSize()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp),
    ) {
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            Spacer(Modifier.height(10.dp))

            when {
                // Zuerst prüfen: Ein freigeschaltetes Konto meldet "approved"
                // und keinen offenen Schritt mehr - ohne diesen Zweig sähe das
                // wie ein neuer Anfang aus ("Verifizierung starten").
                state.isActivated -> ActivatedContent(onRetry = onActivated)

                state.isWaiting -> WaitingContent(onRefresh = {
                    viewModel.refresh { onShowMessage(reviewRunningMessage) }
                }, isRefreshing = state.isRefreshing)

                state.isRejected -> RejectedContent(reason = state.verification?.reason)

                // Ganz vorn: die bestätigte Adresse. Ohne sie lehnt der Server
                // den Start ab.
                state.needsEmailConfirmation -> EmailPendingContent(
                    email = state.email,
                    isSending = state.isSendingMail,
                    error = state.mailError,
                    onResend = {
                        viewModel.resendVerificationEmail { adresse, stunden ->
                            onShowMessage(context.getString(R.string.vgate_mail_resent, adresse, stunden))
                        }
                    },
                )

                // Danach: Unter der Mindestanzahl an Profilfotos lehnt der
                // Server den Start ebenfalls ab, und von hier führt sonst kein
                // Weg zum Upload.
                !state.hasRequiredPhotos -> MissingPhotoContent(
                    missing = state.missingPhotos,
                    isUploading = state.isUploadingPhoto,
                    error = state.photoError,
                    onPhotoPicked = viewModel::onPhotoPicked,
                )

                state.step == VerificationStep.DOCUMENT -> DocumentPendingContent(
                    needsNewUpload = state.needsNewUpload,
                    reason = state.verification?.reason,
                    onContinue = onStartDocument,
                )

                else -> SelfiePendingContent(
                    needsNewUpload = state.needsNewUpload,
                    reason = state.verification?.reason,
                    onContinue = onStartSelfies,
                )
            }

            FieldError(state.error)

            Spacer(Modifier.height(28.dp))
            SectionTitle(stringResource(R.string.common_account))
            Spacer(Modifier.height(10.dp))
            FlexrSecondaryButton(text = stringResource(R.string.common_logout), onClick = onLogout)
            Spacer(Modifier.height(4.dp))
            FlexrDangerButton(text = stringResource(R.string.common_delete_account), onClick = viewModel::showDeleteDialog)
            Spacer(Modifier.height(24.dp))
        }
    }
}

// ---------- Schritt 1: Selfies ----------

@Composable
private fun SelfiePendingContent(
    needsNewUpload: Boolean,
    reason: String?,
    onContinue: () -> Unit,
) {
    val colors = FlexrTheme.colors

    Eyebrow(stringResource(if (needsNewUpload) R.string.vgate_rework_eyebrow else R.string.vgate_step_1_of_2))
    Text(
        text = stringResource(
            if (needsNewUpload) R.string.vgate_rework_title else R.string.vgate_unlock_title,
        ),
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 1)
    Spacer(Modifier.height(14.dp))
    if (needsNewUpload) StatusChip(stringResource(R.string.vgate_rework_chip), danger = true)

    FlexrCard {
        Column {
            if (!reason.isNullOrBlank()) {
                Text(reason, style = MaterialTheme.typography.bodyMedium, color = colors.chalk)
                Spacer(Modifier.height(10.dp))
            }
            Text(
                text = stringResource(R.string.vgate_intro),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(12.dp))
            Text(
                text = stringResource(R.string.vgate_need_title),
                style = MaterialTheme.typography.headlineSmall,
                color = colors.chalk,
            )
            Spacer(Modifier.height(6.dp))
            Bullet(stringResource(R.string.vgate_need_selfie))
            Bullet(stringResource(R.string.vgate_need_document))
        }
    }

    Spacer(Modifier.height(12.dp))
    FlexrCard {
        Column {
            Text(
                text = stringResource(R.string.vgate_media_title),
                style = MaterialTheme.typography.headlineSmall,
                color = colors.chalk,
            )
            Spacer(Modifier.height(6.dp))
            Bullet(stringResource(R.string.vgate_media_human))
            Bullet(stringResource(R.string.vgate_media_private))
            Bullet(stringResource(R.string.vgate_media_deleted))
        }
    }

    Spacer(Modifier.height(18.dp))
    FlexrButton(
        text = stringResource(if (needsNewUpload) R.string.vgate_retry else R.string.vgate_start),
        onClick = onContinue,
    )
}

// ---------- Schritt 2: Ausweis ----------

@Composable
private fun DocumentPendingContent(
    needsNewUpload: Boolean,
    reason: String?,
    onContinue: () -> Unit,
) {
    val colors = FlexrTheme.colors

    Eyebrow(stringResource(if (needsNewUpload) R.string.vgate_rework_eyebrow else R.string.vgate_step_2_of_2))
    Text(
        text = stringResource(
            if (needsNewUpload) R.string.vgate_rework_title else R.string.vgate_document_title,
        ),
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 2)
    Spacer(Modifier.height(14.dp))
    if (needsNewUpload) StatusChip(stringResource(R.string.vgate_rework_chip), danger = true)

    FlexrCard {
        Column {
            if (!reason.isNullOrBlank()) {
                Text(reason, style = MaterialTheme.typography.bodyMedium, color = colors.chalk)
                Spacer(Modifier.height(10.dp))
            }
            Text(
                text = stringResource(R.string.vgate_document_body),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
        }
    }

    Spacer(Modifier.height(18.dp))
    FlexrButton(
        text = stringResource(
            if (needsNewUpload) R.string.vgate_document_btn_rework else R.string.vgate_document_btn,
        ),
        onClick = onContinue,
    )
}

// ---------- In Prüfung ----------

@Composable
private fun WaitingContent(onRefresh: () -> Unit, isRefreshing: Boolean) {
    val colors = FlexrTheme.colors

    Eyebrow(stringResource(R.string.vgate_submitted_eyebrow))
    Text(
        text = stringResource(R.string.vgate_submitted_title),
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 3)
    Spacer(Modifier.height(14.dp))
    StatusChip(stringResource(R.string.vgate_submitted_chip), danger = false)

    FlexrCard {
        Column {
            Text(
                text = stringResource(R.string.vgate_submitted_body),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = stringResource(R.string.vgate_submitted_note),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
        }
    }

    Spacer(Modifier.height(18.dp))
    FlexrButton(
        text = stringResource(if (isRefreshing) R.string.vgate_checking else R.string.vgate_refresh),
        onClick = onRefresh,
        enabled = !isRefreshing,
        loading = isRefreshing,
    )
}

// ---------- E-Mail noch nicht bestätigt ----------

/**
 * Erster Schritt für ein frisch registriertes Konto. Die Adresse steht
 * absichtlich groß da: Ein Tippfehler bei der Registrierung fällt sonst nie
 * auf, und ohne „Passwort vergessen" wäre das Konto damit unrettbar.
 */
@Composable
private fun EmailPendingContent(
    email: String,
    isSending: Boolean,
    error: String?,
    onResend: () -> Unit,
) {
    val colors = FlexrTheme.colors

    Eyebrow(stringResource(R.string.vgate_step_1_of_3))
    Text(
        text = stringResource(R.string.vgate_mail_title),
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 1)
    Spacer(Modifier.height(14.dp))
    StatusChip(stringResource(R.string.vgate_mail_chip), danger = false)

    FlexrCard {
        Column {
            Text(
                text = stringResource(R.string.vgate_mail_sent_to),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = email.ifBlank { stringResource(R.string.vgate_mail_fallback) },
                style = MaterialTheme.typography.bodyLarge,
                color = colors.chalk,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = stringResource(R.string.vgate_mail_body),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
        }
    }

    FieldError(error)

    Spacer(Modifier.height(18.dp))
    FlexrButton(
        text = stringResource(if (isSending) R.string.vgate_mail_sending else R.string.vgate_mail_resend),
        onClick = onResend,
        enabled = !isSending,
        loading = isSending,
    )
}

// ---------- Zu wenige Profilfotos ----------

/**
 * Die Uploads während der Registrierung können scheitern (Funkloch, Aussetzer
 * im Objekt-Storage) — das Konto hat dann weniger als die geforderten
 * [ImageProcessor.MIN_PHOTOS] Fotos. Die Prüfung lässt sich so nicht starten,
 * und der Konto-Bildschirm mit der Fotoverwaltung liegt im Hauptgraphen, den
 * ein nicht freigeschaltetes Konto nie zu sehen bekommt. Ohne diesen
 * Nachreich-Weg blieb nur die Kontolöschung.
 */
@Composable
private fun MissingPhotoContent(
    missing: Int,
    isUploading: Boolean,
    error: String?,
    onPhotoPicked: (Uri) -> Unit,
) {
    val colors = FlexrTheme.colors

    Eyebrow(stringResource(R.string.vgate_photo_eyebrow))
    Text(
        text = stringResource(R.string.vgate_photo_title),
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 1)
    Spacer(Modifier.height(14.dp))
    StatusChip(stringResource(R.string.vgate_photo_chip), danger = true)

    FlexrCard {
        Column {
            Text(
                text = stringResource(R.string.vgate_photo_body, ImageProcessor.MIN_PHOTOS),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = stringResource(R.string.vgate_photo_body2),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = stringResource(
                    R.string.vgate_photo_missing,
                    missing,
                    ImageProcessor.MIN_PHOTOS,
                ),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.plate,
            )
        }
    }

    Spacer(Modifier.height(14.dp))
    // Genau so viele leere Felder, wie noch fehlen: Die schon hochgeladenen
    // Bilder zeigt dieser Schirm nicht (er verwaltet keine Fotos, er holt nur
    // die Mindestanzahl nach), und mit jedem Upload schrumpft das Raster.
    // Entfernen bleibt aus - unterhalb der Mindestanzahl laesst der Server
    // ohnehin nichts loeschen.
    PhotoGridEditor(
        slots = emptyList(),
        onPhotoPicked = onPhotoPicked,
        onRemove = {},
        maxPhotos = missing,
    )
    if (isUploading) {
        Spacer(Modifier.height(10.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            CircularProgressIndicator(Modifier.size(14.dp), color = colors.plate, strokeWidth = 1.5.dp)
            Spacer(Modifier.width(8.dp))
            Text(
                stringResource(R.string.vgate_photo_uploading),
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
            )
        }
    }
    FieldError(error)
}

// ---------- Freigeschaltet, die App zieht gleich nach ----------

/**
 * Sichtbar wird das nur für einen Augenblick: Der Bildschirm stößt beim
 * Erkennen der Freischaltung sofort das Neuladen der Sitzung an, danach ist
 * dieser Graph weg. Bleibt es hängen, weil das Nachladen scheiterte, führt der
 * Knopf hier heraus — ein Wartebildschirm ohne Ausweg wäre die schlechtere
 * Antwort auf einen Netzfehler.
 */
@Composable
private fun ActivatedContent(onRetry: () -> Unit) {
    val colors = FlexrTheme.colors

    Eyebrow(stringResource(R.string.vgate_done_eyebrow))
    Text(
        text = stringResource(R.string.vgate_unlocked_title),
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 3)
    Spacer(Modifier.height(14.dp))
    StatusChip(stringResource(R.string.vgate_unlocked_chip), danger = false)

    FlexrCard {
        Text(
            text = stringResource(R.string.vgate_unlocked_body),
            style = MaterialTheme.typography.bodyMedium,
            color = colors.chalkDim,
        )
    }

    Spacer(Modifier.height(18.dp))
    FlexrButton(text = stringResource(R.string.vgate_unlocked_cta), onClick = onRetry)
}

// ---------- Endgültig abgelehnt ----------

@Composable
private fun RejectedContent(reason: String?) {
    val colors = FlexrTheme.colors

    Eyebrow(stringResource(R.string.vgate_rejected_eyebrow))
    Text(
        text = stringResource(R.string.vgate_rejected_title),
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 3)
    Spacer(Modifier.height(14.dp))
    StatusChip(stringResource(R.string.vgate_rejected_chip), danger = true)

    FlexrCard {
        Column {
            Text(
                text = reason ?: stringResource(R.string.vgate_rejected_fallback),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalk,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = stringResource(R.string.vgate_rejected_body),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = stringResource(R.string.vgate_rejected_deleted),
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
        }
    }
}

// ---------- Bausteine ----------

@Composable
private fun StatusChip(text: String, danger: Boolean) {
    val colors = FlexrTheme.colors
    val tint = if (danger) colors.danger else colors.plate
    Row(
        Modifier
            .clip(CircleShape)
            .border(1.dp, tint.copy(alpha = 0.4f), CircleShape)
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(7.dp).clip(CircleShape).background(tint))
        Spacer(Modifier.width(8.dp))
        Text(
            text = text.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = tint,
        )
    }
    Spacer(Modifier.height(14.dp))
}

@Composable
private fun Bullet(text: String) {
    val colors = FlexrTheme.colors
    Row(Modifier.fillMaxWidth().padding(vertical = 3.dp)) {
        Text("•", style = MaterialTheme.typography.bodyMedium, color = colors.plate)
        Spacer(Modifier.width(8.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium, color = colors.chalkDim)
    }
}
