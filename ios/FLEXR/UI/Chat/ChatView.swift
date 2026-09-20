import SwiftUI

struct ChatView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let matchID: String
    let onBack: () -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var model: ChatModel?
    @State private var showReportDialog = false
    @State private var showBlockDialog = false
    @State private var showClearDialog = false
    @State private var showDeleteDialog = false

    var body: some View {
        Group {
            if let model {
                content(model)
            } else {
                LoadingStateView()
            }
        }
        .task {
            let created = model ?? ChatModel(
                matchID: matchID,
                container: container,
                languageStore: languageStore,
                onMessage: { appModel.show($0) },
                onStickyMessage: { appModel.showSticky($0) }
            )
            model = created
            await created.start()
        }
    }

    @ViewBuilder
    private func content(_ model: ChatModel) -> some View {
        @Bindable var model = model

        VStack(spacing: 0) {
            ChatHeader(
                profile: model.match?.profile,
                isOnline: model.match?.isOnline == true,
                onBack: onBack,
                onReport: { showReportDialog = true },
                onBlock: { showBlockDialog = true },
                onClearHistory: { showClearDialog = true },
                onDeleteChat: { showDeleteDialog = true }
            )

            messageList(model)

            if let until = model.mutedUntil {
                MuteBanner(
                    untilLabel: ServerTime.formatDateTime(until),
                    reason: model.muteReason,
                    appealHint: model.appealHint
                )
            } else if let notice = model.limitNotice {
                // Volles Chat-Kontingent. Bewusst ein stehender Hinweis und
                // keine Einblendung: Ohne freien Platz geht in diesem Chat
                // dauerhaft nichts raus — als kurz aufblitzende Meldung sieht
                // das aus wie ein Aussetzer und nicht wie eine Grenze.
                LimitBanner(text: notice)
            }

            ChatInputRow(
                draft: $model.draft,
                isEnabled: model.mutedUntil == nil,
                canSend: model.canSend,
                onInsertEmoji: model.insertEmoji,
                onSend: { Task { await model.send() } }
            )
            .padding(.bottom, 4)
        }
        .padding(.horizontal, 20)
        .onChange(of: model.isClosed) { _, isClosed in
            if isClosed { onBack() }
        }
        .sheet(isPresented: $showReportDialog) {
            ReportDialog(
                userName: model.match?.profile.name ?? "",
                onSubmit: { reason in
                    showReportDialog = false
                    model.report(reason: reason)
                },
                onDismiss: { showReportDialog = false }
            )
        }
        .confirmDialog(
            isPresented: $showBlockDialog,
            title: s(.reportBlockTitleNamed, model.match?.profile.name ?? ""),
            message: s(.chatBlockBody),
            confirmLabel: s(.commonBlock),
            onConfirm: model.block
        )
        .confirmDialog(
            isPresented: $showClearDialog,
            title: s(.chatClearTitle),
            message: s(.chatClearBody),
            confirmLabel: s(.chatClearConfirm),
            isDestructive: false,
            onConfirm: model.clearHistory
        )
        .confirmDialog(
            isPresented: $showDeleteDialog,
            title: s(.chatDeleteTitle),
            message: s(.chatDeleteBody),
            confirmLabel: s(.commonDelete),
            onConfirm: model.deleteChat
        )
    }

    @ViewBuilder
    private func messageList(_ model: ChatModel) -> some View {
        if model.messages.isEmpty, !model.isLoading, let fehler = model.loadError {
            // Ein Chat, der nicht geladen werden konnte, darf nicht aussehen
            // wie ein Chat, in dem noch nichts steht.
            EmptyStateView(
                icon: .symbol(FlexrIcon.chats),
                title: s(.swipeErrorTitle),
                message: fehler
            ) {
                FlexrSecondaryButton(title: s(.swipeRetry)) {
                    Task { await model.retryLoad() }
                }
                .frame(maxWidth: 220)
            }
            .frame(maxHeight: .infinity)
        } else if model.messages.isEmpty, !model.isLoading {
            EmptyStateView(
                icon: .symbol(FlexrIcon.send),
                title: s(.chatEmptyTitle),
                message: s(.chatEmptySub)
            )
            .frame(maxHeight: .infinity)
        } else {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 7) {
                        ForEach(model.messages) { message in
                            MessageBubble(
                                message: message,
                                isMine: message.senderID == model.ownUserID
                            )
                            .id(message.id)
                        }
                    }
                    .padding(.vertical, 8)
                }
                .scrollDismissesKeyboard(.interactively)
                .frame(maxHeight: .infinity)
                // Neue Nachricht: ans Ende scrollen. Die Tastatur schiebt sich
                // über den Verlauf, deshalb zusätzlich beim Fokuswechsel.
                .onChange(of: model.messages.count) { _, _ in
                    scrollToEnd(proxy, messages: model.messages)
                }
                .onAppear { scrollToEnd(proxy, messages: model.messages, animated: false) }
            }
        }
    }

    private func scrollToEnd(
        _ proxy: ScrollViewProxy,
        messages: [Message],
        animated: Bool = true
    ) {
        guard let last = messages.last else { return }
        if animated {
            withAnimation(.easeOut(duration: 0.2)) { proxy.scrollTo(last.id, anchor: .bottom) }
        } else {
            proxy.scrollTo(last.id, anchor: .bottom)
        }
    }
}

