import Foundation

/// Das Backend liefert `datetime.utcnow()`-Werte, also ISO-Zeitstempel OHNE
/// Zeitzonenangabe, die trotzdem UTC sind. Genau wie im Web-Frontend
/// (`parseServerDate`) und in der Android-App wird deshalb ein fehlender Offset
/// als UTC interpretiert — sonst wäre z. B. eine stundengenaue Chat-Sperre um
/// den lokalen Offset verschoben.
enum ServerTime {

    // MARK: - Parsen

    private static let offsetParsers: [ISO8601DateFormatter] = {
        let withFraction = ISO8601DateFormatter()
        withFraction.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let plain = ISO8601DateFormatter()
        plain.formatOptions = [.withInternetDateTime]
        return [withFraction, plain]
    }()

    /// Ohne Offset: als UTC lesen. Bruchteile sind optional, deshalb zwei Muster.
    private static let naiveParsers: [DateFormatter] = {
        ["yyyy-MM-dd'T'HH:mm:ss.SSSSSS", "yyyy-MM-dd'T'HH:mm:ss.SSS", "yyyy-MM-dd'T'HH:mm:ss"]
            .map { format in
                let formatter = DateFormatter()
                formatter.locale = Locale(identifier: "en_US_POSIX")
                formatter.timeZone = TimeZone(secondsFromGMT: 0)
                formatter.dateFormat = format
                return formatter
            }
    }()

    static func parse(_ raw: String?) -> Date? {
        guard let raw, !raw.trimmingCharacters(in: .whitespaces).isEmpty else { return nil }
        for parser in offsetParsers {
            if let date = parser.date(from: raw) { return date }
        }
        for parser in naiveParsers {
            if let date = parser.date(from: raw) { return date }
        }
        return nil
    }

    private static let isoDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    /// Reines Datum (Geburtsdatum). Zeitzonenfrei gehalten: als UTC-Mitternacht.
    static func parseDate(_ raw: String?) -> Date? {
        guard let raw, raw.count >= 10 else { return nil }
        return isoDateFormatter.date(from: String(raw.prefix(10)))
    }

    static func formatDate(_ date: Date) -> String { isoDateFormatter.string(from: date) }

    // MARK: - Alter

    private static var utcCalendar: Calendar = {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(secondsFromGMT: 0)!
        return calendar
    }()

    /// Alter aus dem Geburtsdatum — das Backend rechnet identisch.
    static func age(from birthdate: Date, today: Date = Date()) -> Int {
        let birth = utcCalendar.startOfDay(for: birthdate)
        let now = utcCalendar.startOfDay(for: today)
        return utcCalendar.dateComponents([.year], from: birth, to: now).year ?? 0
    }

    /// Spätestes bzw. frühestes zulässiges Geburtsdatum für die Altersgrenzen.
    static func birthdate(yearsAgo years: Int, from today: Date = Date()) -> Date {
        utcCalendar.date(byAdding: .year, value: -years, to: utcCalendar.startOfDay(for: today))
            ?? today
    }

    // MARK: - Anzeige

    private static func localFormatter(_ format: String) -> DateFormatter {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "de_AT")
        formatter.dateFormat = format
        return formatter
    }

    private static let timeFormatter = localFormatter("HH:mm")
    private static let dayFormatter = localFormatter("dd.MM.yyyy")
    private static let dateTimeFormatter = localFormatter("dd.MM.yyyy, HH:mm")

    static func formatTime(_ date: Date) -> String { timeFormatter.string(from: date) }

    static func formatDay(_ date: Date) -> String { dayFormatter.string(from: date) }

    static func formatDateTime(_ date: Date) -> String { dateTimeFormatter.string(from: date) }

    /// Geburtsdatum wird als UTC-Mitternacht gehalten — sonst kippt die Anzeige
    /// in Zeitzonen westlich von Greenwich auf den Vortag.
    private static let birthdateFormatter: DateFormatter = {
        let formatter = localFormatter("dd.MM.yyyy")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        return formatter
    }()

    static func formatBirthdate(_ date: Date) -> String { birthdateFormatter.string(from: date) }

    /// Reiner Kalendertag aus `parseDate` (UTC-Mitternacht), z. B. der
    /// Startboost-Stichtag. In UTC formatiert wie das Geburtsdatum, sonst
    /// rutschte der Tag in Zeitzonen westlich von UTC um einen zurück.
    static func formatCalendarDay(_ date: Date, plusDays days: Int = 0) -> String {
        birthdateFormatter.string(from: date.addingTimeInterval(TimeInterval(days * 86_400)))
    }

    /// Verbleibende volle Tage bis zum Zeitpunkt, nie negativ (wie `Math.ceil` im Web).
    static func daysUntil(_ date: Date, now: Date = Date()) -> Int {
        let seconds = date.timeIntervalSince(now)
        if seconds <= 0 { return 0 }
        return Int(ceil(seconds / 86_400))
    }

    // MARK: - Chat

    /// Kalendertage zwischen dem Zeitpunkt und heute: 0 = heute, 1 = gestern.
    static func daysAgo(_ date: Date, now: Date = Date(), calendar: Calendar = .current) -> Int {
        let tag = calendar.startOfDay(for: date)
        let heute = calendar.startOfDay(for: now)
        return calendar.dateComponents([.day], from: tag, to: heute).day ?? 0
    }

    private static func chatFormatter(
        _ format: String,
        language: AppLanguage,
        calendar: Calendar
    ) -> DateFormatter {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.timeZone = calendar.timeZone
        formatter.locale = Locale(identifier: language == .german ? "de_AT" : "en_GB")
        formatter.dateFormat = format
        return formatter
    }

    /// Tagestrenner im Chatverlauf fuer Tage vor gestern ("Samstag, 10. Oktober",
    /// aus einem anderen Jahr mit Jahreszahl). "Heute" und "Gestern" kommen aus
    /// den Texten. Gleiche Regel wie in der Web-App (chatDayLabel) und auf Android.
    static func formatChatDay(
        _ date: Date,
        language: AppLanguage,
        now: Date = Date(),
        calendar: Calendar = .current
    ) -> String {
        let gleichesJahr = calendar.component(.year, from: date) == calendar.component(.year, from: now)
        let format: String
        if language == .german {
            format = gleichesJahr ? "EEEE, d. MMMM" : "EEEE, d. MMMM yyyy"
        } else {
            format = gleichesJahr ? "EEEE d MMMM" : "EEEE d MMMM yyyy"
        }
        return chatFormatter(format, language: language, calendar: calendar).string(from: date)
    }

    /// Zeitpunkt der letzten Nachricht in der Chatliste: heute die Uhrzeit,
    /// innerhalb einer Woche der Wochentag, sonst das Datum. "Gestern" kommt
    /// aus den Texten (siehe [daysAgo]). Wie in der Web-App (chatListTimeLabel).
    static func formatChatListTime(
        _ date: Date,
        language: AppLanguage,
        now: Date = Date(),
        calendar: Calendar = .current
    ) -> String {
        let tage = daysAgo(date, now: now, calendar: calendar)
        let format: String
        if tage <= 0 {
            format = "HH:mm"
        } else if tage < 7 {
            format = "EEE"
        } else if calendar.component(.year, from: date) == calendar.component(.year, from: now) {
            format = "dd.MM."
        } else {
            format = "dd.MM.yy"
        }
        return chatFormatter(format, language: language, calendar: calendar).string(from: date)
    }
}
