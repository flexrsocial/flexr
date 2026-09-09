import SwiftUI

@MainActor
@Observable
final class LoginModel {

    var email = ""
    var password = ""
    var isSubmitting = false
    var error: String?
    /// Konto innerhalb der 30-Tage-Karenz nach Selbstlöschung — der Login
    /// bietet die Reaktivierung an, statt in eine Sackgasse zu führen.
    var reactivateMessage: String?
    var isReactivating = false

    var canSubmit: Bool { !email.isEmpty && !password.isEmpty && !isSubmitting }

    @ObservationIgnored private let auth: AuthRepository
    /// Texte in der gewählten Sprache — siehe [AccountModel] für die Begründung,
    /// warum hier der Speicher und keine Kopie steht.
    @ObservationIgnored private let languageStore: LanguageStore
    private var s: FlexrStrings { languageStore.strings }

    init(auth: AuthRepository, languageStore: LanguageStore) {
        self.auth = auth
        self.languageStore = languageStore
    }

    func login() async {
        guard !isSubmitting else { return }
        guard !email.isEmpty, !password.isEmpty else {
            error = s(.loginMissingFields)
            return
        }

        isSubmitting = true
        error = nil
        do {
            // Erfolg meldet der SessionStore; `AppModel` schaltet daraufhin um.
            try await auth.login(email: email, password: password)
        } catch {
            let apiError = error as? FlexrAPIError
            if apiError?.isAccountDeleted == true {
                // 403 mit code=account_deleted aus routers/auth.login: Das Konto
                // liegt noch in der 30-Tage-Karenz und lässt sich zurückholen.
                reactivateMessage = apiError?.message
            } else {
                self.error = apiError?.message ?? s(.loginFailed)
            }
        }
        isSubmitting = false
    }

    func dismissReactivate() {
        reactivateMessage = nil
    }

    /// Der Alert ist beim Tippen auf „Jetzt reaktivieren" bereits weg — ein
    /// Fehler landet deshalb im Fehlerfeld des Formulars, nicht im Alert.
    func reactivate() async {
        guard !isReactivating else { return }
        isReactivating = true
        error = nil
        do {
            try await auth.reactivate(email: email, password: password)
        } catch {
            self.error = (error as? FlexrAPIError)?.message ?? s(.loginReactivateFailed)
        }
        reactivateMessage = nil
        isReactivating = false
    }
}

struct LoginView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let onOpenLegal: (LegalDocument) -> Void

    @Environment(AppContainer.self) private var container
    @State private var model: LoginModel?
    @State private var showRegister = false

    var body: some View {
        Group {
            if let model {
                content(model)
            } else {
                Color.clear
            }
        }
        .onAppear {
            if model == nil {
                model = LoginModel(auth: container.auth, languageStore: languageStore)
            }
        }
        .fullScreenCover(isPresented: $showRegister) {
            RegisterView(
                onGoToLogin: { showRegister = false },
                onOpenLegal: onOpenLegal
            )
        }
    }

    @ViewBuilder
    private func content(_ model: LoginModel) -> some View {
        @Bindable var model = model

        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                AuthTabs(selected: .login) { tab in
                    if tab == .register { showRegister = true }
                }
                .padding(.top, 8)

                ScreenHeader(
                    eyebrow: s(.loginEyebrow),
                    title: s(.loginTitle),
                    subtitle: s(.loginSubtitle)
                )
                .padding(.top, 24)

                FlexrTextField(
                    text: $model.email,
                    label: s(.fieldEmail),
                    placeholder: s(.loginEmailPlaceholder),
                    keyboardType: .emailAddress,
                    textContentType: .username,
                    autocapitalization: .never
                )

                FlexrPasswordField(
                    text: $model.password,
                    label: s(.fieldPassword),
                    placeholder: "••••••••",
                    submitLabel: .go,
                    onSubmit: { Task { await model.login() } }
                )

                FieldError(message: model.error)

                FlexrButton(
                    title: s(.loginSubmit),
                    isEnabled: model.canSubmit,
                    isLoading: model.isSubmitting
                ) {
                    Task { await model.login() }
                }
                .padding(.top, 22)

                Text(s(.loginRegisterHint))
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .padding(.top, 28)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 40)
        }
        .scrollDismissesKeyboard(.interactively)
        .onChange(of: model.email) { _, _ in model.error = nil }
        .onChange(of: model.password) { _, _ in model.error = nil }
        .alert(
            s(.loginReactivateTitle),
            isPresented: Binding(
                get: { model.reactivateMessage != nil },
                set: { if !$0 { model.dismissReactivate() } }
            )
        ) {
            Button(s(.loginReactivateConfirm)) { Task { await model.reactivate() } }
            Button(s(.commonCancel), role: .cancel) { model.dismissReactivate() }
        } message: {
            Text(model.reactivateMessage ?? "")
        }
    }
}
