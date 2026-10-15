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
import java.time.temporal.ChronoUnit
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

    /** Kalendertage zwischen dem Zeitpunkt und heute: 0 = heute, 1 = gestern. */
    fun daysAgo(
        instant: Instant,
        zone: ZoneId = ZoneId.systemDefault(),
        today: LocalDate = LocalDate.now(zone),
    ): Long = ChronoUnit.DAYS.between(instant.atZone(zone).toLocalDate(), today)

    /**
     * Tagestrenner im Chatverlauf fuer Tage vor gestern ("Samstag, 10. Oktober",
     * aus einem anderen Jahr mit Jahreszahl). "Heute" und "Gestern" kommen aus
     * den Strings. Gleiche Regel wie in der Web-App (chatDayLabel).
     */
    fun formatChatDay(
        instant: Instant,
        locale: Locale,
        zone: ZoneId = ZoneId.systemDefault(),
        today: LocalDate = LocalDate.now(zone),
    ): String {
        val tag = instant.atZone(zone).toLocalDate()
        val deutsch = locale.language == "de"
        val muster = when {
            tag.year == today.year && deutsch -> "EEEE, d. MMMM"
            tag.year == today.year -> "EEEE d MMMM"
            deutsch -> "EEEE, d. MMMM yyyy"
            else -> "EEEE d MMMM yyyy"
        }
        return DateTimeFormatter.ofPattern(muster, locale).format(tag)
    }

    /**
     * Zeitpunkt der letzten Nachricht in der Chatliste: heute die Uhrzeit,
     * innerhalb einer Woche der Wochentag, sonst das Datum. "Gestern" kommt aus
     * den Strings (siehe [daysAgo]). Wie in der Web-App (chatListTimeLabel).
     */
    fun formatChatListTime(
        instant: Instant,
        locale: Locale,
        zone: ZoneId = ZoneId.systemDefault(),
        today: LocalDate = LocalDate.now(zone),
    ): String {
        val zeit = instant.atZone(zone)
        val tage = daysAgo(instant, zone, today)
        return when {
            tage <= 0 -> timeFormatter.format(zeit)
            tage < 7 -> DateTimeFormatter.ofPattern("EEE", locale).format(zeit)
            zeit.year == today.year -> DateTimeFormatter.ofPattern("dd.MM.", locale).format(zeit)
            else -> DateTimeFormatter.ofPattern("dd.MM.yy", locale).format(zeit)
        }
    }

    fun formatDay(instant: Instant): String =
        dayFormatter.format(instant.atZone(ZoneId.systemDefault()))

    /** Kalendertag ohne Zeitzone (z. B. Startboost-Stichtag), "31.12.2026". */
    fun formatDay(date: LocalDate): String = dayFormatter.format(date)

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