// MARK: - Kopfzeile

private struct ChatHeader: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let profile: Profile?
    let isOnline: Bool
    let onBack: () -> Void
    let onReport: () -> Void
    let onBlock: () -> Void
    let onClearHistory: () -> Void
    let onDeleteChat: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 0) {
                Button(action: onBack) {
                    Image(systemName: FlexrIcon.back)
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(FlexrColor.chalk)
                        .frame(width: 36, height: 36)
                }
                .buttonStyle(.plain)
                .accessibilityLabel(s(.commonBack))

                // Der Ring markiert „gerade online" — genau wie in der
                // Matches-/Chats-Übersicht (MatchListItem). Er stand hier
                // vorher unbedingt und zeigte damit fälschlich immer online.
                AvatarImage(
                    source: PhotoImageSource(profile?.primaryPhoto?.avatarURL),
                    name: profile?.name ?? "",
                    size: 42,
                    ringColor: isOnline ? FlexrColor.plateDim : nil,
                    ringWidth: 1.5
                )
                .padding(.leading, 6)

                HStack(spacing: 6) {
                    Text(profile.map { "\($0.name), \($0.age)" } ?? "")
                        .flexrText(.titleMedium)
                        .foregroundStyle(FlexrColor.chalk)
                        .lineLimit(1)
                    if profile?.isVerified == true { VerifiedBadge(size: 14) }
                    if profile?.isPremium == true { PremiumBadge(size: 14) }
                }
                .padding(.leading, 11)
                .frame(maxWidth: .infinity, alignment: .leading)

                // Melden und Blockieren stehen im Menü statt als eigene
                // Symbole in der Kopfzeile: zwei Symbole ohne Beschriftung
                // neben dem Namen waren nicht zu unterscheiden, und Platz für
                // den Namen nahmen sie auch weg.
                Menu {
                    Button {
                        onReport()
                    } label: {
                        Label(s(.commonReport), systemImage: FlexrIcon.report)
                    }
                    Button {
                        onBlock()
                    } label: {
                        Label(s(.commonBlock), systemImage: FlexrIcon.block)
                    }
                    Button(s(.chatClearAction), action: onClearHistory)
                    Button(s(.chatDeleteAction), role: .destructive, action: onDeleteChat)
                } label: {
                    Image(systemName: FlexrIcon.more)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(FlexrColor.chalkDim)
                        .frame(width: 34, height: 34)
                }
                .accessibilityLabel(s(.commonMoreOptions))
            }
            .padding(.vertical, 10)

            HairlineDivider()
        }
    }
}

// MARK: - Nachrichtenblase

