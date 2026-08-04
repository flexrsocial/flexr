import SwiftUI

/// Die vier Hauptbereiche der Tab-Leiste.
enum TopLevelDestination: String, CaseIterable, Identifiable, Hashable {
    case swipe, matches, chats, account

    var id: String { rawValue }

    var label: String {
        switch self {
        case .swipe: "Swipe"
        case .matches: "Matches"
        case .chats: "Chats"
        case .account: "Konto"
        }
    }

    var icon: FlexrGlyph.Kind {
        switch self {
        case .swipe: .dumbbell
        case .matches: .symbol(FlexrIcon.matches)
        case .chats: .symbol(FlexrIcon.chats)
        case .account: .symbol(FlexrIcon.account)
        }
    }
}

/// Ziele innerhalb eines Tabs. Typisierte Routen statt String-Bastelei an den
/// Aufrufstellen — die Entsprechung von `Routes` in der Android-App.
enum Route: Hashable {
    case chat(matchID: String)
    case matchProfile(matchID: String)
    case verification
    case legal(LegalDocument)
}

enum LegalDocument: String, CaseIterable, Identifiable, Hashable {
    case faq, impressum, datenschutz, agb, sicherheit, nutzungsrichtlinien, strafverfolgung

    var id: String { rawValue }

    var title: String {
        switch self {
        case .faq: "Häufige Fragen"
        case .impressum: "Impressum"
        case .datenschutz: "Datenschutzerklärung"
        case .agb: "Allgemeine Geschäftsbedingungen"
        case .sicherheit: "Sicherheitstipps"
        case .nutzungsrichtlinien: "Nutzungsrichtlinien"
        case .strafverfolgung: "Strafverfolgungsbehörden"
        }
    }
}
