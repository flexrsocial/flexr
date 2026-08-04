import SwiftUI

/// Paywall nach Ablauf des Probemonats.
///
/// Der Checkout läuft in einer externen Browser-Sitzung über Stripe — die App
/// nimmt zu keinem Zeitpunkt Zahlungsdaten entgegen.
struct PaywallView: View {

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var externalURL: ExternalURL?
    /// Nur für die Selbstlöschung - der Rest des Modells bleibt ungenutzt,
    /// load() wird bewusst nicht aufgerufen.
    @State private var accountModel: AccountModel?
    @State private var showDeleteDialog = false
    @State private var deletePassword = ""

    private let features = [
        "Unbegrenzt swipen & matchen in deinem Umkreis",
        "Chat mit allen Matches inklusive",
        "Monatlich kündbar, keine versteckten Kosten",
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                EmptyStateView(
                    icon: .symbol(FlexrIcon.locked),
                    title: "Probemonat vorbei",
                    message: "Dein kostenloser Monat ist abgelaufen. Schalte FLEXR wieder frei."
                )
                .padding(.top, 24)

                VStack(alignment: .leading, spacing: 0) {
                    Eyebrow(text: "Mitgliedschaft")
                    HStack(alignment: .bottom, spacing: 0) {
                        Text("5 €")
                            .flexrText(.displayMedium)
                            .foregroundStyle(FlexrColor.chalk)
                        Text(" / Monat")
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalkDim)
                            .padding(.bottom, 5)
                    }

                    ForEach(features, id: \.self) { feature in
                        HStack(alignment: .top, spacing: 10) {
                            Image(systemName: FlexrIcon.check)
                                .font(.system(size: 14, weight: .bold))
                                .foregroundStyle(FlexrColor.lime)
                            Text(feature)
                                .flexrText(.bodyMedium)
                                .foregroundStyle(FlexrColor.chalkDim)
                            Spacer(minLength: 0)
                        }
                        .padding(.vertical, 6)
                    }
                    .padding(.top, 10)

                    FlexrButton(title: "Jetzt abonnieren", action: startCheckout)
                        .padding(.top, 12)
                }
                .padding(20)
                .flexrSurface(radius: FlexrRadius.large, border: FlexrColor.plate.opacity(0.3))

                Text(
                    "Nach der Zahlung kehrst du automatisch in die App zurück. "
                        + "Falls der Status nicht sofort stimmt: kurz warten und erneut öffnen."
                )
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.top, 14)

                FlexrSecondaryButton(title: "Ausloggen") {
                    Task { await appModel.logout() }
                }
                .padding(.top, 24)

                // Nach Ablauf des Probemonats ist der Konto-Screen nicht mehr
                // erreichbar. Ohne diesen Knopf wäre die Selbstlöschung damit
                // unerreichbar - Punkt 5 der Datenschutzerklärung sagt sie zu.
                FlexrDangerButton(title: "Konto löschen") {
                    deletePassword = ""
                    showDeleteDialog = true
                }
                .padding(.top, 10)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 40)
        }
        .externalPage($externalURL)
        .task {
            if accountModel == nil {
                accountModel = AccountModel(container: container) { appModel.show($0) }
            }
        }
        .sheet(isPresented: $showDeleteDialog) {
            if let accountModel {
                DeleteAccountSheet(
                    password: $deletePassword,
                    error: accountModel.deleteError,
                    isDeleting: accountModel.isDeleting,
                    onConfirm: {
                        Task { await accountModel.deleteAccount(password: deletePassword) }
                    },
                    onDismiss: { showDeleteDialog = false }
                )
            }
        }
        .onChange(of: accountModel?.didDeleteAccount ?? false) { _, deleted in
            if deleted { Task { await appModel.logout() } }
        }
    }

    private func startCheckout() {
        Task {
            do {
                externalURL = ExternalURL(try await container.billing.checkoutURL())
            } catch {
                appModel.show(
                    (error as? FlexrAPIError)?.message ?? "Checkout konnte nicht gestartet werden."
                )
            }
        }
    }
}
