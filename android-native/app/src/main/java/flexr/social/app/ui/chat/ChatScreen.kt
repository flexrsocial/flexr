package flexr.social.app.ui.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.ime
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.union
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import flexr.social.app.core.common.ServerTime
import flexr.social.app.core.designsystem.component.EmptyState
import flexr.social.app.core.designsystem.component.VerifiedBadge
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.core.designsystem.theme.MonoStyle
import flexr.social.app.domain.model.Message
import flexr.social.app.ui.components.ConfirmDialog
import flexr.social.app.ui.components.ReportDialog

@Composable
fun ChatScreen(
    onBack: () -> Unit,
    onShowMessage: (String) -> Unit,
    viewModel: ChatViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val messages by viewModel.messages.collectAsStateWithLifecycle()
    val match by viewModel.match.collectAsStateWithLifecycle()
    val ownUserId by viewModel.ownUserId.collectAsStateWithLifecycle()

    val listState = rememberLazyListState()
    var showMenu by remember { mutableStateOf(false) }
    var showReportDialog by remember { mutableStateOf(false) }
    var showBlockDialog by remember { mutableStateOf(false) }
    var showClearDialog by remember { mutableStateOf(false) }
    var showDeleteDialog by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is ChatEvent.Message -> onShowMessage(event.text)
                ChatEvent.Closed -> onBack()
            }
        }
    }

    // Neue Nachricht: ans Ende scrollen.
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) listState.animateScrollToItem(messages.lastIndex)
    }

    // Die Tastatur schiebt sich über den Verlauf. Solange sie einfährt, den
    // Verlauf pro Frame ans Ende nachziehen — sonst bliebe die letzte Nachricht
    // hinter der Tastatur stehen.
    val density = LocalDensity.current
    val imeInsets = WindowInsets.ime
    LaunchedEffect(listState) {
        snapshotFlow { imeInsets.getBottom(density) }
            .collect { imeBottom ->
                val lastIndex = listState.layoutInfo.totalItemsCount - 1
                if (imeBottom > 0 && lastIndex >= 0) listState.scrollToItem(lastIndex)
            }
    }

    Column(
        Modifier
            .fillMaxSize()
            // Nicht imePadding() + navigationBarsPadding(): die beiden Insets
            // würden sich addieren, obwohl die Navigationsleiste bei offener
            // Tastatur hinter ihr liegt. union() nimmt das größere von beiden.
            .windowInsetsPadding(WindowInsets.ime.union(WindowInsets.navigationBars))
            .padding(horizontal = 20.dp),
    ) {
        ChatHeader(
            name = match?.profile?.name,
            age = match?.profile?.age,
            isVerified = match?.profile?.isVerified == true,
            avatarUrl = match?.profile?.primaryPhoto?.avatarUrl,
            onBack = onBack,
            onReport = { showReportDialog = true },
            onBlock = { showBlockDialog = true },
            menuExpanded = showMenu,
            onMenuToggle = { showMenu = !showMenu },
            onClearHistory = {
                showMenu = false
                showClearDialog = true
            },
            onDeleteChat = {
                showMenu = false
                showDeleteDialog = true
            },
        )

        Box(Modifier.fillMaxWidth().weight(1f)) {
            if (messages.isEmpty() && !state.isLoading) {
                EmptyState(
                    icon = FlexrIcons.Send,
                    title = "Noch keine Nachrichten",
                    description = "Schreib die erste — ihr habt schließlich gematcht.",
                )
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(7.dp),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(vertical = 8.dp),
                ) {
                    items(messages, key = { it.id }) { message ->
                        MessageBubble(message = message, isMine = message.senderId == ownUserId)
                    }
                }
            }
        }

        state.mutedUntil?.let { until ->
            MuteBanner(untilLabel = ServerTime.formatDateTime(until))
        }

        ChatInputRow(
            value = state.draft,
            enabled = state.mutedUntil == null,
            onValueChange = viewModel::onDraftChange,
            onSend = viewModel::send,
        )
        Spacer(Modifier.height(4.dp))
    }

    if (showReportDialog) {
        ReportDialog(
            userName = match?.profile?.name.orEmpty(),
            onSubmit = {
                showReportDialog = false
                viewModel.report(it)
            },
            onDismiss = { showReportDialog = false },
        )
    }
    if (showBlockDialog) {
        ConfirmDialog(
            title = "${match?.profile?.name.orEmpty()} blockieren?",
            text = "Ihr seht euch danach nicht mehr. Das Match und der Chat verschwinden.",
            confirmLabel = "Blockieren",
            onConfirm = {
                showBlockDialog = false
                viewModel.block()
            },
            onDismiss = { showBlockDialog = false },
        )
    }
    if (showClearDialog) {
        ConfirmDialog(
            title = "Chatverlauf leeren?",
            text = "Der Verlauf wird nur für dich ausgeblendet — die andere Person sieht ihn weiterhin.",
            confirmLabel = "Leeren",
            destructive = false,
            onConfirm = {
                showClearDialog = false
                viewModel.clearHistory()
            },
            onDismiss = { showClearDialog = false },
        )
    }
    if (showDeleteDialog) {
        ConfirmDialog(
            title = "Chat löschen?",
            text = "Das Match und der gesamte Verlauf werden entfernt. " +
                "Die Person kann dir danach erneut im Deck begegnen.",
            confirmLabel = "Löschen",
            onConfirm = {
                showDeleteDialog = false
                viewModel.deleteChat()
            },
            onDismiss = { showDeleteDialog = false },
        )
    }
}

