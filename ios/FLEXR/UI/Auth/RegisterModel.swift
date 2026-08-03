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

    init(
        auth: AuthRepository,
        profiles: ProfileRepository,
        gyms: GymRepository,
        plz: PlzRepository
    ) {
        self.auth = auth
        self.profiles = profiles
        self.gyms = gyms
        self.plz = plz
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
                        ? (error.localizedDescription)
                        : "Ort konnte nicht ermittelt werden. Bitte später erneut versuchen."
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
            successNotice = "Danke! Vorschlag eingereicht — du kannst das Gym sofort verwenden."
        } catch {
            suggestion.isSubmitting = false
            suggestion.error = error.localizedDescription
            gymSuggestion = suggestion
        }
    }

    // MARK: - Fotos

    func onPhotoPicked(_ data: Data) async {
        guard photos.count < ImageProcessor.maxPhotos else {
            photoError = "Maximal \(ImageProcessor.maxPhotos) Fotos."
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
            photoError = error.errorDescription
        } catch {
            photoError = "Foto konnte nicht geladen werden."
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
                consentWithdrawalWaiver: consentWithdrawalWaiver
            )
            let failures = await uploadPhotos()
            if failures == 0 {
                successNotice = "Profil erstellt. Willkommen bei FLEXR 💪"
            } else if failures == photos.count {
                successNotice = "Profil erstellt — Foto-Upload fehlgeschlagen. "
                    + "Bitte im Konto ein Foto hinzufügen."
            } else {
                successNotice = "Profil erstellt — nicht alle Fotos konnten hochgeladen werden."
            }
        } catch {
            self.error = (error as? FlexrAPIError)?.message ?? "Registrierung fehlgeschlagen."
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
            return "Bitte E-Mail, Passwort (min. \(Self.minPasswordLength) Zeichen), "
                + "Name und Geburtsdatum angeben."
        }
        let age = ServerTime.age(from: birthdate)
        if age < Self.minAge { return "Du musst mindestens 18 Jahre alt sein." }
        if age > Self.maxAge { return "Bitte ein gültiges Geburtsdatum angeben." }
        if resolvedCity == nil {
            return "Bitte eine gültige österreichische Postleitzahl eingeben "
                + "(Ort wird automatisch ermittelt)."
        }
        if gender == nil { return "Bitte ein Geschlecht auswählen." }
        if gymPicker.selectedLabel == nil { return "Bitte ein Gym aus der Liste auswählen." }
        if photos.isEmpty { return "Bitte lade mindestens ein Foto hoch." }
        if !consentSensitiveData || !consentWithdrawalWaiver {
            return "Bitte beide Zustimmungen ankreuzen, um fortzufahren."
        }
        return nil
    }
}
