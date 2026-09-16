import SwiftUI

/// Übersicht der Alters- und Identitätsprüfung für ein noch nicht
/// freigeschaltetes Konto: Was steht an, was wurde bemängelt, wie geht es
/// weiter.
@MainActor
@Observable
final class VerificationGateModel {

    var verification: VerificationState?
    var isLoading = true
    var isRefreshing = false
    var error: String?

    var isUploadingPhoto = false
    var photoError: String?

    var isSendingMail = false
    var mailError: String?

    // Kontolöschung bleibt auch für ein gesperrtes Konto erreichbar — sonst
    // wäre eine abgelehnte Prüfung eine Sackgasse.
    var isDeleting = false
    var deleteError: String?
    var didDeleteAccount = false

    @ObservationIgnored private let verificationRepo: VerificationRepository
    @ObservationIgnored private let profiles: ProfileRepository
    @ObservationIgnored private let languageStore: LanguageStore
    private var s: FlexrStrings { languageStore.strings }

    init(container: AppContainer, languageStore: LanguageStore) {
        self.languageStore = languageStore
        verificationRepo = container.verification
        profiles = container.profiles
    }

    // MARK: - Abgeleitet aus Profil und Prüfstand

    /// Wie viele Profilfotos das Konto hat.
    ///
    /// Unter [ImageProcessor.minPhotos] lehnt der Server den Start der Prüfung
    /// ab. Das passiert, wenn Uploads während der Registrierung scheitern — und
    /// ohne einen Weg, sie hier nachzureichen, bliebe das Konto dauerhaft
    /// stecken: Der Kontobereich liegt im Hauptbaum und ist von hier nicht
    /// erreichbar.
    ///
    /// Solange kein Profil geladen ist, gilt die Mindestanzahl als erfüllt —
    /// sonst fragte der Schirm für einen Augenblick nach Fotos, die längst da
    /// sind.
    var photoCount: Int { profiles.myProfile?.photos.count ?? ImageProcessor.minPhotos }

    /// Eigene Adresse — der Nutzer muss sehen, wohin die Mail ging.
    var email: String { profiles.myProfile?.email ?? "" }

    /// Wie viele Fotos bis zur Mindestanzahl noch fehlen (0, wenn erfüllt).
    var missingPhotos: Int { max(ImageProcessor.minPhotos - photoCount, 0) }

    /// Genug Fotos, damit der Server den Start der Prüfung annimmt.
    var hasRequiredPhotos: Bool { missingPhotos == 0 }

    var step: VerificationNextStep { verification?.nextStep ?? .selfie }
    var status: VerificationStatus { verification?.status ?? .none }
    var isWaiting: Bool { status == .submitted }
    var isRejected: Bool { status == .rejected }

    /// Der Prüfer hat eine neue Aufnahme angefordert.
    var needsNewUpload: Bool { status == .reuploadRequired }

    /// Die Prüfung ist durch und das Konto freigeschaltet. Der Bildschirm darf
    /// dann nicht stehen bleiben — er ist der einzige seines Navigationsbaums,
    /// und der Baum wechselt erst, wenn die Sitzung neu geladen wird.
    var isActivated: Bool { verification?.accountActivated == true }

    /// Die E-Mail-Adresse ist noch nicht bestätigt. Steht vor allen anderen
    /// Schritten: Der Server lehnt `/verification/start` sonst ab, und ein
    /// Mensch soll keine Ausweisaufnahme begutachten, solange nicht feststeht,
    /// dass die Adresse dem Nutzer gehört.
    var needsEmailConfirmation: Bool { verification?.emailVerified == false }

    // MARK: - Laden

    func load() async {
        // Beim Nachladen keinen Ladebildschirm zeigen — der Inhalt steht schon.
        isLoading = verification == nil
        error = nil
        do {
            verification = try await verificationRepo.status()
            isLoading = false
        } catch {
            isLoading = false
            self.error = (error as? FlexrAPIError)?.message ?? s(.documentStatusLoadFailed)
        }
    }

