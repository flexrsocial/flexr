import SwiftUI

/// Kleine Mono-Vorzeile über einer Überschrift (`.eyebrow`).
struct Eyebrow: View {
    let text: String

    var body: some View {
        Text(text.uppercased())
            .flexrText(.eyebrow)
            .foregroundStyle(FlexrColor.plate)
            .padding(.bottom, 6)
    }
}

/// Standard-Kopf eines Bildschirms: Vorzeile plus Überschrift.
struct ScreenHeader: View {
    let eyebrow: String
    let title: String
    var subtitle: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Eyebrow(text: eyebrow)
            Text(title)
                .flexrText(.headlineMedium)
                .foregroundStyle(FlexrColor.chalk)
                .fixedSize(horizontal: false, vertical: true)
            if let subtitle {
                Text(subtitle)
                    .flexrText(.bodyMedium)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .padding(.top, 10)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// Leerzustand mit gestricheltem Symbolkreis (`.empty`).
struct EmptyStateView<Action: View>: View {

    let icon: FlexrGlyph.Kind
    let title: String
    let message: String
    @ViewBuilder var action: () -> Action

    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                Circle().fill(Color.white.opacity(0.015))
                Circle().strokeBorder(FlexrColor.steel, lineWidth: 1.5)
                FlexrGlyph(icon, size: 28)
                    .foregroundStyle(FlexrColor.chalkDim.opacity(0.8))
            }
            .frame(width: 68, height: 68)

            Text(title.uppercased())
                .flexrText(.headlineSmall)
                .foregroundStyle(FlexrColor.chalk)
                .multilineTextAlignment(.center)
                .padding(.top, 12)

            Text(message)
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 260)
                .padding(.top, 4)

            action().padding(.top, 20)
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, 24)
        .padding(.vertical, 48)
    }
}

extension EmptyStateView where Action == EmptyView {
    init(icon: FlexrGlyph.Kind, title: String, message: String) {
        self.init(icon: icon, title: title, message: message, action: { EmptyView() })
    }
}

/// Ganzflächiger Ladezustand.
struct LoadingStateView: View {
    var label: String?

    var body: some View {
        VStack(spacing: 14) {
            ProgressView().tint(FlexrColor.plate)
            if let label {
                Text(label).flexrText(.bodySmall).foregroundStyle(FlexrColor.chalkDim)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

/// Statusanzeige im Kopfbereich: Testmonat / Abo aktiv / abgelaufen.
struct StatusPill: View {
    let text: String
    var isExpired = false

    var body: some View {
        Text(text)
            .flexrText(.mono)
            .foregroundStyle(isExpired ? FlexrColor.danger : FlexrColor.lime)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(Capsule().fill(Color.white.opacity(0.02)))
            .overlay(
                Capsule().strokeBorder(
                    (isExpired ? FlexrColor.danger.opacity(0.4) : FlexrColor.lime.opacity(0.3)),
                    lineWidth: 1
                )
            )
    }
}

/// Blauer Haken für verifizierte Profile.
struct VerifiedBadge: View {
    var size: CGFloat = 16

    var body: some View {
        ZStack {
            Circle().fill(FlexrColor.verified)
            Image(systemName: FlexrIcon.check)
                .font(.system(size: size * 0.56, weight: .bold))
                .foregroundStyle(.white)
        }
        .frame(width: size, height: size)
        .accessibilityLabel("Verifiziertes Profil")
    }
}

/// Merkmal-Chip auf einer Profilkarte (`.stat-chip`).
struct StatChip: View {

    let text: String
    var icon: FlexrGlyph.Kind?
    var isAccent = false
    var hasPulsingDot = false

    @State private var pulse = false

    private var tint: Color { isAccent ? FlexrColor.plate : FlexrColor.lime }

    var body: some View {
        HStack(spacing: 6) {
            if hasPulsingDot {
                Circle()
                    .fill(tint)
                    .frame(width: 7, height: 7)
                    .opacity(pulse ? 0.45 : 1)
                    .animation(.easeInOut(duration: 1).repeatForever(autoreverses: true), value: pulse)
                    .onAppear { pulse = true }
            } else if let icon {
                FlexrGlyph(icon, size: 13).foregroundStyle(tint)
            }
            Text(text).flexrText(.mono).foregroundStyle(tint).lineLimit(1)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .flexrSurface(
            radius: FlexrRadius.extraSmall,
            fill: tint.opacity(0.08),
            border: tint.opacity(isAccent ? 0.35 : 0.24)
        )
    }
}

/// Feine Trennlinie im Markenstil (`--hairline`).
struct HairlineDivider: View {
    var color: Color = FlexrColor.hairline

    var body: some View {
        Rectangle().fill(color).frame(height: 1).frame(maxWidth: .infinity)
    }
}

/// Abschnittsüberschrift im Konto-Bereich.
struct SectionTitle: View {
    let text: String

    var body: some View {
        HStack(spacing: 12) {
            Text(text.uppercased())
                .flexrText(.headlineSmall)
                .foregroundStyle(FlexrColor.chalk)
            HairlineDivider()
        }
        .padding(.bottom, 4)
    }
}

/// Kartenfläche für Gruppen im Konto-Bereich.
struct FlexrCard<Content: View>: View {
    @ViewBuilder var content: () -> Content

    var body: some View {
        content()
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .flexrSurface()
    }
}

/// Zurück-Kopfzeile der Unterseiten (Chat, Profil, Verifizierung, Rechtstexte).
struct BackHeader<Trailing: View>: View {

    let title: String
    var titleStyle: FlexrTextStyle = .titleMedium
    let onBack: () -> Void
    @ViewBuilder var trailing: () -> Trailing

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 6) {
                Button(action: onBack) {
                    Image(systemName: FlexrIcon.back)
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(FlexrColor.chalk)
                        .frame(width: 36, height: 36)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Zurück")

                Text(title)
                    .flexrText(titleStyle)
                    .foregroundStyle(FlexrColor.chalk)
                    .lineLimit(1)

                Spacer(minLength: 8)
                trailing()
            }
            .padding(.vertical, 10)
            HairlineDivider()
        }
    }
}

extension BackHeader where Trailing == EmptyView {
    init(title: String, titleStyle: FlexrTextStyle = .titleMedium, onBack: @escaping () -> Void) {
        self.init(title: title, titleStyle: titleStyle, onBack: onBack, trailing: { EmptyView() })
    }
}
