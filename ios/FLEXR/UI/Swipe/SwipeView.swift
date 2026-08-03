import SwiftUI

struct SwipeView: View {

    let onOpenChat: (String) -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var model: SwipeModel?
    @State private var cardState = SwipeCardState()
    @State private var photoIndex = 0
    @State private var lightboxStartIndex: Int?
    @State private var showReportDialog = false
    @State private var showBlockDialog = false

    var body: some View {
        Group {
            if let model {
                content(model)
            } else {
                LoadingStateView(label: "Lade Profile …")
            }
        }
        .task {
            guard model == nil else { return }
            let created = SwipeModel(
                container: container,
                onMessage: { appModel.show($0) },
                onOpenChat: onOpenChat
            )
            model = created
            await created.requestLocationPermissionIfNeeded()
            await created.syncLocationAndLoadDeck()
        }
    }

    @ViewBuilder
    private func content(_ model: SwipeModel) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            ScreenHeader(eyebrow: "Heutige Sätze", title: "Wer trainiert wo du bist")
                .padding(.top, 18)

            Text(locationLabel(model).uppercased())
                .flexrText(.mono)
                .foregroundStyle(FlexrColor.chalkDim)
                .padding(.top, 8)

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
                    photoIndex = lastIndex
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
            title: model.current.map { "\($0.name) blockieren?" } ?? "Blockieren?",
            message: "Ihr seht euch danach nicht mehr — weder im Deck noch in den Matches.",
            confirmLabel: "Blockieren"
        ) {
            if let profile = model.current {
                model.block(userID: profile.id, name: profile.name)
            }
        }
        .overlay {
            if let matched = model.matchedWith {
                MatchOverlay(
                    matchedProfile: matched,
                    ownAvatarURL: model.ownAvatarURL,
                    onWriteMessage: model.openChatWithMatch,
                    onKeepSwiping: model.dismissMatchOverlay
                )
            }
        }
    }

    private func locationLabel(_ model: SwipeModel) -> String {
        model.usesGPSLocation
            ? "Umkreis \(model.searchRadiusKm) km · GPS-Standort"
            : "Umkreis \(model.searchRadiusKm) km · Standort laut PLZ-Wohnort"
    }

    @ViewBuilder
    private func deck(_ model: SwipeModel) -> some View {
        if model.isLoading {
            LoadingStateView(label: "Lade Profile …")
        } else if let error = model.error {
            EmptyStateView(icon: .dumbbell, title: "Nicht geladen", message: error) {
                FlexrSecondaryButton(title: "Erneut versuchen") {
                    Task { await model.loadDeck() }
                }
            }
        } else if model.isExhausted {
            EmptyStateView(
                icon: .dumbbell,
                title: "Alle Sätze absolviert",
                message: "Keine neuen Profile in deiner Nähe. Schau später nochmal vorbei."
            ) {
                FlexrSecondaryButton(title: "Neu laden") {
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
                        photoIndex: $photoIndex
                    )
                    // Beim Kartenwechsel wieder auf das erste Foto.
                    .id(current.id)

                    HStack(spacing: 26) {
                        RoundActionButton(
                            icon: FlexrIcon.pass,
                            accessibilityLabel: "Ablehnen",
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
                            accessibilityLabel: "Gefällt mir",
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
        photoIndex = 0
        cardState.reset()
    }
}
