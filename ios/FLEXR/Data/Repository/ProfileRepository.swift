import Foundation

/// Eigenes Profil: Stammdaten, Standort und Fotos.
///
/// Das aktuelle Profil ist beobachtbarer Zustand, damit alle Bildschirme
/// (Konto, Chat-Sperre, Match-Overlay) dieselbe Wahrheit sehen — das ersetzt
/// die globale `myProfile`-Variable des Web-Frontends.
@MainActor
@Observable
final class ProfileRepository {

    private(set) var myProfile: MyProfile?

    @ObservationIgnored private let api: FlexrAPI
    @ObservationIgnored private let session: SessionStore

    init(api: FlexrAPI, session: SessionStore) {
        self.api = api
        self.session = session
    }

    @discardableResult
    func refresh() async throws -> MyProfile {
        let profile = try await api.myProfile().toDomain()
        myProfile = profile
        session.userID = profile.id
        return profile
    }

    func clear() {
        myProfile = nil
    }

    @discardableResult
    func updateProfile(
        plz: String,
        city: String,
        gymLabel: String,
        bio: String,
        searchRadiusKm: Int
    ) async throws -> MyProfile {
        let updated = try await api.updateMyProfile(
            UpdateProfileRequestDTO(
                plz: plz,
                city: city,
                gym: gymLabel,
                // Leere Bio bedeutet serverseitig „Bio entfernen".
                bio: bio,
                searchRadiusKm: searchRadiusKm
            )
        ).toDomain()
        myProfile = updated
        return updated
    }

    func deleteAccount(password: String) async throws {
        try await api.deleteMyAccount(DeleteAccountRequestDTO(password: password))
        myProfile = nil
    }

    // MARK: - Einwilligungen (Art. 7 Abs. 3 DSGVO)

    /// Volle Historie des Einwilligungs-Ledgers, neueste Zeile je Art zuerst.
    func consents() async throws -> [ConsentDTO] {
        try await api.myConsents()
    }

    func revokeConsent(_ consentType: String) async throws -> ConsentRevokeResponseDTO {
        try await api.revokeConsent(ConsentRevokeRequestDTO(consentType: consentType))
    }

    /// Einen zuvor erklärten Widerruf zurücknehmen (erneute Einwilligung).
    func grantConsent(_ consentType: String) async throws -> ConsentGrantResponseDTO {
        try await api.grantConsent(ConsentGrantRequestDTO(consentType: consentType))
    }

    // MARK: - Fotos

    /// Lädt Vollbild und Thumbnail direkt in den Objekt-Storage und registriert
    /// anschließend die object_keys — es fließen keine Bilddaten durchs Backend.
    @discardableResult
    func addPhoto(_ photo: PreparedPhoto) async throws -> MyProfile {
        let fullKey = try await upload(photo.full, mimeType: photo.mimeType)
        let thumbKey = try await upload(photo.thumbnail, mimeType: photo.mimeType)
        let updated = try await api.addPhoto(
            AddPhotoRequestDTO(objectKey: fullKey, thumbObjectKey: thumbKey)
        ).toDomain()
        myProfile = updated
        return updated
    }

    @discardableResult
    func deletePhoto(id: String) async throws -> MyProfile {
        let updated = try await api.deletePhoto(id: id).toDomain()
        myProfile = updated
        return updated
    }

    /// Neue Reihenfolge speichern. Erwartet die vollständige Liste der eigenen
    /// Foto-IDs; photos[0] wird zum Hauptfoto (Swipe-Karte, Avatar, Chat-Kopf).
    @discardableResult
    func reorderPhotos(_ photoIDs: [String]) async throws -> MyProfile {
        let updated = try await api.reorderPhotos(
            ReorderPhotosRequestDTO(photoIds: photoIDs)
        ).toDomain()
        myProfile = updated
        return updated
    }

    @discardableResult
    func updateNotificationSettings(
        _ request: NotificationSettingsRequestDTO
    ) async throws -> MyProfile {
        let updated = try await api.updateNotificationSettings(request).toDomain()
        myProfile = updated
        return updated
    }

    private func upload(_ data: Data, mimeType: String) async throws -> String {
        let presign = try await api.presignPhoto(PresignPhotoRequestDTO(contentType: mimeType))
        try await api.upload(to: presign.uploadUrl, contentType: mimeType, data: data)
        return presign.objectKey
    }
}
