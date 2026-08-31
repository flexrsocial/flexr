import PhotosUI
import SwiftUI
import UniformTypeIdentifiers

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
    /// Neue Reihenfolge nach dem Verschieben (vollständige Liste der IDs).
    /// nil schaltet das Sortieren ab — etwa im Onboarding, wo die Fotos noch
    /// gar keine Server-IDs haben.
    var onReorder: (([String]) -> Void)?

    @State private var selection: PhotosPickerItem?
    @State private var draggingID: String?
    @State private var targetID: String?

    /// Sortieren lohnt erst ab zwei Fotos.
    private var reorderable: Bool { onReorder != nil && slots.count > 1 }

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 8), count: 3)

    var body: some View {
        LazyVGrid(columns: columns, spacing: 8) {
            ForEach(0..<maxPhotos, id: \.self) { index in
                if index < slots.count {
                    let slot = slots[index]
                    // Die beiden Zweige bewusst ausgeschrieben statt über einen
                    // `.if`-Hilfsmodifier: der wechselt die View-Identität und
                    // brächte den laufenden Zug durcheinander. `reorderable`
                    // ändert sich innerhalb eines Bildschirms ohnehin nicht.
                    if reorderable {
                        filledSlot(slot, at: index)
                            .onDrag {
                                draggingID = slot.id
                                targetID = nil
                                return NSItemProvider(object: slot.id as NSString)
                            }
                            .onDrop(
                                of: [UTType.text],
                                delegate: PhotoReorderDropDelegate(
                                    targetSlotID: slot.id,
                                    slots: slots,
                                    draggingID: $draggingID,
                                    targetID: $targetID,
                                    onReorder: onReorder
                                )
                            )
                    } else {
                        filledSlot(slot, at: index)
                    }
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

    /// Position 1 ist das Hauptfoto (Swipe-Karte, Avatar, Chat-Kopf) - die
    /// Nummer macht sichtbar, was das Verschieben bewirkt.
    private func filledSlot(_ slot: PhotoSlot, at index: Int) -> some View {
        FilledPhotoSlot(
            slot: slot,
            showsStatus: showsStatus,
            onRemove: { onRemove(slot.id) },
            position: reorderable ? index + 1 : nil,
            isDragged: draggingID == slot.id,
            isDropTarget: targetID == slot.id && draggingID != slot.id
        )
    }
}

/// Nimmt das fallende Foto entgegen und meldet die neue Reihenfolge.
///
/// Verschoben wird, nicht getauscht: beim Tauschen würde ein Foto von Platz 4
/// auf Platz 1 das bisherige Hauptfoto nach hinten werfen, statt die
/// dazwischenliegenden nachrücken zu lassen.
private struct PhotoReorderDropDelegate: DropDelegate {

    let targetSlotID: String
    let slots: [PhotoSlot]
    @Binding var draggingID: String?
    @Binding var targetID: String?
    let onReorder: (([String]) -> Void)?

    func dropEntered(info: DropInfo) {
        guard draggingID != nil else { return }
        targetID = targetSlotID
    }

    func dropExited(info: DropInfo) {
        if targetID == targetSlotID { targetID = nil }
    }

    func dropUpdated(info: DropInfo) -> DropProposal? {
        DropProposal(operation: .move)
    }

    func performDrop(info: DropInfo) -> Bool {
        defer {
            draggingID = nil
            targetID = nil
        }
        guard let draggingID,
              draggingID != targetSlotID,
              let from = slots.firstIndex(where: { $0.id == draggingID }),
              let to = slots.firstIndex(where: { $0.id == targetSlotID })
        else { return false }

        var ids = slots.map(\.id)
        ids.insert(ids.remove(at: from), at: to)
        onReorder?(ids)
        return true
    }
}

private struct FilledPhotoSlot: View {

    let slot: PhotoSlot
    let showsStatus: Bool
    let onRemove: () -> Void
    /// 1-basierte Position; nil blendet die Nummer aus (nicht sortierbar).
    var position: Int?
    var isDragged = false
    var isDropTarget = false

    private var borderColor: Color {
        // Das Ziel des Zugs sticht hervor, solange das Foto darüber schwebt.
        if isDropTarget { return FlexrColor.plate }
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

            if let position {
                VStack {
                    Spacer()
                    HStack {
                        Text("\(position)")
                            .font(.flexrMono(9))
                            .foregroundStyle(position == 1 ? FlexrColor.plateInk : FlexrColor.chalkDim)
                            .padding(.horizontal, 5)
                            .padding(.vertical, 1)
                            .background(
                                RoundedRectangle(cornerRadius: 5, style: .continuous)
                                    .fill(position == 1 ? FlexrColor.plate : .black.opacity(0.62))
                            )
                        Spacer()
                    }
                    .padding(4)
                }
            }

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
        // Das Foto am Finger wird gedimmt, damit sichtbar bleibt, von wo es
        // gerade weggezogen wird.
        .opacity(isDragged ? 0.4 : 1)
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
            return ("Mindestens ein Foto ist nötig, damit dein Profil sichtbar ist.", true)
        }
        if statuses.contains(.approved) {
            return ("Dein Profil ist sichtbar. Neue Fotos werden kurz geprüft.", false)
        }
        if statuses.contains(.pending) {
            return ("Dein Foto wird geprüft.", true)
        }
        return ("Foto abgelehnt. Bitte lade ein anderes hoch.", true)
    }

    var body: some View {
        Text(content.text)
            .flexrText(.bodySmall)
            .foregroundStyle(content.warn ? FlexrColor.plate : FlexrColor.chalkDim)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 8)
    }
}
