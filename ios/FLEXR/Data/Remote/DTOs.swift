import Foundation

/*
 * Eins-zu-eins-Abbildung der Pydantic-Schemas aus backend/app/schemas.py.
 *
 * Die Feldnamen bleiben serverseitig in snake_case; der JSON-Coder des
 * [APIClient] übersetzt sie über `convertFromSnakeCase`/`convertToSnakeCase`.
 * Dadurch braucht es hier — anders als bei kotlinx.serialization mit
 * `@SerialName` — keine Schlüsselzuordnung von Hand.
 */

// MARK: - Auth

struct RegisterRequestDTO: Encodable {
    let email: String
    let password: String
    let name: String
    let birthdate: String
    let plz: String
    let city: String
    let gender: String
    let gym: String
    let bio: String?
    let consentSensitiveData: Bool
    let consentWithdrawalWaiver: Bool
}

struct LoginRequestDTO: Encodable {
    let email: String
    let password: String
}

struct TokenResponseDTO: Decodable {
    let accessToken: String
    let tokenType: String?
}

// MARK: - Profil

struct PhotoDTO: Decodable {
    let id: String
    let url: String
    let thumbUrl: String?
    let position: Int?
    let status: String?
}

struct ProfileDTO: Decodable {
    let id: String
    let name: String
    let age: Int
    let city: String
    let gender: String
    let gym: String
    let bio: String?
    let isOnline: Bool?
    let isVerified: Bool?
    let distanceKm: Int?
    let photos: [PhotoDTO]?
}

struct MyProfileDTO: Decodable {
    let id: String
    let name: String
    let age: Int
    let city: String
    let gender: String
    let gym: String
    let bio: String?
    let isOnline: Bool?
    let isVerified: Bool?
    let distanceKm: Int?
    let photos: [PhotoDTO]?
    let plz: String
    let birthdate: String
    let searchRadiusKm: Int?
    let hasGpsLocation: Bool?
    // phone/phone_verified liefert das Backend zwar mit, die App nutzt sie
    // nicht — die Telefonprüfung ist auch im Web verworfen worden.
    let messagingMutedUntil: String?
}

struct UpdateProfileRequestDTO: Encodable {
    var plz: String?
    var city: String?
    var gym: String?
    var bio: String?
    var searchRadiusKm: Int?
}

struct DeleteAccountRequestDTO: Encodable {
    let password: String
}

struct LocationUpdateRequestDTO: Encodable {
    let lat: Double
    let lon: Double
}

struct PresignPhotoRequestDTO: Encodable {
    let contentType: String
}

struct PresignPhotoResponseDTO: Decodable {
    let uploadUrl: String
    let objectKey: String
}

struct AddPhotoRequestDTO: Encodable {
    let objectKey: String
    let thumbObjectKey: String?
}

// MARK: - Billing

struct MembershipStatusDTO: Decodable {
    let isSubscribed: Bool
    let trialEndsAt: String
    let isActive: Bool
}

struct CheckoutUrlDTO: Decodable {
    let checkoutUrl: String
}

struct PortalUrlDTO: Decodable {
    let portalUrl: String
}

// MARK: - Swipes & Matches

struct SwipeRequestDTO: Encodable {
    let toUserId: String
    let action: String
}

struct SwipeResultDTO: Decodable {
    let matched: Bool
}

struct MessageDTO: Decodable {
    let id: String
    let matchId: String
    let senderId: String
    let content: String
    let createdAt: String
    let readAt: String?
    let wasCensored: Bool?
}

struct SendMessageRequestDTO: Encodable {
    let content: String
}

struct MatchDTO: Decodable {
    let matchId: String
    let profile: ProfileDTO
    let lastMessage: MessageDTO?
    let unreadCount: Int?
    let isOnline: Bool?
}

// MARK: - Gyms

struct GymDTO: Decodable {
    let id: String
    let name: String
    let street: String
    let houseNumber: String
    let plz: String
    let city: String
    let label: String
}

struct GymSuggestRequestDTO: Encodable {
    let name: String
    let street: String
    let houseNumber: String
    let plz: String
    let city: String?
}

// MARK: - Sicherheit

struct ReportRequestDTO: Encodable {
    let reportedUserId: String
    let reason: String
}

/// Empfangsbestätigung einer Meldung (Art. 16 Abs. 4 DSA).
struct ReportAckDTO: Decodable {
    let reference: String
    let createdAt: String?
    let message: String
}

/// Eigene Meldung samt Entscheidung (Art. 16 Abs. 5 DSA).
struct MyReportDTO: Decodable {
    let reference: String
    let reason: String
    let createdAt: String?
    // nil = noch in Prüfung
    let outcome: String?
    let decisionNote: String?
    let decidedAt: String?
}

/// Begründete Mitteilung zu einer laufenden Maßnahme (Art. 17 DSA).
struct ModerationNoticeDTO: Decodable {
    let action: String?
    let reason: String
    let actionAt: String?
    let mutedUntil: String?
    let appealHint: String
}

struct BlockRequestDTO: Encodable {
    let userId: String
}

// MARK: - Foto-Verifizierung

struct VerificationStatusDTO: Decodable {
    let status: String
    let prompts: [String]?
}

struct VerificationSelfieDTO: Encodable {
    let prompt: String
    let objectKey: String
}

struct VerificationSubmitRequestDTO: Encodable {
    let selfies: [VerificationSelfieDTO]
}

// MARK: - PLZ-Lookup (OpenPLZ API, openplzapi.org)

struct OpenPlzLocalityDTO: Decodable {
    let name: String?
    let postalCode: String?
    let municipality: OpenPlzMunicipalityDTO?
}

struct OpenPlzMunicipalityDTO: Decodable {
    let name: String?
}
