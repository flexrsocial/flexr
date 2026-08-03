import SwiftUI

/// Emoji-Auswahl für Bio und Chat — dieselbe Liste und dieselbe Einfügelogik
/// wie im Web-Frontend (`initEmojiPicker`) und in der Android-App.
///
/// Bewusst eine feste Auswahl statt einer vollständigen Unicode-Tabelle: Die
/// Systemtastatur kann ohnehin alles, das Panel ist die schnelle Abkürzung zu
/// dem, was auf einer Gym-Dating-Plattform tatsächlich gebraucht wird.
enum EmojiCatalog {

    static let emojis: [String] = {
        let all = [
            // Training & Sport
            "💪", "🏋️", "🏋️‍♀️", "🤸", "🏃", "🏃‍♀️", "🚴", "🚵", "🧘", "🏊", "🥊", "🤾", "⚽",
            "🏀", "🎾", "🏐", "🏈", "⚾", "🏓", "🏸", "⛷️", "🏂", "🛹", "🧗", "🧗‍♀️", "🤼",
            "⛰️", "🥾", "🚶", "🏇", "🤺", "🎳", "🪂", "🏄", "🚣", "🤽", "🥋", "🥅",
            "🏹", "⛹️", "⛹️‍♀️", "🤹", "🕺", "💃", "🦵", "🦶", "🫀", "🫁", "🦿",
            "⏱️", "⌚", "🧢", "👟", "🩳", "🧦", "🎽", "🧊", "🩹", "🧴", "🪢", "🛼",
            // Energie & Erfolg
            "🔥", "⚡", "💥", "🎯", "🏆", "🥇", "🥈", "🥉", "💯", "✨", "🌟", "⭐",
            "🙌", "👊", "🤝", "✌️", "👏", "🤞", "💫", "🚀", "🎖️", "🏅", "📈", "🔝",
            // Stimmung & Gesichter
            "😄", "😁", "😉", "😎", "🥳", "😏", "🤓", "🙃", "😊", "😜", "🤪", "😇",
            "🫶", "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "😍", "🥰", "😘", "💕",
            "🤗", "😌", "😤", "🥵", "😅", "🤩", "🫡", "🤠",
            // Essen & Trinken
            "🍗", "🥩", "🥦", "🍳", "🥤", "☕", "🍕", "🍺", "🍔", "🌮", "🍣", "🥗",
            "🍎", "🍌", "🥑", "🍫", "🧋", "🍦", "🥞", "🍝", "🍷", "🍹", "🫐", "🥜",
            "🥛", "🧀", "🍚", "🍠", "🥕", "🫑", "🌽", "🥬", "🥒", "🍇", "🍊", "🥝",
            "🍉", "🥚", "🐟", "🍤", "🫘", "🌰", "💊", "🧂", "🥥", "🍯",
            // Lifestyle & Sonstiges
            "🎵", "🎬", "🎮", "📚", "🐶", "🐱", "🐺", "🦁", "☀️", "🌙", "🌈", "🌊",
            "✈️", "🗺️", "📍", "🎉", "🤷", "🤙", "👀", "🧠", "🛠️", "🎸", "📸", "🏝️",
            "🚗", "🏍️", "⛺", "🎿", "🃏", "🎲", "🧩", "🪩",
        ]
        var seen = Set<String>()
        return all.filter { seen.insert($0).inserted }
    }()
}

enum EmojiInsertion {

    /// Setzt ein Emoji an der Cursorposition ein und ersetzt dabei eine
    /// eventuelle Auswahl. Überschreitet das Ergebnis `maxLength`, bleibt der
    /// Text unverändert — genau wie im Web und auf Android.
    ///
    /// Gerechnet wird in UTF-16-Einheiten, weil `UITextView` seine Auswahl als
    /// `NSRange` führt; ein naives Rechnen in `Character`-Schritten würde bei
    /// jedem bereits vorhandenen Emoji danebenliegen.
    static func insert(
        _ emoji: String,
        into text: String,
        selection: NSRange,
        maxLength: Int?
    ) -> (text: String, selection: NSRange) {
        let source = text as NSString
        let start = max(0, min(selection.location, source.length))
        let length = max(0, min(selection.length, source.length - start))

        let next = source.replacingCharacters(in: NSRange(location: start, length: length), with: emoji)
        if let maxLength, next.backendLength > maxLength {
            return (text, selection)
        }
        let caret = start + (emoji as NSString).length
        return (next, NSRange(location: caret, length: 0))
    }
}

/// Aufklappbares Emoji-Raster. Die Höhe ist gedeckelt, damit das Panel in einer
/// scrollenden Spalte liegen kann, ohne den Rest der Seite zu verdrängen.
struct EmojiPickerPanel: View {

    let isExpanded: Bool
    var columns: Int = 8
    var height: CGFloat = 180
    /// Zuletzt deklariert, damit die abschließende Closure an der Aufrufstelle
    /// hier landet und nicht auf `height`.
    let onPick: (String) -> Void

    var body: some View {
        if isExpanded {
            ScrollView {
                LazyVGrid(
                    columns: Array(repeating: GridItem(.flexible(), spacing: 0), count: columns),
                    spacing: 0
                ) {
                    ForEach(EmojiCatalog.emojis, id: \.self) { emoji in
                        Button { onPick(emoji) } label: {
                            Text(emoji)
                                .font(.system(size: 19))
                                .frame(maxWidth: .infinity)
                                .aspectRatio(1, contentMode: .fit)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(6)
            }
            .frame(height: height)
            .flexrSurface(
                radius: FlexrRadius.button,
                fill: FlexrColor.surface2,
                border: FlexrColor.steel
            )
            .transition(.opacity.combined(with: .move(edge: .top)))
        }
    }
}

/// Runder Umschalter, der das Panel auf- und zuklappt.
struct EmojiToggleButton: View {

    let isExpanded: Bool
    var size: CGFloat = 34
    /// Siehe [EmojiPickerPanel]: abschließende Closure muss zuletzt stehen.
    let onToggle: () -> Void

    var body: some View {
        Button(action: onToggle) {
            ZStack {
                Circle().fill(isExpanded ? FlexrColor.surface3 : .clear)
                Image(systemName: FlexrIcon.emoji)
                    .font(.system(size: size * 0.55, weight: .medium))
                    .foregroundStyle(isExpanded ? FlexrColor.plate : FlexrColor.chalkDim)
            }
            .frame(width: size, height: size)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(isExpanded ? "Emoji-Auswahl schließen" : "Emoji einfügen")
    }
}
