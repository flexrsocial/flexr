package flexr.social.app.ui.verification

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.view.LifecycleCameraController
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import flexr.social.app.core.common.SecureScreen
import flexr.social.app.core.designsystem.component.Eyebrow
import flexr.social.app.core.designsystem.component.FieldError
import flexr.social.app.core.designsystem.component.FlexrButton
import flexr.social.app.core.designsystem.component.FlexrCard
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.domain.model.VerificationDocumentType

/**
 * Schritt 2 der Alters- und Identitätsprüfung: amtlicher Lichtbildausweis.
 *
 * Die Kamera öffnet sich erst, wenn ein Aufnahmeplatz angetippt wird — nie von
 * selbst. Vor der ersten Aufnahme steht, wozu die Bilder dienen, dass ein
 * Mensch prüft und dass sie danach gelöscht werden.
 */
@Composable
fun DocumentScreen(
    onBack: () -> Unit,
    onSubmitted: () -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: DocumentViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    // Kein Screenshot und keine Vorschau im App-Umschalter, solange ein
    // Ausweis auf dem Bildschirm liegt.
    SecureScreen()

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is DocumentEvent.Message -> onShowMessage(event.text)
                DocumentEvent.Submitted -> onSubmitted()
                DocumentEvent.StepNoLongerOpen -> onBack()
            }
        }
    }

    val capturing = state.capturing
    if (capturing != null) {
        DocumentCamera(
            side = capturing,
            onCaptured = viewModel::onCaptured,
            onCancel = viewModel::onCaptureCancelled,
            onDenied = viewModel::onCameraDenied,
            onError = onShowMessage,
        )
        return
    }

    DocumentForm(
        state = state,
        onBack = onBack,
        onTypeSelected = viewModel::onTypeSelected,
        onCapture = viewModel::onCaptureRequested,
        onRetake = viewModel::onRetake,
        onSubmit = viewModel::submit,
    )
}

// ---------- Auswahl und Aufnahmeplätze ----------

@Composable
private fun DocumentForm(
    state: DocumentUiState,
    onBack: () -> Unit,
    onTypeSelected: (VerificationDocumentType) -> Unit,
    onCapture: (DocumentSide) -> Unit,
    onRetake: (DocumentSide) -> Unit,
    onSubmit: () -> Unit,
) {
    val colors = FlexrTheme.colors

    Column(
        Modifier
            .fillMaxSize()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp),
    ) {
        Row(
            Modifier.fillMaxWidth().padding(vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack, modifier = Modifier.size(36.dp)) {
                Icon(FlexrIcons.Back, contentDescription = "Zurück", tint = colors.chalk)
            }
            Spacer(Modifier.width(6.dp))
            Text(
                text = "Alter bestätigen",
                style = MaterialTheme.typography.titleMedium,
                color = colors.chalk,
            )
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(colors.hairline))

        if (state.isLoading) {
            LoadingState(label = "Wird geladen …")
            return@Column
        }

        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            Spacer(Modifier.height(16.dp))
            StepBar(current = 2)

            Spacer(Modifier.height(16.dp))
            FlexrCard {
                Column {
                    Text(
                        text = "WARUM WIR DAS BRAUCHEN",
                        style = MaterialTheme.typography.headlineSmall,
                        color = colors.chalk,
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Um FLEXR nutzen zu können, musst du mindestens 18 Jahre alt " +
                            "sein. Lade einmalig einen gültigen amtlichen Lichtbildausweis hoch. " +
                            "Wir verwenden ihn ausschließlich zur Alters- und Identitätsprüfung " +
                            "und löschen die Aufnahme nach Abschluss der Prüfung.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalkDim,
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Die Prüfung erfolgt manuell durch einen Menschen — es kommt " +
                            "keine automatische Gesichtserkennung zum Einsatz.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalkDim,
                    )
                }
            }

            Spacer(Modifier.height(18.dp))
            Eyebrow("Dokumenttyp")
            state.documentTypes.forEach { type ->
                DocumentTypeOption(
                    type = type,
                    selected = type.value == state.selectedType?.value,
                    onClick = { onTypeSelected(type) },
                )
                Spacer(Modifier.height(8.dp))
            }

            Spacer(Modifier.height(8.dp))
            RedactionNote()

            Spacer(Modifier.height(18.dp))
            Eyebrow("Aufnahmen")
            state.requiredSides.forEach { side ->
                CaptureSlot(
                    side = side,
                    image = state.captures[side],
                    onClick = {
                        if (state.captures[side] == null) onCapture(side) else onRetake(side)
                    },
                )
                Spacer(Modifier.height(10.dp))
            }

            FieldError(state.error)
            Spacer(Modifier.height(16.dp))
        }

        if (state.isSubmitting) {
            FlexrButton(text = "Wird übermittelt …", onClick = {}, enabled = false, loading = true)
        } else {
            FlexrButton(
                text = "Zur Prüfung einreichen",
                onClick = onSubmit,
                enabled = state.isComplete,
            )
        }
        Spacer(Modifier.height(10.dp))
        Text(
            text = "Die Aufnahmen sind nicht öffentlich abrufbar und werden nach der Prüfung " +
                "gelöscht.",
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )
        Spacer(Modifier.height(20.dp))
    }
}

