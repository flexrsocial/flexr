import SwiftUI

struct SwipeView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    /// Gehört `MainFlow`, nicht diesem Bildschirm: Die Tab-Leiste baut den
    /// Bildschirm bei jedem Wechsel neu auf. Mit eigenem `@State` stand nach
    /// jeder Rückkehr wieder „Lade Profile …" da, das Deck kam neu vom Server
    /// und die Karte sprang aufs erste Foto (im Web am 15.10.2026 behoben).
    @Binding var model: SwipeModel?
    let onOpenChat: (String) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var cardState = SwipeCardState()
    @State private var lightboxStartIndex: Int?
    @State private var showReportDialog = false
    @State private var showBlockDialog = false
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        Group {
            if let model {
                content(model)
            } else {
                LoadingStateView(label: s(.swipeLoading))
            }
        }
        .task {
            if let model {
                model.bereinigeDeck()
                // Zurück aus einem anderen Tab: Karte und Foto bleiben stehen.
                // Neu geladen wird nur, was sich inzwischen geändert haben
                // kann - Umkreis oder Gym im Konto-Tab, oder ein leeres Deck,
                // in dem seither neue Profile liegen können.
                if model.loadedCriteria != suchkriterien || model.isExhausted {
                    neuLaden(model)
                }
                return
            }
            let created = SwipeModel(
                container: container,
                languageStore: languageStore,
                onMessage: { appModel.show($0) },
                onStickyMessage: { appModel.showSticky($0) },
                onOpenChat: onOpenChat
            )
            created.loadedCriteria = suchkriterien
            model = created
            await created.loadProfileAndDeck()
        }
        // Wer im Konto den Umkreis oder das Gym ändert, während dieser
        // Bildschirm steht (etwa über den Hinweis über dem Deck), bekommt das
        // neue Deck sofort. Neben dem Radius zählt das Gym mit - es ist der
        // Mittelpunkt der Suche.
        .onChange(of: suchkriterien) {
            guard let model else { return }
            neuLaden(model)
        }
        // Zurück in die App: ob inzwischen ein Foto freigegeben ist,
        // entscheidet über den Hinweis über dem Deck.
        .onChange(of: scenePhase) { _, phase in
            guard phase == .active else { return }
            Task { _ = try? await container.profiles.refresh() }
        }
    }

    private func neuLaden(_ model: SwipeModel) {
        model.loadedCriteria = suchkriterien
        if let profil = container.profiles.myProfile {
            model.searchRadiusKm = profil.searchRadiusKm
            model.ownAvatarURL = profil.ownAvatarURL
        }
        model.photoIndex = 0
        Task { await model.loadDeck() }
    }

    /// Die Merkmale, die bestimmen, wen das Deck zeigt.
    private var suchkriterien: String {
        guard let profil = container.profiles.myProfile else { return "" }
        return "\(profil.searchRadiusKm)|\(profil.profile.gym)"
    }

    @ViewBuilder
    private func content(_ model: SwipeModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            ScreenHeader(eyebrow: s(.swipeEyebrow), title: s(.swipeTitle))
                .padding(.top, 18)

            Text(locationLabel(model).uppercased())
                .flexrText(.mono)
                .foregroundStyle(FlexrColor.chalkDim)
                .padding(.top, 8)

            // Solange kein eigenes Foto freigegeben ist, erscheint man in
            // keinem fremden Deck - bis 14.10.2026 erfuhr man das nur klein
            // unter dem Fotoraster im Konto.
            if let profil = container.profiles.myProfile, profil.isAccountActivated,
               profil.photoVisibility != .visible {
                SearchVisibilityBanner(visibility: profil.photoVisibility, compact: true) {
                    appModel.scrollToOwnPhotos = true
                    appModel.selectedTab = .account
                }
                .padding(.top, 14)
            }

            deck(model)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding(.top, 16)
        }
        .padding(.horizontal, 20)
        .fullScreenCover(isPresented: Binding(
            get: { lightboxStartIndex != nil },
            set: { if !$0 { lightboxStartIndex = nil } }
        )) {
            if let startIndex = lightboxStartIndex, let profile = model.current {
                // Nach dem Schließen zeigt die Karte das zuletzt betrachtete Foto.
                PhotoLightbox(photos: profile.photos, startIndex: startIndex) { lastIndex in
                    model.photoIndex = lastIndex
                    lightboxStartIndex = nil
                }
            }
        }
        .sheet(isPresented: $showReportDialog) {
            if let profile = model.current {
                ReportDialog(
                    userName: profile.name,
                    onSubmit: { reason in
                        showReportDialog = false
                        model.report(userID: profile.id, reason: reason)
                    },
                    onDismiss: { showReportDialog = false }
                )
            }
        }
        .confirmDialog(
            isPresented: $showBlockDialog,
            title: model.current.map { s(.reportBlockTitleNamed, $0.name) } ?? s(.swipeBlockTitle),
            message: s(.swipeBlockBody),
            confirmLabel: s(.commonBlock)
        ) {
            if let profile = model.current {
                model.block(userID: profile.id, name: profile.name)
            }
        }
        // Das Match-Overlay legt `MainFlow` über die ganze App: Hier hinge es
        // nur zwischen Kopfzeile und Tab-Leiste, beide blieben sichtbar und
        // antippbar.
    }

    private func locationLabel(_ model: SwipeModel) -> String {
        // Die Umkreissuche geht von der Adresse des eingetragenen Gyms aus,
        // nicht vom Wohnort und nicht von der Geräteposition.
        s(.swipeRadius, model.searchRadiusKm)
    }

    @ViewBuilder
    private func deck(_ model: SwipeModel) -> some View {
        if model.isLoading {
            LoadingStateView(label: s(.swipeLoading))
        } else if let error = model.error {
            EmptyStateView(icon: .dumbbell, title: s(.swipeErrorTitle), message: error) {
                FlexrSecondaryButton(title: s(.swipeRetry)) {
                    Task { await model.loadDeck() }
                }
            }
        } else if model.isExhausted {
            EmptyStateView(
                icon: .dumbbell,
                title: s(.swipeEmptyTitle),
                message: s(.swipeEmptySub)
            ) {
                FlexrSecondaryButton(title: s(.swipeReload)) {
                    Task { await model.loadDeck() }
                }
            }
        } else {
            ZStack(alignment: .bottom) {
                if let next = model.next {
                    BackgroundCard(
                        profile: next,
                        progress: min(abs(cardState.offset.width) / 300, 1)
                    )
                }

                if let current = model.current {
                    SwipeableCard(
                        profile: current,
                        state: cardState,
                        onSwiped: { like in
                            if like { model.like() } else { model.pass() }
                            resetCard()
                        },
                        onOpenPhotos: { lightboxStartIndex = $0 },
                        onReport: { showReportDialog = true },
                        onBlock: { showBlockDialog = true },
                        photoIndex: Binding(
                            get: { model.photoIndex },
                            set: { model.photoIndex = $0 }
                        )
                    )
                    // Beim Kartenwechsel wieder auf das erste Foto.
                    .id(current.id)

                    HStack(spacing: 22) {
                        // Zurücknehmen gibt es nur mit Premium. Ohne Abo steht
                        // hier bewusst gar nichts statt eines gesperrten
                        // Knopfes: Die Reihe ist der meistbenutzte Ort der App,
                        // ein dauerhaft totes Element daneben wäre eine
                        // tägliche Belästigung. Wer Premium sucht, findet es im
                        // Kontobereich.
                        if model.isPremium {
                            RoundActionButton(
                                icon: FlexrIcon.rewind,
                                accessibilityLabel: s(.swipeRewind),
                                tint: FlexrColor.chalkDim,
                                isCompact: true,
                                isEnabled: !model.isRewinding
                            ) {
                                model.rewindLastSwipe()
                            }
                        }
                        RoundActionButton(
                            icon: FlexrIcon.pass,
                            accessibilityLabel: s(.swipePass),
                            tint: FlexrColor.danger
                        ) {
                            Task {
                                await cardState.flyOut(like: false)
                                model.pass()
                                resetCard()
                            }
                        }
                        RoundActionButton(
                            icon: FlexrIcon.like,
                            accessibilityLabel: s(.swipeLike),
                            tint: .white,
                            isLarge: true
                        ) {
                            Task {
                                await cardState.flyOut(like: true)
                                model.like()
                                resetCard()
                            }
                        }
                    }
                    .padding(.bottom, 14)
                }
            }
        }
    }

    private func resetCard() {
        model?.photoIndex = 0
        cardState.reset()
    }
}
