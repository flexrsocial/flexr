import SwiftUI

/// Eingebettete Online-Rücktrittsfunktion (§ 13a FAGG) innerhalb der
/// `LegalDocument.widerruf`-Ansicht — ersetzt einen externen Link auf
/// flexr.social/widerruf.html. Bis zum Absenden ein Formular, danach die
/// Bestätigung mit dem aufgezeichneten Wortlaut.
struct WithdrawalFormView: View {

    @Environment(AppContainer.self) private var container
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    @State private var model: WithdrawalModel?

    var body: some View {
        Group {
            if let model {
                content(model)
            } else {
                Color.clear
            }
        }
        .onAppear {
            if model == nil {
                model = WithdrawalModel(
                    withdrawalRepository: container.withdrawal,
                    profile: container.profiles.myProfile,
                    languageStore: languageStore
                )
            }
        }
    }

    @ViewBuilder
    private func content(_ model: WithdrawalModel) -> some View {
        if let result = model.result {
            WithdrawalResultBox(result: result)
        } else {
            @Bindable var model = model
            VStack(alignment: .leading, spacing: 0) {
                FlexrTextField(
                    text: $model.name,
                    label: s(.withdrawalNameLabel),
                    placeholder: s(.withdrawalNamePlaceholder),
                    textContentType: .name,
                    autocapitalization: .words
                )
                .onChange(of: model.name) { model.onFieldChange() }

                FlexrTextField(
                    text: $model.email,
                    label: s(.withdrawalEmailLabel),
                    placeholder: "du@example.com",
                    keyboardType: .emailAddress,
                    textContentType: .emailAddress,
                    autocapitalization: .never,
                    supportingText: s(.withdrawalEmailHint)
                )
                .onChange(of: model.email) { model.onFieldChange() }

                FlexrTextField(
                    text: $model.contractReference,
                    label: s(.withdrawalContractLabel),
                    placeholder: s(.withdrawalContractPlaceholder),
                    supportingText: s(.withdrawalContractHint)
                )

                FlexrTextField(
                    text: $model.message,
                    label: s(.withdrawalMessageLabel),
                    placeholder: s(.withdrawalMessagePlaceholder),
                    isSingleLine: false,
                    maxLines: 4,
                    maxLength: 1000
                )

                WithdrawalConfirmCheckbox(isOn: $model.confirmed, label: s(.withdrawalConfirmLabel))
                    .padding(.top, 16)
                    .onChange(of: model.confirmed) { model.onFieldChange() }

                FieldError(message: model.error)

                FlexrButton(
                    title: s(.withdrawalSubmit),
                    isEnabled: model.canSubmit,
                    isLoading: model.isSubmitting
                ) {
                    Task { await model.submit() }
                }
                .padding(.top, 16)
            }
            .padding(.bottom, 8)
        }
    }
}

/// Einfache Bestätigungs-Checkbox ohne Link im Fließtext — anders als
/// `ConsentCheckbox` in `RegisterView`, das den Datenschutz-Link einbettet.
private struct WithdrawalConfirmCheckbox: View {

    @Binding var isOn: Bool
    let label: String

    var body: some View {
        Button { isOn.toggle() } label: {
            HStack(alignment: .top, spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 5, style: .continuous)
                        .fill(isOn ? FlexrColor.plate : .clear)
                    RoundedRectangle(cornerRadius: 5, style: .continuous)
                        .strokeBorder(isOn ? FlexrColor.plate : FlexrColor.steel, lineWidth: 1.5)
                    if isOn {
                        Image(systemName: FlexrIcon.check)
                            .font(.system(size: 12, weight: .bold))
                            .foregroundStyle(FlexrColor.plateInk)
                    }
                }
                .frame(width: 22, height: 22)

                Text(label)
                    .flexrText(.bodyMedium)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(isOn ? [.isSelected] : [])
    }
}

private struct WithdrawalResultBox: View {

    let result: WithdrawalAck

    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(result.confirmationSent ? s(.withdrawalResultTitle) : s(.withdrawalResultTitleNoMail))
                .flexrText(.titleSmall)
                .foregroundStyle(FlexrColor.chalk)

            Text(result.message)
                .flexrText(.bodyMedium)
                .foregroundStyle(FlexrColor.chalkDim)

            Text(s(.withdrawalResultWordingLabel))
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalk)
                .padding(.top, 6)

            Text(result.declarationText)
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)

            Text(s(.withdrawalResultHint))
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .padding(.top, 6)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .flexrSurface(fill: FlexrColor.surface2, border: FlexrColor.hairline)
        .padding(.bottom, 8)
    }
}