/** Schrittanzeige: 1 Selfies, 2 Ausweis, 3 Prüfung. */
@Composable
internal fun StepBar(current: Int, modifier: Modifier = Modifier) {
    val colors = FlexrTheme.colors
    Row(modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        (1..3).forEach { step ->
            Box(
                Modifier
                    .weight(1f)
                    .height(3.dp)
                    .clip(RoundedCornerShape(2.dp))
                    .background(
                        when {
                            step < current -> colors.plate
                            step == current -> colors.chalk
                            else -> colors.steel
                        },
                    ),
            )
        }
    }
}

@Composable
private fun DocumentTypeOption(
    type: VerificationDocumentType,
    selected: Boolean,
    onClick: () -> Unit,
) {
    val colors = FlexrTheme.colors
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(13.dp))
            .background(if (selected) colors.plate.copy(alpha = 0.08f) else colors.surface2)
            .border(
                width = 1.dp,
                color = if (selected) colors.plate else colors.steel,
                shape = RoundedCornerShape(13.dp),
            )
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 13.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column {
            Text(
                text = type.label,
                style = MaterialTheme.typography.bodyLarge,
                color = colors.chalk,
            )
            Text(
                text = if (type.needsBack) "Vorder- und Rückseite" else "Datenseite mit Foto",
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
            )
        }
    }
}

/** Hinweis, dass nicht benötigte Angaben geschwärzt werden dürfen. */
@Composable
private fun RedactionNote() {
    val colors = FlexrTheme.colors
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(colors.plate.copy(alpha = 0.06f))
            .border(1.dp, colors.plate.copy(alpha = 0.22f), RoundedCornerShape(12.dp))
            .padding(12.dp),
    ) {
        Column {
            Text(
                text = "Du kannst Informationen schwärzen, die für die Altersprüfung nicht " +
                    "benötigt werden.",
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = "Foto, Geburtsdatum und die zur Prüfung erforderlichen " +
                    "Gültigkeitsinformationen müssen sichtbar bleiben.",
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalk,
                fontWeight = FontWeight.SemiBold,
            )
        }
    }
}