private struct MessageBubble: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let message: Message
    let isMine: Bool

    private var bubbleShape: UnevenRoundedRectangle {
        UnevenRoundedRectangle(
            topLeadingRadius: 16,
            bottomLeadingRadius: isMine ? 16 : 5,
            bottomTrailingRadius: isMine ? 5 : 16,
            topTrailingRadius: 16,
            style: .continuous
        )
    }

    var body: some View {
        VStack(alignment: isMine ? .trailing : .leading, spacing: 3) {
            // Der Spacer ist das Maß, nicht `.frame(maxWidth:)`.
            //
            // `.frame(maxWidth: 300)` schrumpft nicht auf den Inhalt: Der
            // Rahmen nimmt, was ihm angeboten wird, bis zur Grenze — auf dem
            // Telefon also immer die vollen 300 pt, auch bei "test" oder
            // "bjj". Genau das war am 18.09.2026 zu sehen, und der zusätzliche
            // `Spacer(minLength: 0)` half nicht: Gegen einen Spacer, der bei 0
            // anfängt, setzt sich der gierige Rahmen durch.
            //
            // `Spacer(minLength: 56)` dreht das um. Der Blase bleibt die
            // Zeilenbreite minus 56 pt (auf dem Telefon rund 294 pt, also
            // dieselbe Obergrenze wie bisher), und darunter bestimmt sie ihre
            // Breite selbst — kurze Nachrichten werden wieder kurze Blasen.
            // Dasselbe Prinzip wie Androids `widthIn(max = …)` in einem
            // äußeren Row (siehe ChatScreen.kt).
            HStack(spacing: 0) {
                if isMine { Spacer(minLength: 56) }
                bubble
                if !isMine { Spacer(minLength: 56) }
            }

            // Zensur-Hinweis: der Absender erfährt, dass geschützt wurde, der
            // Empfänger den Grund für den Platzhalter.
            if message.wasCensored {
                Text(
                    isMine ? s(.chatCensoredOut) : s(.chatCensoredIn)
                )
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .padding(.horizontal, 4)
            }
        }
        .frame(maxWidth: .infinity, alignment: isMine ? .trailing : .leading)
    }

    /// Der eigentliche Blasen-Inhalt: Text und Zeitstempel mit fester
    /// Innenpolsterung.
    ///
    /// Bewusst **ohne** `.frame(maxWidth:)` — die Blase soll sich auf ihren
    /// Inhalt zusammenziehen. Die Obergrenze setzt der Spacer in `body`.
    private var bubble: some View {
        VStack(alignment: isMine ? .trailing : .leading, spacing: 4) {
            Text(message.content)
                .flexrText(.bodyMedium)
                .foregroundStyle(isMine ? Color(hex: 0x1C1006) : FlexrColor.chalk)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 5) {
                Text(ServerTime.formatTime(message.createdAt))
                    .flexrText(.mono)
                    .foregroundStyle(
                        (isMine ? Color(hex: 0x1C1006) : FlexrColor.chalkDim).opacity(0.6)
                    )
                if isMine {
                    Text(message.readAt != nil ? "✓✓" : "✓")
                        .flexrText(.mono)
                        .foregroundStyle(
                            message.readAt != nil
                                ? Color(hex: 0x1E5F74)
                                : Color(hex: 0x1C1006).opacity(0.6)
                        )
                }
            }
        }
        .padding(.horizontal, 13)
        .padding(.vertical, 9)
        .background {
            if isMine {
                bubbleShape.fill(
                    LinearGradient(
                        colors: [FlexrColor.plateBright, FlexrColor.plate],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
            } else {
                bubbleShape.fill(FlexrColor.surface2)
                bubbleShape.strokeBorder(FlexrColor.hairline, lineWidth: 1)
            }
        }
        .clipShape(bubbleShape)
    }
}