    /// „Status aktualisieren" im Wartezustand.
    ///
    /// Die Freischaltung steht in der Statusantwort selbst
    /// (`account_activated`); sie landet im Zustand, und die Ansicht stößt
    /// daraufhin das Neuladen der Sitzung an. Wer noch wartet, bekommt
    /// wenigstens die Rückmeldung, dass die Prüfung läuft — ohne sie sähe ein
    /// Druck auf den Knopf wie ein Fehler aus.
    func refresh(onStillWaiting: (String) -> Void) async {
        isRefreshing = true
        error = nil
        do {
            let state = try await verificationRepo.status()
            verification = state
            isRefreshing = false
            if !state.accountActivated { onStillWaiting(s(.vgateReviewRunning)) }
        } catch {
            isRefreshing = false
            self.error = (error as? FlexrAPIError)?.message ?? s(.documentStatusLoadFailed)
        }
    }

    // MARK: - Fotos nachreichen

    /// Profilfotos nachreichen, wenn Uploads bei der Registrierung scheiterten.
    ///
    /// Ohne diesen Weg bliebe nur Abmelden (was zurück auf denselben Schirm
    /// führt) oder Kontolöschung — die Fotoverwaltung gehört zum Hauptbaum, den
    /// ein nicht freigeschaltetes Konto nie erreicht.
    func onPhotoPicked(_ data: Data) async {
        isUploadingPhoto = true
        photoError = nil
        do {
            let prepared = try await ImageProcessor.prepare(data: data)
            _ = try await profiles.addPhoto(prepared)
            // Der Prüfstand hängt an der Fotozahl: Mit dem letzten Pflichtfoto
            // wird aus „Fotos fehlen" der Selfie-Schritt.
            await load()
        } catch let error as PhotoTooSmallError {
            photoError = s(.photoTooSmall, error.width, error.height,
                           ImageProcessor.minEdgePx, ImageProcessor.minEdgePx)
        } catch let error as FlexrAPIError {
            photoError = error.message
        } catch {
            photoError = s(.vgatePhotoUploadFailed)
        }
        isUploadingPhoto = false
    }

    // MARK: - E-Mail

    /// Neuen Aktivierungslink anfordern.
    ///
    /// Der Server verwirft dabei einen noch offenen Link — zwei gleichzeitig
    /// gültige Links wären eine unnötig große Angriffsfläche.
    func resendVerificationEmail(onSent: (String) -> Void) async {
        guard !isSendingMail else { return }
        isSendingMail = true
        mailError = nil
        do {
            let info = try await verificationRepo.resendVerificationEmail()
            onSent(s(.vgateMailResent, info.email, info.validHours))
        } catch {
            mailError = (error as? FlexrAPIError)?.message ?? s(.vgateMailSendFailed)
        }
        isSendingMail = false
    }

    // MARK: - Konto löschen

    func deleteAccount(password: String) async {
        guard !password.isEmpty else {
            deleteError = s(.deletePasswordMissing)
            return
        }
        isDeleting = true
        deleteError = nil
        do {
            try await profiles.deleteAccount(password: password)
            didDeleteAccount = true
        } catch {
            deleteError = (error as? FlexrAPIError)?.message ?? s(.commonDeleteFailed)
        }
        isDeleting = false
    }
}

