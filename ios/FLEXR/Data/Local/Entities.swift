import Foundation
import SwiftData

/// Fotoeintrag, wie er am Match hängt. SwiftData speichert ihn als JSON-Blob —
/// eine eigene Tabelle wäre für eine reine Cache-Kopie unnötiger Aufwand.
struct StoredPhoto: Codable, Hashable {
    var id: String
    var url: String
    var thumbURL: String?
    var position: Int
    var status: String

    init(_ photo: Photo) {
        id = photo.id
        url = photo.url
        thumbURL = photo.thumbURL
        position = photo.position
        status = photo.status.rawValue
    }

    func toDomain() -> Photo {
        Photo(id: id, url: url, thumbURL: thumbURL, position: position, status: PhotoStatus(raw: status))
    }
}

/// Lokaler Spiegel der Match-Liste.
///
/// Dient als Single Source of Truth für die Oberfläche: Matches und Chats sind
/// sofort sichtbar, auch ohne Netz, und werden im Hintergrund aufgefrischt.
@Model
final class MatchEntity {

    @Attribute(.unique) var matchID: String
    var profileID: String
    var name: String
    var age: Int
    var city: String
    var gender: String
    var gym: String
    var bio: String?
    var isVerified: Bool
    var isOnline: Bool
    var distanceKm: Int?
    var photosJSON: Data
    var unreadCount: Int
    var lastMessageID: String?
    var lastMessageContent: String?
    var lastMessageSenderID: String?
    var lastMessageAt: Date?
    /// Sortierschlüssel: zuletzt geschriebene Unterhaltung zuerst, Matches ohne
    /// Nachricht nach ihrem Match-Zeitpunkt — wie im Backend.
    var sortedAt: Date
    /// Filter des „Chats"-Tabs. Mit Vorgabewert, damit SwiftData das Feld einer
    /// bereits angelegten Datei leichtgewichtig ergänzen kann statt die Datei
    /// zu verwerfen (siehe FlexrStore).
    var inChats: Bool = false

    init(
        matchID: String,
        profileID: String,
        name: String,
        age: Int,
        city: String,
        gender: String,
        gym: String,
        bio: String?,
        isVerified: Bool,
        isOnline: Bool,
        distanceKm: Int?,
        photosJSON: Data,
        unreadCount: Int,
        lastMessageID: String?,
        lastMessageContent: String?,
        lastMessageSenderID: String?,
        lastMessageAt: Date?,
        sortedAt: Date,
        inChats: Bool
    ) {
        self.matchID = matchID
        self.profileID = profileID
        self.name = name
        self.age = age
        self.city = city
        self.gender = gender
        self.gym = gym
        self.bio = bio
        self.isVerified = isVerified
        self.isOnline = isOnline
        self.distanceKm = distanceKm
        self.photosJSON = photosJSON
        self.unreadCount = unreadCount
        self.lastMessageID = lastMessageID
        self.lastMessageContent = lastMessageContent
        self.lastMessageSenderID = lastMessageSenderID
        self.lastMessageAt = lastMessageAt
        self.sortedAt = sortedAt
        self.inChats = inChats
    }
}

@Model
final class MessageEntity {

    @Attribute(.unique) var messageID: String
    var matchID: String
    var senderID: String
    var content: String
    var createdAt: Date
    var readAt: Date?
    var wasCensored: Bool
    /// true, solange die Nachricht nur lokal existiert (optimistisch gesendet).
    var isPending: Bool

    init(
        messageID: String,
        matchID: String,
        senderID: String,
        content: String,
        createdAt: Date,
        readAt: Date?,
        wasCensored: Bool,
        isPending: Bool = false
    ) {
        self.messageID = messageID
        self.matchID = matchID
        self.senderID = senderID
        self.content = content
        self.createdAt = createdAt
        self.readAt = readAt
        self.wasCensored = wasCensored
        self.isPending = isPending
    }
}

// MARK: - Mapping Entity <-> Domäne

extension MatchEntity {

    var photos: [StoredPhoto] {
        (try? JSONDecoder().decode([StoredPhoto].self, from: photosJSON)) ?? []
    }

    func toDomain() -> MatchSummary {
        MatchSummary(
            matchID: matchID,
            profile: Profile(
                id: profileID,
                name: name,
                age: age,
                city: city,
                gender: Gender(raw: gender),
                gym: gym,
                bio: bio,
                isOnline: isOnline,
                isVerified: isVerified,
                distanceKm: distanceKm,
                photos: photos.map { $0.toDomain() }
            ),
            lastMessage: lastMessageID.map { id in
                Message(
                    id: id,
                    matchID: matchID,
                    senderID: lastMessageSenderID ?? "",
                    content: lastMessageContent ?? "",
                    createdAt: lastMessageAt ?? sortedAt,
                    readAt: nil,
                    wasCensored: false
                )
            },
            unreadCount: unreadCount,
            isOnline: isOnline,
            inChats: inChats
        )
    }

    /// Serverstand in einen bestehenden Datensatz übernehmen.
    func apply(_ summary: MatchSummary, matchedAt: Date = Date()) {
        profileID = summary.profile.id
        name = summary.profile.name
        age = summary.profile.age
        city = summary.profile.city
        gender = summary.profile.gender.apiValue
        gym = summary.profile.gym
        bio = summary.profile.bio
        isVerified = summary.profile.isVerified
        isOnline = summary.isOnline
        distanceKm = summary.profile.distanceKm
        photosJSON = MatchEntity.encode(summary.profile.photos)
        unreadCount = summary.unreadCount
        lastMessageID = summary.lastMessage?.id
        lastMessageContent = summary.lastMessage?.content
        lastMessageSenderID = summary.lastMessage?.senderID
        lastMessageAt = summary.lastMessage?.createdAt
        sortedAt = summary.lastMessage?.createdAt ?? matchedAt
        inChats = summary.inChats
    }

    static func make(_ summary: MatchSummary, matchedAt: Date = Date()) -> MatchEntity {
        MatchEntity(
            matchID: summary.matchID,
            profileID: summary.profile.id,
            name: summary.profile.name,
            age: summary.profile.age,
            city: summary.profile.city,
            gender: summary.profile.gender.apiValue,
            gym: summary.profile.gym,
            bio: summary.profile.bio,
            isVerified: summary.profile.isVerified,
            isOnline: summary.isOnline,
            distanceKm: summary.profile.distanceKm,
            photosJSON: encode(summary.profile.photos),
            unreadCount: summary.unreadCount,
            lastMessageID: summary.lastMessage?.id,
            lastMessageContent: summary.lastMessage?.content,
            lastMessageSenderID: summary.lastMessage?.senderID,
            lastMessageAt: summary.lastMessage?.createdAt,
            sortedAt: summary.lastMessage?.createdAt ?? matchedAt,
            inChats: summary.inChats
        )
    }

    static func encode(_ photos: [Photo]) -> Data {
        (try? JSONEncoder().encode(photos.map(StoredPhoto.init))) ?? Data("[]".utf8)
    }
}

extension MessageEntity {

    func toDomain() -> Message {
        Message(
            id: messageID,
            matchID: matchID,
            senderID: senderID,
            content: content,
            createdAt: createdAt,
            readAt: readAt,
            wasCensored: wasCensored
        )
    }

    static func make(_ message: Message, isPending: Bool = false) -> MessageEntity {
        MessageEntity(
            messageID: message.id,
            matchID: message.matchID,
            senderID: message.senderID,
            content: message.content,
            createdAt: message.createdAt,
            readAt: message.readAt,
            wasCensored: message.wasCensored,
            isPending: isPending
        )
    }
}
