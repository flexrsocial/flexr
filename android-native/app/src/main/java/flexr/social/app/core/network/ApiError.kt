package flexr.social.app.core.network

import flexr.social.app.core.common.ServerTime
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import retrofit2.HttpException
import java.io.IOException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import java.time.Instant

/**
 * Übersetzt HTTP-Fehler des Backends in eine Ausnahme mit anzeigbarer,
 * deutscher Meldung — dieselbe Logik wie die `api()`-Funktion im Web-Frontend:
 * `detail` kann ein String, eine Pydantic-Fehlerliste oder ein Objekt sein.
 */
class FlexrApiException(
    val statusCode: Int,
    override val message: String,
    /** Bei einer befristeten Chat-Sperre: bis wann sie gilt. */
    val mutedUntil: Instant? = null,
    /** Begründung der Maßnahme und Widerspruchsweg (Art. 17 DSA). */
    val moderationReason: String? = null,
    val appealHint: String? = null,
) : Exception(message) {

    val isUnauthorized: Boolean get() = statusCode == 401
    val isPaymentRequired: Boolean get() = statusCode == 402
    val isMessagingMuted: Boolean get() = mutedUntil != null
}

object ApiErrorParser {

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    fun toFlexrException(throwable: Throwable): FlexrApiException = when (throwable) {
        is FlexrApiException -> throwable
        is HttpException -> fromHttpException(throwable)
        is SocketTimeoutException -> FlexrApiException(
            statusCode = 0,
            message = "Zeitüberschreitung. Bitte Verbindung prüfen und erneut versuchen.",
        )
        is UnknownHostException -> FlexrApiException(
            statusCode = 0,
            message = "Keine Internetverbindung.",
        )
        is IOException -> FlexrApiException(
            statusCode = 0,
            message = "Verbindung fehlgeschlagen. Bitte erneut versuchen.",
        )
        else -> FlexrApiException(
            statusCode = -1,
            message = throwable.message ?: "Unbekannter Fehler.",
        )
    }

    private fun fromHttpException(exception: HttpException): FlexrApiException {
        val code = exception.code()
        val raw = runCatching { exception.response()?.errorBody()?.string() }.getOrNull()
        val detail = raw?.let { runCatching { json.parseToJsonElement(it).jsonObject["detail"] }.getOrNull() }

        var mutedUntil: Instant? = null
        var moderationReason: String? = null
        var appealHint: String? = null
        val message = when (detail) {
            is JsonPrimitive -> detail.content
            is JsonArray -> detail.mapNotNull { element ->
                runCatching { element.jsonObject["msg"]?.jsonPrimitive?.content }.getOrNull()
            }.joinToString(", ").ifBlank { defaultMessage(code) }
            is JsonObject -> {
                if (detail["reason"]?.jsonPrimitive?.content == "messaging_muted") {
                    mutedUntil = ServerTime.parse(detail["muted_until"]?.jsonPrimitive?.content)
                }
                // Sperre und Ban tragen Begründung und Widerspruchshinweis mit.
                moderationReason = detail["moderation_reason"]?.jsonPrimitive?.content
                appealHint = detail["appeal_hint"]?.jsonPrimitive?.content
                detail["message"]?.jsonPrimitive?.content ?: defaultMessage(code)
            }
            else -> defaultMessage(code)
        }
        return FlexrApiException(code, message, mutedUntil, moderationReason, appealHint)
    }

    private fun defaultMessage(code: Int): String = when (code) {
        401 -> "Ungültige oder abgelaufene Anmeldung."
        402 -> "Probemonat abgelaufen. Bitte Abo abschließen."
        403 -> "Zugriff nicht möglich."
        404 -> "Nicht gefunden."
        409 -> "Bereits vorhanden."
        429 -> "Zu viele Versuche. Bitte kurz warten."
        in 500..599 -> "Serverfehler. Bitte später erneut versuchen."
        else -> "Fehler ($code)"
    }
}

/**
 * Einheitlicher Aufruf-Wrapper für Repositories: fängt alles ab, was Retrofit
 * werfen kann, und liefert eine typisierte Ausnahme im Fehlerfall.
 */
suspend inline fun <T> apiCall(crossinline block: suspend () -> T): T =
    try {
        block()
    } catch (throwable: Throwable) {
        if (throwable is kotlinx.coroutines.CancellationException) throw throwable
        throw ApiErrorParser.toFlexrException(throwable)
    }
