import SwiftUI

struct RegisterView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let onGoToLogin: () -> Void
    let onOpenLegal: (LegalDocument) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var model: RegisterModel?
    @State private var legalDocument: LegalDocument?

    var body: some View {
        ZStack {
            FlexrBackground()
            VStack(spacing: 0) {
                FlexrTopBar { EmptyView() }
                if let model {
                    form(model)
                } else {
                    Color.clear
                }
            }
        }
        .onAppear {
            if model == nil {
                model = RegisterModel(
                    auth: container.auth,
                    profiles: container.profiles,
                    gyms: container.gyms,
                    plz: container.plz,
                    languageStore: languageStore
                )
            }
        }
        .sheet(item: $legalDocument) { document in
            NavigationStack {
                LegalView(document: document, onBack: { legalDocument = nil })
            }
        }
    }

    @ViewBuilder
    private func form(_ model: RegisterModel) -> some View {
        @Bindable var model = model

        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                AuthTabs(selected: .register) { tab in
                    if tab == .login { onGoToLogin() }
                }
                .padding(.top, 8)

                ScreenHeader(
                    eyebrow: s(.registerEyebrow),
                    title: s(.registerTitle),
                    // Der Text steht fest im Wörterbuch, weil vor dem Login
                    // noch kein /api/billing/status abrufbar ist. Er nennt
                    // deshalb bewusst nur die dauerhaft kostenlose Nutzung und
                    // den Premium-Preis — keine Restkontingente.
                    subtitle: s(.registerSubtitle)
                )
                .padding(.top, 24)

                FlexrTextField(
                    text: $model.email,
                    label: s(.fieldEmail),
                    placeholder: s(.loginEmailPlaceholder),
                    keyboardType: .emailAddress,
                    textContentType: .username,
                    autocapitalization: .never
                )
                FlexrPasswordField(
                    text: $model.password,
                    label: s(.fieldPassword),
                    placeholder: s(.registerPasswordPlaceholder),
                    textContentType: .newPassword,
                    submitLabel: .next
                )
                FlexrTextField(
                    text: $model.name,
                    label: s(.fieldName),
                    placeholder: s(.registerNamePlaceholder),
                    textContentType: .givenName,
                    autocapitalization: .words,
                    maxLength: 100
                )

                BirthdateField(birthdate: $model.birthdate, age: model.age)

                PostalCodeField(postalCode: $model.postalCode, lookupState: model.plzLookup)

                GenderSelector(selected: $model.gender)

                GymPicker(
                    state: $model.gymPicker,
                    onQueryChange: model.onGymQueryChange,
                    onSelect: model.onGymSelected,
                    onSuggestRequested: model.openGymSuggestion
                )

                FlexrTextField(
                    text: $model.bio,
                    label: s(.fieldBio),
                    placeholder: s(.fieldBioPlaceholder),
                    isSingleLine: false,
                    maxLines: 5,
                    maxLength: RegisterModel.bioMaxLength,
                    showsEmojiPicker: true
                )

                FieldLabel(text: s(.registerPhotosLabel))
                PhotoGridEditor(
                    slots: model.photos.map {
                        PhotoSlot(id: $0.id, source: .data($0.preview))
                    },
                    onPhotoPicked: { data in Task { await model.onPhotoPicked(data) } },
                    onRemove: model.removePhoto
                )
                if model.isPreparingPhoto {
                    HStack(spacing: 8) {
                        ProgressView().controlSize(.mini).tint(FlexrColor.plate)
                        Text(s(.registerPhotoPreparing))
                            .flexrText(.bodySmall)
                            .foregroundStyle(FlexrColor.chalkDim)
                    }
                    .padding(.top, 8)
                }
                FieldError(message: model.photoError)

                ConsentCheckbox(
                    isOn: $model.consentSensitiveData,
                    prefix: s(.registerConsentPrefix),
                    linkText: s(.registerConsentLink),
                    suffix: s(.registerConsentSuffix),
                    onLinkTap: { legalDocument = .datenschutz }
                )
                .padding(.top, 20)

                ConsentCheckbox(
                    isOn: $model.consentWithdrawalWaiver,
                    prefix: s(.registerWaiverPrefix),
                    linkText: s(.registerWaiverLink),
                    suffix: s(.registerWaiverSuffix),
                    onLinkTap: { legalDocument = .agb }
                )

                FieldError(message: model.error)

                FlexrButton(
                    title: s(.registerSubmit),
                    isEnabled: model.canSubmit,
                    isLoading: model.isSubmitting
                ) {
                    Task { await model.register() }
                }
                .padding(.top, 22)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 40)
        }
        .scrollDismissesKeyboard(.interactively)
        .onChange(of: model.postalCode) { _, _ in model.postalCodeChanged() }
        .sheet(isPresented: Binding(
            get: { model.gymSuggestion != nil },
            set: { if !$0 { model.closeGymSuggestion() } }
        )) {
            if model.gymSuggestion != nil {
                GymSuggestionSheet(
                    state: Binding(
                        get: { model.gymSuggestion ?? GymSuggestionState() },
                        set: { model.gymSuggestion = $0 }
                    ),
                    onSubmit: { Task { await model.submitGymSuggestion() } },
                    onDismiss: model.closeGymSuggestion
                )
            }
        }
        .onChange(of: model.successNotice) { _, notice in
            // Nach erfolgreicher Registrierung übernimmt `AppModel` den
            // Bildschirmwechsel; hier bleibt nur die Rückmeldung.
            guard let notice else { return }
            appModel.show(notice)
            model.successNotice = nil
        }
    }
}

