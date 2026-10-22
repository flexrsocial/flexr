import SwiftUI

/// „Wer dich geliket hat" — eine Premium-Funktion.
///
/// Ohne Premium liefert der Server keine Fehlermeldung, sondern die Anzahl ohne
/// Profile (`premiumRequired`). Diese Unterscheidung bleibt bis in die
/// Oberfläche erhalten: „3 Leute warten auf dich" ist die ehrliche Antwort —
/// eine Fehlermeldung wäre es nicht. Wer ohne Abo hier landet, hat nichts
/// verloren; er sieht nur nicht, wer es ist.
///
/// Der Weg zum Angebot steht hier nur, wenn der Server diesem Client einen Kauf
/// überhaupt anbietet — in dieser App also über den App Store, und nur mit
/// eingetragener Produktkennung. Fehlt sie, bleibt es bei der Auskunft, ohne
/// Knopf und ohne Preis.
///
/// Seit 2.4.14 öffnet ein Tipp auf eine Zeile das Profil mit X und Herz: Der
/// Untertitel „Ansehen und zurückliken" versprach das schon länger, bis dahin
/// ging Zurückliken nur über das Deck. Ein Like hier ist immer ein Match.
struct IncomingView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let onBack: () -> Void
    let onOpenPremium: () -> Void
    let onOpenChat: (String) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var likes: IncomingLikes?
    @State private var isLoading = true
    @State private var error: String?

    /// Angetipptes Profil: Karte mit X und Herz statt der Liste.
    @State private var selected: Profile?
    /// Zurückgeliked — das Match-Overlay wie im Deck.
    @State private var matchedWith: Profile?
    @State private var isSwiping = false
    @State private var cardState = SwipeCardState()
    @State private var photoIndex = 0
    @State private var lightboxStartIndex: Int?
    @State private var showReportDialog = false
    @State private var showBlockDialog = false

    var body: some View {
        VStack(spacing: 0) {
            BackHeader(
                title: selected.map { "\($0.name), \($0.age)" } ?? s(.incomingHeadline),
                onBack: { if selected != nil { schliesseProfil() } else { onBack() } }
            )
            if let selected {
                profil(selected)
            } else {
                content
            }
        }
        .task { await load() }
        .fullScreenCover(isPresented: Binding(
            get: { lightboxStartIndex != nil },
            set: { if !$0 { lightboxStartIndex = nil } }
        )) {
            if let startIndex = lightboxStartIndex, let selected {
                PhotoLightbox(photos: selected.photos, startIndex: startIndex) { lastIndex in
                    photoIndex = lastIndex
                    lightboxStartIndex = nil
                }
            }
        }
        .sheet(isPresented: $showReportDialog) {
            if let selected {
                ReportDialog(
                    userName: selected.name,
                    onSubmit: { reason in
                        showReportDialog = false
                        report(selected, reason: reason)
                    },
                    onDismiss: { showReportDialog = false }
                )
            }
        }
        .confirmDialog(
            isPresented: $showBlockDialog,
            title: selected.map { s(.reportBlockTitleNamed, $0.name) } ?? s(.matchProfileBlockTitle),
            message: s(.swipeBlockBody),
            confirmLabel: s(.commonBlock),
            onConfirm: { if let selected { block(selected) } }
        )
        .overlay {
            if let matched = matchedWith {
                MatchOverlay(
                    matchedProfile: matched,
                    ownAvatarURL: container.profiles.myProfile?.ownAvatarURL,
                    ownName: s(.swipeOwnName),
                    onWriteMessage: { openChat(with: matched) },
                    onKeepSwiping: { matchedWith = nil }
                )
                .transition(.opacity)
            }
        }
        .animation(.easeOut(duration: 0.2), value: matchedWith?.id)
    }

    /// Das angetippte Profil: dieselbe Karte wie im Match-Profil (waagrecht
    /// gewischt blättert das Foto, Melden und Blockieren auf der Karte),
    /// darunter X und Herz wie im Deck. Die Knöpfe stehen unter der Karte
    /// statt darauf — so verdecken sie keine Bio.
    @ViewBuilder
    private func profil(_ profile: Profile) -> some View {
        VStack(spacing: 0) {
            SwipeableCard(
                profile: profile,
                state: cardState,
                onSwiped: { _ in },
                onOpenPhotos: { lightboxStartIndex = $0 },
                onReport: { showReportDialog = true },
                onBlock: { showBlockDialog = true },
                photoIndex: $photoIndex,
                isDraggable: false
            )
            .id(profile.id)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .padding(.top, 16)

            HStack(spacing: 22) {
                RoundActionButton(
                    icon: FlexrIcon.pass,
                    accessibilityLabel: s(.swipePass),
                    tint: FlexrColor.danger,
                    isEnabled: !isSwiping
                ) {
                    swipe(profile, like: false)
                }
                RoundActionButton(
                    icon: FlexrIcon.like,
                    accessibilityLabel: s(.swipeLike),
                    tint: .white,
                    isLarge: true,
                    isEnabled: !isSwiping
                ) {
                    swipe(profile, like: true)
                }
            }
            .padding(.vertical, 14)
        }
        .padding(.horizontal, 20)
    }

    @ViewBuilder
    private var content: some View {
        if isLoading {
            LoadingStateView(label: s(.incomingLoading))
        } else if let error {
            EmptyStateView(
                icon: .symbol(FlexrIcon.matches),
                title: s(.incomingHeadline),
                message: error
            ) {
                FlexrSecondaryButton(title: s(.swipeRetry)) {
                    Task { await load() }
                }
                .frame(maxWidth: 220)
            }
            .frame(maxHeight: .infinity)
        } else if let likes, likes.premiumRequired, likes.count > 0 {
            // Herz wie im Web: Hier warten Leute, das ist keine Sperre.
            EmptyStateView(
                icon: .symbol(FlexrIcon.matches),
                title: likes.count == 1
                    ? s(.incomingLockedTitleOne)
                    : s(.incomingLockedTitle, likes.count),
                message: s(.incomingLockedSub)
            ) {
                if appModel.membership?.storePurchaseAvailable == true {
                    FlexrButton(title: s(.premiumShowOffer), action: onOpenPremium)
                        .frame(maxWidth: 260)
                }
            }
            .frame(maxHeight: .infinity)
        } else if let likes, !likes.profiles.isEmpty {
            ScrollView {
                LazyVStack(spacing: 10) {
                    ForEach(likes.profiles) { profile in
                        Button {
                            photoIndex = 0
                            selected = profile
                        } label: {
                            IncomingProfileRow(profile: profile)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.top, 16)
                .padding(.bottom, 12)
            }
            .refreshable { await load() }
        } else {
            EmptyStateView(
                icon: .symbol(FlexrIcon.matches),
                title: s(.incomingHeadline),
                message: s(.incomingNone)
            )
            .frame(maxHeight: .infinity)
        }
    }

    private func load() async {
        isLoading = true
        error = nil
        do {
            likes = try await container.swipes.incomingLikes()
        } catch {
            self.error = (error as? FlexrAPIError)?.message ?? s(.incomingLoadFailed)
        }
        isLoading = false
    }

    private func schliesseProfil() {
        selected = nil
        cardState.reset()
    }

    /// Aus der Liste nehmen — nach Like, Pass, Meldung oder Blockierung. Das
    /// Deck nimmt die Person beim nächsten Erscheinen ebenfalls heraus.
    private func entferne(_ profile: Profile) {
        container.swipes.alsErledigtMerken(profile.id)
        if let current = likes {
            likes = IncomingLikes(
                count: max(current.count - 1, 0),
                profiles: current.profiles.filter { $0.id != profile.id },
                premiumRequired: current.premiumRequired
            )
        }
        schliesseProfil()
    }

    private func swipe(_ profile: Profile, like: Bool) {
        guard !isSwiping else { return }
        isSwiping = true
        Task {
            do {
                let outcome = like
                    ? try await container.swipes.like(userID: profile.id)
                    : try await container.swipes.pass(userID: profile.id)
                container.billing.updateLikesRemaining(outcome.likesRemaining)
                entferne(profile)
                if outcome.matched {
                    matchedWith = profile
                    _ = try? await container.matches.refresh()
                }
            } catch {
                // Etwa das aufgebrauchte Like-Kontingent: Die Karte bleibt offen.
                appModel.show((error as? FlexrAPIError)?.message ?? s(.swipeFailed))
            }
            isSwiping = false
        }
    }

    /// „Nachricht schreiben" aus dem Match-Overlay heraus.
    private func openChat(with profile: Profile) {
        matchedWith = nil
        Task {
            let refreshed = (try? await container.matches.refresh()) ?? container.matches.matches
            if let match = refreshed.first(where: { $0.profile.id == profile.id }) {
                onOpenChat(match.matchID)
            } else {
                appModel.show(s(.chatOpenFailed))
            }
        }
    }

    private func report(_ profile: Profile, reason: String) {
        Task {
            do {
                // Empfangsbestätigung mit Aktenzeichen (Art. 16 Abs. 4 DSA).
                // Der Server lässt die Person danach aus den offenen Likes weg.
                let ack = try await container.safety.report(userID: profile.id, reason: reason)
                entferne(profile)
                appModel.showSticky(ack.message)
            } catch {
                appModel.show(error.localizedDescription)
            }
        }
    }

    private func block(_ profile: Profile) {
        Task {
            do {
                try await container.safety.block(userID: profile.id)
                entferne(profile)
                appModel.show(s(.blockDone, profile.name))
            } catch {
                appModel.show(error.localizedDescription)
            }
        }
    }
}

/// Eine Zeile der Liste — dieselbe Form wie `MatchListItem`, damit die Ansicht
/// nicht wie ein fremder Teil der App wirkt. Ein Tipp öffnet das Profil mit X
/// und Herz (bis 2.4.13 ohne Tippziel).
private struct IncomingProfileRow: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let profile: Profile

    private var secondaryLine: String {
        [profile.city, profile.gymName]
            .filter { !$0.isEmpty }
            .joined(separator: " · ")
    }

    var body: some View {
        HStack(spacing: 13) {
            AvatarImage(
                source: PhotoImageSource(profile.primaryPhoto?.avatarURL),
                name: profile.name,
                size: 54,
                accessibilityLabel: s(.commonProfilePhotoOf, profile.name)
            )

            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text("\(profile.name), \(profile.age)")
                        .flexrText(.titleMedium)
                        .foregroundStyle(FlexrColor.chalk)
                        .lineLimit(1)
                    if profile.isVerified { VerifiedBadge(size: 14) }
                    if profile.isPremium { PremiumBadge(size: 14) }
                }
                Text(secondaryLine)
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            Image(systemName: FlexrIcon.forward)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(FlexrColor.chalkDim.opacity(0.6))
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .flexrSurface(radius: FlexrRadius.medium, fill: FlexrColor.surface, border: FlexrColor.hairline)
    }
}
