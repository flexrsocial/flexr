import Foundation

/// Die beiden Sprachen der App.
///
/// Deutsch ist die Ausgangssprache: [FlexrStrings] trägt den deutschen Text als
/// Original, Englisch als Übersetzung. Fehlt ein englischer Eintrag, fällt die
/// Suche auf den deutschen zurück statt auf den nackten Schlüssel — eine
/// vergessene Übersetzung sieht dann nach deutschem Text aus und nicht nach
/// einem Fehler.
enum AppLanguage: String, CaseIterable, Sendable {
    case german = "de"
    case english = "en"

    /// Kurzform für den Sprachregler.
    var badge: String { rawValue.uppercased() }

    /// Zeitzonen des deutschsprachigen Raums. Büsingen (deutsche Exklave in der
    /// Schweiz) und Vaduz (Liechtenstein) sind eigene IANA-Zonen und fielen
    /// sonst als „nicht DACH" durch.
    private static let dachZones: Set<String> = [
        "Europe/Vienna", "Europe/Berlin", "Europe/Zurich",
        "Europe/Busingen", "Europe/Vaduz",
    ]

    private static let dachRegions: Set<String> = ["AT", "DE", "CH", "LI"]

    /// Sprache beim ersten Start, solange der Nutzer nichts gewählt hat.
    ///
    /// Vorgabe ist der Standort („DACH-Raum → Deutsch"), nicht die
    /// Systemsprache: ein in Wien gekauftes Gerät mit englischer Systemsprache
    /// steht trotzdem auf Europe/Vienna. Erst wenn der Ort nichts hergibt,
    /// entscheidet die Systemsprache — und wer sein Gerät auf Deutsch gestellt
    /// hat, bekommt Deutsch auch aus Mailand. Englisch ist der Rückfall für
    /// alles Übrige.
    ///
    /// Dieselbe Reihenfolge wie in der Web-App (`frontend/i18n.js`) und in der
    /// Android-Fassung (`AppLanguage.detect`).
    static func detect(
        timeZoneIdentifier: String = TimeZone.current.identifier,
        locale: Locale = .current
    ) -> AppLanguage {
        if dachZones.contains(timeZoneIdentifier) { return .german }
        if let region = locale.region?.identifier.uppercased(), dachRegions.contains(region) {
            return .german
        }
        if locale.language.languageCode?.identifier.lowercased() == "de" { return .german }
        return .english
    }
}
