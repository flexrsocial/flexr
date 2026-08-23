import SwiftUI

struct AccountView: View {

    let onOpen: (Route) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var model: AccountModel?
    @State private var showDeleteDialog = false
    @State private var deletePassword = ""
    @State private var consentsExpanded = false
    @State private var pendingSensitiveRevoke = false

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
                privacySection(model)
                accountSection()
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
        .sheet(isPresented: $model.checkoutSheetVisible) {
            CheckoutConsentSheet(
                immediateStart: $model.checkoutImmediateStart,
                withdrawalAck: $model.checkoutWithdrawalAck,
                error: model.checkoutError,
                isStarting: model.isStartingCheckout,
                onConfirm: { Task { await model.confirmCheckout() } },
                onDismiss: model.closeCheckoutSheet
            )
        }
        // Der Widerruf von „sensitive_data" leert das Deck in beide Richtungen —
        // das ist die einzige Einwilligung, die eine Rückfrage verdient.
        .alert("Einwilligung widerrufen?", isPresented: $pendingSensitiveRevoke) {
            Button("Widerruf erklären", role: .destructive) {
                Task { await model.revokeConsent("sensitive_data") }
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text(
                "Geschlecht und gesuchtes Geschlecht sind die Grundlage des Matchings."
                    + "\n\nOhne diese Einwilligung schlagen wir dir keine Profile mehr vor "
                    + "und du erscheinst in keinem Deck. Dein Konto bleibt bestehen."
                    + "\n\nWillst du ganz weg, lösche stattdessen dein Konto."
            )
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
                        FlexrLinkButton(title: "Jetzt abonnieren") { model.openCheckoutSheet() }
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
            Text(
                "Ausgangspunkt ist die Adresse deines Gyms — nicht dein Wohnort und nicht "
                    + "dein aktueller Standort. Im eingestellten Umkreis siehst du auch "
                    + "Leute aus anderen Studios in der Nähe."
            )
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

    /// Einwilligungen einsehen und widerrufen — direkt in der App statt nur
    /// über die Web-App. Art. 7 Abs. 3 DSGVO: Der Widerruf darf nicht schwerer
    /// sein als die Erteilung, und die war bei der Registrierung ein Tippen.
    @ViewBuilder
    private func privacySection(_ model: AccountModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            SectionTitle(text: "Datenschutz & Sicherheit").padding(.top, 28)

            Button {
                withAnimation(.easeOut(duration: 0.18)) { consentsExpanded.toggle() }
            } label: {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Einwilligungen")
                            .flexrText(.bodyLarge)
                            .foregroundStyle(FlexrColor.chalk)
                        Text("Einsehen und widerrufen")
                            .flexrText(.bodySmall)
                            .foregroundStyle(FlexrColor.chalkDim)
                    }
                    Spacer()
                    Image(systemName: FlexrIcon.forward)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(FlexrColor.chalkDim)
                        .rotationEffect(.degrees(consentsExpanded ? 90 : 0))
                }
                .padding(.vertical, 13)
                .padding(.horizontal, 4)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            if consentsExpanded {
                ConsentList(
                    consents: model.consents,
                    isLoading: model.consentsLoading,
                    error: model.consentError,
                    isBusy: model.revokingConsentType != nil || model.grantingConsentType != nil,
                    onRevoke: { consentType in
                        if consentType == "sensitive_data" {
                            pendingSensitiveRevoke = true
                        } else {
                            Task { await model.revokeConsent(consentType) }
                        }
                    },
                    onGrant: { consentType in Task { await model.grantConsent(consentType) } }
                )
            }
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
        if status.needsDocument { return "Alter bestätigen" }
        return "Verifizierung"
    }

    private var message: String {
        if isVerified {
            return "Dein Profil ist verifiziert — andere sehen den blauen Haken neben deinem Namen."
        }
        switch status {
        case .submitted:
            return "Deine Verifizierung wird geprüft. Nach der Freigabe bekommst du den blauen Haken."
        case .idRequired, .reuploadRequired:
            // Der Ausweisschritt läuft derzeit nur über flexr.social - die App
            // holt ihn in einer eigenen Version nach.
            return "Es fehlt noch die Aufnahme deines amtlichen Lichtbildausweises. "
                + "Diesen Schritt schließt du gerade noch unter flexr.social ab."
        case .rejected:
            return "Deine Verifizierung konnte nicht abgeschlossen werden. "
                + "Bei Fragen: flexr.social@proton.me"
        default:
            return "Zeig mit einem Live-Selfie und einem Lichtbildausweis, dass du wirklich "
                + "du bist — und hol dir den blauen Haken."
        }
    }

    /// Ein Startknopf ergibt nur Sinn, wenn es etwas zu starten gibt.
    private var canStart: Bool {
        !isVerified && status != .submitted && status != .rejected && !status.needsDocument
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
            } else if canStart {
                HStack {
                    Spacer()
                    Button("Zur Verifizierung", action: onStartVerification)
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

/// Auch von der Paywall aus benutzt - nach Ablauf des Probemonats ist der
/// Konto-Screen nicht mehr erreichbar, die Selbstlöschung muss es aber bleiben
/// (Punkt 5 der Datenschutzerklärung). Deshalb nicht privat.
struct DeleteAccountSheet: View {

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

// MARK: - Einwilligungen

private let consentLabels: [String: String] = [
    "sensitive_data": "Verarbeitung von Geschlecht und gesuchtem Geschlecht",
    "verification_media": "Aufnahmen für die Alters- und Identitätsprüfung",
    "terms": "Angenommene AGB-Fassung",
]

private let consentGrundlage: [String: String] = [
    "sensitive_data": "Ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a DSGVO.",
    "verification_media": "Ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a DSGVO.",
    "terms": "Vertragsschluss, keine Einwilligung — daher nicht widerrufbar.",
]

/// „Sofortiger Leistungsbeginn" steht bewusst nicht in dieser Aufzählung: Die
/// maßgebliche § 10/§ 18-Abs.-1-Z-1-FAGG-Erklärung liegt unveränderlich im
/// CheckoutConsent-Datensatz und wirkt fort, solange der Vertrag läuft — ein
/// Widerruf hier hätte nichts bewirkt, aber das Gegenteil suggeriert.
private let consentRevocable: Set<String> = ["sensitive_data", "verification_media"]

/// Liste der DSGVO-Einwilligungen mit Sofort-Widerruf (Art. 7 Abs. 3 DSGVO) —
/// angehakt wurde mit einem Tippen, also geht auch der Widerruf mit einem
/// Tippen. Texte und Rechtsgrundlagen sind wortgleich mit Web-App
/// (`frontend/app/index.html`, `CONSENT_TEXT`/`CONSENT_GRUNDLAGE`) und
/// Android (`ConsentSection` in `AccountScreen.kt`).
private struct ConsentList: View {

    let consents: [ConsentDTO]
    let isLoading: Bool
    let error: String?
    let isBusy: Bool
    let onRevoke: (String) -> Void
    let onGrant: (String) -> Void

    /// Der Server liefert die volle Historie (neueste zuerst) — für den
    /// Nachweis nach Art. 7 Abs. 1 DSGVO nötig, bleibt also in der Datenbank.
    /// Angezeigt wird pro Art aber nur die neueste Zeile: eine wachsende Liste
    /// aus „widerrufen"/„erteilt"-Karten derselben Sache läse sich wie ein
    /// Protokoll statt wie eine Einstellung.
    private var visible: [ConsentDTO] {
        var gesehen = Set<String>()
        return consents
            .filter { $0.consentType != "immediate_start" }
            .filter { gesehen.insert($0.consentType).inserted }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            if isLoading, visible.isEmpty {
                HStack(spacing: 8) {
                    ProgressView().controlSize(.mini).tint(FlexrColor.plate)
                    Text("Lade …").flexrText(.bodySmall).foregroundStyle(FlexrColor.chalkDim)
                }
            } else if visible.isEmpty, error == nil {
                Text("Keine Einträge.")
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
            } else {
                ForEach(Array(visible.enumerated()), id: \.element.consentType) { index, consent in
                    row(consent)
                    if index != visible.count - 1 { HairlineDivider() }
                }
            }
            FieldError(message: error)
        }
    }

    @ViewBuilder
    private func row(_ consent: ConsentDTO) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            (Text(consentLabels[consent.consentType] ?? consent.consentType)
                .foregroundStyle(FlexrColor.chalk)
                + Text(consent.active ? "" : "  — widerrufen")
                .foregroundStyle(FlexrColor.chalkDim))
                .flexrText(.bodyMedium)
                .frame(maxWidth: .infinity, alignment: .leading)

            Text(details(consent))
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .frame(maxWidth: .infinity, alignment: .leading)

            if consentRevocable.contains(consent.consentType) {
                if consent.active {
                    FlexrLinkButton(
                        title: "Einwilligung widerrufen",
                        isEnabled: !isBusy
                    ) { onRevoke(consent.consentType) }
                } else {
                    FlexrLinkButton(
                        title: "Einwilligung erneut erteilen",
                        isEnabled: !isBusy
                    ) { onGrant(consent.consentType) }
                }
            }
        }
        .padding(.vertical, 10)
    }

    private func details(_ consent: ConsentDTO) -> String {
        let datum = ServerTime.parse(consent.active ? consent.grantedAt : consent.revokedAt)
            .map(ServerTime.formatDay) ?? "—"
        var text = consent.active
            ? "Erteilt am \(datum), Fassung \(consent.version)."
            : "Widerrufen am \(datum)."
        if let grundlage = consentGrundlage[consent.consentType] { text += " " + grundlage }
        return text
    }
}

// MARK: - Erklärungen vor dem Checkout

/// Zwei getrennte, nicht vorangekreuzte Erklärungen vor jedem Wechsel zu
/// Stripe (§ 10 und § 18 Abs. 1 Z 1 FAGG) — ohne beide antwortet das Backend
/// mit `422 field required` (`backend/app/schemas.py:CheckoutRequest`).
/// Wortlaut identisch mit Web-App (`immediateStartOverlay` in
/// `frontend/app/index.html`) und Android (`CheckoutDialog`). Bewusst ein Blatt
/// und kein `alert`: Ein Alert trägt keine zwei antippbaren Kästchen mit
/// mehrzeiligem Fließtext. Nicht privat — die Paywall nutzt denselben Weg.
struct CheckoutConsentSheet: View {

    @Binding var immediateStart: Bool
    @Binding var withdrawalAck: Bool
    let error: String?
    let isStarting: Bool
    let onConfirm: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        NavigationStack {
            ZStack {
                FlexrBackground()
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        CheckoutConsentRow(
                            isOn: $immediateStart,
                            text: "Ich stimme ausdrücklich zu, dass FLEXR bereits vor Ablauf der "
                                + "14-tägigen Rücktrittsfrist mit der Erbringung der "
                                + "kostenpflichtigen Dienstleistung beginnt."
                        )
                        CheckoutConsentRow(
                            isOn: $withdrawalAck,
                            text: "Ich bestätige, dass ich zur Kenntnis genommen habe, dass mein "
                                + "Rücktrittsrecht nach vollständiger Vertragserfüllung durch "
                                + "FLEXR erlischt, wenn die gesetzlichen Voraussetzungen dafür "
                                + "erfüllt sind."
                        )

                        FieldError(message: error)

                        Spacer(minLength: 24)
                        FlexrButton(
                            title: "Weiter zur Zahlung",
                            isEnabled: !isStarting,
                            isLoading: isStarting,
                            action: onConfirm
                        )
                    }
                    .padding(20)
                }
            }
            .navigationTitle("Vor der Zahlung")
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

/// Eine der beiden Checkout-Erklärungen — gleiches Muster wie `ConsentCheckbox`
/// in RegisterView.swift, nur ohne eingebetteten Rechtstext-Link.
private struct CheckoutConsentRow: View {

    @Binding var isOn: Bool
    let text: String

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

            Text(text)
                .flexrText(.bodyMedium)
                .foregroundStyle(FlexrColor.chalk)
                .frame(maxWidth: .infinity, alignment: .leading)
                .contentShape(Rectangle())
                .onTapGesture { isOn.toggle() }
        }
        .padding(.vertical, 8)
    }
}
