import SwiftUI

/// FLEXR Premium — das freiwillige Zusatzpaket.
///
/// War bis zum 10.09.2026 die Bezahlwand, auf der man nach Ablauf des
/// Probemonats zwangsweise landete. Die Nutzung von FLEXR kostet seither
/// dauerhaft nichts; dieser Bildschirm erklärt nur, was Premium zusätzlich
/// kann, und wird aus dem Kontobereich heraus aufgerufen — nie erzwungen.
///
/// Der Checkout läuft in einer externen Browser-Sitzung über Stripe — die App
/// nimmt zu keinem Zeitpunkt Zahlungsdaten entgegen.
struct PaywallView: View {
    /// Zurück in den Kontobereich, aus dem dieser Bildschirm aufgerufen wird.
    let onBack: () -> Void

    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    /// Nur für den Checkout — der Rest des Modells bleibt ungenutzt,
    /// load() wird bewusst nicht aufgerufen.
    @State private var accountModel: AccountModel?

    /// Die Vorteile mit den Zahlen des Servers. Wer die Grenzen in
    /// `config.py` ändert, ändert damit auch diese Liste.
    private var features: [String] {
        let m = appModel.membership
        return [
            m.map { s(.premiumFeatureLikes, $0.freeDailyLikes) } ?? s(.paywallFeatureUnlimited),
            m.map { s(.premiumFeatureChats, $0.freeOpenChats) } ?? s(.paywallFeatureChat),
            s(.premiumFeatureIncoming),
            s(.premiumFeatureRewind),
            m.map { s(.premiumFeatureRadius, max($0.maxRadiusKm, 250), $0.freeMaxRadiusKm) }
                ?? s(.premiumFeatureBadge),
            s(.premiumFeatureBadge),
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
                    Eyebrow(text: s(.premiumEyebrow))
                    HStack(alignment: .bottom, spacing: 0) {
                        // Preis aus dem Serverstatus, damit "10 €" nirgends im
                        // Client festgeschrieben ist.
                        Text(appModel.membership.map { "\($0.priceCents / 100) €" } ?? "10 €")
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

                    // Während der Beta gibt es nichts abzuschließen: Der Server
                    // lehnt den Checkout mit 409 ab, weil ohnehin für alle alles
                    // unbegrenzt ist. Statt eines Knopfes in die Sackgasse steht
                    // dann der Hinweis, dass Premium später kommt.
                    if appModel.membership?.premiumEnabled == false {
                        Text(s(.premiumBetaHint))
                            .flexrText(.bodySmall)
                            .foregroundStyle(FlexrColor.chalkDim)
                            .padding(.top, 12)
                    } else {
                        FlexrButton(title: s(.paywallSubscribe)) {
                            accountModel?.openCheckoutSheet()
                        }
                        .padding(.top, 12)
                    }
                }
                .padding(20)
                .flexrSurface(radius: FlexrRadius.large, border: FlexrColor.plate.opacity(0.3))

                Text(s(.paywallReturnNote))
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.top, 14)

                // Ausloggen und Selbstlöschung standen hier, solange dieser
                // Bildschirm der einzige erreichbare war. Der Kontobereich ist
                // jetzt immer navigierbar; beides sitzt dort, wo man es sucht.
                FlexrSecondaryButton(title: s(.commonBack)) { onBack() }
                    .padding(.top, 24)
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
    }
}
