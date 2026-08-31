package flexr.social.app.ui

import android.net.Uri
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarData
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import flexr.social.app.core.browser.openExternalPage
import flexr.social.app.core.designsystem.component.LoadingState
import flexr.social.app.core.designsystem.component.StatusPill
import flexr.social.app.core.designsystem.theme.FlexrBackground
import flexr.social.app.core.common.ServerTime
import flexr.social.app.domain.model.Membership
import flexr.social.app.ui.account.AccountScreen
import flexr.social.app.ui.auth.LoginScreen
import flexr.social.app.ui.auth.RegisterScreen
import flexr.social.app.ui.chat.ChatScreen
import flexr.social.app.ui.legal.LegalScreen
import flexr.social.app.ui.matches.ChatsScreen
import flexr.social.app.ui.matches.MatchProfileScreen
import flexr.social.app.ui.matches.MatchesScreen
import flexr.social.app.ui.navigation.FlexrBottomBar
import flexr.social.app.ui.navigation.FlexrTopBar
import flexr.social.app.ui.navigation.LegalDocument
import flexr.social.app.ui.navigation.Routes
import flexr.social.app.ui.navigation.TopLevelDestination
import flexr.social.app.ui.paywall.PaywallScreen
import flexr.social.app.ui.swipe.SwipeScreen
import flexr.social.app.ui.verification.DocumentScreen
import flexr.social.app.ui.verification.VerificationGateScreen
import flexr.social.app.ui.verification.VerificationScreen
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Mindestanzeigedauer der Snackbar-Meldungen (`showMessage` in `FlexrApp`). */
private const val MIN_MESSAGE_DURATION_MS = 20_000L

/**
 * Einstiegspunkt der Oberfläche.
 *
 * Je nach Sitzungszustand läuft ein eigener Navigationsgraph: ausgeloggt,
 * zahlungspflichtig gesperrt oder vollständige App. Das hält die Routen
 * sauber getrennt — ein gesperrtes Konto kann gar nicht erst auf das Deck
 * navigieren, statt dort auf einen 402 zu laufen.
 */
@Composable
fun FlexrApp(
    intentData: Uri? = null,
    /** Zielreiter einer angetippten Benachrichtigung, sonst null. */
    notificationTarget: String? = null,
    onNotificationTargetHandled: () -> Unit = {},
    viewModel: MainViewModel = hiltViewModel(),
) {
    val appState by viewModel.appState.collectAsStateWithLifecycle()
    val unreadCount by viewModel.unreadCount.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    val showMessage: (String) -> Unit = { message ->
        scope.launch {
            // Erst 10s, dann laut Rueckmeldung immer noch zu kurz - jetzt 20s.
            // Eigener Timer statt SnackbarDuration.Long (fix bei 10s), damit die
            // Dauer hier direkt im Code einstellbar ist.
            val autoDismiss = launch {
                delay(MIN_MESSAGE_DURATION_MS)
                snackbarHostState.currentSnackbarData?.dismiss()
            }
            snackbarHostState.showSnackbar(message, withDismissAction = true, duration = SnackbarDuration.Indefinite)
            autoDismiss.cancel()
        }
    }

    // Rückkehr aus dem Stripe-Checkout im Browser: Abo-Status neu holen.
    LifecycleEventEffect(Lifecycle.Event.ON_RESUME) {
        if (appState is AppState.Locked) viewModel.refreshMembership()
    }
    LaunchedEffect(intentData) {
        if (intentData?.scheme == "flexr") viewModel.refreshMembership()

        // Aktivierungslink aus der Bestätigungsmail. Der Link ist als App Link
        // eingetragen (AndroidManifest) und landet deshalb hier statt im
        // Browser - schlägt die Prüfung der assetlinks.json fehl, öffnet ihn
        // der Browser und bestätigt dort. Beide Wege führen zum Ziel.
        if (intentData?.path == "/mail-bestaetigen") {
            val token = intentData.getQueryParameter("token")
            if (token.isNullOrBlank()) {
                showMessage("In diesem Link fehlt der Bestätigungscode.")
            } else {
                viewModel.confirmEmailToken(token, showMessage)
            }
        }
    }

    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        FlexrBackground {
            when (val state = appState) {
                AppState.Loading -> LoadingState()

                AppState.LoggedOut -> AuthGraph(
                    snackbarHostState = snackbarHostState,
                    onLoggedIn = viewModel::loadSession,
                    onShowMessage = showMessage,
                )

                is AppState.NeedsVerification -> VerificationGraph(
                    snackbarHostState = snackbarHostState,
                    onLogout = viewModel::logout,
                    onReloadSession = viewModel::loadSession,
                    onShowMessage = showMessage,
                )

                is AppState.Locked -> LockedGraph(
                    membership = state.membership,
                    snackbarHostState = snackbarHostState,
                    onLogout = viewModel::logout,
                    onOpenUrl = { context.openExternalPage(it) },
                    onShowMessage = showMessage,
                )

                is AppState.Ready -> MainGraph(
                    membership = state.membership,
                    ownUserId = state.profile.id,
                    unreadCount = unreadCount,
                    snackbarHostState = snackbarHostState,
                    onLogout = viewModel::logout,
                    onOpenUrl = { context.openExternalPage(it) },
                    onShowMessage = showMessage,
                    notificationTarget = notificationTarget,
                    onNotificationTargetHandled = onNotificationTargetHandled,
                )
            }
        }
    }
}

