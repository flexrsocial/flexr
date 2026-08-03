import SwiftUI

/// Zustand des Gym-Suchfeldes.
struct GymPickerState: Equatable {
    var query = ""
    var results: [Gym] = []
    var isSearching = false
    var isExpanded = false
    /// Vollständiges Label des gewählten Gyms — genau dieser Wert wird gespeichert.
    var selectedLabel: String?
}

/// Gym-Auswahl mit Live-Suche über die Gym-Datenbank (Name, Ort oder PLZ) und
/// Vorschlagsfunktion für fehlende Studios.
///
/// Gespeichert wird immer das volle Label „Name — Straße 1, 1100 Wien"; nur das
/// erkennt das Backend als gültig.
struct GymPicker: View {

    @Binding var state: GymPickerState
    let onQueryChange: (String) -> Void
    let onSelect: (Gym) -> Void
    let onSuggestRequested: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            FlexrTextField(
                text: Binding(
                    get: { state.query },
                    set: { onQueryChange($0) }
                ),
                label: "Gym",
                placeholder: "Gym suchen (Name, Ort oder PLZ) …",
                autocapitalization: .words,
                trailingIcon: FlexrIcon.search,
                submitLabel: .search
            )

            if state.isExpanded {
                VStack(spacing: 0) {
                    if state.isSearching {
                        HStack(spacing: 10) {
                            ProgressView().controlSize(.mini).tint(FlexrColor.plate)
                            Text("Suche …")
                                .flexrText(.bodySmall)
                                .foregroundStyle(FlexrColor.chalkDim)
                            Spacer()
                        }
                        .padding(14)
                    }

                    ScrollView {
                        LazyVStack(spacing: 0) {
                            ForEach(state.results) { gym in
                                Button { onSelect(gym) } label: {
                                    GymResultRow(gym: gym)
                                }
                                .buttonStyle(.plain)
                            }

                            Button(action: onSuggestRequested) {
                                HStack(spacing: 8) {
                                    Image(systemName: FlexrIcon.add)
                                        .font(.system(size: 14, weight: .semibold))
                                    Text("Gym nicht dabei? Jetzt vorschlagen")
                                        .flexrText(.bodyMedium)
                                    Spacer()
                                }
                                .foregroundStyle(FlexrColor.plate)
                                .padding(.horizontal, 14)
                                .padding(.vertical, 13)
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .frame(maxHeight: 260)
                }
                .padding(.top, 6)
                .flexrSurface(fill: FlexrColor.surface2, border: FlexrColor.steel)
            }

            if let label = state.selectedLabel {
                Text(label)
                    .flexrText(.mono)
                    .foregroundStyle(FlexrColor.lime)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 7)
                    .background(
                        RoundedRectangle(cornerRadius: FlexrRadius.extraSmall, style: .continuous)
                            .fill(FlexrColor.lime.opacity(0.07))
                    )
                    .padding(.top, 8)
            }
        }
    }
}

private struct GymResultRow: View {
    let gym: Gym

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(gym.name)
                .flexrText(.bodyMedium)
                .foregroundStyle(FlexrColor.chalk)
                .lineLimit(1)
            if !gym.addressLine.isEmpty {
                Text(gym.addressLine)
                    .flexrText(.mono)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .lineLimit(1)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 14)
        .padding(.vertical, 11)
        .contentShape(Rectangle())
    }
}

/// Eingaben des Vorschlagsdialogs.
struct GymSuggestionState: Equatable {
    var name = ""
    var street = ""
    var houseNumber = ""
    var postalCode = ""
    var isSubmitting = false
    var error: String?

    var isValid: Bool {
        name.trimmingCharacters(in: .whitespaces).count >= 2
            && street.trimmingCharacters(in: .whitespaces).count >= 2
            && !houseNumber.isEmpty
            && PlzRepository.isValidPostalCode(postalCode)
    }
}

/// Dialog „Gym vorschlagen". Der Vorschlag ist sofort für das eigene Profil
/// verwendbar und erscheint nach Freigabe für alle in der Auswahl.
struct GymSuggestionSheet: View {

    @Binding var state: GymSuggestionState
    let onSubmit: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        NavigationStack {
            ZStack {
                FlexrBackground()
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        Text(
                            "Dein Gym fehlt in der Liste? Reich es mit Adresse ein — du kannst es "
                                + "sofort für dein Profil verwenden, nach Prüfung erscheint es für alle."
                        )
                        .flexrText(.bodySmall)
                        .foregroundStyle(FlexrColor.chalkDim)

                        FlexrTextField(
                            text: $state.name,
                            label: "Name des Gyms",
                            placeholder: "z. B. Eisenschmiede",
                            autocapitalization: .words,
                            maxLength: 120
                        )
                        FlexrTextField(
                            text: $state.street,
                            label: "Straße",
                            placeholder: "z. B. Hauptstraße",
                            autocapitalization: .words,
                            maxLength: 120
                        )
                        HStack(alignment: .top, spacing: 10) {
                            FlexrTextField(
                                text: $state.houseNumber,
                                label: "Hausnummer",
                                placeholder: "12",
                                maxLength: 20
                            )
                            FlexrTextField(
                                text: Binding(
                                    get: { state.postalCode },
                                    set: { state.postalCode = String($0.filter(\.isNumber).prefix(4)) }
                                ),
                                label: "Postleitzahl",
                                placeholder: "1010",
                                keyboardType: .numberPad,
                                submitLabel: .done
                            )
                        }

                        FieldError(message: state.error)

                        Spacer(minLength: 24)
                        FlexrButton(
                            title: "Vorschlag einreichen",
                            isEnabled: state.isValid,
                            isLoading: state.isSubmitting,
                            action: onSubmit
                        )
                    }
                    .padding(20)
                }
            }
            .navigationTitle("Gym vorschlagen")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Abbrechen", action: onDismiss)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
            }
        }
    }
}
