import PhotosUI
import SwiftUI
import UniformTypeIdentifiers

/// Ein Feld im Fotoraster — entweder belegt oder leer.
struct PhotoSlot: Identifiable, Equatable {
    let id: String
    let source: PhotoImageSource
    var status: PhotoStatus?
    /// Darf das Foto jetzt weg? Nein heißt: genau die Mindestzahl gültiger
    /// Fotos - der Knopf zeigt dann die Austauschpfeile statt des ✕.
    var removable: Bool = true
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
    /// Gesetzt: Bei mindestens zwei freien Feldern lässt die Fotoauswahl
    /// mehrere Bilder auf einmal zu, in der gewählten Reihenfolge
    /// (Registrierung, seit 2.4.14 - vorher drei Durchgänge für die drei
    /// Pflichtfotos). Das Konto lädt jedes Foto sofort hoch und bleibt bei
    /// einem pro Durchgang.
    var onPhotosPicked: (([Data]) -> Void)?

    @State private var selection: PhotosPickerItem?
    @State private var multiSelection: [PhotosPickerItem] = []
    @State private var draggingID: String?
    @State private var targetID: String?

    /// Sortieren lohnt erst ab zwei Fotos.
    private var reorderable: Bool { onReorder != nil && slots.count > 1 }

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 8), count: 3)

    private var freeSlots: Int { maxPhotos - slots.count }

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
                } else if onPhotosPicked != nil && freeSlots >= 2 {
                    EmptyPhotoSlot(auswahl: .mehrere($multiSelection, max: freeSlots))
                } else {
                    EmptyPhotoSlot(auswahl: .einzeln($selection))
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
        .onChange(of: multiSelection) { _, items in
            guard !items.isEmpty else { return }
            let platz = freeSlots
            Task {
                var daten: [Data] = []
                for item in items.prefix(platz) {
                    if let data = try? await item.loadTransferable(type: Data.self) {
                        daten.append(data)
                    }
                }
                multiSelection = []
                if !daten.isEmpty { onPhotosPicked?(daten) }
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
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

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
        // Belegt: durchgehender Rand, frei: gestrichelt (wie im Web seit
        // 15.10.2026) - vorher hatten belegte Plätze gar keinen.
        guard showsStatus else { return FlexrColor.steel }
        switch slot.status {
        case .approved, .none: return FlexrColor.steel
        case .rejected: return FlexrColor.danger.opacity(0.5)
        case .pending: return FlexrColor.plateDim
        }
    }

    private var shape: RoundedRectangle {
        RoundedRectangle(cornerRadius: 11, style: .continuous)
    }

    var body: some View {
        // Die Kachel bekommt ihre Groesse von dieser leeren Flaeche: volle
        // Spaltenbreite, Hoehe daraus im Verhaeltnis 3:4. Das Foto liegt als
        // Overlay darin und wird auf genau diese Kachel beschnitten, die
        // Bedienelemente liegen darueber.
        //
        // Vorher stand `.aspectRatio(3:4, contentMode: .fill)` am Foto selbst.
        // `.fill` darf ausdruecklich ueber die angebotene Flaeche hinauswachsen:
        // das Bild wuchs aus seiner Rasterzelle heraus, das `clipShape` schnitt
        // nur auf die (zu grosse) Bildflaeche, und die ZStack darum uebernahm
        // diese Groesse. Ergebnis war ein Raster aus verschieden grossen,
        // einander ueberlappenden Kacheln - Web und Android haben an dieser
        // Stelle ein festes Seitenverhaeltnis je Zelle.
        Color.clear
            .aspectRatio(3.0 / 4.0, contentMode: .fit)
            .overlay {
                PhotoImage(source: slot.source, accessibilityLabel: s(.commonProfile))
            }
            .clipShape(shape)
            .overlay(shape.strokeBorder(borderColor, lineWidth: 1.5))
            .overlay(alignment: .topTrailing) {
                // Trefferfläche 44 pt, sichtbar ein 26-pt-Kreis in der Ecke.
                // Vorher war beides 22 pt - ein Tipper knapp daneben landete
                // auf dem Foto, und das Löschen ging „manchmal nicht".
                Button(action: onRemove) {
                    Image(systemName: slot.removable ? FlexrIcon.close : "arrow.left.arrow.right")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(.white)
                        .frame(width: 26, height: 26)
                        .background(Circle().fill(.black.opacity(0.66)))
                        .overlay(Circle().strokeBorder(.white.opacity(0.28), lineWidth: 1))
                        .padding(5)
                        .frame(width: 44, height: 44, alignment: .topTrailing)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(slot.removable ? s(.photoRemove) : s(.photoSwapTitle))
            }
            .overlay(alignment: .bottomLeading) {
                // Abgelehnte bekommen keine Nummer (Datei gelöscht, nie
                // Hauptfoto). Bei „In Prüfung" rückt sie über das Etikett,
                // das unten die ganze Breite belegt - vorher lag sie darunter.
                if let position, !(showsStatus && slot.status == .rejected) {
                    Text("\(position)")
                        .font(.flexrMono(9))
                        .foregroundStyle(position == 1 ? FlexrColor.plateInk : FlexrColor.chalkDim)
                        .padding(.horizontal, 5)
                        .padding(.vertical, 1)
                        .background(
                            RoundedRectangle(cornerRadius: 5, style: .continuous)
                                .fill(position == 1 ? FlexrColor.plate : .black.opacity(0.62))
                        )
                        .padding(.horizontal, 4)
                        .padding(.top, 4)
                        .padding(.bottom, showsStatus && slot.status == .pending ? 26 : 4)
                }
            }
            .overlay(alignment: .bottom) {
                if showsStatus, let status = slot.status, status != .approved {
                    Text(status == .rejected ? s(.photoRejected) : s(.photoPending))
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
            // Das Foto am Finger wird gedimmt, damit sichtbar bleibt, von wo es
            // gerade weggezogen wird.
            .opacity(isDragged ? 0.4 : 1)
            // Trefferflaeche fuer Tippen und Ziehen ist die ganze Kachel, nicht
            // nur deren deckende Stellen - `Color.clear` ist keine davon.
            .contentShape(shape)
    }
}

private struct EmptyPhotoSlot: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    enum Auswahl {
        case einzeln(Binding<PhotosPickerItem?>)
        case mehrere(Binding<[PhotosPickerItem]>, max: Int)
    }

    let auswahl: Auswahl

    private var shape: RoundedRectangle {
        RoundedRectangle(cornerRadius: 11, style: .continuous)
    }

    var body: some View {
        Group {
            switch auswahl {
            case .einzeln(let selection):
                PhotosPicker(selection: selection, matching: .images, photoLibrary: .shared()) {
                    feld
                }
            case .mehrere(let selection, let max):
                PhotosPicker(
                    selection: selection,
                    maxSelectionCount: max,
                    selectionBehavior: .ordered,
                    matching: .images,
                    photoLibrary: .shared()
                ) {
                    feld
                }
            }
        }
        .accessibilityLabel(s(.photoAdd))
    }

    /// Gleiche Groessenlogik wie in FilledPhotoSlot, damit belegte und leere
    /// Felder in derselben Zeile exakt gleich hoch sind.
    private var feld: some View {
        Color.clear
            .aspectRatio(3.0 / 4.0, contentMode: .fit)
            .overlay(shape.fill(Color.white.opacity(0.015)))
            .overlay(
                shape.strokeBorder(
                    FlexrColor.steel,
                    style: StrokeStyle(lineWidth: 1.5, dash: [6, 4])
                )
            )
            .overlay(
                Image(systemName: FlexrIcon.add)
                    .font(.system(size: 24, weight: .medium))
                    .foregroundStyle(FlexrColor.chalkDim)
            )
            .contentShape(shape)
    }
}

/// Sichtbarkeitshinweis unter dem Fotoraster (`.photo-hint`).
struct PhotoVisibilityHint: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let statuses: [PhotoStatus]
    var visibility: PhotoVisibility = .noPhotos

    /// Die Mindestanzahl steht vor dem Moderationsstand: Wer zu wenige Fotos
    /// hat, muss das zuerst erfahren. Abgelehnte zählen nicht mit (wie beim
    /// Server) - bis 14.10.2026 galten zwei gültige plus ein abgelehntes als
    /// „genug". Ins Deck kommt ohnehin nur, wer drei freigegebene hat.
    private var content: (text: String, warn: Bool) {
        if statuses.isEmpty {
            return (s(.photoHintNone, ImageProcessor.minPhotos), true)
        }
        let valid = statuses.filter { $0 != .rejected }.count
        if valid == 0 {
            return (s(.photoHintRejected), true)
        }
        let missing = ImageProcessor.minPhotos - valid
        if missing > 0 {
            return (s(.photoHintTooFew, missing, ImageProcessor.minPhotos), true)
        }
        if visibility == .visible {
            // Genau die Mindestzahl: erklären, warum statt ✕ die Pfeile stehen.
            let ok = s(.photoHintOk)
            return (valid == ImageProcessor.minPhotos
                    ? ok + " " + s(.photoHintAtMin, ImageProcessor.minPhotos)
                    : ok, false)
        }
        if visibility == .pending {
            return (s(.photoHintPending, ImageProcessor.minPhotos), true)
        }
        return (s(.photoHintRejected), true)
    }

    var body: some View {
        Text(content.text)
            .flexrText(.bodySmall)
            .foregroundStyle(content.warn ? FlexrColor.plate : FlexrColor.chalkDim)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 8)
    }
}

/// Deutlicher Hinweis „in der Suche nicht sichtbar" (`.vis-banner` im Web) -
/// über dem Deck und oben im Konto, solange kein Foto freigegeben ist. Bis
/// 14.10.2026 stand das nur klein unter dem Fotoraster.
struct SearchVisibilityBanner: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let visibility: PhotoVisibility
    /// Zweizeilig, als Ganzes antippbar - über dem Deck. Die volle Fassung
    /// nahm dort so viel Höhe, dass die Like-/Nein-Knöpfe (sie liegen über
    /// dem unteren Kartenrand) den Kartentext verdeckten.
    var compact = false
    let onAction: () -> Void

    private var accent: Color {
        visibility == .pending ? FlexrColor.plate : FlexrColor.danger
    }

    private var text: String {
        switch visibility {
        case .pending: s(.visPending, ImageProcessor.minPhotos)
        case .noPhotos: s(.visNone, ImageProcessor.minPhotos)
        default: s(.visRejected, ImageProcessor.minPhotos)
        }
    }

    private var shortText: String {
        switch visibility {
        case .pending: s(.visShortPending)
        case .noPhotos: s(.visShortNone, ImageProcessor.minPhotos)
        default: s(.visShortRejected)
        }
    }

    var body: some View {
        if compact {
            compactBody
        } else {
            fullBody
        }
    }

    private var compactBody: some View {
        Button(action: onAction) {
            HStack(spacing: 10) {
                Image(systemName: "eye.slash")
                    .font(.system(size: 17, weight: .medium))
                    .foregroundStyle(accent)
                    .frame(width: 22)
                VStack(alignment: .leading, spacing: 1) {
                    Text(s(.visTitleShort))
                        .flexrText(.titleSmall)
                        .foregroundStyle(FlexrColor.chalk)
                    Text(shortText)
                        .flexrText(.bodySmall)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(accent)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 9)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous).fill(accent.opacity(0.11))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .strokeBorder(accent.opacity(0.5), lineWidth: 1)
            )
            .contentShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityHint(s(visibility == .pending ? .visCtaPending : .visCtaUpload))
    }

    private var fullBody: some View {
        HStack(alignment: .top, spacing: 11) {
            Image(systemName: "eye.slash")
                .font(.system(size: 18, weight: .medium))
                .foregroundStyle(accent)
                .frame(width: 22)
            VStack(alignment: .leading, spacing: 2) {
                Text(s(.visTitle))
                    .flexrText(.titleSmall)
                    .foregroundStyle(FlexrColor.chalk)
                Text(text)
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
                Button(action: onAction) {
                    Text(s(visibility == .pending ? .visCtaPending : .visCtaUpload))
                        .font(.flexrWorkSans(13, weight: 700))
                        .foregroundStyle(visibility == .pending ? FlexrColor.plateInk : .white)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 7)
                        .background(Capsule().fill(accent))
                }
                .buttonStyle(.plain)
                .padding(.top, 7)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 14, style: .continuous).fill(accent.opacity(0.11))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .strokeBorder(accent.opacity(0.5), lineWidth: 1)
        )
    }
}
