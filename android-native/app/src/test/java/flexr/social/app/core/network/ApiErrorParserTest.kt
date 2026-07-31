package flexr.social.app.core.network

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.Protocol
import okhttp3.Request
import okhttp3.Response
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.HttpException
import java.io.IOException
import java.net.UnknownHostException
import java.time.Instant

class ApiErrorParserTest {

    private fun httpException(code: Int, body: String): HttpException {
        val response = Response.Builder()
            .code(code)
            .message("error")
            .protocol(Protocol.HTTP_1_1)
            .request(Request.Builder().url("https://flexr.social/api/test").build())
            .build()
        return HttpException(
            retrofit2.Response.error<Any>(
                body.toResponseBody("application/json".toMediaType()),
                response,
            ),
        )
    }

    @Test
    fun `detail als text wird uebernommen`() {
        val exception = ApiErrorParser.toFlexrException(
            httpException(409, """{"detail":"E-Mail bereits registriert."}"""),
        )
        assertEquals(409, exception.statusCode)
        assertEquals("E-Mail bereits registriert.", exception.message)
    }

    @Test
    fun `pydantic fehlerliste wird zusammengefasst`() {
        val exception = ApiErrorParser.toFlexrException(
            httpException(
                422,
                """{"detail":[{"msg":"Du musst mindestens 18 Jahre alt sein."},{"msg":"PLZ ungültig."}]}""",
            ),
        )
        assertEquals("Du musst mindestens 18 Jahre alt sein., PLZ ungültig.", exception.message)
    }

    @Test
    fun `chat-sperre liefert das enddatum`() {
        val exception = ApiErrorParser.toFlexrException(
            httpException(
                403,
                """{"detail":{"reason":"messaging_muted","muted_until":"2026-08-01T10:00:00",""" +
                    """"message":"Deine Chat-Sperre ist noch aktiv."}}""",
            ),
        )
        assertTrue(exception.isMessagingMuted)
        assertEquals(Instant.parse("2026-08-01T10:00:00Z"), exception.mutedUntil)
        assertEquals("Deine Chat-Sperre ist noch aktiv.", exception.message)
    }

    @Test
    fun `abgelaufene mitgliedschaft wird erkannt`() {
        val exception = ApiErrorParser.toFlexrException(httpException(402, "{}"))
        assertTrue(exception.isPaymentRequired)
        assertNull(exception.mutedUntil)
    }

    @Test
    fun `netzfehler werden in verstaendliche meldungen uebersetzt`() {
        assertEquals(
            "Keine Internetverbindung.",
            ApiErrorParser.toFlexrException(UnknownHostException("no dns")).message,
        )
        assertEquals(
            "Verbindung fehlgeschlagen. Bitte erneut versuchen.",
            ApiErrorParser.toFlexrException(IOException("broken pipe")).message,
        )
    }
}
