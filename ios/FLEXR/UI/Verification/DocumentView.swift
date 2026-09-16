import PhotosUI
import SwiftUI

/// Vorder- oder Rückseite des Ausweises.
enum DocumentSide: String, CaseIterable, Identifiable, Hashable, Sendable {
    case front, back

    var id: String { rawValue }

    var labelKey: L {
        switch self {
        case .front: .documentSideFront
        case .back: .documentSideBack
        }
    }
}

/// Schritt 2 der Alters- und Identitätsprüfung: amtlicher Lichtbildausweis.
///
/// Die Aufnahmen entstehen über die Rückkamera oder kommen aus der Mediathek
/// und gehen per Presigned PUT in einen privaten Bereich des Objektspeichers.
/// Sie bekommen nie eine öffentliche Adresse und werden nach der Prüfung
/// gelöscht.
@MainActor
@Observable
final class DocumentModel {

    var documentTypes: [VerificationDocumentType] = []
    var selectedType: VerificationDocumentType?
    /// Aufnahmen als JPEG, je Seite.
    var captures: [DocumentSide: Data] = [:]
    /// Welche Seite gerade aufgenommen wird — nil heißt: Übersicht.
    var capturing: DocumentSide?
    var isLoading = true
    var isSubmitting = false
    var error: String?
    var isFinished = false
    /// Der Server sieht diesen Schritt nicht (mehr) vor — etwa weil das Selfie
    /// verworfen wurde. Weiterzumachen hieße, gegen eine geschlossene Tür zu
    /// laufen: der Bildschirm schließt sich stattdessen.
    var stepNoLongerOpen = false

    /// Für die gewählte Ausweisart benötigte Aufnahmen.
    var requiredSides: [DocumentSide] {
        selectedType?.needsBack == true ? [.front, .back] : [.front]
    }

    var isComplete: Bool {
        selectedType != nil && requiredSides.allSatisfy { captures[$0] != nil }
    }

    @ObservationIgnored private let verification: VerificationRepository
    @ObservationIgnored private let profiles: ProfileRepository
    @ObservationIgnored private let onMessage: (String) -> Void

    /// Siehe [VerificationModel]: eine Referenz auf den Speicher, damit ein
    /// Sprachwechsel mitten im Vorgang auch auf spätere Meldungen wirkt.
    @ObservationIgnored private let languageStore: LanguageStore
    private var s: FlexrStrings { languageStore.strings }

    init(
        container: AppContainer,
        languageStore: LanguageStore,
        onMessage: @escaping (String) -> Void
    ) {
        self.languageStore = languageStore
        verification = container.verification
        profiles = container.profiles
        self.onMessage = onMessage
    }

    /// Welche Ausweisarten zulässig sind, bestimmt der Server — nicht der
    /// Client. Er sagt zugleich, ob dieser Schritt überhaupt ansteht.
    func load() async {
        isLoading = true
        error = nil
        do {
            let state = try await verification.status()
            guard state.nextStep == .document else {
                stepNoLongerOpen = true
                return
            }
            documentTypes = state.documentTypes
            selectedType = state.documentTypes.first
        } catch {
            self.error = (error as? FlexrAPIError)?.message
                ?? s(.documentStatusLoadFailed)
        }
        isLoading = false
    }

    func onTypeSelected(_ type: VerificationDocumentType) {
        // Beim Wechsel auf eine Art ohne Rückseite ist eine bereits gemachte
        // Rückseiten-Aufnahme gegenstandslos.
        if !type.needsBack { captures[.back] = nil }
        selectedType = type
        error = nil
    }

    func onCaptureRequested(_ side: DocumentSide) {
        capturing = side
        error = nil
    }

    func onCaptureCancelled() {
        capturing = nil
    }

    func onCameraDenied() {
        capturing = nil
        error = s(.documentCameraDenied)
    }

    func onCaptured(_ image: UIImage) async {
        let side = capturing ?? .front
        guard let data = try? await ImageProcessor.compressDocument(image) else {
            capturing = nil
            error = s(.documentCaptureFailed)
            return
        }
        captures[side] = data
        capturing = nil
        error = nil
    }

    /// Eine bestehende Bilddatei statt einer frischen Aufnahme.
    ///
    /// Wer den Ausweis schon gescannt oder vorab geschwärzt hat, käme mit der
    /// Kamera allein nicht weiter.
    func onFilePicked(side: DocumentSide, data: Data) async {
        guard let compressed = try? await ImageProcessor.compressDocument(data: data) else {
            error = s(.documentFileReadFailed)
            return
        }
        captures[side] = compressed
        capturing = nil
        error = nil
    }

