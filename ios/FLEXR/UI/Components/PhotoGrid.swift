import PhotosUI
import SwiftUI

/// Ein Feld im Fotoraster — entweder belegt oder leer.
struct PhotoSlot: Identifiable, Equatable {
    let id: String
    let source: PhotoImageSource
    var status: PhotoStatus?
}

/// Fotoraster mit sechs Feldern (`.photo-grid` im Web).
///
/// Belegte Felder zeigen das Bild plus — beim eigenen Profil — den
/// Moderationsstatus; leere Felder öffnen die Systemfotoauswahl. `PhotosPicker`
/// braucht keine Berechtigung auf die Mediathek: die App bekommt ausschließlich
/// die gewählten Bilder zu sehen (Entsprechung des Android Photo Pickers).
struct PhotoGridEditor: View {

    let slots: [PhotoSlot]
    let onPhotoPicked: (Data) -> Void
    let onRemove: (String) -> Void
    var maxPhotos = ImageProcessor.maxPhotos
    var showsStatus = false

    @State private var selection: PhotosPickerItem?

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 8), count: 3)

    var body: some View {
        LazyVGrid(columns: columns, spacing: 8) {
            ForEach(0..<maxPhotos, id: \.self) { index in
                if index < slots.count {
                    FilledPhotoSlot(
                        slot: slots[index],
                        showsStatus: showsStatus,
                        onRemove: { onRemove(slots[index].id) }
                    )
                } else {
                    EmptyPhotoSlot(selection: $selection)
                }
            }
        }
        .onChange(of: selection) { _, item in
            guard let item else { return }
            Task {
                if let data = try? await item.loadTransferable(type: Data.self) {
                    onPhotoPicked(data)
                }
                selection = nil
            }
        }
    }
}

private struct FilledPhotoSlot: View {

    let slot: PhotoSlot
    let showsStatus: Bool
    let onRemove: () -> Void

    private var borderColor: Color {
        guard showsStatus else { return .clear }
        switch slot.status {
        case .approved, .none: return .clear
        case .rejected: return FlexrColor.danger.opacity(0.5)
        case .pending: return FlexrColor.plateDim
        }
    }

    var body: some View {
        ZStack(alignment: .topTrailing) {
            PhotoImage(source: slot.source, accessibilityLabel: "Profilfoto")
                .aspectRatio(3.0 / 4.0, contentMode: .fill)
                .clipShape(RoundedRectangle(cornerRadius: 11, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 11, style: .continuous)
                        .strokeBorder(borderColor, lineWidth: 1.5)
                )

            Button(action: onRemove) {
                Image(systemName: FlexrIcon.close)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(.white)
                    .frame(width: 22, height: 22)
                    .background(Circle().fill(.black.opacity(0.6)))
            }
            .buttonStyle(.plain)
            .padding(4)
            .accessibilityLabel("Foto entfernen")

            if showsStatus, let status = slot.status, status != .approved {
                VStack {
                    Spacer()
                    Text(status == .rejected ? "Abgelehnt" : "In Prüfung")
                        .font(.flexrMono(9))
                        .foregroundStyle(status == .rejected ? FlexrColor.danger : FlexrColor.plate)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 2)
                        .background(
                            RoundedRectangle(cornerRadius: 6, style: .continuous)
                                .fill(.black.opacity(0.62))
                        )
                        .padding(4)
                }
            }
        }
        .aspectRatio(3.0 / 4.0, contentMode: .fit)
    }
}

private struct EmptyPhotoSlot: View {

    @Binding var selection: PhotosPickerItem?

    var body: some View {
        PhotosPicker(selection: $selection, matching: .images, photoLibrary: .shared()) {
            ZStack {
                RoundedRectangle(cornerRadius: 11, style: .continuous)
                    .fill(Color.white.opacity(0.015))
                RoundedRectangle(cornerRadius: 11, style: .continuous)
                    .strokeBorder(FlexrColor.steel, lineWidth: 1.5)
                Image(systemName: FlexrIcon.add)
                    .font(.system(size: 24, weight: .medium))
                    .foregroundStyle(FlexrColor.chalkDim)
            }
            .aspectRatio(3.0 / 4.0, contentMode: .fit)
        }
        .accessibilityLabel("Foto hinzufügen")
    }
}

/// Sichtbarkeitshinweis unter dem Fotoraster (`.photo-hint`).
struct PhotoVisibilityHint: View {

    let statuses: [PhotoStatus]

    private var content: (text: String, warn: Bool) {
        if statuses.isEmpty {
            return (
                "Lade mindestens ein Foto hoch — ohne Foto ist dein Profil in der Suche nicht sichtbar.",
                true
            )
        }
        if statuses.contains(.approved) {
            return (
                "Dein Profil ist in der Suche sichtbar. Neue Fotos werden vor der Anzeige geprüft.",
                false
            )
        }
        if statuses.contains(.pending) {
            return (
                "Deine Fotos werden gerade geprüft. Sobald mindestens eines freigegeben ist, "
                    + "erscheinst du in der Suche.",
                true
            )
        }
        return (
            "Deine Fotos wurden abgelehnt. Bitte lade ein anderes Foto hoch, um in der Suche zu erscheinen.",
            true
        )
    }

    var body: some View {
        Text(content.text)
            .flexrText(.bodySmall)
            .foregroundStyle(content.warn ? FlexrColor.plate : FlexrColor.chalkDim)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 8)
    }
}
