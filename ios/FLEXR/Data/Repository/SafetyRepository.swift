import Foundation

/// Melden und Blockieren. Entspricht backend/app/routers/safety.py.
@MainActor
final class SafetyRepository {

    private let api: FlexrAPI

    init(api: FlexrAPI) {
        self.api = api
    }

    /// Meldet einen Nutzer. Die Antwort ist die Empfangsbestätigung mit
    /// Aktenzeichen — sie muss dem Melder angezeigt werden (Art. 16 Abs. 4 DSA).
    func report(userID: String, reason: String) async throws -> ReportAck {
        let ack = try await api.report(
            ReportRequestDTO(
                reportedUserId: userID,
                reason: reason.trimmingCharacters(in: .whitespacesAndNewlines)
            )
        )
        return ReportAck(reference: ack.reference, message: ack.message)
    }

    /// Laufende Beschränkung des eigenen Kontos, oder nil wenn keine besteht.
    func moderationNotice() async throws -> ModerationNotice? {
        guard let dto = try await api.moderationNotice() else { return nil }
        return ModerationNotice(
            reason: dto.reason,
            mutedUntil: ServerTime.parse(dto.mutedUntil),
            appealHint: dto.appealHint
        )
    }

    /// Blockieren wirkt beidseitig: das Match verschwindet auf beiden Seiten.
    func block(userID: String) async throws {
        try await api.block(BlockRequestDTO(userId: userID))
    }

    func blockedUserIDs() async throws -> [String] {
        try await api.listBlocks()
    }

    func unblock(userID: String) async throws {
        try await api.unblock(userID: userID)
    }
}

/// Foto-Verifizierung (blauer Haken).
///
/// Der Server gibt die Anweisung vor ("Schau direkt in die Kamera"), das Selfie entsteht live über die
/// Kamera — kein Galerie-Upload. Das ist der Liveness-Schutz: nur eine echte
/// Person vor der Kamera kann die Aufnahme liefern.
@MainActor
final class VerificationRepository {

    private static let mimeType = "image/jpeg"

    private let api: FlexrAPI

    init(api: FlexrAPI) {
        self.api = api
    }

    func status() async throws -> VerificationState {
        try await api.verificationStatus().toDomain()
    }

    func start() async throws -> VerificationState {
        try await api.startVerification().toDomain()
    }

    /// Lädt die drei Aufnahmen hoch und reicht sie ein. Die Reihenfolge muss
    /// exakt der ausgegebenen Anweisungsliste entsprechen, sonst weist das Backend
    /// die Einreichung zurück.
    func submit(selfies: [(prompt: String, data: Data)]) async throws -> VerificationState {
        var uploaded: [VerificationSelfieDTO] = []
        for selfie in selfies {
            let presign = try await api.presignSelfie(
                PresignPhotoRequestDTO(contentType: Self.mimeType)
            )
            try await api.upload(
                to: presign.uploadUrl,
                contentType: Self.mimeType,
                data: selfie.data
            )
            uploaded.append(
                VerificationSelfieDTO(prompt: selfie.prompt, objectKey: presign.objectKey)
            )
        }
        return try await api.submitVerification(
            VerificationSubmitRequestDTO(selfies: uploaded)
        ).toDomain()
    }
}
