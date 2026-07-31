package flexr.social.app.data.repository

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import com.google.android.gms.location.CurrentLocationRequest
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CancellableContinuation
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume

data class DeviceLocation(val latitude: Double, val longitude: Double)

/**
 * Gerätestandort über die Fused Location Provider API.
 *
 * Native Entsprechung von `navigator.geolocation` im Web, aber mit den
 * Android-Mechanismen: echte Laufzeitberechtigung, Genauigkeitsstufe je nach
 * erteilter Berechtigung (fein/grob) und ein hartes Zeitlimit, damit der
 * Start des Decks nie am GPS-Fix hängt.
 */
@Singleton
class LocationRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {

    private val client by lazy { LocationServices.getFusedLocationProviderClient(context) }

    fun hasPermission(): Boolean = hasFine() || hasCoarse()

    private fun hasFine() = ContextCompat.checkSelfPermission(
        context, Manifest.permission.ACCESS_FINE_LOCATION,
    ) == PackageManager.PERMISSION_GRANTED

    private fun hasCoarse() = ContextCompat.checkSelfPermission(
        context, Manifest.permission.ACCESS_COARSE_LOCATION,
    ) == PackageManager.PERMISSION_GRANTED

    /**
     * Aktuelle Position oder null (keine Berechtigung, kein Fix, Zeitlimit).
     * Zuerst wird die zuletzt bekannte Position versucht — die liegt meist
     * sofort vor und reicht für eine Umkreissuche in Kilometern völlig aus.
     */
    suspend fun currentLocation(): DeviceLocation? {
        if (!hasPermission()) return null

        lastKnownLocation()?.let { return it }

        val priority = if (hasFine()) Priority.PRIORITY_BALANCED_POWER_ACCURACY
        else Priority.PRIORITY_LOW_POWER

        return withTimeoutOrNull(LOCATION_TIMEOUT_MS) {
            suspendCancellableCoroutine { continuation: CancellableContinuation<DeviceLocation?> ->
                val request = CurrentLocationRequest.Builder()
                    .setPriority(priority)
                    .setMaxUpdateAgeMillis(MAX_LOCATION_AGE_MS)
                    .setDurationMillis(LOCATION_TIMEOUT_MS)
                    .build()
                runCatching {
                    client.getCurrentLocation(request, null)
                        .addOnSuccessListener { location ->
                            if (continuation.isActive) {
                                continuation.resume(
                                    location?.let { DeviceLocation(it.latitude, it.longitude) },
                                )
                            }
                        }
                        .addOnFailureListener {
                            if (continuation.isActive) continuation.resume(null)
                        }
                }.onFailure {
                    if (continuation.isActive) continuation.resume(null)
                }
                continuation.invokeOnCancellation { /* Aufgabe läuft aus, kein Handle nötig */ }
            }
        }
    }

    private suspend fun lastKnownLocation(): DeviceLocation? = runCatching {
        withTimeoutOrNull(LAST_KNOWN_TIMEOUT_MS) {
            suspendCancellableCoroutine { continuation: CancellableContinuation<DeviceLocation?> ->
                client.lastLocation
                    .addOnSuccessListener { location ->
                        if (continuation.isActive) {
                            continuation.resume(
                                location
                                    ?.takeIf { System.currentTimeMillis() - it.time < MAX_LOCATION_AGE_MS }
                                    ?.let { DeviceLocation(it.latitude, it.longitude) },
                            )
                        }
                    }
                    .addOnFailureListener {
                        if (continuation.isActive) continuation.resume(null)
                    }
            }
        }
    }.getOrNull()

    private companion object {
        const val LOCATION_TIMEOUT_MS = 6_000L
        const val LAST_KNOWN_TIMEOUT_MS = 1_500L

        /** 5 Minuten — für eine Umkreissuche in km völlig ausreichend. */
        const val MAX_LOCATION_AGE_MS = 300_000L
    }
}
