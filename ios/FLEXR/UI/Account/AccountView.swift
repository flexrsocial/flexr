import SwiftUI

struct AccountView: View {

    let onOpen: (Route) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var model: AccountModel?
    @State private var showDeleteDialog = false
    @State private var deletePassword = ""

    var body: some View {
        Group {
            if let model {
                content(model)
            } else {
                LoadingStateView()
            }
        }
        .task {
            let created = model ?? AccountModel(
                container: container,
                onMessage: { appModel.show($0) }
            )
            model = created
            await created.load()
        }
    }

    @ViewBuilder
    private func content(_ model: AccountModel) -> some View {
        @Bindable var model = model

        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                profileHeader(model)

                let isVerified = model.profile?.profile.isVerified == true
                    || model.verificationStatus == .approved
                // Der Verifiziert-Hinweis verschwindet, sobald er bestätigt
                // wurde; alle anderen Zustände sind Handlungsaufforderungen und
                // bleiben stehen.
                if !isVerified || !model.verifiedHintDismissed {
                    VerificationHint(
                        isVerified: isVerified,
                        status: model.verificationStatus,
                        onDismiss: model.dismissVerifiedHint,
                        onStartVerification: { onOpen(.verification) }
                    )
                    .padding(.top, 14)
                }

                membershipCard(model).padding(.top, 18)

                SectionTitle(text: "Profil").padding(.top, 26)
                PostalCodeField(postalCode: $model.postalCode, lookupState: model.plzLookup)
                GymPicker(
                    state: $model.gymPicker,
                    onQueryChange: model.onGymQueryChange,
                    onSelect: model.onGymSelected,
                    onSuggestRequested: model.openGymSuggestion
                )
                FlexrTextField(
                    text: $model.bio,
                    label: "Bio",
                    placeholder: "Was du suchst, dein Training, gerne mit Emojis 💪",
                    isSingleLine: false,
                    maxLines: 5,
                    maxLength: AccountModel.bioMaxLength,
                    showsEmojiPicker: true
                )

                radiusSlider(model)

                FieldError(message: model.saveError)
                FlexrSecondaryButton(title: "Profil speichern", isLoading: model.isSaving) {
                    Task { await model.saveProfile() }
                }
                .padding(.top, 16)

                photoSection(model)
                notificationSection(model)
                accountSection()
                safetySection()
                legalSection()
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 40)
        }
        .scrollDismissesKeyboard(.interactively)
        .onChange(of: model.postalCode) { _, _ in model.postalCodeChanged() }
        .externalPage($model.externalURL)
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
        .sheet(isPresented: $showDeleteDialog) {
            DeleteAccountSheet(
                password: $deletePassword,
                error: model.deleteError,
                isDeleting: model.isDeleting,
                onConfirm: { Task { await model.deleteAccount(password: deletePassword) } },
                onDismiss: { showDeleteDialog = false }
            )
        }
        .onChange(of: model.didDeleteAccount) { _, deleted in
            if deleted { Task { await appModel.logout() } }
        }
    }

    // MARK: - Kopf: Avatar, Name, Verifizierung

    private func profileHeader(_ model: AccountModel) -> some View {
        HStack(spacing: 14) {
            AvatarImage(
                source: PhotoImageSource(model.profile?.photos.first?.avatarURL),
                name: model.profile?.name ?? "?",
                size: 64,
                ringColor: FlexrColor.plateDim,
                accessibilityLabel: "Dein Profilfoto"
            )

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text(model.profile.map { "\($0.name), \($0.profile.age)" } ?? "—")
                        .flexrText(.titleLarge)
                        .foregroundStyle(FlexrColor.chalk)
                        .lineLimit(1)
                    if model.profile?.profile.isVerified == true { VerifiedBadge() }
                }
                Text(
                    [
                        model.profile?.profile.city,
                        model.profile?.profile.gymName.isEmpty == false
                            ? model.profile?.profile.gymName : nil,
                    ]
                    .compactMap { $0 }
                    .joined(separator: " · ")
                )
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .lineLimit(1)
            }
            Spacer(minLength: 0)
        }
        .padding(.top, 18)
    }

    @ViewBuilder
    private func membershipCard(_ model: AccountModel) -> some View {
        if let membership = model.membership {
            FlexrCard {
                VStack(alignment: .leading, spacing: 0) {
                    Text(
                        membership.isSubscribed
                            ? "Dein Abo ist aktiv (5 €/Monat)."
                            : "Noch \(ServerTime.daysUntil(membership.trialEndsAt)) Tag(e) gratis Probemonat."
                    )
                    .flexrText(.bodyMedium)
                    .foregroundStyle(FlexrColor.chalk)

                    if membership.isSubscribed {
                        FlexrLinkButton(title: "Abo verwalten / kündigen") {
                            model.openBillingPortal()
                        }
                    } else {
                        FlexrLinkButton(title: "Jetzt abonnieren") { model.startCheckout() }
                    }
                }
            }
        }
    }

    private func radiusSlider(_ model: AccountModel) -> some View {
        @Bindable var model = model
        return VStack(alignment: .leading, spacing: 0) {
            FieldLabel(text: "Suchumkreis")
            HStack(spacing: 12) {
                Slider(
                    value: $model.searchRadiusKm,
                    in: Double(AccountModel.minRadiusKm)...Double(AccountModel.maxRadiusKm),
                    step: 1
                )
                .tint(FlexrColor.plate)

                Text("\(Int(model.searchRadiusKm)) km")
                    .flexrText(.mono)
                    .foregroundStyle(FlexrColor.chalk)
            }
            Text("Profile im Umkreis deines Gyms.")
            .flexrText(.bodySmall)
            .foregroundStyle(FlexrColor.chalkDim)
        }
    }

    private func photoSection(_ model: AccountModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            SectionTitle(text: "Fotos").padding(.top, 28)
            PhotoGridEditor(
                slots: (model.profile?.photos ?? []).map {
                    PhotoSlot(id: $0.id, source: .remote($0.url), status: $0.status)
                },
                onPhotoPicked: { data in Task { await model.onPhotoPicked(data) } },
                onRemove: model.removePhoto,
                showsStatus: true
            )
            .padding(.top, 8)

            if model.isUploadingPhoto {
                HStack(spacing: 8) {
                    ProgressView().controlSize(.mini).tint(FlexrColor.plate)
                    Text("Foto wird hochgeladen …")
                        .flexrText(.bodySmall)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
                .padding(.top, 8)
            }

            PhotoVisibilityHint(statuses: (model.profile?.photos ?? []).map(\.status))
            FieldError(message: model.photoError)
        }
    }

    private func notificationSection(_ model: AccountModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            SectionTitle(text: "Benachrichtigungen").padding(.top, 28)
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Neue Nachrichten")
                        .flexrText(.bodyLarge)
                        .foregroundStyle(FlexrColor.chalk)
                    Text("Benachrichtigung, wenn dir ein Match schreibt.")
                        .flexrText(.bodySmall)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
                Spacer(minLength: 12)
                Toggle(
                    "",
                    isOn: Binding(
                        get: { model.notificationsEnabled },
                        set: { enabled in Task { await model.setNotificationsEnabled(enabled) } }
                    )
                )
                .labelsHidden()
                .tint(FlexrColor.plate)
            }
            .padding(.top, 12)
        }
    }

    private func accountSection() -> some View {
        VStack(alignment: .leading, spacing: 0) {
            SectionTitle(text: "Konto").padding(.top, 28)
            FlexrSecondaryButton(title: "Ausloggen") {
                Task { await appModel.logout() }
            }
            .padding(.top, 12)
            FlexrDangerButton(title: "Konto löschen") {
                deletePassword = ""
                showDeleteDialog = true
            }
            .padding(.top, 10)
        }
    }

    /// Art. 16 Abs. 5 DSA: Der Melder muss nachsehen können, was aus seiner
    /// Meldung geworden ist.
    private func safetySection() -> some View {
        VStack(alignment: .leading, spacing: 0) {
            SectionTitle(text: "Sicherheit").padding(.top, 28)
            NavigationRow(title: "Meine Meldungen") { onOpen(.myReports) }
        }
    }

    private func legalSection() -> some View {
        VStack(alignment: .leading, spacing: 0) {
            SectionTitle(text: "Rechtliches").padding(.top, 28)
            ForEach(LegalDocument.allCases) { document in
                NavigationRow(title: document.title) { onOpen(.legal(document)) }
            }
        }
    }
}

