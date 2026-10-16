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
    /// Welcher Teil eines zu hohen Fotos beim Zuschnitt sichtbar bleibt:
    /// 0 = oberer Rand, 0,5 = Mitte (Standard), 1 = unterer Rand. Die Karte
    /// nutzt 0,2 - mittig geschnitten fehlte auf Hochformat-Fotos meist der
    /// Kopf (wie `background-position: center 20%` im Web und
    /// `BiasAlignment(0f, -0.6f)` auf Android).
    var verticalFocus: CGFloat = 0.5
    /// Entsprechung der `contentDescription` auf Android. Ohne sie bleibt das
    /// Foto für VoiceOver stumm — und Fotos sind der Inhalt dieser App.
    var accessibilityLabel: String?
    /// Fläche hinter dem Foto, solange es lädt - und bei `.fit` an den
    /// Rändern. Die Galerie setzt sie auf durchsichtig: Dort stand das
    /// Hochformatfoto sonst auf einem grauen Kasten mit Balken.
    var backdrop: Color = FlexrColor.surface2

    @State private var image: UIImage?
    @State private var isLoading = false

    var body: some View {
        // Der Platzhalter bestimmt die Groesse, das Foto liegt als `overlay`
        // darueber. Das ist der entscheidende Unterschied zu einem ZStack:
        //
        // `Image.resizable().aspectRatio(contentMode: .fill)` meldet bewusst
        // eine Groesse, die den Vorschlag **ueberragt** - anders ginge ein
        // Cover-Zuschnitt gar nicht. In einem ZStack uebernimmt der Stapel
        // diese zu grosse Meldung, und `.clipped()` schneidet dann nichts ab,
        // weil es an genau diesen zu grossen Rahmen geschnitten hat. Die
        // Umgebung rechnete danach mit einer zu hohen Bildflaeche.
        //
        // Ein `overlay` wirkt nie auf die Groesse seines Gastgebers zurueck:
        // `PhotoImage` ist damit immer exakt so gross wie vorgeschlagen, und
        // `.clipped()` schneidet den Ueberstand wirklich weg. Genau dieser
        // Fehler hatte im Fotoraster schon einmal zugeschlagen (siehe den
        // Kommentar in PhotoGrid.swift) - dort mit einem Umweg umgangen,
        // hier jetzt an der Wurzel behoben.
        backdrop
            .overlay {
                if let image {
                    if contentMode == .fill, verticalFocus != 0.5 {
                        // Selbst gerechneter Cover-Zuschnitt: das Foto in
                        // Fuellgroesse, waagrecht mittig, senkrecht um den
                        // gewuenschten Anteil des Ueberstands verschoben.
                        GeometryReader { geometry in
                            let drawn = Self.filledSize(image.size, in: geometry.size)
                            Image(uiImage: image)
                                .resizable()
                                .frame(width: drawn.width, height: drawn.height)
                                .offset(
                                    x: (geometry.size.width - drawn.width) / 2,
                                    y: (geometry.size.height - drawn.height) * verticalFocus
                                )
                        }
                        .transition(.opacity)
                    } else {
                        Image(uiImage: image)
                            .resizable()
                            .aspectRatio(contentMode: contentMode)
                            .transition(.opacity)
                    }
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

    /// Groesse, in der ein Bild seinen Rahmen ganz ausfuellt (wie `.fill`).
    private static func filledSize(_ image: CGSize, in frame: CGSize) -> CGSize {
        guard image.width > 0, image.height > 0 else { return frame }
        let scale = max(frame.width / image.width, frame.height / image.height)
        return CGSize(width: image.width * scale, height: image.height * scale)
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
