package flexr.social.app.core.media

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import android.net.Uri
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.max
import kotlin.math.min

/** Fertig aufbereitetes Foto: Vollbild plus quadratisches Thumbnail. */
data class PreparedPhoto(
    val full: ByteArray,
    val thumbnail: ByteArray,
    val mimeType: String = "image/jpeg",
) {
    // ByteArray hat keine sinnvolle equals/hashCode — für data class explizit setzen.
    override fun equals(other: Any?): Boolean =
        this === other || (other is PreparedPhoto && full.contentEquals(other.full))

    override fun hashCode(): Int = full.contentHashCode()
}

class PhotoTooSmallException(val width: Int, val height: Int) : Exception(
    "Foto zu klein ($width×$height). Mindestens " +
        "${ImageProcessor.MIN_EDGE_PX}×${ImageProcessor.MIN_EDGE_PX} Pixel.",
)

/**
 * Bildaufbereitung vor dem Upload — die native Entsprechung der
 * Canvas-Verarbeitung im Web (`preparePhoto`):
 *
 * - Mindestauflösung 600 px je Seite, sonst wirken Fotos auf den Karten pixelig
 * - Vollbild auf max. 1080 px lange Kante herunterskaliert, JPEG-Qualität 85
 * - quadratisches 256-px-Thumbnail (mittiger Cover-Crop) für kleine Avatare
 * - EXIF-Drehung wird angewandt, damit Hochformat-Aufnahmen nicht liegen
 *
 * Läuft vollständig auf einem Hintergrund-Dispatcher.
 */
@Singleton
class ImageProcessor @Inject constructor(
    @ApplicationContext private val context: Context,
) {

    suspend fun prepare(uri: Uri): PreparedPhoto = withContext(Dispatchers.Default) {
        val bounds = readBounds(uri)
        if (min(bounds.width, bounds.height) < MIN_EDGE_PX) {
            throw PhotoTooSmallException(bounds.width, bounds.height)
        }

        val sampleSize = calculateInSampleSize(bounds.width, bounds.height, MAX_EDGE_PX)
        val decoded = decode(uri, sampleSize) ?: error("Bild konnte nicht gelesen werden.")
        val oriented = applyExifRotation(uri, decoded)

        val full = scaleToMaxEdge(oriented, MAX_EDGE_PX)
        val thumbnail = centerSquare(oriented, THUMB_PX)

        val result = PreparedPhoto(
            full = full.toJpeg(JPEG_QUALITY),
            thumbnail = thumbnail.toJpeg(JPEG_QUALITY),
        )

        if (full !== oriented) full.recycle()
        thumbnail.recycle()
        oriented.recycle()
        result
    }

    /** Aufnahme aus der Kamera (Verifizierungs-Selfie) — bereits im Speicher. */
    suspend fun compressSelfie(bitmap: Bitmap): ByteArray = withContext(Dispatchers.Default) {
        val scaled = scaleToMaxEdge(bitmap, SELFIE_MAX_EDGE_PX)
        val bytes = scaled.toJpeg(JPEG_QUALITY)
        if (scaled !== bitmap) scaled.recycle()
        bytes
    }

    private data class Bounds(val width: Int, val height: Int)

    private fun readBounds(uri: Uri): Bounds {
        val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        context.contentResolver.openInputStream(uri).use {
            BitmapFactory.decodeStream(it, null, options)
        }
        if (options.outWidth <= 0 || options.outHeight <= 0) {
            error("Bild konnte nicht gelesen werden.")
        }
        return Bounds(options.outWidth, options.outHeight)
    }

    private fun decode(uri: Uri, sampleSize: Int): Bitmap? {
        val options = BitmapFactory.Options().apply {
            inSampleSize = sampleSize
            inPreferredConfig = Bitmap.Config.ARGB_8888
        }
        return context.contentResolver.openInputStream(uri).use {
            BitmapFactory.decodeStream(it, null, options)
        }
    }

    private fun applyExifRotation(uri: Uri, bitmap: Bitmap): Bitmap {
        val orientation = runCatching {
            context.contentResolver.openInputStream(uri).use { stream ->
                stream?.let { ExifInterface(it).getAttributeInt(
                    ExifInterface.TAG_ORIENTATION,
                    ExifInterface.ORIENTATION_NORMAL,
                ) }
            }
        }.getOrNull() ?: ExifInterface.ORIENTATION_NORMAL

        val matrix = Matrix()
        when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> matrix.postRotate(90f)
            ExifInterface.ORIENTATION_ROTATE_180 -> matrix.postRotate(180f)
            ExifInterface.ORIENTATION_ROTATE_270 -> matrix.postRotate(270f)
            ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> matrix.postScale(-1f, 1f)
            ExifInterface.ORIENTATION_FLIP_VERTICAL -> matrix.postScale(1f, -1f)
            else -> return bitmap
        }
        val rotated = Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
        if (rotated !== bitmap) bitmap.recycle()
        return rotated
    }

    private fun calculateInSampleSize(width: Int, height: Int, target: Int): Int {
        var sample = 1
        var longEdge = max(width, height)
        while (longEdge / 2 >= target) {
            longEdge /= 2
            sample *= 2
        }
        return sample
    }

    private fun scaleToMaxEdge(bitmap: Bitmap, maxEdge: Int): Bitmap {
        val longEdge = max(bitmap.width, bitmap.height)
        if (longEdge <= maxEdge) return bitmap
        val scale = maxEdge.toFloat() / longEdge
        return Bitmap.createScaledBitmap(
            bitmap,
            Math.round(bitmap.width * scale),
            Math.round(bitmap.height * scale),
            true,
        )
    }

    private fun centerSquare(bitmap: Bitmap, size: Int): Bitmap {
        val side = min(bitmap.width, bitmap.height)
        val left = (bitmap.width - side) / 2
        val top = (bitmap.height - side) / 2
        val cropped = Bitmap.createBitmap(bitmap, left, top, side, side)
        val scaled = Bitmap.createScaledBitmap(cropped, size, size, true)
        if (cropped !== scaled && cropped !== bitmap) cropped.recycle()
        return scaled
    }

    private fun Bitmap.toJpeg(quality: Int): ByteArray =
        ByteArrayOutputStream().use { stream ->
            compress(Bitmap.CompressFormat.JPEG, quality, stream)
            stream.toByteArray()
        }

    companion object {
        const val MIN_EDGE_PX = 600
        const val MAX_EDGE_PX = 1080
        const val THUMB_PX = 256
        const val SELFIE_MAX_EDGE_PX = 1280
        const val JPEG_QUALITY = 85
        const val MAX_PHOTOS = 6
    }
}
