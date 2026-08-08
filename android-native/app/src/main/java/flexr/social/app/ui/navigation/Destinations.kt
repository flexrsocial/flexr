package flexr.social.app.ui.navigation

import androidx.compose.ui.graphics.vector.ImageVector
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

enum class LegalDocument(val title: String) {
    FAQ("Häufige Fragen"),
    IMPRESSUM("Impressum"),
    DATENSCHUTZ("Datenschutzerklärung"),
    AGB("Allgemeine Geschäftsbedingungen"),
    SICHERHEIT("Sicherheitstipps"),
    NUTZUNGSRICHTLINIEN("Nutzungsrichtlinien"),
    STRAFVERFOLGUNG("Strafverfolgungsbehörden"),
}

/** Die vier Hauptbereiche der unteren Navigation. */
enum class TopLevelDestination(
    val route: String,
    val label: String,
    val icon: ImageVector,
) {
    SWIPE(Routes.SWIPE, "Swipe", FlexrIcons.Swipe),
    MATCHES(Routes.MATCHES, "Matches", FlexrIcons.Matches),
    CHATS(Routes.CHATS, "Chats", FlexrIcons.Chats),
    ACCOUNT(Routes.ACCOUNT, "Konto", FlexrIcons.Account),
}