/**
 * Ersetzt den Standard-`Snackbar`: dessen Textzeile begann sichtbar erst in
 * der zweiten Zeile (Innenabstand des Standard-Layouts), noch dazu verschwand
 * er nach ein paar Sekunden ohne Möglichkeit, ihn vorher wegzutippen - bei
 * Widerrufs-Folgetexten (z. B. `AccountScreen.kt`, `revokeConsent`) zu kurz,
 * um sie in Ruhe zu lesen. Eigenes Layout mit engem oberen Abstand plus
 * Schließen-Knopf statt der Standard-`Snackbar`-Komposable.
 */
@Composable
private fun FlexrSnackbar(data: SnackbarData) {
    Surface(
        modifier = Modifier
            .padding(12.dp)
            .fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.inverseSurface,
        contentColor = MaterialTheme.colorScheme.inverseOnSurface,
        tonalElevation = 6.dp,
        shadowElevation = 6.dp,
    ) {
        Row(
            Modifier.padding(start = 16.dp, top = 14.dp, end = 4.dp, bottom = 14.dp),
            verticalAlignment = Alignment.Top,
        ) {
            Text(
                data.visuals.message,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.weight(1f),
            )
            IconButton(
                onClick = { data.dismiss() },
                modifier = Modifier.size(24.dp),
            ) {
                Icon(Icons.Default.Close, contentDescription = "Schließen")
            }
        }
    }
}

// ---------- Ausgeloggt ----------

@Composable
private fun AuthGraph(
    snackbarHostState: SnackbarHostState,
    onLoggedIn: () -> Unit,
    onShowMessage: (String) -> Unit,
) {
    val navController = rememberNavController()

    Scaffold(
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(snackbarHostState) { data -> FlexrSnackbar(data) } },
        topBar = { FlexrTopBar(statusSlot = {}) },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Routes.LOGIN,
            modifier = Modifier.fillMaxSize().padding(padding),
        ) {
            composable(Routes.LOGIN) {
                LoginScreen(
                    onLoggedIn = onLoggedIn,
                    onGoToRegister = { navController.navigate(Routes.REGISTER) },
                )
            }
            composable(Routes.REGISTER) {
                RegisterScreen(
                    onRegistered = { notice ->
                        notice?.let(onShowMessage)
                        onLoggedIn()
                    },
                    onGoToLogin = { navController.popBackStack(Routes.LOGIN, inclusive = false) },
                    onOpenLegal = { navController.navigate(Routes.legal(it)) },
                )
            }
            legalDestination(navController)
        }
    }
}

// ---------- Angemeldet, aber Alters-/Identitätsprüfung offen ----------

/**
 * Eigener Graph statt einer Sperre in den einzelnen Bildschirmen: Ein Konto
 * ohne bestandene Prüfung kann gar nicht erst auf das Deck navigieren, statt
 * dort in einen 403 zu laufen. Die untere Navigation fehlt bewusst.
 */
