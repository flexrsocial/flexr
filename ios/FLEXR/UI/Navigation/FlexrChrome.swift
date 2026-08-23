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

/// Kopfzeile: Wortmarke links, Mitgliedschafts-Status rechts.
struct FlexrTopBar<Status: View>: View {

    @ViewBuilder var status: () -> Status

    var body: some View {
        VStack(spacing: 0) {
            HStack {
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

/// Statusanzeige im Kopf: Abo aktiv, Resttage im Probemonat oder abgelaufen.
struct MembershipPill: View {
    let membership: Membership

    var body: some View {
        if membership.isSubscribed {
            StatusPill(text: "Abo aktiv")
        } else if membership.isActive {
            StatusPill(text: "Testmonat: \(ServerTime.daysUntil(membership.trialEndsAt))d")
        } else {
            StatusPill(text: "Abgelaufen", isExpired: true)
        }
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
                            Text(destination.label.uppercased()).flexrText(.labelSmall)
                        }
                        .foregroundStyle(isSelected ? FlexrColor.plate : FlexrColor.chalkDim)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(destination.label)
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
                    .accessibilityLabel("Schließen")
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
