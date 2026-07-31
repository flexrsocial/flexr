package flexr.social.app.core.common

import java.time.Instant
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.Period
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.util.Locale

/**
 * Das Backend liefert `datetime.utcnow()`-Werte, also ISO-Zeitstempel OHNE
 * Zeitzonenangabe, die trotzdem UTC sind. Genau wie im Web-Frontend
 * (`parseServerDate`) wird deshalb ein fehlender Offset als UTC interpretiert —
 * sonst wäre z. B. eine stundengenaue Chat-Sperre um den lokalen Offset verschoben.
 */
object ServerTime {

    fun parse(raw: String?): Instant? {
        if (raw.isNullOrBlank()) return null
        return try {
            OffsetDateTime.parse(raw).toInstant()
        } catch (_: DateTimeParseException) {
            try {
                LocalDateTime.parse(raw).toInstant(ZoneOffset.UTC)
            } catch (_: DateTimeParseException) {
                null
            }
        }
    }

    fun parseDate(raw: String?): LocalDate? =
        raw?.takeIf { it.isNotBlank() }?.let {
            try {
                LocalDate.parse(it.take(10))
            } catch (_: DateTimeParseException) {
                null
            }
        }

    fun formatDate(date: LocalDate): String = date.format(DateTimeFormatter.ISO_LOCAL_DATE)

    /** Alter aus dem Geburtsdatum — das Backend rechnet identisch. */
    fun ageFrom(birthdate: LocalDate, today: LocalDate = LocalDate.now()): Int =
        Period.between(birthdate, today).years

    private val timeFormatter = DateTimeFormatter.ofPattern("HH:mm", Locale.GERMAN)
    private val dayFormatter = DateTimeFormatter.ofPattern("dd.MM.yyyy", Locale.GERMAN)
    private val dateTimeFormatter = DateTimeFormatter.ofPattern("dd.MM.yyyy, HH:mm", Locale.GERMAN)
    private val birthdateFormatter = DateTimeFormatter.ofPattern("dd.MM.yyyy", Locale.GERMAN)

    fun formatTime(instant: Instant): String =
        timeFormatter.format(instant.atZone(ZoneId.systemDefault()))

    fun formatDay(instant: Instant): String =
        dayFormatter.format(instant.atZone(ZoneId.systemDefault()))

    fun formatDateTime(instant: Instant): String =
        dateTimeFormatter.format(instant.atZone(ZoneId.systemDefault()))

    fun formatBirthdate(date: LocalDate): String = birthdateFormatter.format(date)

    /** Verbleibende volle Tage bis zum Zeitpunkt, nie negativ (wie `Math.ceil` im Web). */
    fun daysUntil(instant: Instant, now: Instant = Instant.now()): Int {
        val millis = instant.toEpochMilli() - now.toEpochMilli()
        if (millis <= 0) return 0
        return Math.ceil(millis / 86_400_000.0).toInt()
    }
}
