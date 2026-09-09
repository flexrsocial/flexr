package flexr.social.app.core.network

import androidx.annotation.StringRes
import flexr.social.app.R
import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.locale.AppStrings
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
    /** Strukturiertes Detail-Objekt des Backends, z.B. "account_deleted" bei
     *  einem Login innerhalb der 30-Tage-Karenzzeit (siehe routers/auth.py). */
    val code: String? = null,
) : Exception(message) {

    val isUnauthorized: Boolean get() = statusCode == 401
    val isPaymentRequired: Boolean get() = statusCode == 402
    val isMessagingMuted: Boolean get() = mutedUntil != null
    val isAccountDeleted: Boolean get() = code == "account_deleted"
}

object ApiErrorParser {

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    /**
     * Texte fuer die Standardmeldungen, gesetzt in `FlexrApplication.onCreate`.
     *
     * Bewusst ein setzbares Feld und kein Konstruktorargument: [apiCall] ist
     * eine inline-Funktion auf oberster Ebene und wird aus jedem Repository
     * gerufen. Eine Abhaengigkeit hier muesste durch saemtliche Repositories
     * und deren Tests gefaedelt werden, ohne dass irgendwo eine Entscheidung
     * davon abhinge.
     *
     * Bleibt das Feld leer — in reinen JVM-Tests ist das der Normalfall —,
     * gelten die deutschen Texte weiter unten. Sie sind die Ausgangssprache
     * und stehen wortgleich in `res/values/strings.xml`; `ApiErrorParserTest`
     * prueft sie in dieser Fassung.
     */
    @Volatile
    var strings: AppStrings? = null

    private fun text(@StringRes id: Int, fallbackDe: String): String =
        strings?.get(id) ?: fallbackDe

    private fun text(@StringRes id: Int, fallbackDe: String, arg: Any): String =
        strings?.get(id, arg) ?: fallbackDe

    fun toFlexrException(throwable: Throwable): FlexrApiException = when (throwable) {
        is FlexrApiException -> throwable
        is HttpException -> fromHttpException(throwable)
        is SocketTimeoutException -> FlexrApiException(
            statusCode = 0,
            message = text(R.string.error_timeout, "Zeitüberschreitung. Bitte Verbindung prüfen und erneut versuchen."),
        )
        is UnknownHostException -> FlexrApiException(
            statusCode = 0,
            message = text(R.string.error_no_internet, "Keine Internetverbindung."),
        )
        is IOException -> FlexrApiException(
            statusCode = 0,
            message = text(R.string.error_connection, "Verbindung fehlgeschlagen. Bitte erneut versuchen."),
        )
        else -> FlexrApiException(
            statusCode = -1,
            message = throwable.message ?: text(R.string.error_unknown, "Unbekannter Fehler."),
        )
    }

    private fun fromHttpException(exception: HttpException): FlexrApiException {
        val code = exception.code()
        val raw = runCatching { exception.response()?.errorBody()?.string() }.getOrNull()
        val detail = raw?.let { runCatching { json.parseToJsonElement(it).jsonObject["detail"] }.getOrNull() }

        var mutedUntil: Instant? = null
        var moderationReason: String? = null
        var appealHint: String? = null
        var errorCode: String? = null
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
                errorCode = detail["code"]?.jsonPrimitive?.content
                detail["message"]?.jsonPrimitive?.content ?: defaultMessage(code)
            }
            else -> defaultMessage(code)
        }
        return FlexrApiException(code, message, mutedUntil, moderationReason, appealHint, errorCode)
    }

    private fun defaultMessage(code: Int): String = when (code) {
        401 -> text(R.string.error_unauthorized, "Ungültige oder abgelaufene Anmeldung.")
        402 -> text(R.string.error_payment_required, "Probemonat abgelaufen. Bitte Abo abschließen.")
        403 -> text(R.string.error_forbidden, "Zugriff nicht möglich.")
        404 -> text(R.string.error_not_found, "Nicht gefunden.")
        409 -> text(R.string.error_conflict, "Bereits vorhanden.")
        429 -> text(R.string.error_rate_limited, "Zu viele Versuche. Bitte kurz warten.")
        in 500..599 -> text(R.string.error_server, "Serverfehler. Bitte später erneut versuchen.")
        else -> text(R.string.error_http, "Fehler ($code)", code)
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
