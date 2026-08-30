import Foundation

/// Konto-Bereich: Profil bearbeiten, Fotos verwalten, Mitgliedschaft,
/// Verifizierung und Kontolöschung.
@MainActor
@Observable
final class AccountModel {

    static let bioMaxLength = 280
    static let minRadiusKm = 2
    static let maxRadiusKm = 250
    private static let lookupDebounce: Duration = .milliseconds(300)

    // Kein `didSet`: Das @Observable-Makro schreibt Stored Properties in
    // berechnete um, Property-Observer sind dort nicht zulässig. Die Ansicht
    // stößt die Ortsermittlung über `.onChange` an; die Längenbegrenzung der
    // Bio übernimmt das Eingabefeld selbst.
    var postalCode = ""
    var plzLookup: PlzLookupState = .idle
    var gymPicker = GymPickerState()
    var gymSuggestion: GymSuggestionState?
    var bio = ""
    var searchRadiusKm = 20.0
    var isSaving = false
    var saveError: String?
    var photoError: String?
    var isUploadingPhoto = false
    var verificationStatus: VerificationStatus = .none
    /// Bestätigter „verifiziert"-Hinweis wird dauerhaft ausgeblendet.
    var verifiedHintDismissed = false
    var notificationsEnabled = true
    // Einwilligungen (Art. 7 Abs. 3 DSGVO)
    var consents: [ConsentDTO] = []
    var consentsLoading = false
    var consentError: String?
    var revokingConsentType: String?
    var grantingConsentType: String?
    // Blockierte Personen
    var blockedUsers: [BlockedUser] = []
    var blockedUsersLoading = false
    var blockedUsersError: String?
    var unblockingUserID: String?
    // Zwei getrennte, nicht vorangekreuzte Erklärungen vor jedem Checkout
    var checkoutSheetVisible = false
    var checkoutImmediateStart = false
    var checkoutWithdrawalAck = false
    var checkoutError: String?
    var isStartingCheckout = false
    var isDeleting = false
    var deleteError: String?
    /// Nach dem Löschen: die App meldet ab.
    var didDeleteAccount = false
    /// Extern zu öffnende Seite (Stripe-Checkout, Billing-Portal).
    var externalURL: ExternalURL?

    var resolvedCity: String? { plzLookup.city }
    var profile: MyProfile? { profiles.myProfile }
    var membership: Membership? { billing.membership }

    @ObservationIgnored private let profiles: ProfileRepository
    @ObservationIgnored private let billing: BillingRepository
    @ObservationIgnored private let gyms: GymRepository
    @ObservationIgnored private let plz: PlzRepository
    @ObservationIgnored private let verification: VerificationRepository
    @ObservationIgnored private let safety: SafetyRepository
    @ObservationIgnored private let session: SessionStore
    @ObservationIgnored private let notifications: MessageRefreshService
    @ObservationIgnored private let onMessage: (String) -> Void

    @ObservationIgnored private var plzLookupTask: Task<Void, Never>?
    @ObservationIgnored private var gymSearchTask: Task<Void, Never>?
    /// Verhindert, dass das Vorbefüllen aus dem Profil eine Ortsermittlung
    /// auslöst — der Ort steht dort ja schon fest.
    @ObservationIgnored private var lastHandledPostalCode: String?

    init(container: AppContainer, onMessage: @escaping (String) -> Void) {
        profiles = container.profiles
        billing = container.billing
        gyms = container.gyms
        plz = container.plz
        verification = container.verification
        safety = container.safety
        session = container.session
        notifications = container.notifications
        self.onMessage = onMessage
    }

    func load() async {
        if let profile = profiles.myProfile { prefill(from: profile) }
        notificationsEnabled = session.notificationsEnabled
        verifiedHintDismissed = session.verifiedHintDismissed

        if let refreshed = try? await profiles.refresh() { prefill(from: refreshed) }
        _ = try? await billing.refresh()
        await refreshVerificationStatus()
        await refreshConsents()
        await refreshBlockedUsers()
    }

    private func prefill(from profile: MyProfile) {
        postalCode = profile.plz
        lastHandledPostalCode = profile.plz
        plzLookup = profile.profile.city.isEmpty ? .idle : .resolved(city: profile.profile.city)
        gymPicker.query = profile.profile.gymName
        gymPicker.selectedLabel = profile.profile.gym.isEmpty ? nil : profile.profile.gym
        gymPicker.isExpanded = false
        bio = profile.profile.bio ?? ""
        searchRadiusKm = Double(profile.searchRadiusKm)
    }

    // MARK: - PLZ

