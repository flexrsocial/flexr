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
          "unread_count": 3, "is_online": true
        }
        """
        let match = try decoder.decode(MatchDTO.self, from: Data(json.utf8)).toDomain()

        XCTAssertEqual(match.matchID, "m1")
        XCTAssertEqual(match.unreadCount, 3)
        XCTAssertTrue(match.isOnline)
        XCTAssertEqual(match.lastMessage?.senderID, "u2")
        XCTAssertTrue(match.lastMessage?.wasCensored == true)
        XCTAssertNil(match.lastMessage?.readAt)
        XCTAssertEqual(match.lastMessage?.createdAt, ServerTime.parse("2026-07-26T20:30:00"))
        XCTAssertEqual(match.profile.gender, .frau)
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
