package flexr.social.app.ui.navigation

import androidx.annotation.StringRes
import androidx.compose.ui.graphics.vector.ImageVector
import flexr.social.app.R
import flexr.social.app.core.designsystem.icon.FlexrIcons

/** Alle Ziele der App. Typisierte Routen statt String-Bastelei an den Aufrufstellen. */
object Routes {
    const val LOGIN = "login"
    const val REGISTER = "register"
    const val PAYWALL = "paywall"

    const val SWIPE = "swipe"
    const val MATCHES = "matches"
    const val CHATS = "chats"
    const val ACCOUNT = "account"

    const val MATCH_PROFILE = "matchProfile/{matchId}"
    const val CHAT = "chat/{matchId}?origin={origin}"
    const val VERIFICATION = "verification"

    /** Alters- und Identitätsprüfung eines noch nicht freigeschalteten Kontos. */
    const val VERIFICATION_GATE = "verificationGate"
    const val VERIFICATION_DOCUMENT = "verificationDocument"

    const val LEGAL = "legal/{document}"

    fun matchProfile(matchId: String) = "matchProfile/$matchId"
    fun chat(matchId: String, origin: String = CHATS) = "chat/$matchId?origin=$origin"
    fun legal(document: LegalDocument) = "legal/${document.name}"
}

/**
 * Die Rechtstexte. Nur der Titel der Ansicht ist uebersetzt - der Inhalt in
 * [flexr.social.app.ui.legal.LegalContent] bleibt bewusst auf Deutsch, weil er
 * in dieser Fassung verbindlich ist.
 */
enum class LegalDocument(@StringRes val titleRes: Int) {
    FAQ(R.string.legal_faq),
    IMPRESSUM(R.string.legal_impressum),
    DATENSCHUTZ(R.string.legal_datenschutz),
    AGB(R.string.legal_agb),
    SICHERHEIT(R.string.legal_sicherheit),
    NUTZUNGSRICHTLINIEN(R.string.legal_nutzungsrichtlinien),
    STRAFVERFOLGUNG(R.string.legal_strafverfolgung),
}

/** Die vier Hauptbereiche der unteren Navigation. */
enum class TopLevelDestination(
    val route: String,
    @StringRes val labelRes: Int,
    val icon: ImageVector,
) {
    SWIPE(Routes.SWIPE, R.string.nav_swipe, FlexrIcons.Swipe),
    MATCHES(Routes.MATCHES, R.string.nav_matches, FlexrIcons.Matches),
    CHATS(Routes.CHATS, R.string.nav_chats, FlexrIcons.Chats),
    ACCOUNT(Routes.ACCOUNT, R.string.nav_account, FlexrIcons.Account),
}
