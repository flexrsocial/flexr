package flexr.social.app.ui.verification

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.net.Uri
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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import flexr.social.app.R
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
        onPickFile = viewModel::onFilePicked,
        onRetake = viewModel::onRetake,
        onSubmit = viewModel::submit,
    )
}

/**
 * Uebersetzte Bezeichnung des Ausweistyps.
 *
 * Der Server liefert sie auf Deutsch. Kennen wir den Wert, nehmen wir die
 * eigene Uebersetzung; alles Unbekannte bleibt so, wie es geliefert wurde.
 */
@Composable
private fun documentTypeLabel(type: VerificationDocumentType): String = when (type.value) {
    "id_card" -> stringResource(R.string.document_type_id_card)
    "passport" -> stringResource(R.string.document_type_passport)
    "drivers_license" -> stringResource(R.string.document_type_license)
    else -> type.label
}

// ---------- Auswahl und Aufnahmeplätze ----------

@Composable
private fun DocumentForm(
    state: DocumentUiState,
    onBack: () -> Unit,
    onTypeSelected: (VerificationDocumentType) -> Unit,
    onCapture: (DocumentSide) -> Unit,
    onPickFile: (DocumentSide, Uri) -> Unit,
    onRetake: (DocumentSide) -> Unit,
    onSubmit: () -> Unit,
) {
    // Die Dateiauswahl merkt sich, fuer welche Seite sie geoeffnet wurde - der
    // Rueckgabewert des Systemdialogs kennt nur die URI.
    var pickForSide by remember { mutableStateOf(DocumentSide.FRONT) }
    val filePicker = rememberLauncherForActivityResult(
        ActivityResultContracts.GetContent(),
    ) { uri -> if (uri != null) onPickFile(pickForSide, uri) }
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
                Icon(FlexrIcons.Back, contentDescription = stringResource(R.string.common_back), tint = colors.chalk)
            }
            Spacer(Modifier.width(6.dp))
            Text(
                text = stringResource(R.string.document_title),
                style = MaterialTheme.typography.titleMedium,
                color = colors.chalk,
            )
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(colors.hairline))

        if (state.isLoading) {
            LoadingState(label = stringResource(R.string.document_loading))
            return@Column
        }

        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            Spacer(Modifier.height(16.dp))
            StepBar(current = 2)

            Spacer(Modifier.height(16.dp))
            FlexrCard {
                Column {
                    Text(
                        text = stringResource(R.string.document_why_title),
                        style = MaterialTheme.typography.headlineSmall,
                        color = colors.chalk,
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = stringResource(R.string.document_why),
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalkDim,
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = stringResource(R.string.document_manual_review),
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalkDim,
                    )
                }
            }

            Spacer(Modifier.height(18.dp))
            Eyebrow(stringResource(R.string.document_type_label))
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
            Eyebrow(stringResource(R.string.document_shots_label))
            state.requiredSides.forEach { side ->
                CaptureSlot(
                    side = side,
                    image = state.captures[side],
                    onClick = {
                        if (state.captures[side] == null) onCapture(side) else onRetake(side)
                    },
                    onPickFile = {
                        pickForSide = side
                        filePicker.launch("image/*")
                    },
                )
                Spacer(Modifier.height(10.dp))
            }
            Text(
                text = stringResource(R.string.document_source_hint),
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
                modifier = Modifier.padding(top = 2.dp),
            )
            Spacer(Modifier.height(6.dp))

            FieldError(state.error)
            Spacer(Modifier.height(16.dp))
        }

        if (state.isSubmitting) {
            FlexrButton(
                text = stringResource(R.string.document_submitting),
                onClick = {},
                enabled = false,
                loading = true,
            )
        } else {
            FlexrButton(
                text = stringResource(R.string.document_submit),
                onClick = onSubmit,
                enabled = state.isComplete,
            )
        }
        Spacer(Modifier.height(10.dp))
        Text(
            text = stringResource(R.string.document_consent_note),
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
                text = documentTypeLabel(type),
                style = MaterialTheme.typography.bodyLarge,
                color = colors.chalk,
            )
            Text(
                text = stringResource(
                    if (type.needsBack) R.string.document_needs_both else R.string.document_needs_front,
                ),
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
                text = stringResource(R.string.document_redact_note),
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = stringResource(R.string.document_redact_note_bold),
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalk,
                fontWeight = FontWeight.SemiBold,
            )
        }
    }
}

@Composable
private fun CaptureSlot(
    side: DocumentSide,
    image: ByteArray?,
    onClick: () -> Unit,
    onPickFile: () -> Unit,
) {
    val colors = FlexrTheme.colors
    Column {
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
                contentDescription = stringResource(R.string.document_side_of_id, stringResource(side.labelRes)),
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
                    text = stringResource(R.string.document_side_done, stringResource(side.labelRes)),
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
                    text = stringResource(R.string.document_capture_side, stringResource(side.labelRes)),
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.chalkDim,
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
        // Zwei sichtbare Wege statt nur der Kamera: wer den Ausweis schon
        // gescannt oder vorab geschwaerzt hat, kaeme sonst nicht weiter.
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SlotActionButton(
                icon = FlexrIcons.Camera,
                label = stringResource(R.string.document_action_camera),
                onClick = onClick,
                modifier = Modifier.weight(1f),
            )
            SlotActionButton(
                icon = FlexrIcons.Upload,
                label = stringResource(R.string.document_action_file),
                onClick = onPickFile,
                modifier = Modifier.weight(1f),
            )
        }
    }
}

/** Flacher Knopf unter dem Aufnahmeplatz — Kamera oder Dateiauswahl. */
@Composable
private fun SlotActionButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = FlexrTheme.colors
    Row(
        modifier
            .clip(RoundedCornerShape(10.dp))
            .border(1.dp, colors.steel, RoundedCornerShape(10.dp))
            .clickable(onClick = onClick)
            .padding(vertical = 9.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(icon, contentDescription = null, tint = colors.chalkDim, modifier = Modifier.size(15.dp))
        Spacer(Modifier.width(6.dp))
        Text(label, style = MaterialTheme.typography.bodySmall, color = colors.chalkDim)
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
    // Aus dem Kamera-Rueckruf heraus ist kein `stringResource` moeglich - der
    // laeuft ausserhalb der Komposition. Deshalb hier einmal aufloesen.
    val captureFailedMessage = stringResource(R.string.document_capture_failed)

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
                Icon(FlexrIcons.Back, contentDescription = stringResource(R.string.common_cancel), tint = colors.chalk)
            }
            Spacer(Modifier.width(6.dp))
            Text(
                text = stringResource(R.string.document_capture_side, stringResource(side.labelRes)),
                style = MaterialTheme.typography.titleMedium,
                color = colors.chalk,
            )
        }

        Spacer(Modifier.height(8.dp))
        Text(
            text = stringResource(R.string.document_frame_hint),
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
                            // Siehe VerificationScreen: die voreingestellte
                            // SurfaceView hält sich nicht an Rahmen und Ecken.
                            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
                            scaleType = PreviewView.ScaleType.FIT_CENTER
                            controller = cameraController
                        }
                    },
                )
            } else {
                Text(
                    text = stringResource(R.string.document_camera_needed),
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.chalkDim,
                    textAlign = TextAlign.Center,
                )
            }
        }

        Spacer(Modifier.height(16.dp))
        if (hasPermission) {
            FlexrButton(
                text = stringResource(R.string.document_capture),
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
                                onError(captureFailedMessage)
                            }
                        },
                    )
                },
            )
        } else {
            FlexrSecondaryButton(
                text = stringResource(R.string.document_allow_camera),
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
