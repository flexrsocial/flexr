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

    /// Verbleibende volle Tage bis zum Zeitpunkt, nie negativ (wie `Math.ceil` im Web).
    static func daysUntil(_ date: Date, now: Date = Date()) -> Int {
        let seconds = date.timeIntervalSince(now)
        if seconds <= 0 { return 0 }
        return Int(ceil(seconds / 86_400))
    }
}