@Composable
private fun ChatHeader(
    name: String?,
    age: Int?,
    isVerified: Boolean,
    avatarUrl: String?,
    onBack: () -> Unit,
    onReport: () -> Unit,
    onBlock: () -> Unit,
    menuExpanded: Boolean,
    onMenuToggle: () -> Unit,
    onClearHistory: () -> Unit,
    onDeleteChat: () -> Unit,
) {
    val colors = FlexrTheme.colors
    Column {
        Row(
            Modifier.fillMaxWidth().padding(vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack, modifier = Modifier.size(36.dp)) {
                Icon(FlexrIcons.Back, contentDescription = "Zurück", tint = colors.chalk)
            }
            Spacer(Modifier.width(6.dp))
            AsyncImage(
                model = avatarUrl,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .size(42.dp)
                    .clip(CircleShape)
                    .background(colors.surface2)
                    .border(1.5.dp, colors.plateDim, CircleShape),
            )
            Spacer(Modifier.width(11.dp))
            Row(Modifier.weight(1f), verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = if (name != null && age != null) "$name, $age" else name.orEmpty(),
                    style = MaterialTheme.typography.titleMedium,
                    color = colors.chalk,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                if (isVerified) {
                    Spacer(Modifier.width(6.dp))
                    VerifiedBadge(size = 14)
                }
            }
            IconButton(onClick = onReport, modifier = Modifier.size(34.dp)) {
                Icon(
                    FlexrIcons.Report,
                    contentDescription = "Melden",
                    tint = colors.chalkDim,
                    modifier = Modifier.size(17.dp),
                )
            }
            IconButton(onClick = onBlock, modifier = Modifier.size(34.dp)) {
                Icon(
                    FlexrIcons.Block,
                    contentDescription = "Blockieren",
                    tint = colors.chalkDim,
                    modifier = Modifier.size(17.dp),
                )
            }
            Box {
                IconButton(onClick = onMenuToggle, modifier = Modifier.size(34.dp)) {
                    Icon(
                        FlexrIcons.More,
                        contentDescription = "Weitere Optionen",
                        tint = colors.chalkDim,
                        modifier = Modifier.size(17.dp),
                    )
                }
                DropdownMenu(
                    expanded = menuExpanded,
                    onDismissRequest = onMenuToggle,
                    containerColor = colors.surface2,
                ) {
                    DropdownMenuItem(
                        text = { Text("Chatverlauf leeren", color = colors.chalk) },
                        onClick = onClearHistory,
                    )
                    DropdownMenuItem(
                        text = { Text("Chat löschen", color = colors.danger) },
                        onClick = onDeleteChat,
                    )
                }
            }
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(colors.hairline))
    }
}

