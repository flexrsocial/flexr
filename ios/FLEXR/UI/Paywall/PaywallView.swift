import SwiftUI

/// FLEXR Premium — das freiwillige Zusatzpaket.
///
/// War bis zum 10.09.2026 die Bezahlwand, auf der man nach Ablauf des
/// Probemonats zwangsweise landete. Die Nutzung von FLEXR kostet seither
/// dauerhaft nichts; dieser Bildschirm erklärt nur, was Premium zusätzlich
/// kann, und wird aus dem Kontobereich heraus aufgerufen — nie erzwungen.
///
/// Gekauft wird über den **App Store** — der einzige zulässige Weg für
/// Funktionen, die in dieser App wirken (App Review Guideline 3.1.1).
/// Zahlungsdaten nimmt die App zu keinem Zeitpunkt entgegen; sie reicht nur
/// den signierten Beleg beim Server ein, der ihn prüft.
///
/// Preis und Währung schreibt der App Store, nicht wir: Apple rechnet sie je
/// nach Land des Kontos. Solange sie noch nicht geladen sind, steht der Preis
/// aus dem Serverstatus da — er stimmt für Österreich, ist aber nur der
/// Platzhalter.
struct PaywallView: View {
    /// Zurück in den Kontobereich, aus dem dieser Bildschirm aufgerufen wird.
    let onBack: () -> Void

    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    /// Die Vorteile mit den Zahlen des Servers. Wer die Grenzen in
    /// `config.py` ändert, ändert damit auch diese Liste.
    private var features: [String] {
        let m = appModel.membership
        // Der Radius-Eintrag entfällt ohne Serverstatus ganz — ein Rückfall
        // auf den Abzeichen-Text hätte ihn doppelt gezeigt.
        return [
            m.map { s(.premiumFeatureLikes, $0.freeDailyLikes) } ?? s(.paywallFeatureUnlimited),
            m.map { s(.premiumFeatureChats, $0.freeOpenChats) } ?? s(.paywallFeatureChat),
            s(.premiumFeatureIncoming),
            s(.premiumFeatureRewind),
            m.map { s(.premiumFeatureRadius, max($0.maxRadiusKm, 250), $0.freeMaxRadiusKm) },
            s(.premiumFeatureBadge),
            s(.paywallFeatureCancel),
        ].compactMap { $0 }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                // Der erklaerende Absatz darunter ("FLEXR zu nutzen kostet
                // nichts ...") ist seit dem 19.09.2026 weg (analog zu Web/
                // Android) - die Preiskachel darunter ruekt dadurch von
                // selbst nach oben.
                EmptyStateView(
                    icon: .symbol(FlexrIcon.locked),
                    title: s(.paywallTitle)
                )
                .padding(.top, 24)

                VStack(alignment: .leading, spacing: 0) {
                    Eyebrow(text: s(.premiumEyebrow))
                    HStack(alignment: .bottom, spacing: 0) {
                        // Preis aus dem Serverstatus, damit "10 €" nirgends im
                        // Client festgeschrieben ist.
                        Text(
                            container.storeKit.preis
                                ?? appModel.membership.map { "\($0.priceCents / 100) €" }
                                ?? "10 €"
                        )
                            .flexrText(.displayMedium)
                            .foregroundStyle(FlexrColor.chalk)
                        Text(s(.paywallPerMonth))
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

                    // Gekauft werden kann nur, was der Server auch anbietet:
                    // Er meldet mit `storePurchaseAvailable`, ob dieser Client
                    // kaufen darf und unter welcher Produktkennung. Fehlt
                    // beides — weil Premium serverseitig aus ist oder noch kein
                    // Produkt eingetragen wurde —, steht statt eines Knopfes in
                    // die Sackgasse der Hinweis.
                    if let produktID = appModel.membership?.storeProductID,
                       appModel.membership?.storePurchaseAvailable == true {
                        FlexrButton(title: s(.paywallSubscribe)) {
                            Task { await kaufen(produktID) }
                        }
                        .padding(.top, 12)
                        .disabled(container.storeKit.laeuftKauf)
                    } else {
                        Text(s(.premiumBetaHint))
                            .flexrText(.bodySmall)
                            .foregroundStyle(FlexrColor.chalkDim)
                            .padding(.top, 12)
                    }
                }
                .padding(20)
                .flexrSurface(radius: FlexrRadius.large, border: FlexrColor.plate.opacity(0.3))

                // Ausloggen und Selbstlöschung standen hier, solange dieser
                // Bildschirm der einzige erreichbare war. Der Kontobereich ist
                // jetzt immer navigierbar; beides sitzt dort, wo man es sucht.
                FlexrSecondaryButton(title: s(.commonBack)) { onBack() }
                    .padding(.top, 24)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 40)
        }
        .task {
            // Den echten Preis holen, bevor jemand tippt.
            if let produktID = appModel.membership?.storeProductID {
                await container.storeKit.produktLaden(produktID)
            }
        }
    }

    /// Kauf anstoßen und das Ergebnis melden. Ein Abbruch bleibt bewusst
    /// stumm: Wer selbst abbricht, braucht darüber keine Meldung.
    private func kaufen(_ produktID: String) async {
        switch await container.storeKit.kaufen(produktID: produktID) {
        case .erfolgreich:
            // Der Server hat den Beleg angenommen — den Status frisch holen,
            // damit Abzeichen und Grenzen sofort stimmen.
            await appModel.refreshMembership()
            appModel.show(s(.purchaseSuccess))
        case .ausstehend:
            appModel.show(s(.purchasePending))
        case .fehlgeschlagen(let meldung):
            appModel.show(meldung)
        case .abgebrochen:
            break
        }
    }
}
