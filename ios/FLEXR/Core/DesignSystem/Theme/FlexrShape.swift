import SwiftUI

/// Eckenradien der Marke — Gegenstück zu `FlexrShapes` (Material 3) der
/// Android-App. Die durchgehende Verwendung dieser Werte hält Karten, Felder
/// und Dialoge auf beiden Plattformen gleich.
enum FlexrRadius {
    static let extraSmall: CGFloat = 7
    static let small: CGFloat = 10
    static let medium: CGFloat = 14
    static let large: CGFloat = 20
    static let extraLarge: CGFloat = 26
    /// Knöpfe und Eingabezeile im Chat.
    static let button: CGFloat = 12
    static let inputBar: CGFloat = 26
}

extension View {
    /// Fläche im Markenstil: abgerundet, gefüllt, mit feiner Umrandung.
    func flexrSurface(
        radius: CGFloat = FlexrRadius.medium,
        fill: Color = FlexrColor.surface,
        border: Color = FlexrColor.hairline,
        borderWidth: CGFloat = 1
    ) -> some View {
        background(
            RoundedRectangle(cornerRadius: radius, style: .continuous).fill(fill)
        )
        .overlay(
            RoundedRectangle(cornerRadius: radius, style: .continuous)
                .strokeBorder(border, lineWidth: borderWidth)
        )
        .clipShape(RoundedRectangle(cornerRadius: radius, style: .continuous))
    }
}