/// Einziger erreichbarer Bildschirm, solange ein Konto die Alters- und
/// Identitätsprüfung nicht bestanden hat.
///
/// Abmelden und Kontolöschung bleiben zugänglich — ohne sie wäre ein
/// abgelehntes Konto eine Sackgasse.
struct VerificationGateView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    /// Ändert sich, sobald ein Prüfschritt betreten oder verlassen wurde —
    /// Anlass, den Stand neu zu holen.
    let reloadToken: Int
    let onStartSelfies: () -> Void
    let onStartDocument: () -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel
    @Environment(\.scenePhase) private var scenePhase

    @State private var model: VerificationGateModel?
    @State private var showDeleteSheet = false
    @State private var deletePassword = ""

    var body: some View {
        Group {
            if let model {
                content(model)
            } else {
                LoadingStateView(label: s(.vgateLoading))
            }
        }
        .task {
            let created = model ?? VerificationGateModel(
                container: container,
                languageStore: languageStore
            )
            model = created
            await created.load()
            // Wie im Ausweisschritt: Steht die Freischaltung schon beim ersten
            // Laden fest, hat die Ansicht den alten Wert nie gesehen — onChange
            // bliebe stumm. Das passiert, wenn zwischen Profilabruf und
            // Statusabruf freigegeben wurde.
            if created.isActivated { await appModel.loadSession() }
        }
        // Rückkehr aus dem Hintergrund: Der Bestätigungslink wird im Browser
        // geöffnet, nicht in der App — ohne dieses Nachladen bliebe der Schirm
        // danach auf „Bestätigung offen" stehen.
        .onChange(of: scenePhase) { _, phase in
            guard phase == .active else { return }
            Task { await model?.load() }
        }
        .onChange(of: reloadToken) { _, _ in
            Task { await model?.load() }
        }
    }

    @ViewBuilder
    private func content(_ model: VerificationGateModel) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                if model.isLoading {
                    LoadingStateView(label: s(.vgateLoading))
                        .padding(.top, 40)
                } else {
                    step(model)
                    FieldError(message: model.error)
                }

                SectionTitle(text: s(.commonAccount))
                    .padding(.top, 28)

                FlexrSecondaryButton(title: s(.commonLogout)) {
                    Task { await appModel.logout() }
                }
                .padding(.top, 10)

                FlexrDangerButton(title: s(.commonDeleteAccount)) {
                    deletePassword = ""
                    showDeleteSheet = true
                }
                .padding(.top, 4)
            }
            .padding(.horizontal, 20)
            .padding(.top, 10)
            .padding(.bottom, 24)
        }
        // Freischaltung erkannt — egal ob über „Status aktualisieren" oder über
        // das Nachladen bei der Rückkehr in die App. Nur eine neu geladene
        // Sitzung führt aus diesem Navigationsbaum heraus.
        .onChange(of: model.isActivated) { _, activated in
            if activated { Task { await appModel.loadSession() } }
        }
        .onChange(of: model.didDeleteAccount) { _, deleted in
            if deleted { Task { await appModel.logout() } }
        }
        .sheet(isPresented: $showDeleteSheet) {
            DeleteAccountSheet(
                password: $deletePassword,
                error: model.deleteError,
                isDeleting: model.isDeleting,
                onConfirm: { Task { await model.deleteAccount(password: deletePassword) } },
                onDismiss: { showDeleteSheet = false }
            )
        }
    }

    /// Welcher Schritt gerade ansteht. Die Reihenfolge der Abfragen ist die
    /// Reihenfolge der Schritte — und nicht beliebig.
    @ViewBuilder
    private func step(_ model: VerificationGateModel) -> some View {
        if model.isActivated {
            // Zuerst prüfen: Ein freigeschaltetes Konto meldet „approved" und
            // keinen offenen Schritt mehr — ohne diesen Zweig sähe das wie ein
            // neuer Anfang aus („Verifizierung starten").
            ActivatedContent { Task { await appModel.loadSession() } }
        } else if model.isWaiting {
            WaitingContent(isRefreshing: model.isRefreshing) {
                Task { await model.refresh { appModel.show($0) } }
            }
        } else if model.isRejected {
            RejectedContent(reason: model.verification?.reason)
        } else if model.needsEmailConfirmation {
            // Ganz vorn: die bestätigte Adresse. Ohne sie lehnt der Server den
            // Start ab.
            EmailPendingContent(
                email: model.email,
                isSending: model.isSendingMail,
                error: model.mailError,
                onResend: {
                    Task { await model.resendVerificationEmail { appModel.show($0) } }
                }
            )
        } else if !model.hasRequiredPhotos {
            // Danach: Unter der Mindestanzahl an Profilfotos lehnt der Server
            // den Start ebenfalls ab, und von hier führt sonst kein Weg zum
            // Upload.
            MissingPhotoContent(
                missing: model.missingPhotos,
                isUploading: model.isUploadingPhoto,
                error: model.photoError,
                onPhotoPicked: { data in Task { await model.onPhotoPicked(data) } }
            )
        } else if model.step == .document {
            DocumentPendingContent(
                needsNewUpload: model.needsNewUpload,
                reason: model.verification?.reason,
                onContinue: onStartDocument
            )
        } else {
            SelfiePendingContent(
                needsNewUpload: model.needsNewUpload,
                reason: model.verification?.reason,
                onContinue: onStartSelfies
            )
        }
    }
}

