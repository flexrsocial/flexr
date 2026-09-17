import SwiftUI

/// Wortmarke im Kopfbereich. Gesetzt nach der verbindlichen Markenvorgabe
/// (frontend/brand/README.md): „FLEX" in Kreideweiß, das „R" in Signalrot.
struct FlexrWordmark: View {
    var body: some View {
        (Text("FLEX").foregroundStyle(FlexrColor.chalk)
            + Text("R").foregroundStyle(FlexrColor.brandRed))
            .flexrText(.brand)
            .accessibilityLabel("FLEXR")
    }
}

/// Kopfzeile: Wortmarke links, rechts genau eine Anzeige.
///
/// Was rechts steht, entscheidet der jeweilige Navigationsbaum — wie in der
/// Android-App: ausgeloggt der Sprachregler, im Gate die Zustandspille,
/// in der fertigen App der Mitgliedschaftsstatus.
///
/// Der Regler stand hier früher zusätzlich auf jedem Bildschirm. Das war eine
/// Dopplung: Angemeldet ist er im Kontobereich erreichbar, und dort steht er
/// mit Beschriftung und Hinweis statt nur als Kürzel. Unerreichbar wäre er nur
/// vor dem Login — genau dort bleibt er deshalb.
struct FlexrTopBar<Status: View>: View {

    @ViewBuilder var status: () -> Status

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 10) {
                FlexrWordmark()
                Spacer()
                status()
            }
            .padding(.horizontal, 20)
            .padding(.top, 14)
            .padding(.bottom, 12)

            ZStack(alignment: .leading) {
                HairlineDivider()
                // Akzentstrich links unter der Kopfzeile, wie im Web
                // (header.top::after).
                Rectangle()
                    .fill(FlexrColor.plate)
                    .frame(width: 64, height: 2)
                    .padding(.leading, 20)
            }
        }
    }
}

/// Statusanzeige im Kopf.
///
/// Es gibt nichts mehr herunterzuzählen: Früher stand hier die Restlaufzeit des
/// Probemonats. Was knapp werden kann, sind die Likes des kostenlosen Kontos —
/// und genau die zeigt die Pille jetzt.
struct MembershipPill: View {
    let membership: Membership

    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    /// Was gerade knapp werden kann — oder, wenn nichts knapp wird, was das
    /// Konto kostet.
    private var zustand: String {
        if membership.isPremium { return s(.statusPremium) }
        if membership.limitsActive, let rest = membership.likesRemaining {
            return s(.statusLikesLeft, rest)
        }
        return s(.statusFree)
    }

    /// Bei erschöpftem Kontingent färbt sich die Pille — mit Premium oder ohne
    /// geltende Grenzen gibt es nichts zu färben.
    private var erschoepft: Bool {
        !membership.isPremium && membership.limitsActive && membership.likesRemaining == 0
    }

    var body: some View {
        // „Beta" steht davor, statt den Zustand zu ersetzen: Bis 17.09.2026
        // hing das Abzeichen daran, dass Premium noch nicht kaufbar war, und
        // wäre beim Scharfschalten von selbst verschwunden — obwohl FLEXR
        // unverändert im Aufbau ist.
        StatusPill(
            text: membership.betaActive ? s(.statusBetaPrefix, zustand) : zustand,
            isExpired: erschoepft
        )
    }
}

/// Untere Hauptnavigation mit Ungelesen-Zähler am Chat-Symbol.
///
/// Bewusst eine eigene Leiste statt `TabView`: Der Marken-Look (Hantel-Symbol,
/// Orange-Akzent, Mono-Beschriftung) lässt sich in der Systemleiste nicht
/// abbilden, und der Zähler soll wie im Web aussehen.
struct FlexrTabBar: View {

    @Binding var selection: TopLevelDestination
    let unreadCount: Int

    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    var body: some View {
        VStack(spacing: 0) {
            HairlineDivider()
            HStack(spacing: 0) {
                ForEach(TopLevelDestination.allCases) { destination in
                    let isSelected = destination == selection
                    Button {
                        selection = destination
                    } label: {
                        VStack(spacing: 4) {
                            ZStack(alignment: .topTrailing) {
                                FlexrGlyph(destination.icon, size: 22)
                                if destination == .chats, unreadCount > 0 {
                                    Text(unreadCount > 99 ? "99+" : "\(unreadCount)")
                                        .flexrText(.labelSmall)
                                        .foregroundStyle(FlexrColor.plateInk)
                                        .padding(.horizontal, 5)
                                        .padding(.vertical, 2)
                                        .background(Capsule().fill(FlexrColor.plate))
                                        .offset(x: 12, y: -8)
                                }
                            }
                            Text(s(destination.labelKey).uppercased()).flexrText(.labelSmall)
                        }
                        .foregroundStyle(isSelected ? FlexrColor.plate : FlexrColor.chalkDim)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(s(destination.labelKey))
                    .accessibilityAddTraits(isSelected ? [.isSelected] : [])
                }
            }
            .padding(.top, 8)
            .background(FlexrColor.ink.opacity(0.96))
        }
    }
}

/// Kurze Rückmeldung am unteren Rand — die Entsprechung der Material-Snackbar.
struct ToastOverlay: View {

    @Binding var message: String?

    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    var body: some View {
        VStack {
            Spacer()
            if let message {
                HStack(alignment: .top, spacing: 8) {
                    Text(message)
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalk)
                        .multilineTextAlignment(.leading)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Button { self.message = nil } label: {
                        Image(systemName: FlexrIcon.close)
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(FlexrColor.chalkDim)
                            .frame(width: 24, height: 24)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(s(.commonClose))
                }
                .padding(.leading, 16)
                .padding(.trailing, 8)
                .padding(.vertical, 13)
                .flexrSurface(fill: FlexrColor.surface3, border: FlexrColor.steel)
                .padding(.horizontal, 16)
                .padding(.bottom, 12)
                .transition(.move(edge: .bottom).combined(with: .opacity))
                .onTapGesture { self.message = nil }
                // Erst 4 s, dann 10 s — laut Rückmeldung immer noch zu kurz.
                // Widerrufs-Folgetexte (AccountView, revokeConsent) sind lang;
                // dazu jetzt ein Schließen-Knopf, damit 20 s nicht im Weg sind.
                .task(id: message) {
                    try? await Task.sleep(for: .seconds(20))
                    if !Task.isCancelled { self.message = nil }
                }
            }
        }
        .animation(.easeOut(duration: 0.22), value: message)
        .allowsHitTesting(message != nil)
    }
}
