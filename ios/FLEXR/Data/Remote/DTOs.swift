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
    /// Sprache, in der gerade registriert wird ("de" oder "en").
    ///
    /// Der Server merkt sie am Profil und schreibt seine Mails danach — sie
    /// entstehen zum Teil ohne die App (Inaktivitäts-Erinnerung aus dem
    /// Tagesjob, Zahlungsmail aus einem Stripe-Webhook, Moderationsmitteilung
    /// aus dem Admin-Bereich) und können die Einstellung nirgends sonst
    /// nachlesen.
    let language: String?
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
    /// Premium-Abzeichen neben dem Namen. Während der Beta trägt es niemand —
    /// der Server liefert es nur, solange Premium scharf geschaltet ist.
    let isPremium: Bool?
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
    let isPremium: Bool?
    let distanceKm: Int?
    let photos: [PhotoDTO]?
    let plz: String
    let birthdate: String
    let searchRadiusKm: Int?
    /// Nur in der eigenen Ansicht — der Nutzer muss sehen, an welche Adresse
    /// die Bestätigungsmail ging.
    let email: String?
    let emailVerified: Bool?
    // Alters- und Identitätsprüfung. Optional mit Vorgaben, die ein älteres
    // Backend ohne diese Felder zu einem nutzbaren Konto machen.
    let verificationRequired: Bool?
    let isAccountActivated: Bool?
    let ageVerified: Bool?
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
    let notifyPendingLikesEmail: Bool?
    let notifyPendingLikesPush: Bool?
    /// Am Profil hinterlegte Sprache. Optional: ein älteres Backend liefert
    /// sie nicht, dann gilt die Ausgangssprache.
    let language: String?
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
    var notifyPendingLikesEmail: Bool?
    var notifyPendingLikesPush: Bool?
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
    let createdAt: String?
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
    /// Kein Profilfeld im engeren Sinn, sondern die Sprache, in der der Server
    /// diesem Nutzer schreibt. Wird allein geschickt, sobald jemand den Regler
    /// bedient — die übrigen Felder bleiben nil und damit unangetastet.
    var language: String?
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

/// Antwort von `GET /api/billing/status`.
///
/// Seit dem 10.09.2026 ist die Nutzung von FLEXR dauerhaft kostenlos; bezahlt
/// wird nur das freiwillige Zusatzpaket FLEXR Premium. Alle Zahlen — Preis,
/// Grenzen, Restkontingente — kommen fertig vom Server, damit Web, Android und
/// iOS nicht dreimal dieselbe Formel treffen müssen.
///
/// **Jedes Feld ist optional.** Ein Server, der eines noch nicht liefert, darf
/// die App nicht am Dekodieren hindern — genau daran wäre eine ältere Fassung
/// gescheitert, hätten wir die Altfelder unten einfach entfernt.
struct MembershipStatusDTO: Decodable {
    let isPremium: Bool?
    let premiumEnabled: Bool?
    let limitsActive: Bool?
    let checkoutAvailable: Bool?
    /// Darf diese App über StoreKit kaufen? Das Gegenstück zu
    /// `checkoutAvailable` - genau einer von beiden ist wahr, nie beide.
    let storePurchaseAvailable: Bool?
    /// Produktkennung im App Store. Preis und Text kommen von dort.
    let storeProductId: String?
    let betaActive: Bool?
    let hasStripeSubscription: Bool?
    let priceCents: Int?
    let currency: String?
    let freeDailyLikes: Int?
    let freeOpenChats: Int?
    let freeMaxRadiusKm: Int?
    let maxRadiusKm: Int?
    /// nil = unbegrenzt (Beta oder Premium).
    let likesRemaining: Int?
    let openChatsRemaining: Int?
    let nextLikeAt: String?

    // Altfelder, vom Server nur noch für Clients vor 2.6.0 geliefert. Diese
    // Fassung wertet sie nicht mehr aus.
    let isSubscribed: Bool?
    let trialEndsAt: String?
    let isActive: Bool?
    let billingEnabled: Bool?
}

/// Die beiden getrennten, nicht vorangekreuzten Erklärungen vor dem Wechsel
/// zur Stripe-Seite (§ 10 und § 18 Abs. 1 Z 1 FAGG). Das Backend lehnt `false`
/// oder ein fehlendes Feld mit 422 ab — ein leerer Aufruf reicht seit dem
/// 17.08.2026 nicht mehr (`CheckoutRequest` in `backend/app/schemas.py`).
/// Gerätetoken für echte Push-Zustellung. Der Token **ist** der Schalter:
/// Wer sich abmeldet, meldet ihn ab, und der Server hat dann niemanden, dem er
/// zustellen könnte.
struct PushTokenRequestDTO: Encodable {
    let platform: String
    let token: String
}

/// Eine signierte StoreKit-Transaktion, wie die App sie von Apple erhält.
///
/// Absichtlich nur dieses eine Feld: Alles andere — Produkt, Ablauf, Umgebung —
/// steht signiert *im* Beleg. Schickte der Client es daneben mit, wäre die
/// nächstliegende Frage, welchem von beiden der Server glaubt; die Antwort kann
/// nur „dem Beleg" lauten, also gibt es das andere gar nicht erst.
struct AppleTransactionRequestDTO: Encodable {
    let signedTransaction: String
}

/// Was nach dem Einreichen gilt. Der Client zeichnet daraufhin sofort neu.
struct StorePurchaseResultDTO: Decodable {
    let isPremium: Bool?
    let premiumUntil: String?
}

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
    /// nil = unbegrenzt (Beta oder Premium). Spart nach jedem Like den
    /// zusätzlichen Aufruf von `/api/billing/status`.
    let likesRemaining: Int?
}

/// Antwort von `GET /api/swipes/incoming`.
struct IncomingLikesDTO: Decodable {
    let count: Int?
    /// Ohne Premium liefert der Server die Zahl, aber keine Profile.
    let profiles: [ProfileDTO]?
    let premiumRequired: Bool?
}

/// Antwort von `POST /api/swipes/rewind`.
struct RewindResultDTO: Decodable {
    let toUserId: String
    let likesRemaining: Int?
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
    /// Was als Nächstes zu tun ist: selfie | document | wait | none.
    let nextStep: String?
    /// Sachlicher Grund aus dem festen Katalog, wenn etwas nachzuholen ist.
    let reason: String?
    let verificationRequired: Bool?
    let accountActivated: Bool?
    let emailVerified: Bool?
    let documentTypes: [VerificationDocumentTypeDTO]?
}

struct VerificationDocumentTypeDTO: Decodable {
    let value: String
    let label: String
    let needsBack: Bool?
}

struct VerificationDocumentPresignRequestDTO: Encodable {
    let contentType: String
    let byteSize: Int
}

struct VerificationDocumentSubmitRequestDTO: Encodable {
    let documentType: String
    let frontObjectKey: String
    let backObjectKey: String?
}

// MARK: - E-Mail-Bestätigung

struct EmailResendResponseDTO: Decodable {
    let email: String
    let validHours: Int?
}

struct EmailConfirmRequestDTO: Encodable {
    let token: String
}

struct EmailConfirmResponseDTO: Decodable {
    let email: String
    let name: String
    let confirmed: Bool?
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