@Composable
private fun VerificationGraph(
    snackbarHostState: SnackbarHostState,
    onLogout: () -> Unit,
    onReloadSession: () -> Unit,
    onShowMessage: (String) -> Unit,
) {
    val navController = rememberNavController()

    Scaffold(
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(snackbarHostState) { data -> FlexrSnackbar(data) } },
        // "In Prüfung" bekamen auch Konten angezeigt, die noch gar nichts
        // eingereicht hatten. Der Pillentext gilt für den ganzen Graphen,
        // also muss er in jedem Schritt stimmen.
        topBar = { FlexrTopBar(statusSlot = { StatusPill("Nicht freigeschaltet") }) },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Routes.VERIFICATION_GATE,
            modifier = Modifier.fillMaxSize().padding(padding),
        ) {
            composable(Routes.VERIFICATION_GATE) {
                VerificationGateScreen(
                    onStartSelfies = { navController.navigate(Routes.VERIFICATION) },
                    onStartDocument = { navController.navigate(Routes.VERIFICATION_DOCUMENT) },
                    // Freigeschaltet: den Sitzungszustand neu bestimmen, damit
                    // die App diesen Graphen verlässt.
                    onActivated = onReloadSession,
                    onLogout = onLogout,
                    onShowMessage = onShowMessage,
                )
            }

            composable(Routes.VERIFICATION) {
                VerificationScreen(
                    // Nach dem Selfie steht der Ausweis an - direkt weiter,
                    // ohne Umweg über die Übersicht.
                    onFinished = {
                        navController.navigate(Routes.VERIFICATION_DOCUMENT) {
                            popUpTo(Routes.VERIFICATION_GATE)
                        }
                    },
                    // Abbruch führt zurück zur Übersicht - von dort aus zeigt der
                    // Server ohnehin an, welcher Schritt wirklich ansteht.
                    onBack = {
                        navController.popBackStack(Routes.VERIFICATION_GATE, inclusive = false)
                    },
                    onShowMessage = onShowMessage,
                )
            }

            composable(Routes.VERIFICATION_DOCUMENT) {
                DocumentScreen(
                    onBack = { navController.popBackStack(Routes.VERIFICATION_GATE, inclusive = false) },
                    onSubmitted = {
                        navController.popBackStack(Routes.VERIFICATION_GATE, inclusive = false)
                        onReloadSession()
                    },
                    onShowMessage = onShowMessage,
                )
            }

            legalDestination(navController)
        }
    }
}

// ---------- Angemeldet, aber Probemonat abgelaufen ----------

@Composable
private fun LockedGraph(
    membership: Membership,
    snackbarHostState: SnackbarHostState,
    onLogout: () -> Unit,
    onOpenUrl: (String) -> Unit,
    onShowMessage: (String) -> Unit,
) {
    val navController = rememberNavController()

    Scaffold(
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(snackbarHostState) { data -> FlexrSnackbar(data) } },
        topBar = {
            FlexrTopBar(statusSlot = { MembershipPill(membership) })
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Routes.PAYWALL,
            modifier = Modifier.fillMaxSize().padding(padding),
        ) {
            composable(Routes.PAYWALL) {
                PaywallScreen(
                    onLogout = onLogout,
                    onOpenUrl = onOpenUrl,
                    onShowMessage = onShowMessage,
                )
            }
            legalDestination(navController)
        }
    }
}

// ---------- Vollständige App ----------