    func onRetake(_ side: DocumentSide) {
        captures[side] = nil
        capturing = side
    }

    func submit() async {
        guard let type = selectedType, let front = captures[.front], isComplete else { return }

        isSubmitting = true
        error = nil
        do {
            _ = try await verification.submitDocument(
                type: type.value,
                front: front,
                back: captures[.back]
            )
            // Aufnahmen sofort aus dem Speicher nehmen — sie liegen jetzt beim
            // Server und werden dort nach der Prüfung gelöscht.
            captures = [:]
            _ = try? await profiles.refresh()
            onMessage(s(.documentSubmitted))
            isFinished = true
        } catch {
            // Aufnahmen behalten, damit nur der Upload zu wiederholen ist.
            self.error = (error as? FlexrAPIError)?.message
                ?? s(.documentSubmitFailed)
        }
        isSubmitting = false
    }
}

struct DocumentView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let onBack: () -> Void
    /// Eingereicht — der Vorgang wartet jetzt auf die Prüfung.
    let onSubmitted: () -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var model: DocumentModel?

    var body: some View {
        Group {
            if let model {
                if let side = model.capturing {
                    DocumentCameraScreen(
                        side: side,
                        onCaptured: { image in Task { await model.onCaptured(image) } },
                        onCancel: model.onCaptureCancelled,
                        onDenied: model.onCameraDenied,
                        onCaptureFailed: { appModel.show(s(.documentCaptureFailed)) }
                    )
                } else {
                    form(model)
                }
            } else {
                LoadingStateView(label: s(.documentLoading))
            }
        }
        .task {
            let created = model ?? DocumentModel(
                container: container,
                languageStore: languageStore,
                onMessage: { appModel.show($0) }
            )
            model = created
            await created.load()
            // Bewusst hier und nicht per onChange: Ist der Schritt schon beim
            // ersten Laden zu, wäre der Wert gesetzt, bevor die Ansicht ihn je
            // als „alt" gesehen hat — onChange bliebe stumm.
            if created.stepNoLongerOpen { onBack() }
        }
    }

    /// Übersetzte Bezeichnung der Ausweisart.
    ///
    /// Der Server liefert sie auf Deutsch. Kennen wir den Wert, nehmen wir die
    /// eigene Übersetzung; alles Unbekannte bleibt so, wie es geliefert wurde.
    private func typeLabel(_ type: VerificationDocumentType) -> String {
        switch type.value {
        case "id_card": s(.documentTypeIdCard)
        case "passport": s(.documentTypePassport)
        case "drivers_license": s(.documentTypeLicense)
        default: type.label
        }
    }

    /// Welche Seiten diese Ausweisart braucht — als fertiger Satz unter der
    /// Bezeichnung. Bewusst eine eigene Funktion statt eines Bedingungsoperators
    /// mitten im Aufruf: `s` ist überladen, und der Übersetzer soll den
    /// Schlüssel nicht erst aus zwei Zweigen herleiten müssen.
    private func sidesHint(_ type: VerificationDocumentType) -> String {
        type.needsBack ? s(.documentNeedsBoth) : s(.documentNeedsFront)
    }

    @ViewBuilder
    private func form(_ model: DocumentModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            BackHeader(title: s(.documentTitle), onBack: onBack)

            if model.isLoading {
                LoadingStateView(label: s(.documentLoading))
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        VerificationStepBar(current: 2)
                            .padding(.top, 16)

                        FlexrCard {
                            VStack(alignment: .leading, spacing: 8) {
                                Eyebrow(text: s(.documentWhyTitle))
                                Text(s(.documentWhy))
                                    .flexrText(.bodyMedium)
                                    .foregroundStyle(FlexrColor.chalkDim)
                                Text(s(.documentManualReview))
                                    .flexrText(.bodyMedium)
                                    .foregroundStyle(FlexrColor.chalkDim)
                            }
                        }
                        .padding(.top, 16)

                        Eyebrow(text: s(.documentTypeLabel))
                            .padding(.top, 18)
                        ForEach(model.documentTypes, id: \.value) { type in
                            DocumentTypeOption(
                                label: typeLabel(type),
                                hint: sidesHint(type),
                                isSelected: type.value == model.selectedType?.value,
                                action: { model.onTypeSelected(type) }
                            )
                            .padding(.bottom, 8)
                        }

                        RedactionNote()
                            .padding(.top, 8)

                        Eyebrow(text: s(.documentShotsLabel))
                            .padding(.top, 18)
                        ForEach(model.requiredSides) { side in
                            CaptureSlot(
                                side: side,
                                image: model.captures[side],
                                onCapture: {
                                    if model.captures[side] == nil {
                                        model.onCaptureRequested(side)
                                    } else {
                                        model.onRetake(side)
                                    }
                                },
                                onFilePicked: { data in
                                    Task { await model.onFilePicked(side: side, data: data) }
                                }
                            )
                            .padding(.bottom, 10)
                        }

                        Text(s(.documentSourceHint))
                            .flexrText(.bodySmall)
                            .foregroundStyle(FlexrColor.chalkDim)

                        FieldError(message: model.error)
                    }
                    .padding(.bottom, 16)
                }

                if model.isSubmitting {
                    FlexrButton(title: s(.documentSubmitting), isEnabled: false, isLoading: true) {}
                } else {
                    FlexrButton(title: s(.documentSubmit), isEnabled: model.isComplete) {
                        Task { await model.submit() }
                    }
                }

                Text(s(.documentConsentNote))
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .padding(.top, 10)
                    .padding(.bottom, 20)
            }
        }
        .padding(.horizontal, 20)
        .onChange(of: model.isFinished) { _, finished in
            if finished { onSubmitted() }
        }
    }
}

