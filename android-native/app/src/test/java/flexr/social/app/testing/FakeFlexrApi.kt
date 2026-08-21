package flexr.social.app.testing

import flexr.social.app.data.remote.FlexrApi
import flexr.social.app.data.remote.dto.AddPhotoRequestDto
import flexr.social.app.data.remote.dto.AgeCheckRequestDto
import flexr.social.app.data.remote.dto.AgeCheckResponseDto
import flexr.social.app.data.remote.dto.BlockRequestDto
import flexr.social.app.data.remote.dto.CheckoutRequestDto
import flexr.social.app.data.remote.dto.CheckoutUrlDto
import flexr.social.app.data.remote.dto.ConsentDto
import flexr.social.app.data.remote.dto.ConsentRevokeRequestDto
import flexr.social.app.data.remote.dto.ConsentRevokeResponseDto
import flexr.social.app.data.remote.dto.DeleteAccountRequestDto
import flexr.social.app.data.remote.dto.GymDto
import flexr.social.app.data.remote.dto.GymSuggestRequestDto
import flexr.social.app.data.remote.dto.LoginRequestDto
import flexr.social.app.data.remote.dto.MatchDto
import flexr.social.app.data.remote.dto.MembershipStatusDto
import flexr.social.app.data.remote.dto.MessageDto
import flexr.social.app.data.remote.dto.ModerationNoticeDto
import flexr.social.app.data.remote.dto.MyProfileDto
import flexr.social.app.data.remote.dto.PlzLookupDto
import flexr.social.app.data.remote.dto.PortalUrlDto
import flexr.social.app.data.remote.dto.PresignPhotoRequestDto
import flexr.social.app.data.remote.dto.PresignPhotoResponseDto
import flexr.social.app.data.remote.dto.ProfileDto
import flexr.social.app.data.remote.dto.RegisterRequestDto
import flexr.social.app.data.remote.dto.ReportAckDto
import flexr.social.app.data.remote.dto.ReportRequestDto
import flexr.social.app.data.remote.dto.SendMessageRequestDto
import flexr.social.app.data.remote.dto.SwipeRequestDto
import flexr.social.app.data.remote.dto.SwipeResultDto
import flexr.social.app.data.remote.dto.TokenResponseDto
import flexr.social.app.data.remote.dto.UpdateProfileRequestDto
import flexr.social.app.data.remote.dto.EmailConfirmRequestDto
import flexr.social.app.data.remote.dto.EmailConfirmResponseDto
import flexr.social.app.data.remote.dto.EmailResendResponseDto
import flexr.social.app.data.remote.dto.VerificationDocumentPresignRequestDto
import flexr.social.app.data.remote.dto.VerificationDocumentSubmitRequestDto
import flexr.social.app.data.remote.dto.VerificationStatusDto
import flexr.social.app.data.remote.dto.VerificationSubmitRequestDto
import okhttp3.RequestBody

/**
 * Vollständige, absichtlich „leere" Umsetzung von [FlexrApi].
 *
 * Jeder Endpunkt scheitert mit einer klaren Meldung. Ein Test überschreibt nur
 * die Aufrufe, um die es ihm geht — ruft der Prüfling darüber hinaus etwas auf,
 * fällt genau das auf, statt in einem stillen Standardwert unterzugehen.
 *
 * Die echten Repositories laufen darüber unverändert; getestet wird damit auch
 * ihre Umsetzung samt DTO-Abbildung, nicht nur eine nachgebaute Fassade.
 */
open class FakeFlexrApi : FlexrApi {

    private fun nichtVorgesehen(name: String): Nothing =
        error("FakeFlexrApi.$name wurde aufgerufen, ist im Test aber nicht hinterlegt.")

    // ---------- auth.py ----------

    override suspend fun register(body: RegisterRequestDto): TokenResponseDto =
        nichtVorgesehen("register")

    override suspend fun login(body: LoginRequestDto): TokenResponseDto =
        nichtVorgesehen("login")

    override suspend fun checkAge(body: AgeCheckRequestDto): AgeCheckResponseDto =
        nichtVorgesehen("checkAge")

    // ---------- profiles.py ----------

    override suspend fun getMyProfile(): MyProfileDto = nichtVorgesehen("getMyProfile")

    override suspend fun updateMyProfile(body: UpdateProfileRequestDto): MyProfileDto =
        nichtVorgesehen("updateMyProfile")

    override suspend fun deleteMyAccount(body: DeleteAccountRequestDto) =
        nichtVorgesehen("deleteMyAccount")

    override suspend fun getMyConsents(): List<ConsentDto> =
        nichtVorgesehen("getMyConsents")

