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

    /// Die aktuelle Sprache. Änderungen zeichnen die Oberfläche neu — jede View
    /// liest ihre Texte über [strings], und das hängt an dieser Eigenschaft.
    var language: AppLanguage {
        didSet {
            guard language != oldValue else { return }
            defaults.set(language.rawValue, forKey: Self.key)
            // Netzwerkstapel und Hintergrunddienste kennen die Oberfläche
            // nicht und holen ihre Texte aus einer statischen Fassung — die
            // muss mitwandern. Siehe die Begründung bei `FlexrStrings.current`.
            FlexrStrings.current = strings
        }
    }

    /// Texttabelle in der gewählten Sprache.
    var strings: FlexrStrings { FlexrStrings(language: language) }

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        let saved = defaults.string(forKey: Self.key).flatMap(AppLanguage.init(rawValue:))
        language = saved ?? AppLanguage.detect()
        FlexrStrings.current = strings
    }
}
