package flexr.social.app.ui.verification

import android.net.Uri
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
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import flexr.social.app.ui.account.DeleteAccountDialog
import flexr.social.app.core.designsystem.component.Eyebrow
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrCard
import flexr.social.app.core.designsystem.component.FlexrDangerButton
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.component.SectionTitle
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.domain.model.VerificationStep
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
        LoadingState(label = "Status wird geladen …")
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
                    viewModel.refresh { onShowMessage("Die Prüfung läuft noch.") }
                }, isRefreshing = state.isRefreshing)

                state.isRejected -> RejectedContent(reason = state.verification?.reason)

                // Vor allen offenen Schritten: Ohne Profilfoto lehnt der Server
                // den Start ab, und von hier führt sonst kein Weg zum Upload.
                !state.hasProfilePhoto -> MissingPhotoContent(
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
            SectionTitle("Konto")
            Spacer(Modifier.height(10.dp))
            FlexrSecondaryButton(text = "Ausloggen", onClick = onLogout)
            Spacer(Modifier.height(4.dp))
            FlexrDangerButton(text = "Konto löschen", onClick = viewModel::showDeleteDialog)
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

    Eyebrow(if (needsNewUpload) "Nachbesserung" else "Schritt 1 von 2")
    Text(
        text = if (needsNewUpload) {
            "Wir konnten deine Verifizierung noch nicht abschließen."
        } else {
            "Konto freischalten"
        },
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 1)
    Spacer(Modifier.height(14.dp))
    if (needsNewUpload) StatusChip("Neue Aufnahme nötig", danger = true)

    FlexrCard {
        Column {
            if (!reason.isNullOrBlank()) {
                Text(reason, style = MaterialTheme.typography.bodyMedium, color = colors.chalk)
                Spacer(Modifier.height(10.dp))
            }
            Text(
                text = "FLEXR ist ab 18. Damit hier keine Minderjährigen und keine Fake-Profile " +
                    "landen, prüfen wir einmalig, ob du wirklich du bist und mindestens " +
                    "18 Jahre alt.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(12.dp))
            Text(
                text = "DAS BRAUCHST DU",
                style = MaterialTheme.typography.headlineSmall,
                color = colors.chalk,
            )
            Spacer(Modifier.height(6.dp))
            Bullet("Ein Live-Selfie, frontal in die Kamera — die Kamera öffnet sich erst, wenn du startest")
            Bullet("Eine Aufnahme deines Personalausweises, Reisepasses oder Führerscheins")
        }
    }

    Spacer(Modifier.height(12.dp))
    FlexrCard {
        Column {
            Text(
                text = "WAS MIT DEN AUFNAHMEN PASSIERT",
                style = MaterialTheme.typography.headlineSmall,
                color = colors.chalk,
            )
            Spacer(Modifier.height(6.dp))
            Bullet("Ein Mensch vergleicht Profilfoto, Selfie und Ausweisfoto — keine automatische Gesichtserkennung")
            Bullet("Die Aufnahmen sind nicht öffentlich abrufbar")
            Bullet("Nach Abschluss der Prüfung werden sie gelöscht")
        }
    }

    Spacer(Modifier.height(18.dp))
    FlexrButton(
        text = if (needsNewUpload) "Verifizierung wiederholen" else "Verifizierung starten",
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

    Eyebrow(if (needsNewUpload) "Nachbesserung" else "Schritt 2 von 2")
    Text(
        text = if (needsNewUpload) {
            "Wir konnten deine Verifizierung noch nicht abschließen."
        } else {
            "Alter bestätigen"
        },
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 2)
    Spacer(Modifier.height(14.dp))
    if (needsNewUpload) StatusChip("Neue Aufnahme nötig", danger = true)

    FlexrCard {
        Column {
            if (!reason.isNullOrBlank()) {
                Text(reason, style = MaterialTheme.typography.bodyMedium, color = colors.chalk)
                Spacer(Modifier.height(10.dp))
            }
            Text(
                text = "Dein Selfie liegt vor. Jetzt fehlt noch eine Aufnahme deines " +
                    "amtlichen Lichtbildausweises, damit wir dein Alter bestätigen können.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
        }
    }

    Spacer(Modifier.height(18.dp))
    FlexrButton(
        text = if (needsNewUpload) "Erneut hochladen" else "Ausweis aufnehmen",
        onClick = onContinue,
    )
}

// ---------- In Prüfung ----------

@Composable
private fun WaitingContent(onRefresh: () -> Unit, isRefreshing: Boolean) {
    val colors = FlexrTheme.colors

    Eyebrow("In Prüfung")
    Text(
        text = "Verifizierung wird geprüft",
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 3)
    Spacer(Modifier.height(14.dp))
    StatusChip("Prüfung läuft", danger = false)

    FlexrCard {
        Column {
            Text(
                text = "Deine Angaben wurden übermittelt. Wir prüfen jetzt, ob du mindestens " +
                    "18 Jahre alt bist und ob die Verifizierung zu deinem Profil gehört. Sobald " +
                    "die Prüfung abgeschlossen ist, kannst du FLEXR vollständig nutzen.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = "Die Aufnahmen deines Ausweises werden nach Abschluss der Prüfung " +
                    "gelöscht. Dein Probemonat startet erst mit der Freischaltung — die " +
                    "Wartezeit kostet dich also keine Gratiszeit.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
        }
    }

    Spacer(Modifier.height(18.dp))
    FlexrButton(
        text = if (isRefreshing) "Wird geprüft …" else "Status aktualisieren",
        onClick = onRefresh,
        enabled = !isRefreshing,
        loading = isRefreshing,
    )
}

// ---------- Profilfoto fehlt ----------

/**
 * Der Upload während der Registrierung kann scheitern (Funkloch, Aussetzer im
 * Objekt-Storage) — das Konto existiert dann ohne Foto. Die Prüfung lässt sich
 * so nicht starten, und der Konto-Bildschirm mit der Fotoverwaltung liegt im
 * Hauptgraphen, den ein nicht freigeschaltetes Konto nie zu sehen bekommt.
 * Ohne diesen Nachreich-Weg blieb nur die Kontolöschung.
 */
@Composable
private fun MissingPhotoContent(
    isUploading: Boolean,
    error: String?,
    onPhotoPicked: (Uri) -> Unit,
) {
    val colors = FlexrTheme.colors

    Eyebrow("Profilfoto fehlt")
    Text(
        text = "Zuerst dein Profilfoto",
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 1)
    Spacer(Modifier.height(14.dp))
    StatusChip("Foto fehlt", danger = true)

    FlexrCard {
        Column {
            Text(
                text = "Für die Prüfung vergleicht ein Mensch dein Profilfoto mit deinem " +
                    "Selfie und deinem Ausweis. Ohne Profilfoto kann sie nicht starten.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = "Beim Anlegen deines Profils hat der Upload nicht geklappt. Hol ihn " +
                    "hier nach — danach geht es normal weiter.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
        }
    }

    Spacer(Modifier.height(14.dp))
    PhotoGridEditor(
        slots = emptyList(),
        onPhotoPicked = onPhotoPicked,
        onRemove = {},
        maxPhotos = 1,
    )
    if (isUploading) {
        Spacer(Modifier.height(10.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            CircularProgressIndicator(Modifier.size(14.dp), color = colors.plate, strokeWidth = 1.5.dp)
            Spacer(Modifier.width(8.dp))
            Text(
                "Foto wird hochgeladen …",
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

    Eyebrow("Geschafft")
    Text(
        text = "Konto freigeschaltet",
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 3)
    Spacer(Modifier.height(14.dp))
    StatusChip("Freigeschaltet", danger = false)

    FlexrCard {
        Text(
            text = "Deine Prüfung ist durch. Wir laden gerade dein Profil — gleich " +
                "steht dir FLEXR vollständig offen.",
            style = MaterialTheme.typography.bodyMedium,
            color = colors.chalkDim,
        )
    }

    Spacer(Modifier.height(18.dp))
    FlexrButton(text = "Weiter zu FLEXR", onClick = onRetry)
}

// ---------- Endgültig abgelehnt ----------

@Composable
private fun RejectedContent(reason: String?) {
    val colors = FlexrTheme.colors

    Eyebrow("Abgeschlossen")
    Text(
        text = "Verifizierung nicht erfolgreich",
        style = MaterialTheme.typography.headlineMedium,
        color = colors.chalk,
    )
    Spacer(Modifier.height(14.dp))
    StepBar(current = 3)
    Spacer(Modifier.height(14.dp))
    StatusChip("Nicht freigeschaltet", danger = true)

    FlexrCard {
        Column {
            Text(
                text = reason ?: "Wir konnten deine Verifizierung nicht abschließen.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalk,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = "Dein Konto wurde nicht freigeschaltet. Wenn du glaubst, dass das ein " +
                    "Fehler ist, schreib uns an flexr.social@proton.me.",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = "Alle Aufnahmen deines Ausweises und dein Verifizierungs-Selfie wurden " +
                    "gelöscht.",
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