private struct NavigationRow: View {

    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Text(title)
                    .flexrText(.bodyLarge)
                    .foregroundStyle(FlexrColor.chalk)
                Spacer()
                Image(systemName: FlexrIcon.forward)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(FlexrColor.chalkDim)
            }
            .padding(.vertical, 13)
            .padding(.horizontal, 4)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

/// Hinweisfeld zum Verifizierungsstand.
///
/// Der Bestätigungs-Hinweis lässt sich mit „Verstanden" dauerhaft wegklicken;
/// steht die Verifizierung noch aus, führt „Zur Verifizierung" direkt in den
/// Ablauf. Beide Aktionen sind sichtbare Schaltflächen statt einer unsichtbar
/// anklickbaren Fläche.
private struct VerificationHint: View {

    let isVerified: Bool
    let status: VerificationStatus
    let onDismiss: () -> Void
    let onStartVerification: () -> Void

    private var tint: Color {
        if isVerified { return FlexrColor.verified }
        if status == .submitted { return FlexrColor.chalkDim }
        return FlexrColor.plate
    }

    private var label: String {
        if isVerified { return "Verifiziert" }
        if status == .submitted { return "Prüfung läuft …" }
        return "Verifizierung"
    }

    private var message: String {
        if isVerified {
            return "Dein Profil ist verifiziert — andere sehen den blauen Haken neben deinem Namen."
        }
        switch status {
        case .submitted:
            return "Deine Selfies sind in Prüfung. Nach der Freigabe bekommst du den blauen Haken."
        case .rejected:
            return "Deine letzte Verifizierung wurde abgelehnt — du kannst es erneut versuchen."
        default:
            return "Zeig mit 3 Live-Selfies, dass du wirklich du bist — und hol dir den blauen Haken."
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 8) {
                if isVerified {
                    VerifiedBadge(size: 15)
                } else if status != .submitted {
                    Image(systemName: FlexrIcon.warning)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(tint)
                }
                Text(label).flexrText(.titleSmall).foregroundStyle(tint)
            }

            Text(message).flexrText(.bodySmall).foregroundStyle(FlexrColor.chalkDim)

            if isVerified {
                HStack {
                    Spacer()
                    Button("Verstanden", action: onDismiss)
                        .flexrText(.labelLarge)
                        .foregroundStyle(tint)
                }
            } else if status != .submitted {
                HStack {
                    Spacer()
                    Button(
                        status == .rejected ? "Erneut versuchen" : "Zur Verifizierung",
                        action: onStartVerification
                    )
                    .flexrText(.labelLarge)
                    .foregroundStyle(tint)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .flexrSurface(fill: tint.opacity(0.07), border: tint.opacity(0.35))
    }
}

private struct DeleteAccountSheet: View {

    @Binding var password: String
    let error: String?
    let isDeleting: Bool
    let onConfirm: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        NavigationStack {
            ZStack {
                FlexrBackground()
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        Text(
                            "Dein Konto wird sofort deaktiviert und ist für andere nicht mehr "
                                + "sichtbar. Alle Daten inklusive Fotos werden nach 30 Tagen "
                                + "endgültig und unwiderruflich gelöscht (siehe Datenschutzerklärung)."
                        )
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)

                        FlexrPasswordField(
                            text: $password,
                            label: "Zur Bestätigung dein Passwort",
                            placeholder: "••••••••",
                            textContentType: .password,
                            isError: error != nil,
                            supportingText: error
                        )

                        Spacer(minLength: 24)
                        FlexrDangerButton(
                            title: "Endgültig löschen",
                            isEnabled: !isDeleting,
                            isLoading: isDeleting,
                            isSolid: true,
                            action: onConfirm
                        )
                    }
                    .padding(20)
                }
            }
            .navigationTitle("Konto löschen")
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