// MARK: - Schritt 1: Selfies

private struct SelfiePendingContent: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let needsNewUpload: Bool
    let reason: String?
    let onContinue: () -> Void

    var body: some View {
        // Die Schlüssel vorab und ausdrücklich typisiert: `s` ist überladen,
        // ein Bedingungsoperator mitten im Aufruf macht dem Übersetzer die
        // Herleitung unnötig schwer.
        let eyebrowKey: L = needsNewUpload ? .vgateReworkEyebrow : .vgateStep1of2
        let titleKey: L = needsNewUpload ? .vgateReworkTitle : .vgateUnlockTitle
        let buttonKey: L = needsNewUpload ? .vgateRetry : .vgateStart

        VStack(alignment: .leading, spacing: 0) {
            GateHeader(
                eyebrow: s(eyebrowKey),
                title: s(titleKey),
                stepIndex: 1,
                chip: needsNewUpload ? GateChip.Content(text: s(.vgateReworkChip), isDanger: true) : nil
            )

            FlexrCard {
                VStack(alignment: .leading, spacing: 10) {
                    if let reason, !reason.isEmpty {
                        Text(reason)
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalk)
                    }
                    Text(s(.vgateIntro))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                    Eyebrow(text: s(.vgateNeedTitle))
                        .padding(.top, 2)
                    Bullet(text: s(.vgateNeedSelfie))
                    Bullet(text: s(.vgateNeedDocument))
                }
            }

            FlexrCard {
                VStack(alignment: .leading, spacing: 10) {
                    Eyebrow(text: s(.vgateMediaTitle))
                    Bullet(text: s(.vgateMediaHuman))
                    Bullet(text: s(.vgateMediaPrivate))
                    Bullet(text: s(.vgateMediaDeleted))
                }
            }
            .padding(.top, 12)

            FlexrButton(title: s(buttonKey), action: onContinue)
                .padding(.top, 18)
        }
    }
}

// MARK: - Schritt 2: Ausweis

private struct DocumentPendingContent: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let needsNewUpload: Bool
    let reason: String?
    let onContinue: () -> Void

    var body: some View {
        let eyebrowKey: L = needsNewUpload ? .vgateReworkEyebrow : .vgateStep2of2
        let titleKey: L = needsNewUpload ? .vgateReworkTitle : .vgateDocumentTitle
        let buttonKey: L = needsNewUpload ? .vgateDocumentBtnRework : .vgateDocumentBtn

        VStack(alignment: .leading, spacing: 0) {
            GateHeader(
                eyebrow: s(eyebrowKey),
                title: s(titleKey),
                stepIndex: 2,
                chip: needsNewUpload ? GateChip.Content(text: s(.vgateReworkChip), isDanger: true) : nil
            )

            FlexrCard {
                VStack(alignment: .leading, spacing: 10) {
                    if let reason, !reason.isEmpty {
                        Text(reason)
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalk)
                    }
                    Text(s(.vgateDocumentBody))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
            }

            FlexrButton(title: s(buttonKey), action: onContinue)
                .padding(.top, 18)
        }
    }
}