/// Geburtsdatum: nicht tippen, sondern auswählen — der native Kalender mit
/// 18-Jahres-Grenze. Das Backend prüft ebenso.
private struct BirthdateField: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    @Binding var birthdate: Date?
    let age: Int?

    @State private var isPresented = false
    @State private var draft = ServerTime.birthdate(yearsAgo: RegisterModel.minAge)

    private var range: ClosedRange<Date> {
        ServerTime.birthdate(yearsAgo: RegisterModel.maxAge)
            ... ServerTime.birthdate(yearsAgo: RegisterModel.minAge)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            FieldLabel(text: s(.registerBirthdateLabel))
            Button { isPresented = true } label: {
                HStack {
                    Text(birthdate.map(ServerTime.formatBirthdate) ?? s(.registerBirthdatePlaceholder))
                        .flexrText(.bodyLarge)
                        .foregroundStyle(birthdate != nil ? FlexrColor.chalk : FlexrColor.chalkDim)
                    Spacer()
                    if let age {
                        Text(s(.registerAgeYears, age))
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalkDim)
                    }
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 15)
                .contentShape(Rectangle())
                .flexrSurface(radius: FlexrRadius.small, border: FlexrColor.steel)
            }
            .buttonStyle(.plain)
        }
        .sheet(isPresented: $isPresented) {
            NavigationStack {
                ZStack {
                    FlexrBackground()
                    DatePicker(
                        s(.registerBirthdateLabel),
                        selection: $draft,
                        in: range,
                        displayedComponents: .date
                    )
                    .datePickerStyle(.graphical)
                    .environment(\.timeZone, TimeZone(secondsFromGMT: 0)!)
                    .tint(FlexrColor.plate)
                    .padding(20)
                }
                .navigationTitle(s(.registerBirthdateLabel))
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button(s(.commonCancel)) { isPresented = false }
                            .foregroundStyle(FlexrColor.chalkDim)
                    }
                    ToolbarItem(placement: .confirmationAction) {
                        Button(s(.commonApply)) {
                            birthdate = draft
                            isPresented = false
                        }
                        .foregroundStyle(FlexrColor.plate)
                    }
                }
            }
            .presentationDetents([.medium, .large])
            .onAppear { draft = birthdate ?? ServerTime.birthdate(yearsAgo: RegisterModel.minAge) }
        }
    }
}

private struct GenderSelector: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    @Binding var selected: Gender?

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            FieldLabel(text: s(.registerGenderLabel))
            HStack(spacing: 0) {
                ForEach(Gender.allCases, id: \.self) { gender in
                    let isSelected = selected == gender
                    Button { selected = gender } label: {
                        Text(s(gender.labelKey))
                            .flexrText(.bodyLarge)
                            .foregroundStyle(isSelected ? FlexrColor.plate : FlexrColor.chalkDim)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 13)
                            .background(
                                RoundedRectangle(cornerRadius: FlexrRadius.small, style: .continuous)
                                    .fill(isSelected ? FlexrColor.plate.opacity(0.16) : FlexrColor.surface)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: FlexrRadius.small, style: .continuous)
                                    .strokeBorder(
                                        isSelected ? FlexrColor.plate : FlexrColor.steel,
                                        lineWidth: 1
                                    )
                            )
                            .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .padding(.trailing, gender == Gender.allCases.last ? 0 : 8)
                }
            }
        }
    }
}

/// Einwilligung mit eingebettetem Link auf den jeweiligen Rechtstext.
private struct ConsentCheckbox: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    @Binding var isOn: Bool
    let prefix: String
    let linkText: String
    let suffix: String
    let onLinkTap: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Button { isOn.toggle() } label: {
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
            }
            .buttonStyle(.plain)
            .accessibilityAddTraits(isOn ? [.isSelected] : [])

            // Der Link steckt im Fließtext; getippt wird auf den ganzen Absatz,
            // weil SwiftUI-`Text` keine bereichsweise Trefferfläche kennt.
            (Text(prefix).foregroundStyle(FlexrColor.chalkDim)
                + Text(linkText).foregroundStyle(FlexrColor.plate).underline()
                + Text(suffix).foregroundStyle(FlexrColor.chalkDim))
                .flexrText(.bodySmall)
                .frame(maxWidth: .infinity, alignment: .leading)
                .contentShape(Rectangle())
                .onTapGesture(perform: onLinkTap)
                .accessibilityAddTraits(.isLink)
        }
        .padding(.vertical, 6)
    }
}