@Composable
private fun MessageBubble(message: Message, isMine: Boolean) {
    val colors = FlexrTheme.colors
    Column(
        Modifier.fillMaxWidth(),
        horizontalAlignment = if (isMine) Alignment.End else Alignment.Start,
    ) {
        Column(
            Modifier
                .widthIn(max = 300.dp)
                .clip(
                    if (isMine) RoundedCornerShape(16.dp, 16.dp, 5.dp, 16.dp)
                    else RoundedCornerShape(16.dp, 16.dp, 16.dp, 5.dp),
                )
                .then(
                    if (isMine) {
                        Modifier.background(
                            Brush.linearGradient(listOf(colors.plateBright, colors.plate)),
                        )
                    } else {
                        Modifier
                            .background(colors.surface2)
                            .border(
                                1.dp,
                                colors.hairline,
                                RoundedCornerShape(16.dp, 16.dp, 16.dp, 5.dp),
                            )
                    },
                )
                .padding(horizontal = 13.dp, vertical = 9.dp),
        ) {
            Text(
                text = message.content,
                style = MaterialTheme.typography.bodyMedium,
                color = if (isMine) Color(0xFF1C1006) else colors.chalk,
            )
            Row(
                Modifier.align(if (isMine) Alignment.End else Alignment.Start).padding(top = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = ServerTime.formatTime(message.createdAt),
                    style = MonoStyle,
                    color = (if (isMine) Color(0xFF1C1006) else colors.chalkDim).copy(alpha = 0.6f),
                )
                if (isMine) {
                    Spacer(Modifier.width(5.dp))
                    Text(
                        text = if (message.readAt != null) "✓✓" else "✓",
                        style = MonoStyle,
                        color = if (message.readAt != null) Color(0xFF1E5F74)
                        else Color(0xFF1C1006).copy(alpha = 0.6f),
                    )
                }
            }
        }
        // Zensur-Hinweis: der Absender erfährt, dass geschützt wurde, der
        // Empfänger den Grund für den Platzhalter.
        if (message.wasCensored) {
            Text(
                text = if (isMine) {
                    "🔒 Zum Schutz zensiert — der Empfänger sieht keine Links/Kontaktdaten."
                } else {
                    "🔒 Ein Link oder Kontaktdaten wurden zu deinem Schutz entfernt."
                },
                style = MaterialTheme.typography.bodySmall,
                color = colors.chalkDim,
                modifier = Modifier.padding(top = 3.dp, start = 4.dp, end = 4.dp),
            )
        }
    }
}

/** Hinweis bei befristeter Chat-Sperre („Abmahnung"). */
@Composable
private fun MuteBanner(untilLabel: String) {
    val colors = FlexrTheme.colors
    Row(
        Modifier
            .fillMaxWidth()
            .padding(top = 12.dp)
            .clip(MaterialTheme.shapes.medium)
            .background(colors.danger.copy(alpha = 0.12f))
            .border(1.dp, colors.danger.copy(alpha = 0.4f), MaterialTheme.shapes.medium)
            .padding(horizontal = 14.dp, vertical = 11.dp),
        horizontalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        Text("⚠️", style = MaterialTheme.typography.bodyMedium)
        Text(
            text = "Deine Chat-Funktion ist vorübergehend gesperrt. Du kannst bis " +
                "$untilLabel Uhr keine Nachrichten senden. Bitte halte dich an unsere " +
                "Community-Regeln.",
            style = MaterialTheme.typography.bodySmall,
            color = Color(0xFFFFB3B3),
        )
    }
}

@Composable
private fun ChatInputRow(
    value: String,
    enabled: Boolean,
    onValueChange: (String) -> Unit,
    onSend: () -> Unit,
) {
    val colors = FlexrTheme.colors
    Row(
        Modifier
            .fillMaxWidth()
            .padding(top = 8.dp)
            .clip(RoundedCornerShape(26.dp))
            .background(MaterialTheme.colorScheme.surface)
            .border(1.dp, colors.steel, RoundedCornerShape(26.dp))
            .padding(start = 16.dp, end = 5.dp, top = 5.dp, bottom = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        BasicTextField(
            value = value,
            onValueChange = onValueChange,
            enabled = enabled,
            modifier = Modifier.weight(1f).padding(vertical = 10.dp),
            textStyle = MaterialTheme.typography.bodyLarge.copy(color = colors.chalk),
            cursorBrush = SolidColor(colors.plate),
            maxLines = 5,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
            keyboardActions = KeyboardActions(onSend = { onSend() }),
            decorationBox = { inner ->
                if (value.isEmpty()) {
                    Text(
                        text = if (enabled) "Nachricht schreiben…" else "Chat vorübergehend gesperrt",
                        style = MaterialTheme.typography.bodyLarge,
                        color = colors.chalkDim,
                    )
                }
                inner()
            },
        )
        Spacer(Modifier.width(6.dp))
        Box(
            Modifier
                .size(40.dp)
                .clip(CircleShape)
                .background(
                    if (enabled && value.isNotBlank()) {
                        Brush.linearGradient(listOf(colors.plateBright, colors.plate))
                    } else {
                        Brush.linearGradient(listOf(colors.surface3, colors.surface3))
                    },
                ),
            contentAlignment = Alignment.Center,
        ) {
            IconButton(onClick = onSend, enabled = enabled && value.isNotBlank()) {
                Icon(
                    FlexrIcons.Send,
                    contentDescription = "Senden",
                    tint = if (enabled && value.isNotBlank()) Color.White else colors.chalkDim,
                    modifier = Modifier.size(18.dp),
                )
            }
        }
    }
}
