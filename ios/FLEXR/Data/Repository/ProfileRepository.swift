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

    /// GPS-Position speichern — sie hat für die Umkreissuche Vorrang vor der PLZ.
    @discardableResult

    /// Ohne Standortfreigabe: gespeicherte Position löschen, es gilt wieder die PLZ.
    @discardableResult

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

    private func upload(_ data: Data, mimeType: String) async throws -> String {
        let presign = try await api.presignPhoto(PresignPhotoRequestDTO(contentType: mimeType))
        try await api.upload(to: presign.uploadUrl, contentType: mimeType, data: data)
        return presign.objectKey
    }
}