@Composable
private fun CaptureSlot(side: DocumentSide, image: ByteArray?, onClick: () -> Unit) {
    val colors = FlexrTheme.colors
    Box(
        Modifier
            .fillMaxWidth()
            .aspectRatio(3f / 2f)
            .clip(RoundedCornerShape(14.dp))
            .background(colors.surface2)
            .border(
                width = if (image != null) 1.dp else 1.5.dp,
                color = if (image != null) colors.plate else colors.steel,
                shape = RoundedCornerShape(14.dp),
            )
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        if (image != null) {
            AsyncImage(
                model = image,
                contentDescription = "${side.label} des Ausweises",
                contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxSize(),
            )
            Box(
                Modifier
                    .align(Alignment.BottomStart)
                    .padding(8.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(Color.Black.copy(alpha = 0.62f))
                    .padding(horizontal = 8.dp, vertical = 4.dp),
            ) {
                Text(
                    text = "${side.label} ✓ — tippen zum Wiederholen",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.chalk,
                )
            }
        } else {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(
                    FlexrIcons.Camera,
                    contentDescription = null,
                    tint = colors.chalkDim,
                    modifier = Modifier.size(24.dp),
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = side.label + " aufnehmen",
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.chalkDim,
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}

// ---------- Kamera ----------

/**
 * Vollflächige Aufnahme über die Rückkamera. Bewusst ein eigener Zustand statt
 * eines Dialogs: Der Ausweis soll formatfüllend im Sucher liegen.
 */
@Composable
private fun DocumentCamera(
    side: DocumentSide,
    onCaptured: (Bitmap) -> Unit,
    onCancel: () -> Unit,
    onDenied: () -> Unit,
    onError: (String) -> Unit,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val colors = FlexrTheme.colors

    var hasPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED,
        )
    }
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        hasPermission = granted
        if (!granted) onDenied()
    }
    LaunchedEffect(Unit) {
        if (!hasPermission) permissionLauncher.launch(Manifest.permission.CAMERA)
    }

    val cameraController = remember {
        LifecycleCameraController(context).apply {
            setEnabledUseCases(LifecycleCameraController.IMAGE_CAPTURE)
            cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
        }
    }
    DisposableEffect(lifecycleOwner, hasPermission) {
        if (hasPermission) cameraController.bindToLifecycle(lifecycleOwner)
        onDispose { cameraController.unbind() }
    }

    Column(
        Modifier
            .fillMaxSize()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp),
    ) {
        Row(
            Modifier.fillMaxWidth().padding(vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onCancel, modifier = Modifier.size(36.dp)) {
                Icon(FlexrIcons.Back, contentDescription = "Abbrechen", tint = colors.chalk)
            }
            Spacer(Modifier.width(6.dp))
            Text(
                text = side.label + " aufnehmen",
                style = MaterialTheme.typography.titleMedium,
                color = colors.chalk,
            )
        }

        Spacer(Modifier.height(8.dp))
        Text(
            text = "Lege den Ausweis flach hin und füll den Rahmen möglichst aus. Achte darauf, " +
                "dass Foto und Geburtsdatum scharf zu lesen sind.",
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )

        Spacer(Modifier.height(14.dp))
        Box(
            Modifier
                .fillMaxWidth()
                .weight(1f)
                .clip(RoundedCornerShape(18.dp))
                .background(colors.surface2)
                .border(1.5.dp, colors.plate.copy(alpha = 0.35f), RoundedCornerShape(18.dp)),
            contentAlignment = Alignment.Center,
        ) {
            if (hasPermission) {
                AndroidView(
                    modifier = Modifier.fillMaxSize(),
                    factory = { viewContext ->
                        PreviewView(viewContext).apply {
                            scaleType = PreviewView.ScaleType.FIT_CENTER
                            controller = cameraController
                        }
                    },
                )
            } else {
                Text(
                    text = "Kamerazugriff wird benötigt.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.chalkDim,
                    textAlign = TextAlign.Center,
                )
            }
        }

        Spacer(Modifier.height(16.dp))
        if (hasPermission) {
            FlexrButton(
                text = "Aufnehmen",
                icon = FlexrIcons.Camera,
                onClick = {
                    cameraController.takePicture(
                        ContextCompat.getMainExecutor(context),
                        object : ImageCapture.OnImageCapturedCallback() {
                            override fun onCaptureSuccess(image: ImageProxy) {
                                val bitmap = image.toUprightBitmap()
                                image.close()
                                onCaptured(bitmap)
                            }

                            override fun onError(exception: ImageCaptureException) {
                                onError("Aufnahme fehlgeschlagen, bitte erneut.")
                            }
                        },
                    )
                },
            )
        } else {
            FlexrSecondaryButton(
                text = "Kamerazugriff erlauben",
                onClick = { permissionLauncher.launch(Manifest.permission.CAMERA) },
            )
        }
        Spacer(Modifier.height(20.dp))
    }
}

/** Aufnahme in die tatsächliche Blickrichtung drehen (Sensor- vs. Anzeigelage). */
private fun ImageProxy.toUprightBitmap(): Bitmap {
    val bitmap = toBitmap()
    val rotation = imageInfo.rotationDegrees
    if (rotation == 0) return bitmap
    val matrix = Matrix().apply { postRotate(rotation.toFloat()) }
    return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
}
