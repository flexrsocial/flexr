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
    // phone/phone_verified liefert das Backend zwar mit, die App nutzt sie
    // nicht — die Telefonprüfung ist auch im Web verworfen worden.
    let messagingMutedUntil: String?
    // Schalterstellung unter "Benachrichtigungen". Optional mit Vorgabe "an":
    // ein aelteres Backend ohne diese Felder soll nicht so aussehen, als haette
    // der Nutzer alles abgeschaltet.
    let notifyMatchEmail: Bool?
    let notifyMatchPush: Bool?
    let notifyQueueEmail: Bool?
    let notifyQueuePush: Bool?
    let notifyInactiveEmail: Bool?
    let notifyInactivePush: Bool?
}

/// Einzelner Schalter - nur das geaenderte Feld wird geschickt, die uebrigen
/// bleiben nil und damit unangetastet.
struct NotificationSettingsRequestDTO: Encodable {
    var notifyMatchEmail: Bool?
    var notifyMatchPush: Bool?
    var notifyQueueEmail: Bool?
    var notifyQueuePush: Bool?
    var notifyInactiveEmail: Bool?
    var notifyInactivePush: Bool?
}

/// Neue Reihenfolge der eigenen Fotos (Drag & Drop im Profil).
struct ReorderPhotosRequestDTO: Encodable {
    let photoIds: [String]
}

/// Eine vom Server bereitgelegte, noch nicht angezeigte Benachrichtigung.
struct PushNotificationDTO: Decodable {
    let id: String
    let topic: String
    let title: String
    let body: String
    let target: String?
}

struct MarkDeliveredRequestDTO: Encodable {
    let ids: [String]
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

// MARK: - Einwilligungen (Art. 7 Abs. 3 DSGVO)

/// Ein Eintrag des Einwilligungs-Ledgers (`GET /api/profiles/me/consents`).
/// Der Server liefert die volle Historie, neueste zuerst — angezeigt wird nur
/// die jeweils neueste Zeile je Art (siehe ConsentSection in AccountView).
struct ConsentDTO: Decodable, Equatable {
    let consentType: String
    let version: String
    let grantedAt: String
    let revokedAt: String?
    let active: Bool
}

struct ConsentRevokeRequestDTO: Encodable {
    let consentType: String
}

struct ConsentRevokeResponseDTO: Decodable {
    let revoked: Bool
    let consentType: String
    let consequence: String
}

struct ConsentGrantRequestDTO: Encodable {
    let consentType: String
}

struct ConsentGrantResponseDTO: Decodable {
    let granted: Bool
    let consentType: String
    let consequence: String
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

/// Die beiden getrennten, nicht vorangekreuzten Erklärungen vor dem Wechsel
/// zur Stripe-Seite (§ 10 und § 18 Abs. 1 Z 1 FAGG). Das Backend lehnt `false`
/// oder ein fehlendes Feld mit 422 ab — ein leerer Aufruf reicht seit dem
/// 17.08.2026 nicht mehr (`CheckoutRequest` in `backend/app/schemas.py`).
struct CheckoutRequestDTO: Encodable {
    let immediateStart: Bool
    let withdrawalAck: Bool
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
    /// Ob das Match unter „Chats" erscheint. Bleibt nach „Chatverlauf leeren"
    /// `true` (der Chat bleibt gelistet, nur ohne `lastMessage`) und wird erst
    /// durch „Chat löschen" `false`, bis erneut eine Nachricht eintrifft.
    let inChats: Bool?
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

/// Blockierte Person für die Verwaltungsliste im Konto — entspricht
/// `backend/app/schemas.py::BlockedUserOut`. Bewusst nur das Nötigste zum
/// Wiedererkennen, kein Bio/Gym/Entfernung (siehe dortiger Docstring).
struct BlockedUserOutDTO: Decodable {
    let userId: String
    let name: String
    let age: Int?
    let photoUrl: String?
    let blockedAt: String?
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

// MARK: - PLZ-Lookup (eigenes Backend, GET /api/geo/plz/{plz})

struct PlzLookupDTO: Decodable {
    let plz: String
    let city: String
}
