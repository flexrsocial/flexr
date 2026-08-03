import SwiftUI

/// Markenpalette, 1:1 übernommen aus den CSS-Custom-Properties der Web-App
/// (`:root` in frontend/index.html) und deckungsgleich mit `FlexrPalette` der
/// Android-App. Die Namen bleiben bewusst gleich, damit alle drei Oberflächen
/// nachweislich dieselbe Farbwelt verwenden.
enum FlexrColor {

    static let ink = Color(hex: 0x121212)          // --ink
    static let surface = Color(hex: 0x1C1C1C)      // --surface
    static let surface2 = Color(hex: 0x242424)     // --surface-2
    static let surface3 = Color(hex: 0x2C2C2C)     // --surface-3
    static let steel = Color(hex: 0x3A3A3A)        // --steel
    static let hairline = Color(white: 1, opacity: 0.07)  // --hairline

    static let chalk = Color(hex: 0xEDE9E2)        // --chalk
    static let chalkDim = Color(hex: 0xA8A49B)     // --chalk-dim

    static let plate = Color(hex: 0xFF5A1F)        // --plate
    static let plateBright = Color(hex: 0xFF7A45)  // --plate-bright
    static let plateDim = Color(hex: 0xC94515)     // --plate-dim
    static let plateDeep = Color(hex: 0xEF4C15)    // Endpunkt des Knopfverlaufs
    static let plateInk = Color(hex: 0x191008)     // Schrift auf orangem Grund

    static let lime = Color(hex: 0xC7FF4A)         // --lime
    static let danger = Color(hex: 0xE34848)       // --danger

    /// Logo-Rot des Wortzeichens — bewusst getrennt vom UI-Orange (siehe brand/README).
    static let brandRed = Color(hex: 0xE8412B)

    /// Blauer Haken verifizierter Profile.
    static let verified = Color(hex: 0x2D9CDB)

    /// Verlauf der primären Aktion (`.btn` im Web).
    static let plateGradient = LinearGradient(
        colors: [plateBright, plate, plateDeep],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    /// Kartenfläche im Deck und in den Listen.
    static let cardGradient = LinearGradient(
        colors: [Color(hex: 0x202020), Color(hex: 0x191919)],
        startPoint: .top,
        endPoint: .bottom
    )

    static let listItemGradient = LinearGradient(
        colors: [Color(hex: 0x1F1F1F), Color(hex: 0x1A1A1A)],
        startPoint: .top,
        endPoint: .bottom
    )
}

extension Color {
    init(hex: UInt32, opacity: Double = 1) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: opacity
        )
    }
}

/// Hintergrund der App-Fläche: entspricht dem mehrschichtigen Verlauf aus
/// `.app` im Web (orangefarbener Schleier über der Grundfarbe).
struct FlexrBackground: View {
    var body: some View {
        ZStack {
            FlexrColor.ink
            RadialGradient(
                colors: [FlexrColor.plate.opacity(0.12), .clear],
                center: UnitPoint(x: 0.12, y: -0.04),
                startRadius: 0,
                endRadius: 460
            )
        }
        .ignoresSafeArea()
    }
}