    func postalCodeChanged() {
        guard postalCode != lastHandledPostalCode else { return }
        lastHandledPostalCode = postalCode
        plzLookup = .idle
        saveError = nil
        plzLookupTask?.cancel()
        guard PlzRepository.isValidPostalCode(postalCode) else { return }

        let value = postalCode
        plzLookupTask = Task {
            try? await Task.sleep(for: Self.lookupDebounce)
            guard !Task.isCancelled else { return }
            plzLookup = .loading
            do {
                let city = try await plz.municipality(forPostalCode: value)
                guard !Task.isCancelled else { return }
                plzLookup = .resolved(city: city)
            } catch {
                guard !Task.isCancelled else { return }
                plzLookup = .failed(
                    message: error is UnknownPostalCodeError
                        ? error.localizedDescription
                        : "Ort konnte nicht ermittelt werden."
                )
            }
        }
    }

    // MARK: - Gym

    func onGymQueryChange(_ value: String) {
        let keepSelection = gymPicker.selectedLabel
            .map { $0.components(separatedBy: " — ").first == value } ?? false
        gymPicker.query = value
        gymPicker.isExpanded = true
        if !keepSelection { gymPicker.selectedLabel = nil }
        saveError = nil

        gymSearchTask?.cancel()
        gymSearchTask = Task {
            try? await Task.sleep(for: Self.lookupDebounce)
            guard !Task.isCancelled else { return }
            gymPicker.isSearching = true
            let results = (try? await gyms.search(query: value)) ?? []
            guard !Task.isCancelled else { return }
            gymPicker.results = results
            gymPicker.isSearching = false
        }
    }

    func onGymSelected(_ gym: Gym) {
        gymPicker.query = gym.name
        gymPicker.selectedLabel = gym.label
        gymPicker.isExpanded = false
    }

    func openGymSuggestion() {
        gymSuggestion = GymSuggestionState(
            name: gymPicker.query.trimmingCharacters(in: .whitespaces)
        )
        gymPicker.isExpanded = false
    }

    func closeGymSuggestion() { gymSuggestion = nil }

    func submitGymSuggestion() async {
        guard var suggestion = gymSuggestion, suggestion.isValid, !suggestion.isSubmitting else { return }
        suggestion.isSubmitting = true
        suggestion.error = nil
        gymSuggestion = suggestion

        do {
            let gym = try await gyms.suggest(
                name: suggestion.name,
                street: suggestion.street,
                houseNumber: suggestion.houseNumber,
                plz: suggestion.postalCode
            )
            gymSuggestion = nil
            gymPicker.query = gym.name
            gymPicker.selectedLabel = gym.label
            gymPicker.isExpanded = false
            onMessage("Danke! Vorschlag eingereicht — sofort verwendbar.")
        } catch {
            suggestion.isSubmitting = false
            suggestion.error = error.localizedDescription
            gymSuggestion = suggestion
        }
    }

    // MARK: - Profil speichern

    func saveProfile() async {
        guard let city = resolvedCity else {
            saveError = "Bitte eine gültige österreichische Postleitzahl eingeben "
                + "(Ort wird automatisch ermittelt)."
            return
        }
        guard let profile, !profile.photos.isEmpty else {
            saveError = "Bitte lade mindestens ein Foto hoch, bevor du speicherst."
            return
        }
        guard let gymLabel = gymPicker.selectedLabel else {
            saveError = "Bitte ein Gym aus der Liste auswählen."
            return
        }

        isSaving = true
        saveError = nil
        do {
            _ = try await profiles.updateProfile(
                plz: postalCode,
                city: city,
                gymLabel: gymLabel,
                bio: bio.trimmingCharacters(in: .whitespacesAndNewlines),
                searchRadiusKm: Int(searchRadiusKm.rounded())
            )
            onMessage("Profil gespeichert ✓")
        } catch {
            saveError = (error as? FlexrAPIError)?.message ?? "Speichern fehlgeschlagen."
        }
        isSaving = false
    }

    // MARK: - Fotos

    func onPhotoPicked(_ data: Data) async {
        isUploadingPhoto = true
        photoError = nil
        do {
            let prepared = try await ImageProcessor.prepare(data: data)
            _ = try await profiles.addPhoto(prepared)
        } catch let error as PhotoTooSmallError {
            photoError = error.errorDescription
        } catch let error as FlexrAPIError {
            photoError = error.message
        } catch {
            photoError = "Foto-Upload fehlgeschlagen."
        }
        isUploadingPhoto = false
    }