/// Hinweis bei befristeter Chat-Sperre („Abmahnung").
///
/// Art. 17 DSA verlangt zu jeder Beschränkung eine Begründung und den Hinweis
/// darauf, wie man dagegen vorgehen kann — beides steht deshalb im Banner.
private struct MuteBanner: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let untilLabel: String
    let reason: String?
    let appealHint: String?

    var body: some View {
        HStack(alignment: .top, spacing: 9) {
            Text("⚠️").flexrText(.bodyMedium)
            VStack(alignment: .leading, spacing: 6) {
                Text(s(.chatMutedBanner, untilLabel))
                .flexrText(.bodySmall)
                .foregroundStyle(Color(hex: 0xFFB3B3))

                if let reason, !reason.isEmpty {
                    Text(s(.chatMuteReason, reason))
                        .flexrText(.bodySmall)
                        .foregroundStyle(FlexrColor.chalk)
                }
                if let appealHint, !appealHint.isEmpty {
                    Text(appealHint)
                        .flexrText(.bodySmall)
                        .foregroundStyle(FlexrColor.chalkDim)
                }
            }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 11)
        .flexrSurface(
            fill: FlexrColor.danger.opacity(0.12),
            border: FlexrColor.danger.opacity(0.4)
        )
        .padding(.top, 12)
    }
}

/// Hinweis, wenn eine Grenze des kostenlosen Kontos das Senden verhindert
/// (derzeit: zu viele gleichzeitige Unterhaltungen).
///
/// Bewusst in Plate-Orange und nicht in Rot wie [MuteBanner]: Das hier ist
/// keine Maßnahme gegen den Nutzer, sondern eine Tarifgrenze. Der Wortlaut
/// kommt vom Server, damit die Zahl nicht an zwei Stellen gepflegt wird.
private struct LimitBanner: View {

    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 9) {
            FlexrGlyph(.symbol(FlexrIcon.premium), size: 14)
                .foregroundStyle(FlexrColor.plate)
            Text(text)
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalk)
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 11)
        .flexrSurface(
            fill: FlexrColor.plate.opacity(0.1),
            border: FlexrColor.plateDim
        )
        .padding(.top, 12)
    }
}

// MARK: - Eingabezeile

private struct ChatInputRow: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    @Binding var draft: String
    let isEnabled: Bool
    let canSend: Bool
    let onInsertEmoji: (String, NSRange) -> NSRange
    let onSend: () -> Void

    @State private var isEmojiOpen = false
    @State private var selection = NSRange(location: 0, length: 0)
    @State private var inputHeight: CGFloat = 22

    var body: some View {
        VStack(spacing: 0) {
            EmojiPickerPanel(isExpanded: isEmojiOpen && isEnabled) { emoji in
                selection = onInsertEmoji(emoji, selection)
            }
            .padding(.bottom, 8)

            HStack(alignment: .bottom, spacing: 4) {
                EmojiToggleButton(isExpanded: isEmojiOpen) {
                    guard isEnabled else { return }
                    withAnimation(.easeOut(duration: 0.18)) { isEmojiOpen.toggle() }
                }

                GrowingTextView(
                    text: $draft,
                    selection: $selection,
                    measuredHeight: $inputHeight,
                    font: FlexrFont.uiFont("WorkSans-Regular", size: 15, weight: 400),
                    placeholder: s(isEnabled ? .chatInputPlaceholder : .chatInputLocked),
                    isEnabled: isEnabled,
                    maxLength: ChatModel.maxLength,
                    maxLines: 5
                )
                .frame(height: max(inputHeight, 22))
                .padding(.vertical, 10)

                Button(action: onSend) {
                    Image(systemName: FlexrIcon.send)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(canSend ? Color.white : FlexrColor.chalkDim)
                        .frame(width: 40, height: 40)
                        .background(
                            Circle().fill(
                                canSend
                                    ? AnyShapeStyle(
                                        LinearGradient(
                                            colors: [FlexrColor.plateBright, FlexrColor.plate],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                    : AnyShapeStyle(FlexrColor.surface3)
                            )
                        )
                }
                .buttonStyle(.plain)
                .disabled(!canSend)
                .accessibilityLabel("Senden")
            }
            .padding(.leading, 6)
            .padding(.trailing, 5)
            .padding(.vertical, 5)
            .flexrSurface(radius: FlexrRadius.inputBar, border: FlexrColor.steel)
            .padding(.top, 8)
        }
    }
}
