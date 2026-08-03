import SwiftUI

/// Woher ein angezeigtes Bild stammt.
enum PhotoImageSource: Equatable, Hashable {
    /// Foto aus dem Objekt-Storage — geht über den [ImageStore].
    case remote(String)
    /// Bereits im Speicher: Vorschau im Onboarding, Verifizierungs-Selfie.
    case data(Data)

    init?(_ urlString: String?) {
        guard let urlString, !urlString.isEmpty else { return nil }
        self = .remote(urlString)
    }
}

/// Bildanzeige mit Platzhalter und weichem Einblenden.
///
/// Entspricht `AsyncImage` von Coil in der Android-App: Speicher- und
/// Plattencache liegen im [ImageStore], hier steht nur die Darstellung.
struct PhotoImage: View {

    let source: PhotoImageSource?
    var contentMode: ContentMode = .fill
    /// Entsprechung der `contentDescription` auf Android. Ohne sie bleibt das
    /// Foto für VoiceOver stumm — und Fotos sind der Inhalt dieser App.
    var accessibilityLabel: String?

    @State private var image: UIImage?
    @State private var isLoading = false

    var body: some View {
        ZStack {
            FlexrColor.surface2
            if let image {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: contentMode)
                    .transition(.opacity)
            }
        }
        .clipped()
        .task(id: source) { await load() }
        .animation(.easeOut(duration: 0.2), value: image != nil)
        .accessibilityElement()
        .accessibilityLabel(accessibilityLabel ?? "")
        .accessibilityAddTraits(accessibilityLabel == nil ? [] : .isImage)
        .accessibilityHidden(accessibilityLabel == nil)
    }

    private func load() async {
        guard let source else {
            image = nil
            return
        }
        switch source {
        case .data(let data):
            image = UIImage(data: data)
        case .remote(let urlString):
            if isLoading { return }
            isLoading = true
            let loaded = await ImageStore.shared.image(for: urlString)
            isLoading = false
            image = loaded
        }
    }
}

/// Runder Avatar mit Initiale als Rückfallebene.
struct AvatarImage: View {

    let source: PhotoImageSource?
    let name: String
    var size: CGFloat = 54
    var ringColor: Color?
    var ringWidth: CGFloat = 2
    var accessibilityLabel: String?

    var body: some View {
        ZStack {
            if source != nil {
                PhotoImage(source: source, accessibilityLabel: accessibilityLabel)
            } else {
                FlexrColor.surface2
                Text(String(name.prefix(1)).uppercased())
                    .font(.flexrHeadline(size: size * 0.4))
                    .foregroundStyle(FlexrColor.chalkDim)
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
        .overlay {
            if let ringColor {
                Circle().strokeBorder(ringColor, lineWidth: ringWidth)
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibilityLabel ?? "")
        .accessibilityHidden(accessibilityLabel == nil)
    }
}
