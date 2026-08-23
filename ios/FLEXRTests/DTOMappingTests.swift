import XCTest

@testable import FLEXR

/// Der Backend-Vertrag steht in snake_case, die DTOs in camelCase; übersetzt
/// wird über `convertFromSnakeCase`/`convertToSnakeCase` statt über eine
/// Schlüsselzuordnung von Hand (Android: `@SerialName`).
///
/// Genau das prüft dieser Test: Fällt ein Feldname aus dem Muster, bleibt es
/// sonst bis zur Laufzeit unbemerkt und das Feld ist still leer.
final class DTOMappingTests: XCTestCase {

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.outputFormatting = .sortedKeys
        return encoder
    }()

    func testMyProfileWirdVollstaendigGelesen() throws {
        let json = """
        {
          "id": "u1", "name": "Max", "age": 30, "city": "Wien", "gender": "mann",
          "gym": "Eisenschmiede — Hauptstraße 1, 1100 Wien", "bio": "Beintag",
          "is_online": true, "is_verified": true, "distance_km": 7,
          "photos": [
            {"id": "p2", "url": "https://r2/2", "thumb_url": "https://r2/2t", "position": 1,
             "status": "pending"},
            {"id": "p1", "url": "https://r2/1", "thumb_url": "https://r2/1t", "position": 0,
             "status": "approved"}
          ],
          "plz": "1100", "birthdate": "1996-07-26", "search_radius_km": 25,
          "messaging_muted_until": "2026-08-01T10:00:00"
        }
        """
        let profile = try decoder.decode(MyProfileDTO.self, from: Data(json.utf8)).toDomain()

        XCTAssertEqual(profile.id, "u1")
        XCTAssertEqual(profile.plz, "1100")
        XCTAssertEqual(profile.searchRadiusKm, 25)
        XCTAssertEqual(profile.profile.distanceKm, 7)
        XCTAssertTrue(profile.profile.isVerified)
        XCTAssertEqual(profile.birthdate, ServerTime.parseDate("1996-07-26"))
        XCTAssertEqual(profile.messagingMutedUntil, ServerTime.parse("2026-08-01T10:00:00"))
        // Fotos kommen nach position sortiert an, nicht in Antwortreihenfolge.
        XCTAssertEqual(profile.photos.map(\.id), ["p1", "p2"])
        XCTAssertEqual(profile.photos[0].status, .approved)
        XCTAssertEqual(profile.photos[1].status, .pending)
        XCTAssertEqual(profile.photos[0].avatarURL, "https://r2/1t")
        // Gespeichert ist das volle Label, angezeigt wird nur der Name.
        XCTAssertEqual(profile.profile.gymName, "Eisenschmiede")
    }

    func testFotoOhneThumbnailFaelltAufsVollbildZurueck() throws {
        let json = #"{"id":"p1","url":"https://r2/1"}"#
        let photo = try decoder.decode(PhotoDTO.self, from: Data(json.utf8)).toDomain()
        XCTAssertEqual(photo.avatarURL, "https://r2/1")
        XCTAssertEqual(photo.status, .pending)
        XCTAssertEqual(photo.position, 0)
    }

    func testMatchMitLetzterNachricht() throws {
        let json = """
        {
          "match_id": "m1",
          "profile": {"id": "u2", "name": "Lea", "age": 28, "city": "Graz", "gender": "frau",
                      "gym": "Studio — Weg 2, 8010 Graz"},
          "last_message": {"id": "n1", "match_id": "m1", "sender_id": "u2",
                           "content": "Hi", "created_at": "2026-07-26T20:30:00",
                           "read_at": null, "was_censored": true},
          "unread_count": 3, "is_online": true, "in_chats": true
        }
        """
        let match = try decoder.decode(MatchDTO.self, from: Data(json.utf8)).toDomain()

        XCTAssertEqual(match.matchID, "m1")
        XCTAssertEqual(match.unreadCount, 3)
        XCTAssertTrue(match.isOnline)
        XCTAssertTrue(match.inChats)
        XCTAssertEqual(match.lastMessage?.senderID, "u2")
        XCTAssertTrue(match.lastMessage?.wasCensored == true)
        XCTAssertNil(match.lastMessage?.readAt)
        XCTAssertEqual(match.lastMessage?.createdAt, ServerTime.parse("2026-07-26T20:30:00"))
        XCTAssertEqual(match.profile.gender, .frau)
    }

    /// Nach „Chatverlauf leeren" liefert der Server `last_message: null`, aber
    /// `in_chats: true` — der Chat bleibt gelistet, nur eben leer. Genau daran
    /// hing der Bug, der den Chat in allen Clients aus der Liste warf.
    func testGeleerterChatBleibtInDerChatliste() throws {
        let json = """
        {
          "match_id": "m2",
          "profile": {"id": "u3", "name": "Nina", "age": 27, "city": "Linz", "gender": "frau",
                      "gym": "Studio — Weg 3, 4020 Linz"},
          "last_message": null, "unread_count": 0, "is_online": false, "in_chats": true
        }
        """
        let match = try decoder.decode(MatchDTO.self, from: Data(json.utf8)).toDomain()
        XCTAssertNil(match.lastMessage)
        XCTAssertTrue(match.inChats)
    }

    /// Ältere Antworten ohne das Feld: dann entscheidet wie früher die letzte
    /// Nachricht, damit die Chatliste nicht schlagartig leer ist.
    func testFehlendesInChatsFaelltAufLetzteNachrichtZurueck() throws {
        let json = """
        {
          "match_id": "m3",
          "profile": {"id": "u4", "name": "Ida", "age": 31, "city": "Wien", "gender": "frau",
                      "gym": "Studio — Weg 4, 1100 Wien"},
          "last_message": null, "unread_count": 0, "is_online": false
        }
        """
        XCTAssertFalse(try decoder.decode(MatchDTO.self, from: Data(json.utf8)).toDomain().inChats)
    }

    func testEinwilligungsEintragWirdGelesen() throws {
        let json = """
        [
          {"consent_type": "sensitive_data", "version": "2026-08-03",
           "granted_at": "2026-08-03T09:00:00", "revoked_at": null, "active": true},
          {"consent_type": "verification_media", "version": "2026-08-03",
           "granted_at": "2026-08-01T09:00:00", "revoked_at": "2026-08-20T18:00:00",
           "active": false}
        ]
        """
        let consents = try decoder.decode([ConsentDTO].self, from: Data(json.utf8))
        XCTAssertEqual(consents.count, 2)
        XCTAssertEqual(consents[0].consentType, "sensitive_data")
        XCTAssertEqual(consents[0].version, "2026-08-03")
        XCTAssertTrue(consents[0].active)
        XCTAssertNil(consents[0].revokedAt)
        XCTAssertFalse(consents[1].active)
        XCTAssertEqual(consents[1].revokedAt, "2026-08-20T18:00:00")
    }

    func testWiderrufsAntwortTraegtDieFolge() throws {
        let json = """
        {"revoked": true, "consent_type": "sensitive_data",
         "consequence": "Du erscheinst in keinem Deck mehr."}
        """
        let antwort = try decoder.decode(ConsentRevokeResponseDTO.self, from: Data(json.utf8))
        XCTAssertTrue(antwort.revoked)
        XCTAssertEqual(antwort.consentType, "sensitive_data")
        XCTAssertEqual(antwort.consequence, "Du erscheinst in keinem Deck mehr.")
    }

    func testAnfragenGehenInSnakeCaseRaus() throws {
        let swipe = try encoder.encode(SwipeRequestDTO(toUserId: "u2", action: "like"))
        XCTAssertEqual(String(decoding: swipe, as: UTF8.self), #"{"action":"like","to_user_id":"u2"}"#)

        let photo = try encoder.encode(
            AddPhotoRequestDTO(objectKey: "k", thumbObjectKey: "t")
        )
        XCTAssertEqual(
            String(decoding: photo, as: UTF8.self),
            #"{"object_key":"k","thumb_object_key":"t"}"#
        )

        let report = try encoder.encode(ReportRequestDTO(reportedUserId: "u2", reason: "Spam"))
        XCTAssertEqual(
            String(decoding: report, as: UTF8.self),
            #"{"reason":"Spam","reported_user_id":"u2"}"#
        )

        // Ohne genau diese beiden Felder antwortet /api/billing/checkout mit 422.
        let checkout = try encoder.encode(
            CheckoutRequestDTO(immediateStart: true, withdrawalAck: true)
        )
        XCTAssertEqual(
            String(decoding: checkout, as: UTF8.self),
            #"{"immediate_start":true,"withdrawal_ack":true}"#
        )

        let widerruf = try encoder.encode(
            ConsentRevokeRequestDTO(consentType: "sensitive_data")
        )
        XCTAssertEqual(
            String(decoding: widerruf, as: UTF8.self),
            #"{"consent_type":"sensitive_data"}"#
        )
    }

    /// `UpdateProfileRequestDTO` schickt nur gesetzte Felder — ein `nil` würde
    /// serverseitig sonst als „Wert löschen" ankommen.
    func testNichtGesetzteFelderWerdenNichtMitgeschickt() throws {
        let body = try encoder.encode(UpdateProfileRequestDTO(bio: "neu"))
        XCTAssertEqual(String(decoding: body, as: UTF8.self), #"{"bio":"neu"}"#)
    }

    func testPlzLookupAntwortWirdGelesen() throws {
        let json = #"{"plz":"1100","city":"Wien"}"#
        let lookup = try decoder.decode(PlzLookupDTO.self, from: Data(json.utf8))
        XCTAssertEqual(lookup.plz, "1100")
        XCTAssertEqual(lookup.city, "Wien")
    }

    func testUnbekannteZustaendeFallenAufDenSicherenWertZurueck() {
        XCTAssertEqual(PhotoStatus(raw: "irgendwas"), .pending)
        XCTAssertEqual(Gender(raw: nil), .mann)
        XCTAssertEqual(VerificationStatus(raw: "in_progress"), .inProgress)
        // Schritte der Alters- und Identitätsprüfung
        XCTAssertEqual(VerificationStatus(raw: "id_required"), .idRequired)
        XCTAssertEqual(VerificationStatus(raw: "reupload_required"), .reuploadRequired)
        XCTAssertTrue(VerificationStatus(raw: "id_required").needsDocument)
        XCTAssertFalse(VerificationStatus(raw: "submitted").needsDocument)
        XCTAssertEqual(VerificationStatus(raw: "irgendwas"), .none)
    }
}
