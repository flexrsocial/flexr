import XCTest

@testable import FLEXR

/// Eigenes Bild und Löschbarkeit der Fotos (seit 22.09.2026 vom Server,
/// `MyProfileOut.avatar_url` / `deletable`) - und der Rückfall, wenn ein
/// älteres Backend die Felder noch nicht liefert.
///
/// Anlass: `photos.first` war das eigene Bild, auch wenn genau dieses Foto
/// abgelehnt und seine Datei längst gelöscht war; abgelehnte Fotos zählten
/// zur Mindestanzahl und ließen sich nicht entfernen.
final class FotoRegelnTests: XCTestCase {

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

    private func profil(photos: String, extra: String = "") throws -> MyProfile {
        let json = """
        {
          "id": "u1", "name": "Anna", "age": 31, "city": "Wien", "gender": "frau",
          "gym": "John Harris Fitness", "plz": "1070", "birthdate": "1995-04-12",
          "photos": [\(photos)]\(extra)
        }
        """
        return try decoder.decode(MyProfileDTO.self, from: Data(json.utf8)).toDomain()
    }

    private let abgelehntZuerst = """
        {"id": "p1", "url": "https://r2/1", "thumb_url": "https://r2/1t", "position": 0, "status": "rejected"},
        {"id": "p2", "url": "https://r2/2", "thumb_url": "https://r2/2t", "position": 1, "status": "approved"},
        {"id": "p3", "url": "https://r2/3", "position": 2, "status": "approved"}
        """

    func testServerwerteHabenVorrang() throws {
        let p = try profil(
            photos: """
            {"id": "p1", "url": "https://r2/1", "position": 0, "status": "rejected", "deletable": true},
            {"id": "p2", "url": "https://r2/2", "position": 1, "status": "approved", "deletable": false}
            """,
            extra: #", "avatar_url": "https://server/avatar", "min_photos": 3, "max_photos": 6"#
        )
        XCTAssertEqual(p.ownAvatarURL, "https://server/avatar")
        XCTAssertEqual(p.photos[0].deletable, true)
        XCTAssertEqual(p.photos[1].deletable, false)
    }

    func testRueckfallUeberspringtAbgelehnteFotos() throws {
        let p = try profil(photos: abgelehntZuerst)
        XCTAssertNil(p.serverAvatarURL)
        XCTAssertEqual(p.ownAvatarURL, "https://r2/2t")
        XCTAssertEqual(p.validPhotoCount, 2)
        XCTAssertNil(p.photos[0].deletable)
    }

    func testOhneFreigegebeneFotosZaehltEinWartendes() throws {
        let p = try profil(photos: """
            {"id": "p1", "url": "https://r2/1", "position": 0, "status": "rejected"},
            {"id": "p2", "url": "https://r2/2", "position": 1, "status": "pending"}
            """)
        XCTAssertEqual(p.ownAvatarURL, "https://r2/2")
    }

    func testNurAbgelehnteFotosErgebenKeinBild() throws {
        let p = try profil(photos: """
            {"id": "p1", "url": "https://r2/1", "position": 0, "status": "rejected"}
            """)
        XCTAssertNil(p.ownAvatarURL)
        XCTAssertEqual(p.validPhotoCount, 0)
    }

    // MARK: - Zugangsdaten (Passwort ändern, E-Mail ändern, Passwort vergessen)

    func testZugangsdatenDTOsInSnakeCase() throws {
        let pw = String(decoding: try encoder.encode(
            PasswordChangeRequestDTO(currentPassword: "alt12345", newPassword: "neu12345")), as: UTF8.self)
        XCTAssertEqual(pw, #"{"current_password":"alt12345","new_password":"neu12345"}"#)

        let mail = String(decoding: try encoder.encode(
            EmailChangeRequestDTO(newEmail: "neu@example.com", password: "x")), as: UTF8.self)
        XCTAssertEqual(mail, #"{"new_email":"neu@example.com","password":"x"}"#)

        let forgot = String(decoding: try encoder.encode(
            PasswordForgotRequestDTO(email: "a@b.at", language: "en")), as: UTF8.self)
        XCTAssertEqual(forgot, #"{"email":"a@b.at","language":"en"}"#)
    }
}
