import Foundation
import Observation

/// Gewählte Sprache, dauerhaft gespeichert.
///
/// Bewusst getrennt vom [SessionStore]: die Sprachwahl gehört dem Gerät, nicht
/// dem Konto — beim Abmelden soll sie stehen bleiben.
///
/// Solange nichts gewählt wurde, gilt [AppLanguage.detect]; ein Wechsel der
/// Systemsprache oder ein Umzug wirkt damit weiter, bis der Nutzer den Regler
/// einmal selbst bedient.
@MainActor
@Observable
final class LanguageStore {

    private static let key = "flexr_language"

    private let defaults: UserDefaults

    /// Ob der Regler auf diesem Gerät je bedient wurde.
    ///
    /// [language] verschweigt den Unterschied bewusst (es liefert dann die
    /// Vorgabe aus [AppLanguage.detect]). Beim Abgleich mit dem Profil zählt er
    /// aber: Eine Wahl auf diesem Gerät schlägt das Profil, eine bloße Vorgabe
    /// nicht.
    private(set) var hasExplicitChoice: Bool

    /// Wird nach jeder Wahl gerufen. Setzt der Einstiegspunkt (`FlexrApp`), um
    /// die Sprache ans Profil zu melden — der Speicher selbst kennt weder
    /// Netzwerk noch Repositories.
    @ObservationIgnored var onChange: ((AppLanguage) -> Void)?

    /// Läuft gerade eine Übernahme vom Profil? Dann ist die Zuweisung an
    /// [language] keine Wahl des Nutzers, und [didSet] darf weder speichern
    /// noch melden. Ohne diese Klammer müsste [adopt] die Nebenwirkungen
    /// hinterher zurücknehmen — das hinge an der Reihenfolge.
    @ObservationIgnored private var isAdopting = false

    /// Die aktuelle Sprache. Änderungen zeichnen die Oberfläche neu — jede View
    /// liest ihre Texte über [strings], und das hängt an dieser Eigenschaft.
    var language: AppLanguage {
        didSet {
            guard language != oldValue else { return }
            // Netzwerkstapel und Hintergrunddienste kennen die Oberfläche
            // nicht und holen ihre Texte aus einer statischen Fassung — die
            // muss mitwandern. Siehe die Begründung bei `FlexrStrings.current`.
            FlexrStrings.current = strings
            guard !isAdopting else { return }
            defaults.set(language.rawValue, forKey: Self.key)
            hasExplicitChoice = true
            onChange?(language)
        }
    }

    /// Texttabelle in der gewählten Sprache.
    var strings: FlexrStrings { FlexrStrings(language: language) }

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        let saved = defaults.string(forKey: Self.key).flatMap(AppLanguage.init(rawValue:))
        hasExplicitChoice = saved != nil
        language = saved ?? AppLanguage.detect()
        FlexrStrings.current = strings
    }

    /// Sprache vom Profil übernehmen, ohne daraus eine Wahl zu machen.
    ///
    /// Für den Fall „neues Gerät, nie gewählt": Die Oberfläche stellt sich um,
    /// [hasExplicitChoice] bleibt aber falsch — erst ein Griff zum Regler macht
    /// daraus eine Entscheidung dieses Geräts.
    func adopt(_ language: AppLanguage) {
        guard !hasExplicitChoice, language != self.language else { return }
        isAdopting = true
        self.language = language
        isAdopting = false
    }
}
