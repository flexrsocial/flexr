import Foundation

/// Ein im Onboarding gewähltes Foto: Vorschau plus fertig aufbereitete Daten.
struct PendingPhoto: Identifiable, Equatable {
    let id: String
    let preview: Data
    let prepared: PreparedPhoto
}

/// Registrierung inklusive Profilanlage.
///
/// Ablauf wie im Web: erst das Konto anlegen (dabei entsteht der Token), dann
/// die im Onboarding gewählten Fotos hochladen — vorher gibt es keine
/// Nutzer-ID, unter der sie abgelegt werden könnten.
@MainActor
@Observable
final class RegisterModel {

    static let minPasswordLength = 8
    static let minAge = 18
    static let maxAge = 99
    static let bioMaxLength = 280
    private static let lookupDebounce: Duration = .milliseconds(300)

    var email = ""
    var password = ""
    var name = ""
    var birthdate: Date?
    // Kein `didSet`: Das @Observable-Makro schreibt Stored Properties in
    // berechnete um, Property-Observer sind dort nicht zulässig. Die Ansicht
    // stößt die Ortsermittlung deshalb über `.onChange` an.
    var postalCode = ""
    var plzLookup: PlzLookupState = .idle
    var gender: Gender?
    var gymPicker = GymPickerState()
    var gymSuggestion: GymSuggestionState?
    var bio = ""
    var photos: [PendingPhoto] = []
    var photoError: String?
    var isPreparingPhoto = false
    var consentSensitiveData = false
    var consentWithdrawalWaiver = false
    var isSubmitting = false
    var error: String?
    /// Meldung, die nach dem Wechsel in die App eingeblendet wird.
    var successNotice: String?

    var resolvedCity: String? { plzLookup.city }
    var age: Int? { birthdate.map { ServerTime.age(from: $0) } }

    var canSubmit: Bool {
        !isSubmitting
            && !email.isEmpty
            && password.count >= Self.minPasswordLength
            && !name.isEmpty
            && birthdate != nil
            && resolvedCity != nil
            && gender != nil
            && gymPicker.selectedLabel != nil
            && !photos.isEmpty
            && consentSensitiveData
            && consentWithdrawalWaiver
    }

    @ObservationIgnored private let auth: AuthRepository
    @ObservationIgnored private let profiles: ProfileRepository
    @ObservationIgnored private let gyms: GymRepository
    @ObservationIgnored private let plz: PlzRepository

    @ObservationIgnored private var plzLookupTask: Task<Void, Never>?
    @ObservationIgnored private var gymSearchTask: Task<Void, Never>?

    /// Texte in der gewählten Sprache. Als Referenz auf den Speicher und nicht
    /// als Kopie: eine Umstellung mitten in der Sitzung wirkt dann sofort auch
    /// auf Meldungen, die dieses Modell danach erzeugt.
    @ObservationIgnored private let languageStore: LanguageStore
    private var s: FlexrStrings { languageStore.strings }

    init(
        auth: AuthRepository,
        profiles: ProfileRepository,
        gyms: GymRepository,
        plz: PlzRepository,
        languageStore: LanguageStore
    ) {
        self.auth = auth
        self.profiles = profiles
        self.gyms = gyms
        self.plz = plz
        self.languageStore = languageStore
    }

    // MARK: - PLZ

