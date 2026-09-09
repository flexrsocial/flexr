import SwiftUI

/// Paywall nach Ablauf des Probemonats.
///
/// Der Checkout läuft in einer externen Browser-Sitzung über Stripe — die App
/// nimmt zu keinem Zeitpunkt Zahlungsdaten entgegen.
struct PaywallView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    /// Für Selbstlöschung UND Checkout - der Rest des Modells bleibt ungenutzt,
    /// load() wird bewusst nicht aufgerufen.
    @State private var accountModel: AccountModel?
    @State private var showDeleteDialog = false
    @State private var deletePassword = ""

    private var features: [String] {
        [
            s(.paywallFeatureUnlimited),
            s(.paywallFeatureChat),
            s(.paywallFeatureCancel),
        ]
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                EmptyStateView(
                    icon: .symbol(FlexrIcon.locked),
                    title: s(.paywallTitle),
                    message: s(.paywallSub)
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

                    FlexrButton(title: s(.paywallSubscribe)) {
                        accountModel?.openCheckoutSheet()
                    }
                    .padding(.top, 12)
                }
                .padding(20)
                .flexrSurface(radius: FlexrRadius.large, border: FlexrColor.plate.opacity(0.3))

                Text(s(.paywallReturnNote))
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.top, 14)

                FlexrSecondaryButton(title: s(.commonLogout)) {
                    Task { await appModel.logout() }
                }
                .padding(.top, 24)

                // Nach Ablauf des Probemonats ist der Konto-Screen nicht mehr
                // erreichbar. Ohne diesen Knopf wäre die Selbstlöschung damit
                // unerreichbar - Punkt 5 der Datenschutzerklärung sagt sie zu.
                FlexrDangerButton(title: s(.commonDeleteAccount)) {
                    deletePassword = ""
                    showDeleteDialog = true
                }
                .padding(.top, 10)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 40)
        }
        .externalPage(
            Binding(
                get: { accountModel?.externalURL },
                set: { accountModel?.externalURL = $0 }
            )
        )
        .task {
            if accountModel == nil {
                accountModel = AccountModel(container: container, languageStore: languageStore) {
                    appModel.show($0)
                }
            }
        }
        .sheet(isPresented: Binding(
            get: { accountModel?.checkoutSheetVisible ?? false },
            set: { if !$0 { accountModel?.closeCheckoutSheet() } }
        )) {
            if let accountModel {
                CheckoutConsentSheet(
                    immediateStart: Binding(
                        get: { accountModel.checkoutImmediateStart },
                        set: { accountModel.checkoutImmediateStart = $0 }
                    ),
                    withdrawalAck: Binding(
                        get: { accountModel.checkoutWithdrawalAck },
                        set: { accountModel.checkoutWithdrawalAck = $0 }
                    ),
                    error: accountModel.checkoutError,
                    isStarting: accountModel.isStartingCheckout,
                    onConfirm: { Task { await accountModel.confirmCheckout() } },
                    onDismiss: accountModel.closeCheckoutSheet
                )
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
}
