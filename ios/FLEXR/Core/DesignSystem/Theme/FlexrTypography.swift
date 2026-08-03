import CoreText
import SwiftUI
import UIKit

/// Schriftfamilien der Marke.
///
/// Es sind dieselben drei Schnitte wie im Web und in der Android-App: Oswald
/// für Überschriften, Work Sans für Fließtext, JetBrains Mono für technische
/// Labels — mitgeliefert als Variable Fonts, damit die App ohne Netz korrekt
/// aussieht.
///
/// iOS kennt keine Compose-`FontVariation`; die Gewichtsachse wird deshalb
/// direkt über das Font-Descriptor-Attribut `kCTFontVariationAttribute` gesetzt.
/// Ohne das läge jeder Schnitt auf seinem Standardgewicht (400) und die
/// Hierarchie wäre weg.
enum FlexrFont {

    private enum PostScriptName {
        static let oswald = "Oswald-Regular"
        static let workSans = "WorkSans-Regular"
        static let jetBrainsMono = "JetBrainsMono-Regular"
    }

    /// Achsenkennung 'wght' als Vier-Byte-Zahl, wie CoreText sie erwartet.
    private static let weightAxis = 0x77676874

    private static let cache = NSCache<NSString, UIFont>()

    static func oswald(_ size: CGFloat, weight: CGFloat = 500) -> Font {
        Font(uiFont(PostScriptName.oswald, size: size, weight: weight))
    }

    static func workSans(_ size: CGFloat, weight: CGFloat = 400) -> Font {
        Font(uiFont(PostScriptName.workSans, size: size, weight: weight))
    }

    static func mono(_ size: CGFloat, weight: CGFloat = 500) -> Font {
        Font(uiFont(PostScriptName.jetBrainsMono, size: size, weight: weight))
    }

    static func uiFont(_ postScriptName: String, size: CGFloat, weight: CGFloat) -> UIFont {
        let key = "\(postScriptName)|\(size)|\(weight)" as NSString
        if let cached = cache.object(forKey: key) { return cached }

        let descriptor = UIFontDescriptor(fontAttributes: [
            .name: postScriptName,
            UIFontDescriptor.AttributeName(rawValue: kCTFontVariationAttribute as String):
                [weightAxis: weight],
        ])
        let base = UIFont(descriptor: descriptor, size: size)
        // Systemschriftgröße respektieren, aber gedeckelt — die Karten und die
        // Chat-Blasen vertragen keine beliebig große Schrift.
        let scaled = UIFontMetrics.default.scaledFont(for: base, maximumPointSize: size * 1.5)
        cache.setObject(scaled, forKey: key)
        return scaled
    }
}

/// Ein Textstil der Marke: Schrift, Sperrung und Zeilenabstand zusammen.
///
/// SwiftUI trennt Sperrung und Zeilenabstand von der `Font`; damit ein Stil
/// trotzdem an einer Stelle steht, bündelt ihn dieser Typ und wird über
/// `.flexrText(_:)` angewandt.
struct FlexrTextStyle {
    let font: Font
    var tracking: CGFloat = 0
    var lineSpacing: CGFloat = 0
}

extension FlexrTextStyle {
    // Display / Headline: Oswald, leichte Sperrung — wie `h1,h2,h3,.display` im Web.
    static let displayLarge = FlexrTextStyle(font: .flexrOswald(40, weight: 700), tracking: 0.8)
    static let displayMedium = FlexrTextStyle(font: .flexrOswald(30, weight: 700), tracking: 0.6)
    static let headlineLarge = FlexrTextStyle(font: .flexrOswald(26, weight: 600), tracking: 0.52)
    static let headlineMedium = FlexrTextStyle(font: .flexrOswald(22, weight: 600), tracking: 0.44)
    static let headlineSmall = FlexrTextStyle(font: .flexrOswald(17, weight: 600), tracking: 0.68, lineSpacing: 1)

    static let titleLarge = FlexrTextStyle(font: .flexrOswald(20, weight: 500), lineSpacing: 1)
    static let titleMedium = FlexrTextStyle(font: .flexrOswald(16, weight: 500), tracking: 0.16, lineSpacing: 2)
    static let titleSmall = FlexrTextStyle(font: .flexrWorkSans(14, weight: 600), lineSpacing: 2)

    static let bodyLarge = FlexrTextStyle(font: .flexrWorkSans(15), lineSpacing: 4)
    static let bodyMedium = FlexrTextStyle(font: .flexrWorkSans(14), lineSpacing: 4)
    static let bodySmall = FlexrTextStyle(font: .flexrWorkSans(13), lineSpacing: 4)

    static let labelLarge = FlexrTextStyle(font: .flexrOswald(15, weight: 600), tracking: 0.9)
    static let labelMedium = FlexrTextStyle(font: .flexrMono(11), tracking: 0.66, lineSpacing: 1)
    static let labelSmall = FlexrTextStyle(font: .flexrMono(10), tracking: 0.8, lineSpacing: 1)

    /// `.eyebrow` aus dem Web: Mono, gesperrt, Versalien, Akzentfarbe.
    static let eyebrow = FlexrTextStyle(font: .flexrMono(11), tracking: 1.32, lineSpacing: 1)
    /// `.mono` — technische Werte (Entfernung, Radius, Zeitstempel).
    static let mono = FlexrTextStyle(font: .flexrMono(11), tracking: 0.22, lineSpacing: 2)
    /// Wortmarke im Header, leicht verbreitert (`.brand` im Web).
    static let brand = FlexrTextStyle(font: .flexrOswald(22, weight: 700), tracking: 1.32)

    /// Derselbe Stil in anderer Größe — die Sperrung wächst mit.
    func resized(_ points: CGFloat, weight: CGFloat, family: FlexrTextStyle.Family) -> FlexrTextStyle {
        let font: Font = switch family {
        case .oswald: .flexrOswald(points, weight: weight)
        case .workSans: .flexrWorkSans(points, weight: weight)
        case .mono: .flexrMono(points, weight: weight)
        }
        return FlexrTextStyle(font: font, tracking: tracking, lineSpacing: lineSpacing)
    }

    enum Family { case oswald, workSans, mono }
}

extension Font {
    static func flexrOswald(_ size: CGFloat, weight: CGFloat = 500) -> Font {
        FlexrFont.oswald(size, weight: weight)
    }

    static func flexrWorkSans(_ size: CGFloat, weight: CGFloat = 400) -> Font {
        FlexrFont.workSans(size, weight: weight)
    }

    static func flexrMono(_ size: CGFloat, weight: CGFloat = 500) -> Font {
        FlexrFont.mono(size, weight: weight)
    }

    /// Kurzform für Stellen, die nur eine Größe brauchen (Avatar-Initiale).
    static func flexrHeadline(size: CGFloat) -> Font { FlexrFont.oswald(size, weight: 600) }
}

extension View {
    func flexrText(_ style: FlexrTextStyle) -> some View {
        font(style.font)
            .tracking(style.tracking)
            .lineSpacing(style.lineSpacing)
    }
}
