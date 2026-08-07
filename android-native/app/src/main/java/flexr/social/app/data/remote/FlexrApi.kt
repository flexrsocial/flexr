package flexr.social.app.data.remote

import flexr.social.app.data.remote.dto.AddPhotoRequestDto
import flexr.social.app.data.remote.dto.BlockRequestDto
import flexr.social.app.data.remote.dto.CheckoutUrlDto
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
import flexr.social.app.data.remote.dto.VerificationStatusDto
import flexr.social.app.data.remote.dto.VerificationSubmitRequestDto
import okhttp3.RequestBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.HTTP
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.Url

/**
 * Vollständige Abbildung der FastAPI-Router aus backend/app/routers/.
 * Ein Endpunkt pro Methode, gleiche Pfade wie im Web-Frontend.
 */
interface FlexrApi {

    // ---------- auth.py ----------

    @POST("api/auth/register")
    suspend fun register(@Body body: RegisterRequestDto): TokenResponseDto

    @POST("api/auth/login")
    suspend fun login(@Body body: LoginRequestDto): TokenResponseDto

    // ---------- profiles.py ----------

    @GET("api/profiles/me")
    suspend fun getMyProfile(): MyProfileDto

    @PATCH("api/profiles/me")
    suspend fun updateMyProfile(@Body body: flexr.social.app.data.remote.dto.UpdateProfileRequestDto): MyProfileDto

    /** DELETE mit Body — Retrofits @DELETE erlaubt das nicht, @HTTP schon. */
    @HTTP(method = "DELETE", path = "api/profiles/me", hasBody = true)
    suspend fun deleteMyAccount(@Body body: DeleteAccountRequestDto)



    @POST("api/profiles/me/photos/presign")
    suspend fun presignPhoto(@Body body: PresignPhotoRequestDto): PresignPhotoResponseDto

    @POST("api/profiles/me/photos")
    suspend fun addPhoto(@Body body: AddPhotoRequestDto): MyProfileDto

    @DELETE("api/profiles/me/photos/{photoId}")
    suspend fun deletePhoto(@Path("photoId") photoId: String): MyProfileDto

    // ---------- swipes.py ----------

    @GET("api/swipes/deck")
    suspend fun getDeck(): List<ProfileDto>

    @POST("api/swipes")
    suspend fun swipe(@Body body: SwipeRequestDto): SwipeResultDto

    // ---------- matches.py / messages.py ----------

    @GET("api/matches")
    suspend fun getMatches(): List<MatchDto>

    @DELETE("api/matches/{matchId}")
    suspend fun unmatch(@Path("matchId") matchId: String)

    @GET("api/matches/{matchId}/messages")
    suspend fun getMessages(@Path("matchId") matchId: String): List<MessageDto>

    @POST("api/matches/{matchId}/messages")
    suspend fun sendMessage(
        @Path("matchId") matchId: String,
        @Body body: SendMessageRequestDto,
    ): MessageDto

    @DELETE("api/matches/{matchId}/messages")
    suspend fun clearMessages(@Path("matchId") matchId: String)

    // ---------- billing.py ----------

    @GET("api/billing/status")
    suspend fun getMembershipStatus(): MembershipStatusDto

    @POST("api/billing/checkout")
    suspend fun createCheckout(): CheckoutUrlDto

    @POST("api/billing/portal")
    suspend fun createPortal(): PortalUrlDto

    // ---------- safety.py ----------

    @POST("api/reports")
    suspend fun report(@Body body: ReportRequestDto): ReportAckDto

    @GET("api/moderation/notice")
    suspend fun moderationNotice(): ModerationNoticeDto?

    @POST("api/blocks")
    suspend fun block(@Body body: BlockRequestDto)

    @GET("api/blocks")
    suspend fun listBlocks(): List<String>

    @DELETE("api/blocks/{userId}")
    suspend fun unblock(@Path("userId") userId: String)

    // ---------- gyms.py ----------

    @GET("api/gyms")
    suspend fun searchGyms(@Query("q") query: String): List<GymDto>

    @POST("api/gyms/suggest")
    suspend fun suggestGym(@Body body: GymSuggestRequestDto): GymDto

    // ---------- geo.py ----------

    @GET("api/geo/plz/{plz}")
    suspend fun lookupPostalCode(@Path("plz") plz: String): PlzLookupDto

    // ---------- verification.py ----------

    @GET("api/verification/status")
    suspend fun getVerificationStatus(): VerificationStatusDto

    @POST("api/verification/start")
    suspend fun startVerification(): VerificationStatusDto

    @POST("api/verification/selfies/presign")
    suspend fun presignSelfie(@Body body: PresignPhotoRequestDto): PresignPhotoResponseDto

    @POST("api/verification/submit")
    suspend fun submitVerification(@Body body: VerificationSubmitRequestDto): VerificationStatusDto

    // ---------- Objekt-Storage (Presigned PUT, absolute URL) ----------

    /**
     * Lädt eine Bilddatei direkt in den Objekt-Storage (S3/Cloudflare R2).
     * Bewusst absolut adressiert (@Url) — es fließen keine Bilddaten durchs Backend.
     */
    @PUT
    suspend fun uploadToPresignedUrl(
        @Url url: String,
        @Header("Content-Type") contentType: String,
        @Body body: RequestBody,
    )
}
