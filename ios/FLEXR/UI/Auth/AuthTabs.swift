import SwiftUI

enum AuthTab: String, CaseIterable, Identifiable {
    case login, register

    var id: String { rawValue }

    /// Bis 2.4.11 fest deutsch - auch bei englischer Oberfläche.
    var titleKey: L {
        switch self {
        case .login: .loginSubmit
        case .register: .authTabRegister
        }
    }
}

/// Umschalter zwischen Anmeldung und Registrierung (`.auth-tabs` im Web).
struct AuthTabs: View {
    @Environment(LanguageStore.self) private var languageStore

    let selected: AuthTab
    let onSelect: (AuthTab) -> Void

    var body: some View {
        HStack(spacing: 0) {
            ForEach(AuthTab.allCases) { tab in
                let isSelected = tab == selected
                Button { if !isSelected { onSelect(tab) } } label: {
                    Text(languageStore.strings(tab.titleKey))
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
                .accessibilityAddTraits(isSelected ? [.isSelected] : [])
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