/// Schrittanzeige: 1 Selfies, 2 Ausweis, 3 Prüfung.
struct VerificationStepBar: View {

    let current: Int

    var body: some View {
        HStack(spacing: 6) {
            ForEach(1...3, id: \.self) { step in
                RoundedRectangle(cornerRadius: 2, style: .continuous)
                    .fill(color(for: step))
                    .frame(height: 3)
            }
        }
        .accessibilityElement()
        .accessibilityLabel("\(current) / 3")
    }

    private func color(for step: Int) -> Color {
        if step < current { return FlexrColor.plate }
        if step == current { return FlexrColor.chalk }
        return FlexrColor.steel
    }
}

// MARK: - Auswahl und Aufnahmeplätze

private struct DocumentTypeOption: View {

    let label: String
    let hint: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 0) {
                Text(label)
                    .flexrText(.bodyLarge)
                    .foregroundStyle(FlexrColor.chalk)
                Text(hint)
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 14)
            .padding(.vertical, 13)
            .contentShape(Rectangle())
            .background(
                RoundedRectangle(cornerRadius: 13, style: .continuous)
                    .fill(isSelected ? FlexrColor.plate.opacity(0.08) : FlexrColor.surface2)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 13, style: .continuous)
                    .strokeBorder(isSelected ? FlexrColor.plate : FlexrColor.steel, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(isSelected ? [.isSelected] : [])
    }
}

/// Hinweis, dass nicht benötigte Angaben geschwärzt werden dürfen.
private struct RedactionNote: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(s(.documentRedactNote))
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
            Text(s(.documentRedactNoteBold))
                .flexrText(.bodySmall)
                .fontWeight(.semibold)
                .foregroundStyle(FlexrColor.chalk)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(FlexrColor.plate.opacity(0.06))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .strokeBorder(FlexrColor.plate.opacity(0.22), lineWidth: 1)
        )
    }
}

