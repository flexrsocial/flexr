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

        let placeholderLabel = UILabel()
        placeholderLabel.numberOfLines = 0
        placeholderLabel.textColor = UIColor(FlexrColor.chalkDim)
        placeholderLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(placeholderLabel)
        NSLayoutConstraint.activate([
            placeholderLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            placeholderLabel.topAnchor.constraint(equalTo: view.topAnchor),
            placeholderLabel.trailingAnchor.constraint(lessThanOrEqualTo: view.trailingAnchor),
        ])
        context.coordinator.placeholderLabel = placeholderLabel
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
