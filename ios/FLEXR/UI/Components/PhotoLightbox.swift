import SwiftUI

/// Foto-Vollbild mit Wischgalerie.
///
/// Nativ über eine seitenweise scrollende `TabView` gelöst: Wischen, Fangpunkte
/// und Seitenanzeige kommen vom Framework — im Web war das handgeschriebene
/// Touch-Logik. Beim Schließen wird der zuletzt betrachtete Index
/// zurückgemeldet, damit die Karte dahinter dasselbe Foto zeigt.
struct PhotoLightbox: View {

    let photos: [Photo]
    let startIndex: Int
    let onClose: (Int) -> Void

    @State private var index: Int

    init(photos: [Photo], startIndex: Int, onClose: @escaping (Int) -> Void) {
        self.photos = photos
        self.startIndex = startIndex
        self.onClose = onClose
        _index = State(initialValue: min(max(startIndex, 0), max(photos.count - 1, 0)))
    }

    var body: some View {
        ZStack {
            Color.black.opacity(0.96).ignoresSafeArea()

            TabView(selection: $index) {
                ForEach(photos.indices, id: \.self) { offset in
                    let photo = photos[offset]
                    PhotoImage(
                        source: .remote(photo.url),
                        contentMode: .fit,
                        accessibilityLabel: "Foto \(offset + 1) von \(photos.count)"
                    )
                    .padding(.horizontal, 16)
                    .padding(.vertical, 64)
                    .tag(offset)
                }
            }
            .tabViewStyle(.page(indexDisplayMode: .never))

            VStack {
                HStack {
                    Spacer()
                    Button { onClose(index) } label: {
                        Image(systemName: FlexrIcon.close)
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(width: 42, height: 42)
                            .background(Circle().fill(.white.opacity(0.08)))
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Schließen")
                }
                .padding(16)

                Spacer()

                if photos.count > 1 {
                    Text("\(index + 1) / \(photos.count)")
                        .flexrText(.mono)
                        .foregroundStyle(FlexrColor.chalkDim)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Capsule().fill(.white.opacity(0.08)))
                        .padding(.bottom, 26)
                }
            }
        }
    }
}
