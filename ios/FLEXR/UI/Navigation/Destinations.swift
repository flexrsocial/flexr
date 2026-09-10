import SwiftUI

/// Die vier Hauptbereiche der Tab-Leiste.
enum TopLevelDestination: String, CaseIterable, Identifiable, Hashable {
    case swipe, matches, chats, account

    var id: String { rawValue }

    /// Beschriftung als Textschluessel — aufgeloest wird erst dort, wo
    /// gezeichnet wird; nur da ist die gewaehlte Sprache bekannt.
    var labelKey: L {
        switch self {
        case .swipe: .navSwipe
        case .matches: .navMatches
        case .chats: .navChats
        case .account: .navAccount
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
    /// FLEXR Premium. Früher ein eigener Navigationsbaum (der gesperrte
    /// Zustand nach Ablauf des Probemonats), seit dem 10.09.2026 ein normales
    /// Ziel aus dem Kontobereich.
    case premium
    case legal(LegalDocument)
}

enum LegalDocument: String, CaseIterable, Identifiable, Hashable {
    case faq, impressum, datenschutz, agb, sicherheit, nutzungsrichtlinien, strafverfolgung

    var id: String { rawValue }

    /// Nur der Titel der Ansicht ist uebersetzt — der Inhalt in
    /// `UI/Legal/LegalContent.swift` bleibt bewusst auf Deutsch, weil er in
    /// dieser Fassung verbindlich ist.
    var titleKey: L {
        switch self {
        case .faq: .legalFaq
        case .impressum: .legalImpressum
        case .datenschutz: .legalDatenschutz
        case .agb: .legalAgb
        case .sicherheit: .legalSicherheit
        case .nutzungsrichtlinien: .legalNutzungsrichtlinien
        case .strafverfolgung: .legalStrafverfolgung
        }
    }
}
