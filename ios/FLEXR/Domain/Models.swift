import Foundation

enum PhotoStatus: String, Codable, Sendable {
    case pending, approved, rejected

    init(raw: String?) {
        switch raw?.lowercased() {
        case "approved": self = .approved
        case "rejected": self = .rejected
        default: self = .pending
        }
    }
}

enum Gender: String, CaseIterable, Codable, Sendable {
    case mann, frau

    var apiValue: String { rawValue }

    var label: String {
        switch self {
        case .mann: "Mann"
        case .frau: "Frau"
        }
    }

    init(raw: String?) {
        self = raw?.lowercased() == "frau" ? .frau : .mann
    }
}

struct Photo: Identifiable, Hashable, Sendable {
    let id: String
    let url: String
    let thumbURL: String?
    let position: Int
    let status: PhotoStatus

    /// Für kleine Avatare: Thumbnail bevorzugen, sonst Vollbild (Bestandsfotos).
    var avatarURL: String { thumbURL ?? url }
}

struct Profile: Identifiable, Hashable, Sendable {
    let id: String
    let name: String
    let age: Int
    let city: String
    let gender: Gender
    let gym: String
    let bio: String?
    let isOnline: Bool
    let isVerified: Bool
    let distanceKm: Int?
    let photos: [Photo]

    /// Gym wird als volles Label „Name — Straße 1, 1100 Wien" gespeichert.
    var gymName: String {
        gym.components(separatedBy: " — ").first ?? gym
    }

    var primaryPhoto: Photo? { photos.first }
}

struct MyProfile: Hashable, Sendable {
    let profile: Profile
    let plz: String
    let birthdate: Date?
    let searchRadiusKm: Int
    let messagingMutedUntil: Date?

    var id: String { profile.id }
    var name: String { profile.name }
    var photos: [Photo] { profile.photos }

    /// Aktive Chat-Sperre („Abmahnung"), sonst nil.
    func activeMuteUntil(now: Date = Date()) -> Date? {
        guard let messagingMutedUntil, messagingMutedUntil > now else { return nil }
        return messagingMutedUntil
    }
}

struct Membership: Hashable, Sendable {
    let isSubscribed: Bool
    let trialEndsAt: Date
    let isActive: Bool
}

struct Message: Identifiable, Hashable, Sendable {
    let id: String
    let matchID: String
    let senderID: String
    let content: String
    let createdAt: Date
    let readAt: Date?
    let wasCensored: Bool
}

struct MatchSummary: Identifiable, Hashable, Sendable {
    let matchID: String
    let profile: Profile
    let lastMessage: Message?
    let unreadCount: Int
    let isOnline: Bool
    /// Bleibt nach „Chatverlauf leeren" true (der Chat bleibt gelistet, nur
    /// leer) und wird erst durch „Chat löschen" false, bis erneut eine
    /// Nachricht eintrifft.
    var inChats: Bool = false

    var id: String { matchID }
}

struct Gym: Identifiable, Hashable, Sendable {
    let id: String
    let name: String
    let street: String
    let houseNumber: String
    let plz: String
    let city: String
    let label: String

    var addressLine: String {
        [
            "\(street) \(houseNumber)".trimmingCharacters(in: .whitespaces),
            "\(plz) \(city)".trimmingCharacters(in: .whitespaces),
        ]
        .filter { !$0.isEmpty }
        .joined(separator: ", ")
    }
}

/// Stand der Alters- und Identitätsprüfung.
///
/// `idRequired` und `reuploadRequired` gehören zum Ausweisschritt, den diese App
/// noch nicht selbst anbietet — siehe VerificationHint in AccountView.swift.
enum VerificationStatus: String, Sendable {
    case none, inProgress, idRequired, reuploadRequired, submitted, approved, rejected

    init(raw: String?) {
        switch raw?.lowercased() {
        case "in_progress": self = .inProgress
        case "id_required": self = .idRequired
        case "reupload_required": self = .reuploadRequired
        case "submitted": self = .submitted
        case "approved": self = .approved
        case "rejected": self = .rejected
        default: self = .none
        }
    }

    /// Der Ausweisschritt steht noch aus.
    var needsDocument: Bool { self == .idRequired || self == .reuploadRequired }
}

struct VerificationState: Sendable {
    let status: VerificationStatus
    let prompts: [String]
}

/// Ergebnis eines Swipes.
struct SwipeOutcome: Sendable {
    let matched: Bool
}

/// Bestätigung einer abgegebenen Meldung. Das Aktenzeichen macht sie für den
/// Melder nachverfolgbar (Art. 16 Abs. 4 DSA).
struct ReportAck: Sendable {
    let reference: String
    let message: String
}

/// Begründete Mitteilung zu einer Beschränkung des eigenen Kontos (Art. 17 DSA)
/// — Grund, Dauer und der Weg zum Widerspruch.
struct ModerationNotice: Sendable {
    let reason: String
    let mutedUntil: Date?
    let appealHint: String
}

/// Blockierte Person für die Verwaltungsliste im Konto. Bewusst nur Name,
/// Alter und Vorschaubild — kein Bio/Gym/Entfernung, siehe
/// `backend/app/schemas.py::BlockedUserOut`.
struct BlockedUser: Identifiable, Sendable {
    let userId: String
    let name: String
    let age: Int?
    let photoUrl: String?
    let blockedAt: Date?

    var id: String { userId }
}
