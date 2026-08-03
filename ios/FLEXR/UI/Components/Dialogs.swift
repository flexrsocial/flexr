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
            Button("Abbrechen", role: .cancel) {}
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
                        Text("Was ist vorgefallen? Deine Meldung wird von uns geprüft.")
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalkDim)

                        FlexrTextField(
                            text: $reason,
                            label: "Grund",
                            placeholder: "Kurze Beschreibung",
                            isSingleLine: false,
                            maxLines: 5,
                            maxLength: 500
                        )

                        Spacer(minLength: 24)

                        FlexrDangerButton(title: "Melden", isEnabled: isValid) {
                            onSubmit(reason.trimmingCharacters(in: .whitespacesAndNewlines))
                        }
                    }
                    .padding(20)
                }
            }
            .navigationTitle("\(userName) melden")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Abbrechen", action: onDismiss)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
