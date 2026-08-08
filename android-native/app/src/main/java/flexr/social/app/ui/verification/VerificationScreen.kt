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
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
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
import flexr.social.app.core.designsystem.component.FlexrSecondaryButton
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme

/**
 * Live-Verifizierung mit der Frontkamera.
 *
 * CameraX übernimmt Vorschau und Aufnahme; das Bild verlässt den Speicher nie
 * als Datei, sondern geht direkt komprimiert in den Upload.
 */
@Composable
fun VerificationScreen(
    onBack: () -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: VerificationViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    // Verifizierungs-Selfies gehören genauso wenig in den Recents-Cache.
    SecureScreen()

    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val colors = FlexrTheme.colors

    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED,
        )
    }
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        hasCameraPermission = granted
        if (!granted) viewModel.onCameraDenied()
    }

    LaunchedEffect(Unit) {
        if (!hasCameraPermission) permissionLauncher.launch(Manifest.permission.CAMERA)
    }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is VerificationEvent.Message -> onShowMessage(event.text)
                VerificationEvent.Finished -> onBack()
            }
        }
    }

    val cameraController = remember {
        LifecycleCameraController(context).apply {
            setEnabledUseCases(LifecycleCameraController.IMAGE_CAPTURE)
            cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA
        }
    }
    DisposableEffect(lifecycleOwner, hasCameraPermission) {
        if (hasCameraPermission) cameraController.bindToLifecycle(lifecycleOwner)
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
            IconButton(onClick = onBack, modifier = Modifier.size(36.dp)) {
                Icon(FlexrIcons.Back, contentDescription = "Zurück", tint = colors.chalk)
            }
            Spacer(Modifier.width(6.dp))
            Text(
                text = "Foto-Verifizierung",
                style = MaterialTheme.typography.titleMedium,
                color = colors.chalk,
            )
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(colors.hairline))

        if (state.isStarting) {
            LoadingState(label = "Posen werden geladen …")
            return@Column
        }

        Spacer(Modifier.height(18.dp))
        Eyebrow("Pose ${(state.currentIndex + 1).coerceAtMost(state.total)} / ${state.total}")
        Text(
            text = state.currentPrompt ?: "Fertig!",
            style = MaterialTheme.typography.headlineMedium,
            color = colors.chalk,
        )

        Spacer(Modifier.height(16.dp))
        Box(
            Modifier
                .fillMaxWidth()
                .aspectRatio(3f / 4f)
                .clip(RoundedCornerShape(18.dp))
                .background(colors.surface2)
                .border(1.5.dp, colors.plate.copy(alpha = 0.35f), RoundedCornerShape(18.dp)),
            contentAlignment = Alignment.Center,
        ) {
            if (hasCameraPermission) {
                AndroidView(
                    modifier = Modifier.fillMaxSize(),
                    factory = { viewContext ->
                        PreviewView(viewContext).apply {
                            scaleType = PreviewView.ScaleType.FILL_CENTER
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

        Spacer(Modifier.height(14.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            repeat(state.total) { index ->
                val capture = state.captures.getOrNull(index)
                Box(
                    Modifier
                        .weight(1f)
                        .aspectRatio(1f)
                        .clip(RoundedCornerShape(10.dp))
                        .background(colors.surface2)
                        .border(1.dp, colors.steel, RoundedCornerShape(10.dp)),
                    contentAlignment = Alignment.Center,
                ) {
                    if (capture != null) {
                        AsyncImage(
                            model = capture,
                            contentDescription = "Aufnahme ${index + 1}",
                            contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxSize(),
                        )
                    } else {
                        Text(
                            text = "${index + 1}",
                            style = MaterialTheme.typography.titleMedium,
                            color = colors.chalkDim,
                        )
                    }
                }
            }
        }

        FieldError(state.error)

        Spacer(Modifier.height(16.dp))
        when {
            state.isSubmitting -> FlexrButton(
                text = "Wird hochgeladen …",
                onClick = {},
                enabled = false,
                loading = true,
            )

            state.isComplete -> FlexrSecondaryButton(
                text = "Einreichen wiederholen",
                onClick = viewModel::retrySubmit,
            )

            !hasCameraPermission -> FlexrSecondaryButton(
                text = "Kamerazugriff erlauben",
                onClick = { permissionLauncher.launch(Manifest.permission.CAMERA) },
            )

            else -> FlexrButton(
                text = "Aufnehmen",
                icon = FlexrIcons.Camera,
                onClick = {
                    cameraController.takePicture(
                        ContextCompat.getMainExecutor(context),
                        object : ImageCapture.OnImageCapturedCallback() {
                            override fun onCaptureSuccess(image: ImageProxy) {
                                val bitmap = image.toUprightBitmap()
                                image.close()
                                viewModel.onCaptured(bitmap)
                            }

                            override fun onError(exception: ImageCaptureException) {
                                onShowMessage("Aufnahme fehlgeschlagen, bitte erneut.")
                            }
                        },
                    )
                },
            )
        }

        Spacer(Modifier.height(12.dp))
        Text(
            text = "Die Selfies werden ausschließlich manuell mit deinen Profilfotos verglichen " +
                "und nach der Prüfung gelöscht. Keine automatisierte biometrische Auswertung.",
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
        )
        Spacer(Modifier.height(24.dp))
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