@Composable
private fun MainGraph(
    membership: Membership,
    ownUserId: String,
    unreadCount: Int,
    snackbarHostState: SnackbarHostState,
    onLogout: () -> Unit,
    onOpenUrl: (String) -> Unit,
    onShowMessage: (String) -> Unit,
    notificationTarget: String? = null,
    onNotificationTargetHandled: () -> Unit = {},
) {
    val navController = rememberNavController()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route
    val isTopLevel = TopLevelDestination.entries.any { it.route == currentRoute }

    // Tipp auf eine Benachrichtigung: zum passenden Reiter springen.
    //
    // Gleiches Navigationsmuster wie die untere Leiste, damit kein zweiter
    // Eintrag im Backstack entsteht. Das Ziel wird anschliessend verbraucht -
    // ohne das wuerde jede Neuzusammensetzung (Drehen, Rueckkehr aus dem
    // Hintergrund) erneut dorthin springen und den Nutzer festhalten.
    LaunchedEffect(notificationTarget) {
        val target = notificationTarget ?: return@LaunchedEffect
        if (TopLevelDestination.entries.any { it.route == target }) {
            navController.navigate(target) {
                popUpTo(navController.graph.startDestinationId) { saveState = true }
                launchSingleTop = true
                restoreState = true
            }
        }
        onNotificationTargetHandled()
    }

    Scaffold(
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(snackbarHostState) { data -> FlexrSnackbar(data) } },
        topBar = {
            if (isTopLevel) {
                FlexrTopBar(statusSlot = { MembershipPill(membership) })
            }
        },
        bottomBar = {
            if (isTopLevel) {
                FlexrBottomBar(
                    currentRoute = currentRoute,
                    unreadCount = unreadCount,
                    onNavigate = { destination ->
                        navController.navigate(destination.route) {
                            popUpTo(navController.graph.startDestinationId) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    },
                )
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Routes.SWIPE,
            modifier = Modifier.fillMaxSize().padding(padding),
        ) {
            composable(Routes.SWIPE) {
                SwipeScreen(
                    onOpenChat = { matchId ->
                        navController.navigate(Routes.chat(matchId, Routes.CHATS))
                    },
                    onShowMessage = onShowMessage,
                )
            }

            composable(Routes.MATCHES) {
                MatchesScreen(
                    onOpenMatchProfile = { navController.navigate(Routes.matchProfile(it)) },
                )
            }

            composable(Routes.CHATS) {
                ChatsScreen(
                    ownUserId = ownUserId,
                    onOpenChat = { navController.navigate(Routes.chat(it, Routes.CHATS)) },
                )
            }

            composable(Routes.ACCOUNT) {
                AccountScreen(
                    onLogout = onLogout,
                    onOpenVerification = { navController.navigate(Routes.VERIFICATION) },
                    onOpenDocumentStep = { navController.navigate(Routes.VERIFICATION_DOCUMENT) },
                    onOpenLegal = { navController.navigate(Routes.legal(it)) },
                    onOpenUrl = onOpenUrl,
                    onShowMessage = onShowMessage,
                )
            }

            composable(
                route = Routes.MATCH_PROFILE,
                arguments = listOf(navArgument("matchId") { type = NavType.StringType }),
            ) {
                MatchProfileScreen(
                    onBack = { navController.popBackStack() },
                    onOpenChat = { matchId ->
                        navController.navigate(Routes.chat(matchId, Routes.MATCHES))
                    },
                    onShowMessage = onShowMessage,
                )
            }

            composable(
                route = Routes.CHAT,
                arguments = listOf(
                    navArgument("matchId") { type = NavType.StringType },
                    navArgument("origin") {
                        type = NavType.StringType
                        defaultValue = Routes.CHATS
                    },
                ),
            ) {
                ChatScreen(
                    onBack = { navController.popBackStack() },
                    onShowMessage = onShowMessage,
                )
            }


            composable(Routes.VERIFICATION) {
                VerificationScreen(
                    // Auch bei einem bereits freigeschalteten Konto (Bestands-
                    // konto, das sich freiwillig verifiziert) folgt auf das
                    // Selfie der Ausweisschritt.
                    onFinished = {
                        navController.navigate(Routes.VERIFICATION_DOCUMENT) {
                            popUpTo(Routes.ACCOUNT)
                        }
                    },
                    onBack = { navController.popBackStack(Routes.ACCOUNT, inclusive = false) },
                    onShowMessage = onShowMessage,
                )
            }

            composable(Routes.VERIFICATION_DOCUMENT) {
                DocumentScreen(
                    onBack = { navController.popBackStack() },
                    onSubmitted = { navController.popBackStack(Routes.ACCOUNT, inclusive = false) },
                    onShowMessage = onShowMessage,
                )
            }

            legalDestination(navController)
        }
    }
}

/** Rechtstexte sind aus jedem Graphen erreichbar. */
private fun androidx.navigation.NavGraphBuilder.legalDestination(navController: NavHostController) {
    composable(
        route = Routes.LEGAL,
        arguments = listOf(navArgument("document") { type = NavType.StringType }),
    ) { entry ->
        val document = runCatching {
            LegalDocument.valueOf(entry.arguments?.getString("document").orEmpty())
        }.getOrDefault(LegalDocument.FAQ)

        LegalScreen(document = document, onBack = { navController.popBackStack() })
    }
}

/** Statusanzeige im Kopf: Abo aktiv, Resttage im Probemonat oder abgelaufen. */
@Composable
private fun MembershipPill(membership: Membership) {
    when {
        membership.isSubscribed -> StatusPill("Abo aktiv")
        membership.isActive -> StatusPill("Testmonat: ${ServerTime.daysUntil(membership.trialEndsAt)}d")
        else -> StatusPill("Abgelaufen", expired = true)
    }
}