// MARK: - In Prüfung

private struct WaitingContent: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let isRefreshing: Bool
    let onRefresh: () -> Void

    var body: some View {
        let buttonKey: L = isRefreshing ? .vgateChecking : .vgateRefresh

        VStack(alignment: .leading, spacing: 0) {
            GateHeader(
                eyebrow: s(.vgateSubmittedEyebrow),
                title: s(.vgateSubmittedTitle),
                stepIndex: 3,
                chip: GateChip.Content(text: s(.vgateSubmittedChip), isDanger: false)
            )

            FlexrCard {
                VStack(alignment: .leading, spacing: 10) {
                    Text(s(.vgateSubmittedBody))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                    Text(s(.vgateSubmittedNote))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
            }

            FlexrButton(
                title: s(buttonKey),
                isEnabled: !isRefreshing,
                isLoading: isRefreshing,
                action: onRefresh
            )
            .padding(.top, 18)
        }
    }
}

// MARK: - E-Mail noch nicht bestätigt

/// Erster Schritt für ein frisch registriertes Konto. Die Adresse steht
/// absichtlich groß da: Ein Tippfehler bei der Registrierung fällt sonst nie
/// auf, und ohne „Passwort vergessen" wäre das Konto damit unrettbar.
private struct EmailPendingContent: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let email: String
    let isSending: Bool
    let error: String?
    let onResend: () -> Void

    var body: some View {
        let buttonKey: L = isSending ? .vgateMailSending : .vgateMailResend

        VStack(alignment: .leading, spacing: 0) {
            GateHeader(
                eyebrow: s(.vgateStep1of3),
                title: s(.vgateMailTitle),
                stepIndex: 1,
                chip: GateChip.Content(text: s(.vgateMailChip), isDanger: false)
            )

            FlexrCard {
                VStack(alignment: .leading, spacing: 8) {
                    Text(s(.vgateMailSentTo))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                    Text(email.isEmpty ? s(.vgateMailFallback) : email)
                        .flexrText(.bodyLarge)
                        .foregroundStyle(FlexrColor.chalk)
                    Text(s(.vgateMailBody))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                        .padding(.top, 2)
                }
            }

            FieldError(message: error)

            FlexrButton(
                title: s(buttonKey),
                isEnabled: !isSending,
                isLoading: isSending,
                action: onResend
            )
            .padding(.top, 18)
        }
    }
}

// MARK: - Zu wenige Profilfotos

/// Die Uploads während der Registrierung können scheitern (Funkloch, Aussetzer
/// im Objektspeicher) — das Konto hat dann weniger als die geforderten
/// [ImageProcessor.minPhotos] Fotos. Die Prüfung lässt sich so nicht starten,
/// und die Fotoverwaltung liegt im Hauptbaum, den ein nicht freigeschaltetes
/// Konto nie zu sehen bekommt. Ohne diesen Nachreich-Weg bliebe nur die
/// Kontolöschung.
private struct MissingPhotoContent: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let missing: Int
    let isUploading: Bool
    let error: String?
    let onPhotoPicked: (Data) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            GateHeader(
                eyebrow: s(.vgatePhotoEyebrow),
                title: s(.vgatePhotoTitle),
                stepIndex: 1,
                chip: GateChip.Content(text: s(.vgatePhotoChip), isDanger: true)
            )

            FlexrCard {
                VStack(alignment: .leading, spacing: 10) {
                    Text(s(.vgatePhotoBody, ImageProcessor.minPhotos))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                    Text(s(.vgatePhotoBody2))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                    Text(s(.vgatePhotoMissing, missing, ImageProcessor.minPhotos))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.plate)
                }
            }

            // Genau so viele leere Felder, wie noch fehlen: Die schon
            // hochgeladenen Bilder zeigt dieser Schirm nicht — er verwaltet
            // keine Fotos, er holt nur die Mindestanzahl nach. Entfernen bleibt
            // aus, unterhalb der Mindestanzahl lässt der Server ohnehin nichts
            // löschen.
            PhotoGridEditor(
                slots: [],
                onPhotoPicked: onPhotoPicked,
                onRemove: { _ in },
                maxPhotos: missing
            )
            .padding(.top, 14)

            if isUploading {
                HStack(spacing: 8) {
                    ProgressView().controlSize(.mini).tint(FlexrColor.plate)
                    Text(s(.vgatePhotoUploading))
                        .flexrText(.bodySmall)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
                .padding(.top, 10)
            }

            FieldError(message: error)
        }
    }
}

