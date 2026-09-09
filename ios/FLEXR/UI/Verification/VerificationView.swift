import SwiftUI

/// Foto-Verifizierung: ein Selfie, frontal in die Kamera, live aufgenommen.
///
/// Bewusst kein Galerie-Upload — die Aufnahme muss vor der Kamera entstehen.
@MainActor
@Observable
final class VerificationModel {

    var prompts: [String] = []
    var currentIndex = 0
    /// Aufgenommene Selfies als JPEG, in der Reihenfolge der Anweisungen.
    var captures: [Data] = []
    var isStarting = true
    var isSubmitting = false
    var error: String?
    var isFinished = false

    var currentPrompt: String? { prompts[safe: currentIndex] }
    var total: Int { prompts.count }
    var isComplete: Bool { !prompts.isEmpty && captures.count == prompts.count }

    @ObservationIgnored private let verification: VerificationRepository
    @ObservationIgnored private let profiles: ProfileRepository
    @ObservationIgnored private let onMessage: (String) -> Void

    /// Texte in der gewählten Sprache. Als Referenz auf den Speicher und nicht
    /// als Kopie: eine Umstellung mitten in der Sitzung wirkt dann sofort auch
    /// auf Meldungen, die dieses Modell danach erzeugt.
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

    func start() async {
        isStarting = true
        error = nil
        do {
            let state = try await verification.start()
            prompts = state.prompts
            currentIndex = 0
            captures = []
        } catch {
            self.error = (error as? FlexrAPIError)?.message
                ?? s(.verifyStartFailed)
        }
        isStarting = false
    }

    func onCameraDenied() {
        error = s(.verifyCameraDenied)
    }

    func onCaptured(_ image: UIImage) async {
        guard let data = try? await ImageProcessor.compressSelfie(image) else {
            error = s(.verifyCaptureFailed)
            return
        }
        captures.append(data)
        currentIndex += 1
        error = nil
        if isComplete { await submit() }
    }

    func submit() async {
        isSubmitting = true
        error = nil
        do {
            _ = try await verification.submit(
                selfies: Array(zip(prompts, captures)).map { (prompt: $0.0, data: $0.1) }
            )
            _ = try? await profiles.refresh()
            onMessage(s(.verifySubmitted))
            isFinished = true
        } catch {
            // Aufnahmen behalten, damit nur der Upload wiederholt werden muss.
            self.error = (error as? FlexrAPIError)?.message
                ?? s(.verifySubmitFailed)
        }
        isSubmitting = false
    }

    func retrySubmit() async {
        guard isComplete else { return }
        await submit()
    }
}

struct VerificationView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let onBack: () -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var model: VerificationModel?
    @State private var camera = CameraController()
    @State private var hasCameraPermission = false

    var body: some View {
        Group {
            if let model {
                content(model)
            } else {
                LoadingStateView(label: s(.verifyPreparing))
            }
        }
        .task {
            let created = model ?? VerificationModel(
                container: container,
                languageStore: languageStore,
                onMessage: { appModel.show($0) }
            )
            model = created

            hasCameraPermission = await camera.requestPermission()
            if !hasCameraPermission { created.onCameraDenied() }
            await created.start()
            if hasCameraPermission { await camera.start() }
        }
        .onDisappear { camera.stop() }
    }

    @ViewBuilder
    private func content(_ model: VerificationModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            BackHeader(title: s(.verifyTitle), onBack: onBack)

            if model.isStarting {
                LoadingStateView(label: s(.verifyPreparing))
            } else {
                Eyebrow(text: s(.verifyShotOf, min(model.currentIndex + 1, max(model.total, 1)), model.total))
                    .padding(.top, 18)
                Text(model.currentPrompt ?? s(.verifyDone))
                    .flexrText(.headlineMedium)
                    .foregroundStyle(FlexrColor.chalk)

                cameraPane
                    .padding(.top, 16)

                thumbnails(model)
                    .padding(.top, 14)

                FieldError(message: model.error)

                actionButton(model)
                    .padding(.top, 16)

                Text(s(.verifyPrivacyNote))
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .padding(.top, 12)

                Spacer(minLength: 24)
            }
        }
        .padding(.horizontal, 20)
        .onChange(of: model.isFinished) { _, finished in
            if finished { onBack() }
        }
    }

    private var cameraPane: some View {
        ZStack {
            FlexrColor.surface2
            if hasCameraPermission {
                CameraPreview(session: camera.session)
                    // Frontkamera: gespiegelt zeigen, wie es die Nutzerin vom
                    // Spiegel kennt. Die Aufnahme selbst bleibt ungespiegelt.
                    .scaleEffect(x: -1, y: 1)
            } else {
                Text(s(.verifyCameraNeeded))
                    .flexrText(.bodyMedium)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .multilineTextAlignment(.center)
            }
        }
        .aspectRatio(3.0 / 4.0, contentMode: .fit)
        .frame(maxWidth: .infinity)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .strokeBorder(FlexrColor.plate.opacity(0.35), lineWidth: 1.5)
        )
    }

    private func thumbnails(_ model: VerificationModel) -> some View {
        HStack(spacing: 8) {
            ForEach(0..<max(model.total, 1), id: \.self) { index in
                ZStack {
                    RoundedRectangle(cornerRadius: FlexrRadius.small, style: .continuous)
                        .fill(FlexrColor.surface2)
                    RoundedRectangle(cornerRadius: FlexrRadius.small, style: .continuous)
                        .strokeBorder(FlexrColor.steel, lineWidth: 1)

                    if let capture = model.captures[safe: index] {
                        PhotoImage(
                            source: .data(capture),
                            accessibilityLabel: s(.verifyShotIndex, index + 1)
                        )
                        .clipShape(
                            RoundedRectangle(cornerRadius: FlexrRadius.small, style: .continuous)
                        )
                    } else {
                        Text("\(index + 1)")
                            .flexrText(.titleMedium)
                            .foregroundStyle(FlexrColor.chalkDim)
                    }
                }
                .aspectRatio(1, contentMode: .fit)
            }
        }
    }

    @ViewBuilder
    private func actionButton(_ model: VerificationModel) -> some View {
        if model.isSubmitting {
            FlexrButton(title: s(.verifyUploading), isEnabled: false, isLoading: true) {}
        } else if model.isComplete {
            FlexrSecondaryButton(title: s(.verifyRetrySubmit)) {
                Task { await model.retrySubmit() }
            }
        } else if !hasCameraPermission {
            FlexrSecondaryButton(title: s(.verifyAllowCamera)) {
                Task {
                    hasCameraPermission = await camera.requestPermission()
                    if hasCameraPermission {
                        await camera.start()
                    } else {
                        // Zweite Ablehnung: iOS fragt nicht erneut, es geht nur
                        // noch über die Systemeinstellungen.
                        if let url = URL(string: UIApplication.openSettingsURLString) {
                            _ = await UIApplication.shared.open(url)
                        }
                    }
                }
            }
        } else {
            FlexrButton(title: s(.verifyCapture), icon: .symbol(FlexrIcon.camera)) {
                Task {
                    guard let image = await camera.capture() else {
                        appModel.show(s(.verifyCaptureFailed))
                        return
                    }
                    await model.onCaptured(image)
                }
            }
        }
    }
}