    func removePhoto(id: String) {
        guard (profile?.photos.count ?? 0) > 1 else {
            photoError = "Mindestens ein Foto ist erforderlich. Lade zuerst ein weiteres hoch."
            return
        }
        photoError = nil
        Task {
            do {
                _ = try await profiles.deletePhoto(id: id)
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }

    // MARK: - Verifizierung

    func refreshVerificationStatus() async {
        verificationStatus = (try? await verification.status())?.status ?? .none
    }

    /// „Verstanden" auf dem Verifiziert-Hinweis: dauerhaft ausblenden.
    func dismissVerifiedHint() {
        verifiedHintDismissed = true
        session.verifiedHintDismissed = true
    }

    // MARK: - Mitgliedschaft

    /// Zwei getrennte, nicht vorangekreuzte Erklärungen vor jedem Checkout
    /// (§ 10 und § 18 Abs. 1 Z 1 FAGG) — ohne beide lehnt das Backend die
    /// Anfrage mit 422 ab (`CheckoutRequest` in `backend/app/schemas.py`).
    func openCheckoutSheet() {
        checkoutImmediateStart = false
        checkoutWithdrawalAck = false
        checkoutError = nil
        checkoutSheetVisible = true
    }

    func closeCheckoutSheet() {
        checkoutSheetVisible = false
    }

    func confirmCheckout() async {
        guard !isStartingCheckout else { return }
        guard checkoutImmediateStart, checkoutWithdrawalAck else {
            checkoutError = "Bitte bestätige beide Erklärungen, um fortzufahren."
            return
        }
        isStartingCheckout = true
        checkoutError = nil
        do {
            let url = try await billing.checkoutURL(immediateStart: true, withdrawalAck: true)
            checkoutSheetVisible = false
            externalURL = ExternalURL(url)
        } catch {
            checkoutError = (error as? FlexrAPIError)?.message
                ?? "Checkout konnte nicht gestartet werden."
        }
        isStartingCheckout = false
    }

    func openBillingPortal() {
        Task {
            do {
                externalURL = ExternalURL(try await billing.portalURL())
            } catch {
                onMessage(error.localizedDescription)
            }
        }
    }

    // MARK: - Benachrichtigungen

    func setNotificationsEnabled(_ enabled: Bool) async {
        if enabled {
            // Ab iOS braucht das Anzeigen von Benachrichtigungen eine
            // Erlaubnis — hier im Moment des Einschaltens erfragt, wo der Zweck
            // offensichtlich ist.
            let granted = await notifications.requestNotificationPermission()
            if !granted {
                notificationsEnabled = false
                session.notificationsEnabled = false
                notifications.cancel()
                onMessage("Ohne Berechtigung können keine Benachrichtigungen angezeigt werden.")
                return
            }
        }
        notificationsEnabled = enabled
        session.notificationsEnabled = enabled
        if enabled { notifications.schedule() } else { notifications.cancel() }
    }

    // MARK: - Einwilligungen

    func refreshConsents() async {
        consentsLoading = true
        consentError = nil
        do {
            consents = try await profiles.consents()
        } catch {
            consentError = (error as? FlexrAPIError)?.message
                ?? "Einwilligungen konnten nicht geladen werden."
        }
        consentsLoading = false
    }

    func revokeConsent(_ consentType: String) async {
        guard revokingConsentType == nil, grantingConsentType == nil else { return }
        revokingConsentType = consentType
        consentError = nil
        do {
            let result = try await profiles.revokeConsent(consentType)
            consents = try await profiles.consents()
            onMessage(result.consequence)
        } catch {
            consentError = (error as? FlexrAPIError)?.message
                ?? "Der Widerruf konnte nicht gespeichert werden."
        }
        revokingConsentType = nil
    }

    /// Einen zuvor erklärten Widerruf rückgängig machen.
    func grantConsent(_ consentType: String) async {
        guard revokingConsentType == nil, grantingConsentType == nil else { return }
        grantingConsentType = consentType
        consentError = nil
        do {
            let result = try await profiles.grantConsent(consentType)
            consents = try await profiles.consents()
            onMessage(result.consequence)
        } catch {
            consentError = (error as? FlexrAPIError)?.message
                ?? "Die erneute Einwilligung konnte nicht gespeichert werden."
        }
        grantingConsentType = nil
    }

    // MARK: - Blockierte Personen

    func refreshBlockedUsers() async {
        blockedUsersLoading = true
        blockedUsersError = nil
        do {
            blockedUsers = try await safety.blockedUsers()
        } catch {
            blockedUsersError = (error as? FlexrAPIError)?.message
                ?? "Deine Blockierungen konnten nicht geladen werden."
        }
        blockedUsersLoading = false
    }

    /// Hebt eine Blockierung auf. Löst weder Match noch Chatverlauf auf, blendet
    /// sie nur wieder ein — entspricht `DELETE /api/blocks/{id}` in safety.py.
    func unblockUser(_ userID: String) async {
        guard unblockingUserID == nil else { return }
        unblockingUserID = userID
        blockedUsersError = nil
        do {
            try await safety.unblock(userID: userID)
            blockedUsers.removeAll { $0.userId == userID }
        } catch {
            blockedUsersError = (error as? FlexrAPIError)?.message ?? "Aufheben fehlgeschlagen."
        }
        unblockingUserID = nil
    }

    // MARK: - Konto löschen

    func deleteAccount(password: String) async {
        guard !password.isEmpty else {
            deleteError = "Bitte gib zur Bestätigung dein Passwort ein."
            return
        }
        isDeleting = true
        deleteError = nil
        do {
            try await profiles.deleteAccount(password: password)
            onMessage("Dein Konto wurde deaktiviert und wird in 30 Tagen endgültig gelöscht.")
            didDeleteAccount = true
        } catch {
            deleteError = (error as? FlexrAPIError)?.message ?? "Löschen fehlgeschlagen."
        }
        isDeleting = false
    }
}
