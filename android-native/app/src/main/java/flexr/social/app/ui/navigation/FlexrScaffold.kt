package flexr.social.app.ui.navigation

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import flexr.social.app.core.designsystem.theme.BrandStyle
import flexr.social.app.core.designsystem.theme.FlexrPalette
import flexr.social.app.core.designsystem.theme.FlexrTheme

/**
 * Wortmarke im Kopfbereich. Gesetzt nach der verbindlichen Markenvorgabe
 * (frontend/brand/README.md): „FLEX" in Kreideweiß, das „R" in Signalrot.
 */
@Composable
fun FlexrWordmark(modifier: Modifier = Modifier) {
    val text: AnnotatedString = buildAnnotatedString {
        withStyle(SpanStyle(color = FlexrTheme.colors.chalk)) { append("FLEX") }
        withStyle(SpanStyle(color = FlexrPalette.BrandRed)) { append("R") }
    }
    Text(text = text, style = BrandStyle, modifier = modifier)
}

/** Kopfzeile: Wortmarke links, Mitgliedschafts-Status rechts. */
@Composable
fun FlexrTopBar(
    statusSlot: @Composable () -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .windowInsetsPadding(WindowInsets.statusBars)
                .padding(start = 20.dp, end = 20.dp, top = 14.dp, bottom = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            FlexrWordmark()
            statusSlot()
        }
        Box(
            Modifier
                .align(Alignment.BottomStart)
                .fillMaxWidth()
                .height(1.dp)
                .background(FlexrTheme.colors.hairline),
        )
        // Akzentstrich links unter der Kopfzeile, wie im Web (header.top::after)
        Box(
            Modifier
                .align(Alignment.BottomStart)
                .padding(start = 20.dp)
                .size(width = 64.dp, height = 2.dp)
                .background(FlexrTheme.colors.plate),
        )
    }
}

/** Untere Hauptnavigation mit Ungelesen-Zähler am Chat-Symbol. */
@Composable
fun FlexrBottomBar(
    currentRoute: String?,
    unreadCount: Int,
    onNavigate: (TopLevelDestination) -> Unit,
    modifier: Modifier = Modifier,
) {
    NavigationBar(
        modifier = modifier,
        containerColor = MaterialTheme.colorScheme.background.copy(alpha = 0.96f),
        tonalElevation = 0.dp,
    ) {
        TopLevelDestination.entries.forEach { destination ->
            val selected = currentRoute == destination.route
            NavigationBarItem(
                selected = selected,
                onClick = { onNavigate(destination) },
                icon = {
                    if (destination == TopLevelDestination.CHATS && unreadCount > 0) {
                        BadgedBox(
                            badge = {
                                Badge(
                                    containerColor = FlexrTheme.colors.plate,
                                    contentColor = FlexrTheme.colors.plateInk,
                                ) { Text(if (unreadCount > 99) "99+" else "$unreadCount") }
                            },
                        ) {
                            Icon(destination.icon, contentDescription = null, modifier = Modifier.size(22.dp))
                        }
                    } else {
                        Icon(destination.icon, contentDescription = null, modifier = Modifier.size(22.dp))
                    }
                },
                label = {
                    Text(
                        destination.label.uppercase(),
                        style = MaterialTheme.typography.labelSmall,
                    )
                },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = FlexrTheme.colors.plate,
                    selectedTextColor = FlexrTheme.colors.plate,
                    unselectedIconColor = FlexrTheme.colors.chalkDim,
                    unselectedTextColor = FlexrTheme.colors.chalkDim,
                    indicatorColor = FlexrTheme.colors.plate.copy(alpha = 0.12f),
                ),
            )
        }
    }
}
