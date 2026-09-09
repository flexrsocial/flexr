import SwiftUI

/// Bestätigungsdialog für Aktionen mit Folgen (Blockieren, Löschen, Auflösen).
///
/// Im Web war das ein `confirm()` des Browsers — nativ ein richtiger Dialog.
struct ConfirmDialog: ViewModifier {

    @Binding var isPresented: Bool
    let title: String
    let message: String
    let confirmLabel: String
    var isDestructive = true
    let onConfirm: () -> Void

    func body(content: Content) -> some View {
        content.alert(title, isPresented: $isPresented) {
            Button(confirmLabel, role: isDestructive ? .destructive : nil, action: onConfirm)
            Button(s(.commonCancel), role: .cancel) {}
        } message: {
            Text(message)
        }
    }
}

extension View {
    func confirmDialog(
        isPresented: Binding<Bool>,
        title: String,
        message: String,
        confirmLabel: String,
        isDestructive: Bool = true,
        onConfirm: @escaping () -> Void
    ) -> some View {
        modifier(
            ConfirmDialog(
                isPresented: isPresented,
                title: title,
                message: message,
                confirmLabel: confirmLabel,
                isDestructive: isDestructive,
                onConfirm: onConfirm
            )
        )
    }
}

/// Meldedialog mit Freitextbegründung.
///
/// Im Web war das ein `prompt()` des Browsers — nativ ein richtiger Dialog mit
/// Längenprüfung (3–500 Zeichen, wie das Backend sie erwartet).
struct ReportDialog: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let userName: String
    let onSubmit: (String) -> Void
    let onDismiss: () -> Void

    @State private var reason = ""

    private var isValid: Bool {
        reason.trimmingCharacters(in: .whitespacesAndNewlines).count >= 3
    }

    var body: some View {
        NavigationStack {
            ZStack {
                FlexrBackground()
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        Text(s(.reportDialogBody))
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalkDim)

                        FlexrTextField(
                            text: $reason,
                            label: s(.reportReasonLabel),
                            placeholder: s(.reportReasonPlaceholder),
                            isSingleLine: false,
                            maxLines: 5,
                            maxLength: 500
                        )

                        Spacer(minLength: 24)

                        FlexrDangerButton(title: s(.commonReport), isEnabled: isValid) {
                            onSubmit(reason.trimmingCharacters(in: .whitespacesAndNewlines))
                        }
                    }
                    .padding(20)
                }
            }
            .navigationTitle(s(.reportDialogTitle, userName))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(s(.commonCancel), action: onDismiss)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
