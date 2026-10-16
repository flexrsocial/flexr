import SwiftUI
import UIKit

/// Mehrzeiliges Eingabefeld, das seine Höhe mitwachsen lässt und die
/// Cursorposition nach außen gibt.
///
/// SwiftUIs `TextField`/`TextEditor` verraten die Auswahl nicht — für das
/// Einfügen eines Emojis an der Cursorposition (Parität zum Web-Frontend und
/// zur Android-App) ist sie aber nötig. Deshalb ein `UITextView` mit
/// Delegierten für Text, Auswahl und Höhe.
struct GrowingTextView: UIViewRepresentable {

    @Binding var text: String
    /// Cursor bzw. Auswahl im Text — Grundlage für das Emoji-Einfügen.
    @Binding var selection: NSRange
    @Binding var measuredHeight: CGFloat

    var font: UIFont
    var placeholder: String?
    var isEnabled: Bool = true
    var maxLength: Int?
    var maxLines: Int = 5
    var keyboardType: UIKeyboardType = .default
    var returnKeyType: UIReturnKeyType = .default
    var submitsOnReturn: Bool = false
    var onSubmit: (() -> Void)?
    /// Name des Feldes für VoiceOver. Ohne ihn hieß jedes dieser Felder nur
    /// „Textfeld" - die Beschriftung darüber ist ein eigener Text.
    var voiceOverLabel: String?
    /// Beschriftung eines „Fertig"-Knopfs über der Tastatur. Mehrzeilige
    /// Felder haben keine Eingabetaste, die schließt - auf dem Kontobildschirm
    /// lag die Tastatur sonst über der Tab-Leiste, bis man sie wegzog.
    var doneLabel: String?
    /// Meldet Fokus an und aus, damit der Rahmen des Feldes wie bei den
    /// einzeiligen Feldern orange wird.
    var onFocusChange: ((Bool) -> Void)?

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> UITextView {
        let view = UITextView()
        view.delegate = context.coordinator
        view.backgroundColor = .clear
        view.textContainerInset = .zero
        view.textContainer.lineFragmentPadding = 0
        view.isScrollEnabled = false
        view.adjustsFontForContentSizeCategory = true
        view.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)

        // Eine Zeile, am Rahmen des Feldes gekürzt. Die Anker eines
        // `UITextView` (einer Scroll-Ansicht) beschreiben dessen Inhalt, nicht
        // seinen Rahmen: Am Inhalt verankert lief der Platzhalter bis 2.4.11
        // unter den Emoji-Knopf daneben („gerne mit E☺jis").
        let placeholderLabel = UILabel()
        placeholderLabel.numberOfLines = 1
        placeholderLabel.lineBreakMode = .byTruncatingTail
        placeholderLabel.textColor = UIColor(FlexrColor.chalkDim)
        placeholderLabel.translatesAutoresizingMaskIntoConstraints = false
        placeholderLabel.isAccessibilityElement = false
        view.addSubview(placeholderLabel)
        NSLayoutConstraint.activate([
            placeholderLabel.leadingAnchor.constraint(equalTo: view.frameLayoutGuide.leadingAnchor),
            placeholderLabel.topAnchor.constraint(equalTo: view.frameLayoutGuide.topAnchor),
            placeholderLabel.trailingAnchor.constraint(lessThanOrEqualTo: view.frameLayoutGuide.trailingAnchor),
        ])
        context.coordinator.placeholderLabel = placeholderLabel

        if let doneLabel {
            let toolbar = UIToolbar()
            toolbar.overrideUserInterfaceStyle = .dark
            toolbar.tintColor = UIColor(FlexrColor.plate)
            toolbar.items = [
                UIBarButtonItem(systemItem: .flexibleSpace),
                UIBarButtonItem(
                    title: doneLabel,
                    style: .done,
                    target: view,
                    action: #selector(UIResponder.resignFirstResponder)
                ),
            ]
            toolbar.sizeToFit()
            view.inputAccessoryView = toolbar
        }
        return view
    }

    func updateUIView(_ view: UITextView, context: Context) {
        context.coordinator.parent = self

        view.font = font
        view.textColor = UIColor(FlexrColor.chalk)
        view.tintColor = UIColor(FlexrColor.plate)
        view.keyboardType = keyboardType
        view.returnKeyType = returnKeyType
        view.isEditable = isEnabled
        view.isSelectable = true
        view.keyboardAppearance = .dark
        // Nur bei Änderung (Sprachwechsel) - nicht bei jedem Tastendruck an
        // der Leiste über der Tastatur rühren.
        if view.accessibilityLabel != voiceOverLabel ?? placeholder {
            view.accessibilityLabel = voiceOverLabel ?? placeholder
        }
        if let doneLabel, let fertig = (view.inputAccessoryView as? UIToolbar)?.items?.last,
           fertig.title != doneLabel {
            fertig.title = doneLabel
        }

        if view.text != text {
            view.text = text
        }
        if view.selectedRange != selection, selection.location <= (view.text as NSString).length {
            view.selectedRange = selection
        }

        context.coordinator.placeholderLabel?.font = font
        context.coordinator.placeholderLabel?.text = placeholder
        context.coordinator.placeholderLabel?.isHidden = !text.isEmpty

        // Ab `maxLines` scrollt das Feld statt weiter zu wachsen.
        let lineHeight = font.lineHeight
        let maximum = lineHeight * CGFloat(maxLines)
        let fitting = view.sizeThatFits(
            CGSize(width: view.bounds.width, height: .greatestFiniteMagnitude)
        ).height
        let target = min(max(fitting, lineHeight), maximum)
        view.isScrollEnabled = fitting > maximum

        if abs(target - measuredHeight) > 0.5 {
            DispatchQueue.main.async { measuredHeight = target }
        }
    }

    final class Coordinator: NSObject, UITextViewDelegate {
        var parent: GrowingTextView
        weak var placeholderLabel: UILabel?

        init(_ parent: GrowingTextView) { self.parent = parent }

        func textViewDidChange(_ textView: UITextView) {
            var value = textView.text ?? ""
            if let maxLength, value.backendLength > maxLength {
                value = value.truncatedToBackendLength(maxLength)
                textView.text = value
            }
            placeholderLabel?.isHidden = !value.isEmpty
            parent.text = value
            parent.selection = textView.selectedRange
        }

        func textViewDidChangeSelection(_ textView: UITextView) {
            parent.selection = textView.selectedRange
        }

        // Nicht direkt aus dem Rückruf: Das Ende der Bearbeitung kann mitten in
        // einer SwiftUI-Aktualisierung kommen (Bildschirm wird abgebaut).
        func textViewDidBeginEditing(_ textView: UITextView) {
            let melden = parent.onFocusChange
            DispatchQueue.main.async { melden?(true) }
        }

        func textViewDidEndEditing(_ textView: UITextView) {
            let melden = parent.onFocusChange
            DispatchQueue.main.async { melden?(false) }
        }

        func textView(
            _ textView: UITextView,
            shouldChangeTextIn range: NSRange,
            replacementText text: String
        ) -> Bool {
            if parent.submitsOnReturn, text == "\n" {
                parent.onSubmit?()
                return false
            }
            guard let maxLength else { return true }
            let current = (textView.text as NSString?) ?? ""
            let updated = current.replacingCharacters(in: range, with: text)
            return updated.backendLength <= maxLength
        }

        private var maxLength: Int? { parent.maxLength }
    }
}