    func postalCodeChanged() {
        plzLookup = .idle
        error = nil
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
                        ? s(.errorPostalCodeUnknown)
                        : s(.plzLookupFailed)
                )
            }
        }
    }

    // MARK: - Gym

    func onGymQueryChange(_ value: String) {
        // Der Name allein ist keine gültige Auswahl — sobald der Text vom
        // gewählten Gym abweicht, gilt die Auswahl als aufgehoben.
        let keepSelection = gymPicker.selectedLabel
            .map { $0.components(separatedBy: " — ").first == value } ?? false
        gymPicker.query = value
        gymPicker.isExpanded = true
        if !keepSelection { gymPicker.selectedLabel = nil }
        error = nil
        searchGyms(value)
    }

    func onGymSelected(_ gym: Gym) {
        gymPicker.query = gym.name
        gymPicker.selectedLabel = gym.label
        gymPicker.isExpanded = false
    }

    private func searchGyms(_ query: String) {
        gymSearchTask?.cancel()
        gymSearchTask = Task {
            try? await Task.sleep(for: Self.lookupDebounce)
            guard !Task.isCancelled else { return }
            gymPicker.isSearching = true
            let results = (try? await gyms.search(query: query)) ?? []
            guard !Task.isCancelled else { return }
            gymPicker.results = results
            gymPicker.isSearching = false
        }
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
            successNotice = s(.gymSuggestThanks)
        } catch {
            suggestion.isSubmitting = false
            suggestion.error = error.localizedDescription
            gymSuggestion = suggestion
        }
    }

    // MARK: - Fotos

    func onPhotoPicked(_ data: Data) async {
        guard photos.count < ImageProcessor.maxPhotos else {
            photoError = s(.registerPhotoMax, ImageProcessor.maxPhotos)
            return
        }
        isPreparingPhoto = true
        photoError = nil
        do {
            let prepared = try await ImageProcessor.prepare(data: data)
            photos.append(
                PendingPhoto(id: UUID().uuidString, preview: prepared.thumbnail, prepared: prepared)
            )
        } catch let error as PhotoTooSmallError {
            photoError = s(.photoTooSmall, error.width, error.height,
                           ImageProcessor.minEdgePx, ImageProcessor.minEdgePx)
        } catch {
            photoError = s(.registerPhotoLoadFailed)
        }
        isPreparingPhoto = false
    }

    func removePhoto(id: String) {
        photos.removeAll { $0.id == id }
    }

    // MARK: - Absenden

    func register() async {
        if let message = validate() {
            error = message
            return
        }
        guard let birthdate, let city = resolvedCity, let gender,
              let gymLabel = gymPicker.selectedLabel
        else { return }

        isSubmitting = true
        error = nil
        do {
            try await auth.register(
                email: email,
                password: password,
                name: name,
                birthdate: birthdate,
                plz: postalCode,
                city: city,
                gender: gender,
                gymLabel: gymLabel,
                bio: bio,
                consentSensitiveData: consentSensitiveData,
                consentWithdrawalWaiver: consentWithdrawalWaiver,
                // Sprache, in der gerade registriert wird. Der Server merkt
                // sie am Profil und schreibt seine Mails danach — sie
                // entstehen zum Teil ohne die App (Tagesjob, Stripe-Webhook,
                // Moderation) und können die Einstellung nirgends sonst
                // nachlesen.
                language: languageStore.language.rawValue
            )
            let failures = await uploadPhotos()
            if failures == 0 {
                successNotice = s(.registerDone)
            } else if failures == photos.count {
                successNotice = s(.registerDoneNoPhoto)
            } else {
                successNotice = s(.registerDonePartial)
            }
        } catch {
            self.error = (error as? FlexrAPIError)?.message ?? s(.registerFailed)
        }
        isSubmitting = false
    }

    /// Lädt die Fotos einzeln hoch und liefert die Anzahl der Fehlschläge.
    private func uploadPhotos() async -> Int {
        var failures = 0
        for photo in photos {
            do {
                try await profiles.addPhoto(photo.prepared)
            } catch {
                failures += 1
            }
        }
        return failures
    }

    private func validate() -> String? {
        guard !email.isEmpty, password.count >= Self.minPasswordLength, !name.isEmpty,
              let birthdate
        else {
            return s(.registerErrRequired, Self.minPasswordLength)
        }
        let age = ServerTime.age(from: birthdate)
        if age < Self.minAge { return s(.registerErrUnder18) }
        if age > Self.maxAge { return s(.registerErrBirthdate) }
        if resolvedCity == nil { return s(.registerErrPostalCode) }
        if gender == nil { return s(.registerErrGender) }
        if gymPicker.selectedLabel == nil { return s(.registerErrGym) }
        if photos.isEmpty { return s(.registerErrPhoto) }
        if !consentSensitiveData || !consentWithdrawalWaiver {
            return s(.registerErrConsents)
        }
        return nil
    }
}
