import SwiftUI

/// Ergebnis der Ortsermittlung zu einer Postleitzahl.
enum PlzLookupState: Equatable {
    case idle
    case loading
    case resolved(city: String)
    case failed(message: String)

    var city: String? {
        if case .resolved(let city) = self { return city }
        return nil
    }
}

/// Kombiniertes PLZ-/Ortsfeld: links vier Ziffern, rechts der automatisch
/// ermittelte Gemeindename.
///
/// Es gibt bewusst keine Städteauswahl — die PLZ bestimmt den Ort, damit ganz
/// Österreich abgedeckt ist.
struct PostalCodeField: View {

    @Binding var postalCode: String
    let lookupState: PlzLookupState
    var label = "Postleitzahl"

    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            FieldLabel(text: label)

            HStack(spacing: 0) {
                TextField("1010", text: $postalCode)
                    .flexrText(.bodyLarge)
                    .foregroundStyle(FlexrColor.chalk)
                    .tint(FlexrColor.plate)
                    .keyboardType(.numberPad)
                    .frame(width: 56)
                    .focused($isFocused)
                    .onChange(of: postalCode) { _, newValue in
                        let digits = String(newValue.filter(\.isNumber).prefix(4))
                        if digits != newValue { postalCode = digits }
                    }

                Rectangle()
                    .fill(FlexrColor.steel)
                    .frame(width: 1, height: 22)
                    .padding(.leading, 8)

                hint.padding(.leading, 10)

                Spacer(minLength: 0)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 14)
            .flexrSurface(
                radius: FlexrRadius.small,
                fill: FlexrColor.surface,
                border: isFocused ? FlexrColor.plate : FlexrColor.steel,
                borderWidth: isFocused ? 2 : 1
            )

            if case .failed(let message) = lookupState {
                Text(message)
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.danger)
                    .padding(.top, 6)
            }
        }
    }

    @ViewBuilder
    private var hint: some View {
        switch lookupState {
        case .idle:
            hintText("— PLZ eingeben —", isResolved: false)
        case .loading:
            HStack(spacing: 8) {
                ProgressView().controlSize(.mini).tint(FlexrColor.plate)
                hintText("Lädt …", isResolved: false)
            }
        case .resolved(let city):
            hintText(city, isResolved: true)
        case .failed:
            hintText("— unbekannte PLZ —", isResolved: false)
        }
    }

    private func hintText(_ text: String, isResolved: Bool) -> some View {
        Text(text)
            .flexrText(.bodyMedium)
            .foregroundStyle(isResolved ? FlexrColor.chalk : FlexrColor.chalkDim)
            .lineLimit(1)
    }
}
