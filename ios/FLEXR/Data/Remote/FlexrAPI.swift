import Foundation

/// Vollständige Abbildung der FastAPI-Router aus backend/app/routers/.
/// Ein Aufruf pro Endpunkt, gleiche Pfade wie im Web-Frontend und in der
/// Android-App.
struct FlexrAPI {

    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    // MARK: - auth.py

    func register(_ body: RegisterRequestDTO) async throws -> TokenResponseDTO {
        try await client.send(.post, "api/auth/register", body: body)
    }

    func login(_ body: LoginRequestDTO) async throws -> TokenResponseDTO {
        try await client.send(.post, "api/auth/login", body: body)
    }

    // MARK: - profiles.py

    func myProfile() async throws -> MyProfileDTO {
        try await client.send(.get, "api/profiles/me")
    }

    func updateMyProfile(_ body: UpdateProfileRequestDTO) async throws -> MyProfileDTO {
        try await client.send(.patch, "api/profiles/me", body: body)
    }

    /// DELETE mit Körper — vom Backend so vorgesehen (Passwortbestätigung).
    func deleteMyAccount(_ body: DeleteAccountRequestDTO) async throws {
        try await client.send(.delete, "api/profiles/me", body: body)
    }



    func presignPhoto(_ body: PresignPhotoRequestDTO) async throws -> PresignPhotoResponseDTO {
        try await client.send(.post, "api/profiles/me/photos/presign", body: body)
    }

    func addPhoto(_ body: AddPhotoRequestDTO) async throws -> MyProfileDTO {
        try await client.send(.post, "api/profiles/me/photos", body: body)
    }

    func deletePhoto(id: String) async throws -> MyProfileDTO {
        try await client.send(.delete, "api/profiles/me/photos/\(id)")
    }

    // MARK: - swipes.py

    func deck() async throws -> [ProfileDTO] {
        try await client.send(.get, "api/swipes/deck")
    }

    func swipe(_ body: SwipeRequestDTO) async throws -> SwipeResultDTO {
        try await client.send(.post, "api/swipes", body: body)
    }

    // MARK: - matches.py / messages.py

    func matches() async throws -> [MatchDTO] {
        try await client.send(.get, "api/matches")
    }

    func unmatch(matchID: String) async throws {
        try await client.send(.delete, "api/matches/\(matchID)")
    }

    func messages(matchID: String) async throws -> [MessageDTO] {
        try await client.send(.get, "api/matches/\(matchID)/messages")
    }

    func sendMessage(matchID: String, body: SendMessageRequestDTO) async throws -> MessageDTO {
        try await client.send(.post, "api/matches/\(matchID)/messages", body: body)
    }

    func clearMessages(matchID: String) async throws {
        try await client.send(.delete, "api/matches/\(matchID)/messages")
    }

    // MARK: - billing.py

    func membershipStatus() async throws -> MembershipStatusDTO {
        try await client.send(.get, "api/billing/status")
    }

    func createCheckout() async throws -> CheckoutUrlDTO {
        try await client.send(.post, "api/billing/checkout")
    }

    func createPortal() async throws -> PortalUrlDTO {
        try await client.send(.post, "api/billing/portal")
    }

    // MARK: - safety.py

    func report(_ body: ReportRequestDTO) async throws -> ReportAckDTO {
        try await client.send(.post, "api/reports", body: body)
    }

    func myReports() async throws -> [MyReportDTO] {
        try await client.send(.get, "api/reports/mine")
    }

    func moderationNotice() async throws -> ModerationNoticeDTO? {
        try await client.sendOptional(.get, "api/moderation/notice", as: ModerationNoticeDTO.self)
    }

    func block(_ body: BlockRequestDTO) async throws {
        try await client.send(.post, "api/blocks", body: body)
    }

    func listBlocks() async throws -> [String] {
        try await client.send(.get, "api/blocks")
    }

    func unblock(userID: String) async throws {
        try await client.send(.delete, "api/blocks/\(userID)")
    }

    // MARK: - gyms.py

    func searchGyms(query: String) async throws -> [GymDTO] {
        try await client.send(.get, "api/gyms", query: ["q": query])
    }

    func suggestGym(_ body: GymSuggestRequestDTO) async throws -> GymDTO {
        try await client.send(.post, "api/gyms/suggest", body: body)
    }

    // MARK: - verification.py

    func verificationStatus() async throws -> VerificationStatusDTO {
        try await client.send(.get, "api/verification/status")
    }

    func startVerification() async throws -> VerificationStatusDTO {
        try await client.send(.post, "api/verification/start")
    }

    func presignSelfie(_ body: PresignPhotoRequestDTO) async throws -> PresignPhotoResponseDTO {
        try await client.send(.post, "api/verification/selfies/presign", body: body)
    }

    func submitVerification(_ body: VerificationSubmitRequestDTO) async throws -> VerificationStatusDTO {
        try await client.send(.post, "api/verification/submit", body: body)
    }

    // MARK: - Objekt-Storage (Presigned PUT, absolute URL)

    /// Lädt eine Bilddatei direkt in den Objekt-Storage. Es fließen keine
    /// Bilddaten durchs Backend.
    func upload(to presignedURL: String, contentType: String, data: Data) async throws {
        try await client.upload(to: presignedURL, contentType: contentType, data: data)
    }
}

/// Ortsverzeichnis zu einer Postleitzahl.
///
/// Als Protokoll, damit [PlzRepository] im Test ohne Netz auskommt — die
/// Entsprechung des Retrofit-Interfaces in der Android-App.
protocol PostalCodeLookup {
    func localities(postalCode: String) async throws -> [OpenPlzLocalityDTO]
}

/// Öffentliche PLZ-Datenbank (openplzapi.org) für die Ortsermittlung —
/// dieselbe Quelle, die das Web-Frontend nutzt. Damit ist ganz Österreich
/// abgedeckt, ohne eine gepflegte Städteliste in der App.
struct OpenPlzAPI: PostalCodeLookup {

    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func localities(postalCode: String) async throws -> [OpenPlzLocalityDTO] {
        try await client.send(.get, "at/Localities", query: ["postalCode": postalCode])
    }
}
