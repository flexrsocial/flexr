package flexr.social.app.push

import flexr.social.app.FlexrApplication
import flexr.social.app.ui.navigation.Routes
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Hält die Abmachung zwischen Server, Manifest und App zusammen.
 *
 * Diese drei Werte stehen an drei Orten, die kein Compiler miteinander
 * vergleicht: in `backend/app/push.py` (der Server schickt sie), in
 * `AndroidManifest.xml` (das Firebase-SDK liest sie, **wenn die App beendet
 * ist** und kein eigener Code läuft) und im Kotlin-Code. Läuft einer davon
 * weg, fällt das im Alltag nicht auf: Die App im Vordergrund zeichnet ihre
 * Benachrichtigung selbst und sieht richtig aus - nur bei geschlossener App
 * landet sie dann in einem fremden Kanal oder führt ins Leere.
 */
class PushZustellungTest {

    private val manifest: String by lazy {
        File("src/main/AndroidManifest.xml").readText()
    }

    @Test
    fun `das SDK zeigt bei beendeter App denselben Kanal an wie die App selbst`() {
        val ausManifest = Regex(
            """default_notification_channel_id"\s*\n?\s*android:value="([^"]+)"""",
        ).find(manifest)?.groupValues?.get(1)

        assertEquals(FlexrApplication.CHANNEL_MESSAGES, ausManifest)
    }

    @Test
    fun `das SDK zeichnet mit dem Symbol und der Farbe der App`() {
        assertTrue(
            "default_notification_icon fehlt im Manifest",
            manifest.contains("""android:name="com.google.firebase.messaging.default_notification_icon""""),
        )
        assertTrue(
            "default_notification_color fehlt im Manifest",
            manifest.contains("""android:name="com.google.firebase.messaging.default_notification_color""""),
        )
    }

    @Test
    fun `der Schluessel des Ziels heisst so wie in der Nutzlast des Servers`() {
        // backend/app/push.py: "data": {"target": target or ""} mit
        // target="chats" fuer eine Chatnachricht (routers/messages.py).
        assertEquals("target", FlexrMessagingService.DATA_TARGET)
        assertEquals("chats", Routes.CHATS)
    }
}
