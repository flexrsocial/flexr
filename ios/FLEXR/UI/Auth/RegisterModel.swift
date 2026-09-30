import Foundation

/// Ein im Onboarding gewähltes Foto: Vorschau plus fertig aufbereitete Daten.
struct PendingPhoto: Identifiable, Equatable {
    let id: String
    let preview: Data
    let prepared: PreparedPhoto
}

/// Pflichtfelder der Registrierung, in der Reihenfolge des Formulars.
enum RegisterField: Hashable {
    case email, password, passwordConfirm, name, birthdate, postalCode, gender, gym, photos, consent
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
    /// Zweite Eingabe gegen Tippfehler: Ein vertipptes Passwort fällt sonst
    /// erst beim nächsten Login auf, wenn niemand mehr weiß, was drinstand.
    var passwordConfirm = ""
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
    var isSubmitting = false
    var error: String?
    /// Zu welchem Feld `error` gehoert (Pruefung beim Absenden). Die Ansicht
    /// zeigt die Meldung dann direkt unter dem Feld und scrollt hin - vorher
    /// stand sie nur unten am Knopf (wie in Web-App und Android). `nil` heisst
    /// Meldung unten am Knopf (Antwort des Servers).
    var errorField: RegisterField?
    /// Zaehlt jeden Absendeversuch mit Feldfehler, damit auch ein zweiter
    /// Versuch am selben Feld erneut dorthin scrollt.
    var errorSeq = 0
    /// Meldung, die nach dem Wechsel in die App eingeblendet wird.
    var successNotice: String?

    var resolvedCity: String? { plzLookup.city }

    /// Vergeben wird nur, was zweimal gleich kam.
    var passwordsMatch: Bool { password == passwordConfirm }

    /// Hinweis am Wiederholungsfeld — aber erst, wenn dort etwas steht.
    /// Sonst stünde die Meldung schon beim ersten Zeichen des ersten Feldes.
    var passwordConfirmError: String? {
        guard !passwordConfirm.isEmpty, !passwordsMatch else { return nil }
        return s(.registerErrPasswordMismatchShort)
    }

    /// Wie viele Fotos bis zur Mindestanzahl noch fehlen (0, wenn erfüllt).
    var missingPhotos: Int { max(ImageProcessor.minPhotos - photos.count, 0) }
    var age: Int? { birthdate.map { ServerTime.age(from: $0) } }

    var canSubmit: Bool {
        !isSubmitting
            && !email.isEmpty
            && password.count >= Self.minPasswordLength
            && passwordsMatch
            && !name.isEmpty
            && birthdate != nil
            && resolvedCity != nil
            && gender != nil
            && gymPicker.selectedLabel != nil
            && photos.count >= ImageProcessor.minPhotos
            && consentSensitiveData
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

    /// Meldung fuer genau dieses Feld, falls die Pruefung es beanstandet hat.
    func fieldError(_ field: RegisterField) -> String? {
        errorField == field ? error : nil
    }

    /// Das beanstandete Feld wurde bearbeitet: Markierung und Meldung weg.
    func fieldEdited(_ field: RegisterField) {
        guard errorField == field else { return }
        errorField = nil
        error = nil
    }

    func register() async {
        if case let (field, message)? = validate() {
            error = message
            errorField = field
            errorSeq += 1
            return
        }
        errorField = nil
        guard let birthdate, let city = resolvedCity, let gender,
              let gymLabel = gymPicker.selectedLabel
        else { return }

        isSubmitting = true
        error = nil
        // Die Klammer um Registrierung *und* Erstupload: Ohne sie schaltet
        // `AppModel` beim Speichern des Tokens sofort auf die fertige App um
        // und räumt diesen Bildschirm samt laufendem Upload ab.
        auth.beginRegistration()
        defer { auth.finishRegistration() }
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

    /// Erstes fehlendes Feld samt Meldung - oder nil, wenn alles passt.
    private func validate() -> (RegisterField, String)? {
        let required = s(.registerErrRequired, Self.minPasswordLength)
        if email.isEmpty { return (.email, required) }
        if password.count < Self.minPasswordLength { return (.password, required) }
        if name.isEmpty { return (.name, required) }
        guard let birthdate else { return (.birthdate, required) }
        if !passwordsMatch { return (.passwordConfirm, s(.registerErrPasswordMismatch)) }
        let age = ServerTime.age(from: birthdate)
        if age < Self.minAge { return (.birthdate, s(.registerErrUnder18)) }
        if age > Self.maxAge { return (.birthdate, s(.registerErrBirthdate)) }
        if resolvedCity == nil { return (.postalCode, s(.registerErrPostalCode)) }
        if gender == nil { return (.gender, s(.registerErrGender)) }
        if gymPicker.selectedLabel == nil { return (.gym, s(.registerErrGym)) }
        if photos.count < ImageProcessor.minPhotos {
            return (.photos, s(.registerErrPhoto, ImageProcessor.minPhotos))
        }
        if !consentSensitiveData { return (.consent, s(.registerErrConsents)) }
        return nil
    }
}
