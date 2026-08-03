import SwiftUI

enum AuthTab: String, CaseIterable, Identifiable {
    case login, register

    var id: String { rawValue }

    var title: String {
        switch self {
        case .login: "Einloggen"
        case .register: "Registrieren"
        }
    }
}

/// Umschalter zwischen Anmeldung und Registrierung (`.auth-tabs` im Web).
struct AuthTabs: View {

    let selected: AuthTab
    let onSelect: (AuthTab) -> Void

    var body: some View {
        HStack(spacing: 0) {
            ForEach(AuthTab.allCases) { tab in
                let isSelected = tab == selected
                Button { if !isSelected { onSelect(tab) } } label: {
                    Text(tab.title)
                        .flexrText(.labelLarge)
                        .foregroundStyle(isSelected ? FlexrColor.plate : FlexrColor.chalkDim)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 11)
                        .background(
                            RoundedRectangle(cornerRadius: 9, style: .continuous)
                                .fill(isSelected ? FlexrColor.surface3 : .clear)
                        )
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
            }
        }
        .padding(4)
        .background(
            RoundedRectangle(cornerRadius: FlexrRadius.button, style: .continuous)
                .fill(Color.white.opacity(0.03))
        )
        .animation(.easeOut(duration: 0.18), value: selected)
    }
}
