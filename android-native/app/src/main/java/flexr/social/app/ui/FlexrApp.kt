package flexr.social.app.ui

import android.net.Uri
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
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
import flexr.social.app.ui.verification.VerificationScreen
import kotlinx.coroutines.launch

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
    viewModel: MainViewModel = hiltViewModel(),
) {
    val appState by viewModel.appState.collectAsStateWithLifecycle()
    val unreadCount by viewModel.unreadCount.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    val showMessage: (String) -> Unit = { message ->
        scope.launch { snackbarHostState.showSnackbar(message) }
    }

    // Rückkehr aus dem Stripe-Checkout im Browser: Abo-Status neu holen.
    LifecycleEventEffect(Lifecycle.Event.ON_RESUME) {
        if (appState is AppState.Locked) viewModel.refreshMembership()
    }
    LaunchedEffect(intentData) {
        if (intentData?.scheme == "flexr") viewModel.refreshMembership()
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
                )
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
        snackbarHost = { SnackbarHost(snackbarHostState) },
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
        snackbarHost = { SnackbarHost(snackbarHostState) },
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
) {
    val navController = rememberNavController()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route
    val isTopLevel = TopLevelDestination.entries.any { it.route == currentRoute }

    Scaffold(
        containerColor = Color.Transparent,
        snackbarHost = { SnackbarHost(snackbarHostState) },
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
                    onBack = { navController.popBackStack() },
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
