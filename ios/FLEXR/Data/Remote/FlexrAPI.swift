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

    /// Macht eine Selbstlöschung innerhalb der 30-Tage-Karenzzeit rückgängig.
    /// Nimmt dieselben Zugangsdaten wie [login] entgegen (siehe
    /// routers/auth.reactivate).
    func reactivate(_ body: LoginRequestDTO) async throws -> TokenResponseDTO {
        try await client.send(.post, "api/auth/reactivate", body: body)
    }

    /// Zurücksetz-Link per Mail anfordern. Das Zurücksetzen selbst passiert im Browser.
    func forgotPassword(_ body: PasswordForgotRequestDTO) async throws -> OkResponseDTO {
        try await client.send(.post, "api/auth/password/forgot", body: body)
    }

    // MARK: - profiles.py

    /// Beendet alle anderen Sitzungen - die Antwort trägt einen frischen Token.
    func changePassword(_ body: PasswordChangeRequestDTO) async throws -> TokenResponseDTO {
        try await client.send(.post, "api/profiles/me/password", body: body)
    }

    func changeEmail(_ body: EmailChangeRequestDTO) async throws -> MyProfileDTO {
        try await client.send(.post, "api/profiles/me/email", body: body)
    }

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

    func myConsents() async throws -> [ConsentDTO] {
        try await client.send(.get, "api/profiles/me/consents")
    }

    func revokeConsent(_ body: ConsentRevokeRequestDTO) async throws -> ConsentRevokeResponseDTO {
        try await client.send(.post, "api/profiles/me/consents/revoke", body: body)
    }

    func grantConsent(_ body: ConsentGrantRequestDTO) async throws -> ConsentGrantResponseDTO {
        try await client.send(.post, "api/profiles/me/consents/grant", body: body)
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

    /// Reihenfolge der eigenen Fotos - photos[0] ist das Hauptfoto.
    func reorderPhotos(_ body: ReorderPhotosRequestDTO) async throws -> MyProfileDTO {
        try await client.send(.put, "api/profiles/me/photos/order", body: body)
    }

    func updateNotificationSettings(
        _ body: NotificationSettingsRequestDTO
    ) async throws -> MyProfileDTO {
        try await client.send(.patch, "api/profiles/me/notifications", body: body)
    }

    // MARK: - notifications.py

    /// Bereitliegende App-Benachrichtigungen abholen.
    ///
    /// `X-Flexr-Background` weist den Abruf als Hintergrundabgleich aus: ohne
    /// den Header wuerde ausgerechnet der Lauf, der die Inaktivitaets-Erinnerung
    /// ausliefern soll, den Nutzer dauerhaft als aktiv erscheinen lassen.
    func pendingNotifications() async throws -> [PushNotificationDTO] {
        try await client.send(
            .get, "api/notifications/pending",
            headers: ["X-Flexr-Background": "1"]
        )
    }

    /// Gerätetoken für echte Push-Zustellung anmelden.
    ///
    /// Bei jedem Start, nicht nur nach dem Anmelden: iOS vergibt den Token neu,
    /// wenn die App neu installiert oder wiederhergestellt wird. Mehrfaches
    /// Anmelden desselben Tokens ist deshalb der Normalfall und schreibt
    /// serverseitig nur dieselbe Zeile fort.
    func registerPushToken(platform: String, token: String) async throws {
        try await client.send(
            .post,
            "api/notifications/token",
            body: PushTokenRequestDTO(platform: platform, token: token)
        )
    }

    func unregisterPushToken(platform: String, token: String) async throws {
        try await client.send(
            .delete,
            "api/notifications/token",
            body: PushTokenRequestDTO(platform: platform, token: token)
        )
    }

    func markNotificationsDelivered(_ body: MarkDeliveredRequestDTO) async throws {
        try await client.send(
            .post, "api/notifications/delivered",
            body: body,
            headers: ["X-Flexr-Background": "1"]
        )
    }

    // MARK: - swipes.py

    func deck() async throws -> [ProfileDTO] {
        try await client.send(.get, "api/swipes/deck")
    }

    func swipe(_ body: SwipeRequestDTO) async throws -> SwipeResultDTO {
        try await client.send(.post, "api/swipes", body: body)
    }

    /// Wer mich geliket hat. Ohne Premium kommt keine Fehlermeldung, sondern
    /// nur die Anzahl ohne Profile (`premium_required = true`).
    func incomingLikes() async throws -> IncomingLikesDTO {
        try await client.send(.get, "api/swipes/incoming")
    }

    /// Letzten Swipe zurücknehmen — nur mit Premium, sonst 403.
    func rewindLastSwipe() async throws -> RewindResultDTO {
        try await client.send(.post, "api/swipes/rewind")
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

    /// „Chat löschen": Match, Swipe und Nachrichten bleiben bestehen — nur die
    /// Unterhaltung verschwindet aus der Chats-Übersicht (siehe `in_chats`).
    func deleteChat(matchID: String) async throws {
        try await client.send(.delete, "api/matches/\(matchID)/chat")
    }

    // MARK: - billing.py

    func membershipStatus() async throws -> MembershipStatusDTO {
        try await client.send(.get, "api/billing/status")
    }

    func createCheckout(_ body: CheckoutRequestDTO) async throws -> CheckoutUrlDTO {
        try await client.send(.post, "api/billing/checkout", body: body)
    }

    func createPortal() async throws -> PortalUrlDTO {
        try await client.send(.post, "api/billing/portal")
    }

    /// Eine signierte StoreKit-Transaktion einreichen.
    ///
    /// Wird nach jedem Kauf aufgerufen und außerdem beim Start für alle
    /// laufenden Berechtigungen. Mehrfaches Einreichen desselben Belegs ist
    /// ausdrücklich vorgesehen und schreibt serverseitig nur dieselbe Zeile
    /// fort — daran hängt die Wiederherstellung nach einem Gerätewechsel.
    func submitAppleTransaction(_ signedTransaction: String) async throws -> StorePurchaseResultDTO {
        try await client.send(
            .post,
            "api/billing/apple/transaction",
            body: AppleTransactionRequestDTO(signedTransaction: signedTransaction)
        )
    }

    // MARK: - safety.py

    func report(_ body: ReportRequestDTO) async throws -> ReportAckDTO {
        try await client.send(.post, "api/reports", body: body)
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

    /// Wie `listBlocks()`, aber mit Name, Alter und Vorschaubild statt nur der
    /// IDs. Eigene Methode statt eines Parameters an `listBlocks()`, damit der
    /// Server-Standard (ohne `?detail=true`) unverändert die reine ID-Liste
    /// bleibt — siehe Docstring in `backend/app/routers/safety.py`.
    func listBlockedUsers() async throws -> [BlockedUserOutDTO] {
        try await client.send(.get, "api/blocks", query: ["detail": "true"])
    }

    func unblock(userID: String) async throws {
        try await client.send(.delete, "api/blocks/\(userID)")
    }

    // MARK: - withdrawal.py

    /// Online-Rücktrittsfunktion (§ 13a FAGG) — direkt aus der App statt aus
    /// dem Formular auf flexr.social/widerruf.html. Braucht keine Anmeldung;
    /// ein mitgeschickter Token ordnet die Erklärung nur zusätzlich dem Konto zu.
    func declareWithdrawal(_ body: WithdrawalRequestDTO) async throws -> WithdrawalAckDTO {
        try await client.send(.post, "api/withdrawal", body: body)
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

    /// Schritt 2: amtlicher Lichtbildausweis, privat abgelegt und nur temporär.
    func presignDocument(
        _ body: VerificationDocumentPresignRequestDTO
    ) async throws -> PresignPhotoResponseDTO {
        try await client.send(.post, "api/verification/document/presign", body: body)
    }

    func submitDocument(
        _ body: VerificationDocumentSubmitRequestDTO
    ) async throws -> VerificationStatusDTO {
        try await client.send(.post, "api/verification/document/submit", body: body)
    }

    /// Eingereichte Aufnahmen zurückziehen, solange niemand geprüft hat.
    func discardDocuments() async throws -> VerificationStatusDTO {
        try await client.send(.delete, "api/verification/document")
    }

    // MARK: - E-Mail-Bestätigung (email_verify.py)

    /// Neuen Aktivierungslink anfordern (nur für unbestätigte Adressen).
    func resendVerificationEmail() async throws -> EmailResendResponseDTO {
        try await client.send(.post, "api/auth/email/resend")
    }

    /// Token aus dem Aktivierungslink einlösen — braucht keine Anmeldung.
    func confirmEmail(_ body: EmailConfirmRequestDTO) async throws -> EmailConfirmResponseDTO {
        try await client.send(.post, "api/auth/email/confirm", body: body)
    }

    // MARK: - Objekt-Storage (Presigned PUT, absolute URL)

    /// Lädt eine Bilddatei direkt in den Objekt-Storage. Es fließen keine
    /// Bilddaten durchs Backend.
    func upload(to presignedURL: String, contentType: String, data: Data) async throws {
        try await client.upload(to: presignedURL, contentType: contentType, data: data)
    }
}

/// Ortsermittlung zu einer Postleitzahl.
///
/// Als Protokoll, damit [PlzRepository] im Test ohne Netz auskommt — die
/// Entsprechung des Retrofit-Interfaces in der Android-App.
protocol PostalCodeLookup {
    func lookupPostalCode(_ plz: String) async throws -> PlzLookupDTO
}

/// PLZ-Lookup über das eigene Backend (GET /api/geo/plz/{plz}).
///
/// Früher fragten alle Clients openplzapi.org direkt an. Das war weder
/// verlässlich (der Dienst weist manche HTTP-Clients mit 418 ab) noch korrekt
/// (die seitenweise Ortschaftsliste ließ die Heuristik bei großen PLZ
/// danebengreifen). Das Backend liefert den amtlichen Ortsnamen.
struct BackendPlzAPI: PostalCodeLookup {

    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func lookupPostalCode(_ plz: String) async throws -> PlzLookupDTO {
        try await client.send(.get, "api/geo/plz/\(plz)")
    }
}
