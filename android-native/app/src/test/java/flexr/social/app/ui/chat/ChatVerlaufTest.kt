package flexr.social.app.ui.chat

import flexr.social.app.domain.model.Message
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.Instant
import java.time.ZoneId

class ChatVerlaufTest {

    private val wien = ZoneId.of("Europe/Vienna")

    private fun nachricht(id: String, zeit: String) = Message(
        id = id,
        matchId = "m",
        senderId = "a",
        content = id,
        createdAt = Instant.parse(zeit),
        readAt = null,
        wasCensored = false,
    )

    @Test
    fun `vor der ersten nachricht jedes tages steht ein trenner`() {
        val eintraege = mitTagestrennern(
            listOf(
                nachricht("1", "2026-10-10T07:18:00Z"),
                nachricht("2", "2026-10-14T17:07:00Z"),
                nachricht("3", "2026-10-14T18:00:00Z"),
                nachricht("4", "2026-10-15T11:13:00Z"),
            ),
            wien,
        )
        assertEquals(
            listOf("tag-2026-10-10", "1", "tag-2026-10-14", "2", "3", "tag-2026-10-15", "4"),
            eintraege.map { it.key },
        )
    }

    @Test
    fun `der tag richtet sich nach der ortszeit, nicht nach UTC`() {
        // 22:30 UTC am 14.10. ist in Wien schon der 15.10. (00:30).
        val eintraege = mitTagestrennern(
            listOf(
                nachricht("1", "2026-10-14T21:30:00Z"),
                nachricht("2", "2026-10-14T22:30:00Z"),
            ),
            wien,
        )
        assertEquals(listOf("tag-2026-10-14", "1", "tag-2026-10-15", "2"), eintraege.map { it.key })
    }

    @Test
    fun `ohne nachrichten gibt es keine trenner`() {
        assertEquals(emptyList<ChatEintrag>(), mitTagestrennern(emptyList(), wien))
    }
}