// MARK: - Freigeschaltet, die App zieht gleich nach

/// Sichtbar wird das nur für einen Augenblick: Der Bildschirm stößt beim
/// Erkennen der Freischaltung sofort das Neuladen der Sitzung an, danach ist
/// dieser Navigationsbaum weg. Bleibt es hängen, weil das Nachladen scheiterte,
/// führt der Knopf hier heraus — ein Wartebildschirm ohne Ausweg wäre die
/// schlechtere Antwort auf einen Netzfehler.
private struct ActivatedContent: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let onContinue: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            GateHeader(
                eyebrow: s(.vgateDoneEyebrow),
                title: s(.vgateUnlockedTitle),
                stepIndex: 3,
                chip: GateChip.Content(text: s(.vgateUnlockedChip), isDanger: false)
            )

            FlexrCard {
                Text(s(.vgateUnlockedBody))
                    .flexrText(.bodyMedium)
                    .foregroundStyle(FlexrColor.chalkDim)
            }

            FlexrButton(title: s(.vgateUnlockedCta), action: onContinue)
                .padding(.top, 18)
        }
    }
}

// MARK: - Endgültig abgelehnt

private struct RejectedContent: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let reason: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            GateHeader(
                eyebrow: s(.vgateRejectedEyebrow),
                title: s(.vgateRejectedTitle),
                stepIndex: 3,
                chip: GateChip.Content(text: s(.vgateRejectedChip), isDanger: true)
            )

            FlexrCard {
                VStack(alignment: .leading, spacing: 10) {
                    Text(reason ?? s(.vgateRejectedFallback))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalk)
                    Text(s(.vgateRejectedBody))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                    Text(s(.vgateRejectedDeleted))
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
            }
        }
    }
}

// MARK: - Bausteine

/// Vorzeile, Überschrift, Schrittanzeige und Zustandsmarke — bei jedem der
/// sechs Zustände derselbe Aufbau.
private struct GateHeader: View {

    let eyebrow: String
    let title: String
    let stepIndex: Int
    var chip: GateChip.Content?

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Eyebrow(text: eyebrow)
            Text(title)
                .flexrText(.headlineMedium)
                .foregroundStyle(FlexrColor.chalk)
                .fixedSize(horizontal: false, vertical: true)
            VerificationStepBar(current: stepIndex)
                .padding(.top, 14)
            if let chip {
                GateChip(content: chip)
                    .padding(.top, 14)
            }
        }
        .padding(.bottom, 14)
    }
}

private struct GateChip: View {

    struct Content {
        let text: String
        let isDanger: Bool
    }

    let content: Content

    private var tint: Color { content.isDanger ? FlexrColor.danger : FlexrColor.plate }

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(tint)
                .frame(width: 7, height: 7)
            Text(content.text.uppercased())
                .flexrText(.labelSmall)
                .foregroundStyle(tint)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .overlay(Capsule().strokeBorder(tint.opacity(0.4), lineWidth: 1))
    }
}

private struct Bullet: View {

    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Text("•")
                .flexrText(.bodyMedium)
                .foregroundStyle(FlexrColor.plate)
            Text(text)
                .flexrText(.bodyMedium)
                .foregroundStyle(FlexrColor.chalkDim)
            Spacer(minLength: 0)
        }
    }
}
