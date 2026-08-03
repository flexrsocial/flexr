import SwiftUI

struct ChatView: View {

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
                onMessage: { appModel.show($0) }
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
            title: "\(model.match?.profile.name ?? "") blockieren?",
            message: "Ihr seht euch danach nicht mehr. Das Match und der Chat verschwinden.",
            confirmLabel: "Blockieren",
            onConfirm: model.block
        )
        .confirmDialog(
            isPresented: $showClearDialog,
            title: "Chatverlauf leeren?",
            message: "Der Verlauf wird nur für dich ausgeblendet — die andere Person sieht ihn weiterhin.",
            confirmLabel: "Leeren",
            isDestructive: false,
            onConfirm: model.clearHistory
        )
        .confirmDialog(
            isPresented: $showDeleteDialog,
            title: "Chat löschen?",
            message: "Das Match und der gesamte Verlauf werden entfernt. "
                + "Die Person kann dir danach erneut im Deck begegnen.",
            confirmLabel: "Löschen",
            onConfirm: model.deleteChat
        )
    }

    @ViewBuilder
    private func messageList(_ model: ChatModel) -> some View {
        if model.messages.isEmpty, !model.isLoading {
            EmptyStateView(
                icon: .symbol(FlexrIcon.send),
                title: "Noch keine Nachrichten",
                message: "Schreib die erste — ihr habt schließlich gematcht."
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

    let profile: Profile?
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
                .accessibilityLabel("Zurück")

                AvatarImage(
                    source: PhotoImageSource(profile?.primaryPhoto?.avatarURL),
                    name: profile?.name ?? "",
                    size: 42,
                    ringColor: FlexrColor.plateDim,
                    ringWidth: 1.5
                )
                .padding(.leading, 6)

                HStack(spacing: 6) {
                    Text(profile.map { "\($0.name), \($0.age)" } ?? "")
                        .flexrText(.titleMedium)
                        .foregroundStyle(FlexrColor.chalk)
                        .lineLimit(1)
                    if profile?.isVerified == true { VerifiedBadge(size: 14) }
                }
                .padding(.leading, 11)
                .frame(maxWidth: .infinity, alignment: .leading)

                Button(action: onReport) {
                    Image(systemName: FlexrIcon.report)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundStyle(FlexrColor.chalkDim)
                        .frame(width: 34, height: 34)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Melden")

                Button(action: onBlock) {
                    Image(systemName: FlexrIcon.block)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundStyle(FlexrColor.chalkDim)
                        .frame(width: 34, height: 34)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Blockieren")

                Menu {
                    Button("Chatverlauf leeren", action: onClearHistory)
                    Button("Chat löschen", role: .destructive, action: onDeleteChat)
                } label: {
                    Image(systemName: FlexrIcon.more)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(FlexrColor.chalkDim)
                        .frame(width: 34, height: 34)
                }
                .accessibilityLabel("Weitere Optionen")
            }
            .padding(.vertical, 10)

            HairlineDivider()
        }
    }
}

// MARK: - Nachrichtenblase

private struct MessageBubble: View {

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
            VStack(alignment: isMine ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .flexrText(.bodyMedium)
                    .foregroundStyle(isMine ? Color(hex: 0x1C1006) : FlexrColor.chalk)
                    .frame(maxWidth: .infinity, alignment: isMine ? .trailing : .leading)

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
            .frame(maxWidth: 300, alignment: isMine ? .trailing : .leading)
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

            // Zensur-Hinweis: der Absender erfährt, dass geschützt wurde, der
            // Empfänger den Grund für den Platzhalter.
            if message.wasCensored {
                Text(
                    isMine
                        ? "🔒 Zum Schutz zensiert — der Empfänger sieht keine Links/Kontaktdaten."
                        : "🔒 Ein Link oder Kontaktdaten wurden zu deinem Schutz entfernt."
                )
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .padding(.horizontal, 4)
            }
        }
        .frame(maxWidth: .infinity, alignment: isMine ? .trailing : .leading)
    }
}

/// Hinweis bei befristeter Chat-Sperre („Abmahnung").
///
/// Art. 17 DSA verlangt zu jeder Beschränkung eine Begründung und den Hinweis
/// darauf, wie man dagegen vorgehen kann — beides steht deshalb im Banner.
private struct MuteBanner: View {

    let untilLabel: String
    let reason: String?
    let appealHint: String?

    var body: some View {
        HStack(alignment: .top, spacing: 9) {
            Text("⚠️").flexrText(.bodyMedium)
            VStack(alignment: .leading, spacing: 6) {
                Text(
                    "Deine Chat-Funktion ist vorübergehend gesperrt. Du kannst bis "
                        + "\(untilLabel) Uhr keine Nachrichten senden."
                )
                .flexrText(.bodySmall)
                .foregroundStyle(Color(hex: 0xFFB3B3))

                if let reason, !reason.isEmpty {
                    Text("Grund: \(reason)")
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

// MARK: - Eingabezeile

private struct ChatInputRow: View {

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
                    placeholder: isEnabled ? "Nachricht schreiben…" : "Chat vorübergehend gesperrt",
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
