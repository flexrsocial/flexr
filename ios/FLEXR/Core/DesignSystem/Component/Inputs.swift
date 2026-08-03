import SwiftUI

/// Feldbeschriftung im FLEXR-Stil: klein, gesperrt, Versalien, gedämpft.
struct FieldLabel: View {
    let text: String

    var body: some View {
        Text(text.uppercased())
            .font(.flexrWorkSans(12))
            .tracking(0.48)
            .foregroundStyle(FlexrColor.chalkDim)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 16)
            .padding(.bottom, 6)
    }
}

/// Standard-Eingabefeld der App.
///
/// Die Beschriftung steht — wie im Web — über dem Feld statt als schwebendes
/// Label; das hält lange deutsche Beschriftungen lesbar. Mehrzeilige Felder und
/// solche mit Emoji-Auswahl laufen über [GrowingTextView], weil dort die
/// Cursorposition gebraucht wird.
struct FlexrTextField: View {

    @Binding var text: String
    let label: String
    var placeholder: String?
    var keyboardType: UIKeyboardType = .default
    var textContentType: UITextContentType?
    var autocapitalization: TextInputAutocapitalization = .sentences
    var isSingleLine = true
    var maxLines = 1
    var isEnabled = true
    var isError = false
    var supportingText: String?
    var trailingIcon: String?
    var onTrailingIconTap: (() -> Void)?
    var maxLength: Int?
    var submitLabel: SubmitLabel = .next
    var onSubmit: (() -> Void)?
    /// Blendet einen Emoji-Umschalter ins Feld ein (Parität zum Web-Frontend).
    var showsEmojiPicker = false

    @State private var isEmojiOpen = false
    @State private var selection = NSRange(location: 0, length: 0)
    @State private var editorHeight: CGFloat = 22
    @FocusState private var isFocused: Bool

    private var usesEditor: Bool { !isSingleLine || showsEmojiPicker }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            FieldLabel(text: label)

            HStack(alignment: .top, spacing: 8) {
                if usesEditor {
                    GrowingTextView(
                        text: $text,
                        selection: $selection,
                        measuredHeight: $editorHeight,
                        font: FlexrFont.uiFont("WorkSans-Regular", size: 15, weight: 400),
                        placeholder: placeholder,
                        isEnabled: isEnabled,
                        maxLength: maxLength,
                        maxLines: maxLines,
                        keyboardType: keyboardType,
                        returnKeyType: isSingleLine ? .done : .default,
                        submitsOnReturn: isSingleLine,
                        onSubmit: onSubmit
                    )
                    .frame(height: max(editorHeight, 22))
                } else {
                    TextField(placeholder ?? "", text: $text)
                        .flexrText(.bodyLarge)
                        .foregroundStyle(FlexrColor.chalk)
                        .tint(FlexrColor.plate)
                        .keyboardType(keyboardType)
                        .textContentType(textContentType)
                        .textInputAutocapitalization(autocapitalization)
                        .autocorrectionDisabled(keyboardType == .emailAddress)
                        .disabled(!isEnabled)
                        .focused($isFocused)
                        .submitLabel(submitLabel)
                        .onSubmit { onSubmit?() }
                        .onChange(of: text) { _, newValue in
                            if let maxLength, newValue.backendLength > maxLength {
                                text = newValue.truncatedToBackendLength(maxLength)
                            }
                        }
                }

                if let trailingIcon {
                    Button { onTrailingIconTap?() } label: {
                        Image(systemName: trailingIcon)
                            .font(.system(size: 17, weight: .medium))
                            .foregroundStyle(FlexrColor.chalkDim)
                    }
                    .buttonStyle(.plain)
                } else if showsEmojiPicker {
                    EmojiToggleButton(isExpanded: isEmojiOpen) {
                        withAnimation(.easeOut(duration: 0.18)) { isEmojiOpen.toggle() }
                    }
                    .padding(.top, -6)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 14)
            .flexrSurface(
                radius: FlexrRadius.small,
                fill: FlexrColor.surface,
                border: isError ? FlexrColor.danger : (isFocused ? FlexrColor.plate : FlexrColor.steel),
                borderWidth: isFocused ? 2 : 1
            )

            if showsEmojiPicker {
                EmojiPickerPanel(isExpanded: isEmojiOpen) { emoji in
                    let result = EmojiInsertion.insert(
                        emoji,
                        into: text,
                        selection: selection,
                        maxLength: maxLength
                    )
                    text = result.text
                    selection = result.selection
                }
                .padding(.top, 6)
            }

            HStack(alignment: .top) {
                if let supportingText {
                    Text(supportingText)
                        .flexrText(.bodySmall)
                        .foregroundStyle(isError ? FlexrColor.danger : FlexrColor.chalkDim)
                        .padding(.top, 6)
                    Spacer(minLength: 8)
                }
                if let maxLength {
                    Spacer(minLength: 0)
                    Text("\(text.backendLength)/\(maxLength)")
                        .flexrText(.labelSmall)
                        .foregroundStyle(FlexrColor.chalkDim)
                        .padding(.top, 8)
                }
            }
        }
    }
}

/// Passwortfeld mit Sichtbarkeitsschalter.
struct FlexrPasswordField: View {

    @Binding var text: String
    let label: String
    var placeholder: String?
    var textContentType: UITextContentType? = .password
    var isError = false
    var supportingText: String?
    var submitLabel: SubmitLabel = .done
    var onSubmit: (() -> Void)?

    @State private var isVisible = false
    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            FieldLabel(text: label)

            HStack(spacing: 8) {
                Group {
                    if isVisible {
                        TextField(placeholder ?? "", text: $text)
                    } else {
                        SecureField(placeholder ?? "", text: $text)
                    }
                }
                .flexrText(.bodyLarge)
                .foregroundStyle(FlexrColor.chalk)
                .tint(FlexrColor.plate)
                .textContentType(textContentType)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .focused($isFocused)
                .submitLabel(submitLabel)
                .onSubmit { onSubmit?() }

                Button { isVisible.toggle() } label: {
                    Image(systemName: isVisible ? FlexrIcon.eyeOff : FlexrIcon.eye)
                        .font(.system(size: 17, weight: .medium))
                        .foregroundStyle(FlexrColor.chalkDim)
                }
                .buttonStyle(.plain)
                .accessibilityLabel(isVisible ? "Passwort verbergen" : "Passwort anzeigen")
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 14)
            .flexrSurface(
                radius: FlexrRadius.small,
                fill: FlexrColor.surface,
                border: isError ? FlexrColor.danger : (isFocused ? FlexrColor.plate : FlexrColor.steel),
                borderWidth: isFocused ? 2 : 1
            )

            if let supportingText {
                Text(supportingText)
                    .flexrText(.bodySmall)
                    .foregroundStyle(isError ? FlexrColor.danger : FlexrColor.chalkDim)
                    .padding(.top, 6)
            }
        }
    }
}

/// Fehlerzeile unter einer Eingabegruppe (`.field-err`).
struct FieldError: View {
    let message: String?

    var body: some View {
        if let message, !message.isEmpty {
            Text(message)
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.danger)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 8)
        }
    }
}
