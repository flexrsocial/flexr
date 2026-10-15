package flexr.social.app.ui.chat

import flexr.social.app.domain.model.Message
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId

/** Eintrag im Chatverlauf: ein Tagestrenner oder eine Nachricht. */
internal sealed interface ChatEintrag {
    val key: String

    data class Tag(val datum: LocalDate, val zeitpunkt: Instant) : ChatEintrag {
        override val key: String get() = "tag-$datum"
    }

    data class Nachricht(val message: Message) : ChatEintrag {
        override val key: String get() = message.id
    }
}

/**
 * Setzt vor die erste Nachricht jedes Kalendertags einen Trenner. Die Blasen
 * zeigen dann nur noch die Uhrzeit - vorher stand an jeder Nachricht eines
 * frueheren Tages das volle Datum. Gleiche Regel wie in der Web-App.
 */
internal fun mitTagestrennern(messages: List<Message>, zone: ZoneId): List<ChatEintrag> {
    val eintraege = ArrayList<ChatEintrag>(messages.size + 4)
    var letzterTag: LocalDate? = null
    for (message in messages) {
        val tag = message.createdAt.atZone(zone).toLocalDate()
        if (tag != letzterTag) {
            eintraege += ChatEintrag.Tag(tag, message.createdAt)
            letzterTag = tag
        }
        eintraege += ChatEintrag.Nachricht(message)
    }
    return eintraege
}
