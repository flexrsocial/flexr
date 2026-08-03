import SwiftUI

/// Primäre Aktion der Marke: Orange-Verlauf, Versalien in Oswald, gesperrt —
/// die SwiftUI-Entsprechung der `.btn`-Regel aus der Web-App.
struct FlexrButton: View {

    let title: String
    var icon: FlexrGlyph.Kind?
    var isEnabled = true
    var isLoading = false
    let action: () -> Void

    @State private var isPressed = false

    private var active: Bool { isEnabled && !isLoading }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 9) {
                if isLoading {
                    ProgressView()
                        .controlSize(.small)
                        .tint(FlexrColor.plateInk)
                } else if let icon {
                    FlexrGlyph(icon, size: 17)
                }
                Text(title.uppercased())
                    .flexrText(.labelLarge)
                    .multilineTextAlignment(.center)
            }
            .foregroundStyle(FlexrColor.plateInk)
            .frame(maxWidth: .infinity)
            .padding(.horizontal, 18)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: FlexrRadius.button, style: .continuous)
                    .fill(FlexrColor.plateGradient)
            )
        }
        .buttonStyle(.plain)
        .disabled(!active)
        .opacity(active ? 1 : 0.4)
        .scaleEffect(isPressed ? 0.98 : 1)
        .animation(.easeOut(duration: 0.12), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in if active { isPressed = true } }
                .onEnded { _ in isPressed = false }
        )
    }
}

/// Zurückhaltende Aktion: transparenter Grund mit Stahlrahmen (`.btn.secondary`).
struct FlexrSecondaryButton: View {

    let title: String
    var icon: FlexrGlyph.Kind?
    var isEnabled = true
    var isLoading = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 9) {
                if isLoading {
                    ProgressView().controlSize(.small).tint(FlexrColor.chalk)
                } else if let icon {
                    FlexrGlyph(icon, size: 17)
                }
                Text(title.uppercased()).flexrText(.labelLarge)
            }
            .foregroundStyle(FlexrColor.chalk)
            .frame(maxWidth: .infinity, minHeight: 50)
            .flexrSurface(
                radius: FlexrRadius.button,
                fill: Color.white.opacity(0.03),
                border: FlexrColor.steel
            )
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled || isLoading)
        .opacity(isEnabled && !isLoading ? 1 : 0.5)
    }
}

/// Zerstörende Aktion als Geisterknopf (`.btn.danger-ghost`).
struct FlexrDangerButton: View {

    let title: String
    var isEnabled = true
    var isLoading = false
    var isSolid = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 9) {
                if isLoading {
                    ProgressView()
                        .controlSize(.small)
                        .tint(isSolid ? .white : FlexrColor.danger)
                }
                Text(title.uppercased()).flexrText(.labelLarge)
            }
            .foregroundStyle(isSolid ? Color.white : FlexrColor.danger)
            .frame(maxWidth: .infinity, minHeight: 50)
            .flexrSurface(
                radius: FlexrRadius.button,
                fill: isSolid ? FlexrColor.danger : FlexrColor.danger.opacity(0.08),
                border: FlexrColor.danger.opacity(isSolid ? 1 : 0.45)
            )
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled || isLoading)
        .opacity(isEnabled && !isLoading ? 1 : 0.5)
    }
}

/// Textlink-Optik für Nebenaktionen (`.link-btn` / `.membership-link`).
struct FlexrLinkButton: View {

    let title: String
    var color: Color = FlexrColor.plate
    var isEnabled = true
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .flexrText(.bodyMedium)
                .underline()
                .foregroundStyle(isEnabled ? color : FlexrColor.chalkDim)
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled)
        .padding(.vertical, 8)
    }
}

/// Runder Aktionsknopf unter dem Deck (`.round-btn`).
struct RoundActionButton: View {

    let icon: String
    let accessibilityLabel: String
    var tint: Color = .white
    var isLarge = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            ZStack {
                if isLarge {
                    Circle().fill(FlexrColor.plateGradient)
                } else {
                    Circle().fill(
                        LinearGradient(
                            colors: [Color(hex: 0x222222), Color(hex: 0x1B1B1B)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    Circle().strokeBorder(FlexrColor.steel, lineWidth: 1)
                }
                Image(systemName: icon)
                    .font(.system(size: isLarge ? 26 : 22, weight: .semibold))
                    .foregroundStyle(tint)
            }
            .frame(width: isLarge ? 64 : 56, height: isLarge ? 64 : 56)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(accessibilityLabel)
    }
}
