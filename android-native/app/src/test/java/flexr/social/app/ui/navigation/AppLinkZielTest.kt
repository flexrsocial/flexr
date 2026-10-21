package flexr.social.app.ui.navigation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * Seit 2.7.38 öffnen die Links in den Aktivitäts-Mails die App, wenn sie
 * installiert ist (`https://flexr.social/app/open/<reiter>`).
 */
class AppLinkZielTest {

    @Test
    fun `Mail-Links fuehren auf den passenden Reiter`() {
        assertEquals(Routes.MATCHES, appLinkTarget("/app/open/matches"))
        assertEquals(Routes.SWIPE, appLinkTarget("/app/open/swipe"))
        assertEquals(Routes.SWIPE, appLinkTarget("/app/open/swipe/"))
        assertEquals(Routes.CHATS, appLinkTarget("/app/open/chats"))
    }

    @Test
    fun `ohne oder mit unbekanntem Ziel oeffnet die App nur`() {
        assertNull(appLinkTarget("/app/open/"))
        assertNull(appLinkTarget("/app/open/premium"))
        assertNull(appLinkTarget("/app/open/../account"))
    }

    @Test
    fun `andere Pfade sind kein Reiter-Link`() {
        assertNull(appLinkTarget(null))
        assertNull(appLinkTarget("/mail-bestaetigen"))
        assertNull(appLinkTarget("/app/"))
        assertNull(appLinkTarget("/app/openmatches"))
    }
}
