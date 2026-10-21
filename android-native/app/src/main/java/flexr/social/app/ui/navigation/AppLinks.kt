package flexr.social.app.ui.navigation

/**
 * Pfad der Mail-Links in die App: `https://flexr.social/app/open/<reiter>`
 * (neues Match → `matches`, neue Profile/offene Likes/lange nicht gesehen →
 * `swipe`, Freischaltung → `swipe`, Nachbesserung → nur `/app/open/`).
 *
 * Seit 2.7.38 als App Link eingetragen (AndroidManifest): Ist die App
 * installiert, öffnet der Link sie statt der Web-App. Ohne App liefert nginx
 * unter jedem `/app/…`-Pfad die Web-App aus, die den Reiter genauso öffnet.
 * Bis 2.7.37 zeigten die Links auf `/app/?open=…`; die Abfrage lässt sich
 * in einem Intent-Filter nicht unterscheiden, `/app/` selbst gehört aber auch
 * dem Reset-Link, den nur der Browser kann.
 */
const val APP_LINK_PREFIX = "/app/open/"

private val APP_LINK_ZIELE = setOf(Routes.SWIPE, Routes.MATCHES, Routes.CHATS, Routes.ACCOUNT)

/**
 * Reiter aus dem Pfad eines Mail-Links, sonst `null` (dann öffnet die App
 * einfach). Unbekannte Ziele aus einer neueren Serverfassung führen nicht auf
 * eine leere Route.
 */
fun appLinkTarget(path: String?): String? {
    if (path == null || !path.startsWith(APP_LINK_PREFIX)) return null
    val ziel = path.removePrefix(APP_LINK_PREFIX).trim('/')
    return ziel.takeIf { it in APP_LINK_ZIELE }
}
