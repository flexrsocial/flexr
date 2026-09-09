import SwiftUI

/// Sprachregler: zwei Segmente mit gleitendem Knopf — dieselbe Optik wie in der
/// Web-App (`.lang-switch` in `frontend/app/index.html`) und in der
/// Android-Fassung.
///
/// Er steht an zwei Stellen: oben in der Kopfzeile, wo ihn auch ein noch nicht
/// angemeldeter Nutzer sofort sieht, und im Kontobereich unter „Einstellungen",
/// wo man Einstellungen sucht.
struct LanguageSwitch: View {

    @Environment(LanguageStore.self) private var languageStore

    private let segmentWidth: CGFloat = 38
    private let segmentHeight: CGFloat = 24

    var body: some View {
        let language = languageStore.language
        ZStack(alignment: .leading) {
            Capsule()
                .fill(FlexrColor.plate)
                .frame(width: segmentWidth, height: segmentHeight)
                .offset(x: language == .english ? segmentWidth : 0)
                .animation(.easeInOut(duration: 0.2), value: language)

            HStack(spacing: 0) {
                ForEach(AppLanguage.allCases, id: \.rawValue) { entry in
                    Button {
                        languageStore.language = entry
                    } label: {
                        Text(entry.badge)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundStyle(
                                entry == language ? FlexrColor.plateInk : FlexrColor.chalkDim
                            )
                            .frame(width: segmentWidth, height: segmentHeight)
                            .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(2)
        .background(Capsule().fill(FlexrColor.surface2))
        .overlay(Capsule().strokeBorder(FlexrColor.steel, lineWidth: 1))
        .accessibilityElement(children: .contain)
        .accessibilityLabel(languageStore.strings(.langLabel))
    }
}
