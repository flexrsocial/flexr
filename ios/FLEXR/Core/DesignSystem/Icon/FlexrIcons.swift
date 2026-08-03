import SwiftUI

/// Marken-Symbol: die FLEXR-Hantel — dieselbe Geometrie wie in der Android-App
/// (zwei schmale äußere Scheiben, zwei breite innere, durchgehender Steg).
/// Als Pfad ist es in jeder Größe scharf und nimmt die Vordergrundfarbe an.
///
/// Etwas leichter gestrichen als das Launcher-Icon, damit es bei 22 pt in der
/// Tab-Leiste nicht zuläuft.
struct FlexrDumbbell: View {

    /// Streckenzüge im 24×24-Raster: x, oben, unten, Strichstärke.
    private static let plates: [(x: CGFloat, top: CGFloat, bottom: CGFloat, width: CGFloat)] = [
        (4.2, 7.2, 16.8, 1.9),    // äußere Scheibe links
        (8.2, 4.6, 19.4, 2.6),    // innere Scheibe links
        (15.8, 4.6, 19.4, 2.6),   // innere Scheibe rechts
        (19.8, 7.2, 16.8, 1.9),   // äußere Scheibe rechts
    ]

    var body: some View {
        GeometryReader { geometry in
            let unit = min(geometry.size.width, geometry.size.height) / 24
            ZStack {
                ForEach(Self.plates.indices, id: \.self) { index in
                    let plate = Self.plates[index]
                    Path { path in
                        path.move(to: CGPoint(x: plate.x * unit, y: plate.top * unit))
                        path.addLine(to: CGPoint(x: plate.x * unit, y: plate.bottom * unit))
                    }
                    .stroke(
                        style: StrokeStyle(lineWidth: plate.width * unit, lineCap: .round, lineJoin: .round)
                    )
                }
                Path { path in
                    path.move(to: CGPoint(x: 3.4 * unit, y: 12 * unit))
                    path.addLine(to: CGPoint(x: 20.6 * unit, y: 12 * unit))
                }
                .stroke(style: StrokeStyle(lineWidth: 2 * unit, lineCap: .round))
            }
        }
        .aspectRatio(1, contentMode: .fit)
    }
}

/// Symbolsatz der App an einer Stelle gebündelt.
///
/// Wo Apple bereits ein passendes, den Nutzern vertrautes SF Symbol liefert,
/// wird es verwendet — das ist auf iOS die richtige Wahl gegenüber
/// nachgebauten Material- oder Web-Icons.
enum FlexrIcon {
    static let matches = "heart.fill"
    static let chats = "bubble.left.and.bubble.right.fill"
    static let account = "person.fill"
    static let like = "heart.fill"
    static let pass = "xmark"
    static let unmatch = "heart.slash.fill"
    static let report = "flag"
    static let block = "nosign"
    static let back = "chevron.left"
    static let forward = "chevron.right"
    static let send = "paperplane.fill"
    static let more = "ellipsis"
    static let camera = "camera.fill"
    static let locked = "lock.fill"
    static let place = "mappin.and.ellipse"
    static let close = "xmark"
    static let emoji = "face.smiling"
    static let search = "magnifyingglass"
    static let add = "plus"
    static let remove = "minus"
    static let check = "checkmark"
    static let warning = "exclamationmark.triangle.fill"
    static let eye = "eye"
    static let eyeOff = "eye.slash"
}

/// Ein Symbol in fester Kantenlänge — Hantel oder SF Symbol.
struct FlexrGlyph: View {

    enum Kind: Equatable {
        case dumbbell
        case symbol(String)
    }

    let kind: Kind
    var size: CGFloat = 20

    init(_ kind: Kind, size: CGFloat = 20) {
        self.kind = kind
        self.size = size
    }

    init(_ symbol: String, size: CGFloat = 20) {
        self.kind = .symbol(symbol)
        self.size = size
    }

    var body: some View {
        switch kind {
        case .dumbbell:
            FlexrDumbbell().frame(width: size, height: size)
        case .symbol(let name):
            Image(systemName: name)
                .font(.system(size: size * 0.86, weight: .semibold))
                .frame(width: size, height: size)
        }
    }
}