private struct CaptureSlot: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let side: DocumentSide
    let image: Data?
    let onCapture: () -> Void
    let onFilePicked: (Data) -> Void

    @State private var selection: PhotosPickerItem?

    var body: some View {
        VStack(spacing: 8) {
            Button(action: onCapture) {
                ZStack {
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(FlexrColor.surface2)

                    if let image {
                        PhotoImage(
                            source: .data(image),
                            contentMode: .fit,
                            accessibilityLabel: s(.documentSideOfId, s(side.labelKey))
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

                        Text(s(.documentSideDone, s(side.labelKey)))
                            .flexrText(.bodySmall)
                            .foregroundStyle(FlexrColor.chalk)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(
                                RoundedRectangle(cornerRadius: 6, style: .continuous)
                                    .fill(Color.black.opacity(0.62))
                            )
                            .padding(8)
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                    } else {
                        VStack(spacing: 6) {
                            Image(systemName: FlexrIcon.camera)
                                .font(.system(size: 22, weight: .medium))
                                .foregroundStyle(FlexrColor.chalkDim)
                            Text(s(.documentCaptureSide, s(side.labelKey)))
                                .flexrText(.bodyMedium)
                                .foregroundStyle(FlexrColor.chalkDim)
                                .multilineTextAlignment(.center)
                        }
                    }
                }
                .aspectRatio(3.0 / 2.0, contentMode: .fit)
                .frame(maxWidth: .infinity)
                .contentShape(Rectangle())
                .overlay(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .strokeBorder(
                            image != nil ? FlexrColor.plate : FlexrColor.steel,
                            lineWidth: image != nil ? 1 : 1.5
                        )
                )
            }
            .buttonStyle(.plain)

            // Zwei sichtbare Wege statt nur der Kamera: wer den Ausweis schon
            // gescannt oder vorab geschwärzt hat, käme sonst nicht weiter.
            HStack(spacing: 8) {
                SlotActionButton(icon: FlexrIcon.camera, label: s(.documentActionCamera), action: onCapture)
                PhotosPicker(selection: $selection, matching: .images, photoLibrary: .shared()) {
                    SlotActionLabel(icon: FlexrIcon.photoLibrary, label: s(.documentActionFile))
                }
                .buttonStyle(.plain)
            }
        }
        .onChange(of: selection) { _, item in
            guard let item else { return }
            Task {
                if let data = try? await item.loadTransferable(type: Data.self) {
                    onFilePicked(data)
                }
                selection = nil
            }
        }
    }
}

/// Flacher Knopf unter dem Aufnahmeplatz — Kamera oder Dateiauswahl.
private struct SlotActionButton: View {
    let icon: String
    let label: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            SlotActionLabel(icon: icon, label: label)
        }
        .buttonStyle(.plain)
    }
}

private struct SlotActionLabel: View {
    let icon: String
    let label: String

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 13, weight: .semibold))
            Text(label)
                .flexrText(.bodySmall)
        }
        .foregroundStyle(FlexrColor.chalkDim)
        .frame(maxWidth: .infinity)
        .padding(.vertical, 9)
        .contentShape(Rectangle())
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .strokeBorder(FlexrColor.steel, lineWidth: 1)
        )
    }
}

// MARK: - Kamera

/// Vollflächige Aufnahme über die Rückkamera. Bewusst ein eigener Bildschirm
/// statt eines Blattes: Der Ausweis soll formatfüllend im Sucher liegen.
private struct DocumentCameraScreen: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let side: DocumentSide
    let onCaptured: (UIImage) -> Void
    let onCancel: () -> Void
    let onDenied: () -> Void
    let onCaptureFailed: () -> Void

    @State private var camera = CameraController(position: .back)
    @State private var hasPermission = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            BackHeader(title: s(.documentCaptureSide, s(side.labelKey)), onBack: onCancel)

            Text(s(.documentFrameHint))
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .padding(.top, 8)

            ZStack {
                FlexrColor.surface2
                if hasPermission {
                    CameraPreview(session: camera.session)
                } else {
                    Text(s(.documentCameraNeeded))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                        .multilineTextAlignment(.center)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .strokeBorder(FlexrColor.plate.opacity(0.35), lineWidth: 1.5)
            )
            .padding(.top, 14)

            if hasPermission {
                FlexrButton(title: s(.documentCapture), icon: .symbol(FlexrIcon.camera)) {
                    Task {
                        guard let image = await camera.capture() else {
                            onCaptureFailed()
                            return
                        }
                        onCaptured(image)
                    }
                }
                .padding(.top, 16)
            } else {
                FlexrSecondaryButton(title: s(.documentAllowCamera)) {
                    Task {
                        hasPermission = await camera.requestPermission()
                        if hasPermission {
                            await camera.start()
                        } else {
                            // Zweite Ablehnung: iOS fragt nicht erneut, es geht
                            // nur noch über die Systemeinstellungen.
                            if let url = URL(string: UIApplication.openSettingsURLString) {
                                _ = await UIApplication.shared.open(url)
                            }
                        }
                    }
                }
                .padding(.top, 16)
            }
        }
        .padding(.horizontal, 20)
        .padding(.bottom, 20)
        .task {
            hasPermission = await camera.requestPermission()
            if hasPermission {
                await camera.start()
            } else {
                onDenied()
            }
        }
        .onDisappear { camera.stop() }
    }
}
