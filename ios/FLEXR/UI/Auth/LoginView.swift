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

    init(auth: AuthRepository) {
        self.auth = auth
    }

    func login() async {
        guard !isSubmitting else { return }
        guard !email.isEmpty, !password.isEmpty else {
            error = "Bitte E-Mail und Passwort angeben."
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
                self.error = apiError?.message ?? "Login fehlgeschlagen."
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
            self.error = (error as? FlexrAPIError)?.message ?? "Reaktivierung fehlgeschlagen."
        }
        reactivateMessage = nil
        isReactivating = false
    }
}

struct LoginView: View {

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
            if model == nil { model = LoginModel(auth: container.auth) }
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
                    eyebrow: "Willkommen zurück",
                    title: "Zurück ins\nGym-Date.",
                    subtitle: "Melde dich mit deinen Zugangsdaten an."
                )
                .padding(.top, 24)

                FlexrTextField(
                    text: $model.email,
                    label: "E-Mail",
                    placeholder: "max@example.com",
                    keyboardType: .emailAddress,
                    textContentType: .username,
                    autocapitalization: .never
                )

                FlexrPasswordField(
                    text: $model.password,
                    label: "Passwort",
                    placeholder: "••••••••",
                    submitLabel: .go,
                    onSubmit: { Task { await model.login() } }
                )

                FieldError(message: model.error)

                FlexrButton(
                    title: "Einloggen",
                    isEnabled: model.canSubmit,
                    isLoading: model.isSubmitting
                ) {
                    Task { await model.login() }
                }
                .padding(.top, 22)

                Text("Neu hier? Erstell dein Profil und teste FLEXR einen Monat gratis.")
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
            "Konto reaktivieren?",
            isPresented: Binding(
                get: { model.reactivateMessage != nil },
                set: { if !$0 { model.dismissReactivate() } }
            )
        ) {
            Button("Jetzt reaktivieren") { Task { await model.reactivate() } }
            Button("Abbrechen", role: .cancel) { model.dismissReactivate() }
        } message: {
            Text(model.reactivateMessage ?? "")
        }
    }
}
