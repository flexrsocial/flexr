package flexr.social.app.core.locale

import java.util.Locale
import java.util.TimeZone

/**
 * Die beiden Sprachen der App.
 *
 * Deutsch ist die Ausgangs- und Standardsprache: `res/values/strings.xml`
 * traegt die deutschen Texte, `res/values-en/strings.xml` die englischen.
 * Fehlt eine englische Uebersetzung, faellt Android von selbst auf die
 * deutsche Fassung zurueck.
 */
enum class AppLanguage(val code: String, val locale: Locale) {
    GERMAN("de", Locale.forLanguageTag("de-AT")),
    ENGLISH("en", Locale.ENGLISH),
    ;

    companion object {

        val DEFAULT = GERMAN

        fun fromCode(code: String?): AppLanguage? =
            entries.firstOrNull { it.code == code }

        /**
         * Zeitzonen des deutschsprachigen Raums. Buesingen (deutsche Exklave in
         * der Schweiz) und Vaduz (Liechtenstein) sind eigene IANA-Zonen und
         * wuerden sonst als "nicht DACH" durchfallen.
         */
        private val DACH_ZONES = setOf(
            "Europe/Vienna", "Europe/Berlin", "Europe/Zurich",
            "Europe/Busingen", "Europe/Vaduz",
        )

        private val DACH_COUNTRIES = setOf("AT", "DE", "CH", "LI")

        /**
         * Sprache beim ersten Start, wenn der Nutzer noch nichts gewaehlt hat.
         *
         * Vorgabe ist der Standort ("DACH-Raum -> Deutsch"), nicht die
         * Systemsprache: ein in Wien gekauftes Geraet mit englischer
         * Systemsprache steht trotzdem auf Europe/Vienna. Erst wenn der Ort
         * nichts hergibt, entscheidet die Systemsprache — und wer sein Geraet
         * auf Deutsch gestellt hat, bekommt Deutsch auch aus Mailand.
         * Englisch ist der Rueckfall fuer alles Uebrige.
         *
         * Dieselbe Reihenfolge wie in der Web-App (frontend/i18n.js).
         */
        fun detect(
            timeZoneId: String = TimeZone.getDefault().id,
            deviceLocale: Locale = Locale.getDefault(),
        ): AppLanguage {
            if (timeZoneId in DACH_ZONES) return GERMAN
            if (deviceLocale.country.uppercase() in DACH_COUNTRIES) return GERMAN
            if (deviceLocale.language.lowercase() == "de") return GERMAN
            return if (deviceLocale.language.isBlank()) DEFAULT else ENGLISH
        }
    }
}