    override suspend fun revokeMyConsent(body: ConsentRevokeRequestDto): ConsentRevokeResponseDto =
        nichtVorgesehen("revokeMyConsent")

    override suspend fun presignPhoto(body: PresignPhotoRequestDto): PresignPhotoResponseDto =
        nichtVorgesehen("presignPhoto")

    override suspend fun addPhoto(body: AddPhotoRequestDto): MyProfileDto =
        nichtVorgesehen("addPhoto")

    override suspend fun deletePhoto(photoId: String): MyProfileDto =
        nichtVorgesehen("deletePhoto")

    // ---------- swipes.py ----------

    override suspend fun getDeck(): List<ProfileDto> = nichtVorgesehen("getDeck")

    override suspend fun swipe(body: SwipeRequestDto): SwipeResultDto = nichtVorgesehen("swipe")

    // ---------- matches.py / messages.py ----------

    override suspend fun getMatches(): List<MatchDto> = nichtVorgesehen("getMatches")

    override suspend fun unmatch(matchId: String) = nichtVorgesehen("unmatch")

    override suspend fun getMessages(matchId: String): List<MessageDto> =
        nichtVorgesehen("getMessages")

    override suspend fun sendMessage(matchId: String, body: SendMessageRequestDto): MessageDto =
        nichtVorgesehen("sendMessage")

    override suspend fun clearMessages(matchId: String) = nichtVorgesehen("clearMessages")

    override suspend fun deleteChat(matchId: String) = nichtVorgesehen("deleteChat")

    // ---------- billing.py ----------

    override suspend fun getMembershipStatus(): MembershipStatusDto =
        nichtVorgesehen("getMembershipStatus")

    override suspend fun createCheckout(body: CheckoutRequestDto): CheckoutUrlDto =
        nichtVorgesehen("createCheckout")

    override suspend fun createPortal(): PortalUrlDto = nichtVorgesehen("createPortal")

    // ---------- safety.py ----------

    override suspend fun report(body: ReportRequestDto): ReportAckDto = nichtVorgesehen("report")

    override suspend fun moderationNotice(): ModerationNoticeDto? =
        nichtVorgesehen("moderationNotice")

    override suspend fun block(body: BlockRequestDto) = nichtVorgesehen("block")

    override suspend fun listBlocks(): List<String> = nichtVorgesehen("listBlocks")

    override suspend fun unblock(userId: String) = nichtVorgesehen("unblock")

    // ---------- gyms.py ----------

    override suspend fun searchGyms(query: String): List<GymDto> = nichtVorgesehen("searchGyms")

    override suspend fun suggestGym(body: GymSuggestRequestDto): GymDto =
        nichtVorgesehen("suggestGym")

    // ---------- geo.py ----------

    override suspend fun lookupPostalCode(plz: String): PlzLookupDto =
        nichtVorgesehen("lookupPostalCode")

    // ---------- verification.py ----------

    override suspend fun resendVerificationEmail(): EmailResendResponseDto =
        nichtVorgesehen("resendVerificationEmail")

    override suspend fun confirmEmail(body: EmailConfirmRequestDto): EmailConfirmResponseDto =
        nichtVorgesehen("confirmEmail")

    override suspend fun getVerificationStatus(): VerificationStatusDto =
        nichtVorgesehen("getVerificationStatus")

    override suspend fun startVerification(): VerificationStatusDto =
        nichtVorgesehen("startVerification")

    override suspend fun presignSelfie(body: PresignPhotoRequestDto): PresignPhotoResponseDto =
        nichtVorgesehen("presignSelfie")

    override suspend fun submitVerification(body: VerificationSubmitRequestDto): VerificationStatusDto =
        nichtVorgesehen("submitVerification")

    override suspend fun presignDocument(
        body: VerificationDocumentPresignRequestDto,
    ): PresignPhotoResponseDto = nichtVorgesehen("presignDocument")

    override suspend fun submitDocument(
        body: VerificationDocumentSubmitRequestDto,
    ): VerificationStatusDto = nichtVorgesehen("submitDocument")

    override suspend fun discardDocuments(): VerificationStatusDto =
        nichtVorgesehen("discardDocuments")

    // ---------- Objekt-Storage ----------

    // Rückgabetyp ausdrücklich Unit: Ohne ihn leitet Kotlin aus
    // nichtVorgesehen() den Typ Nothing ab, und ein Test könnte die Methode
    // nicht mehr mit einer echten Umsetzung überschreiben.
    override suspend fun uploadToPresignedUrl(
        url: String,
        contentType: String,
        body: RequestBody,
    ): Unit = nichtVorgesehen("uploadToPresignedUrl")
}
