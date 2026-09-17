import SwiftUI

/// „Wer dich geliket hat" — eine Premium-Funktion.
///
/// Ohne Premium liefert der Server keine Fehlermeldung, sondern die Anzahl ohne
/// Profile (`premiumRequired`). Diese Unterscheidung bleibt bis in die
/// Oberfläche erhalten: „3 Leute warten auf dich" ist die ehrliche Antwort —
/// eine Fehlermeldung wäre es nicht. Wer ohne Abo hier landet, hat nichts
/// verloren; er sieht nur nicht, wer es ist.
///
/// Der Weg zum Angebot steht hier nur, wenn der Server diesem Client einen
/// Abschluss überhaupt anbietet. In der App tut er das nicht (App Review
/// Guideline 3.1.1, siehe `backend/app/clients.py`) — dann bleibt es bei der
/// Auskunft, ohne Knopf und ohne Preis.
struct IncomingView: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let onBack: () -> Void
    let onOpenPremium: () -> Void

    @Environment(AppContainer.self) private var container
    @Environment(AppModel.self) private var appModel

    @State private var likes: IncomingLikes?
    @State private var isLoading = true
    @State private var error: String?

    var body: some View {
        VStack(spacing: 0) {
            BackHeader(title: s(.incomingHeadline), onBack: onBack)
            content
        }
        .task { await load() }
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
            EmptyStateView(
                icon: .symbol(FlexrIcon.premium),
                title: likes.count == 1
                    ? s(.incomingLockedTitleOne)
                    : s(.incomingLockedTitle, likes.count),
                message: s(.incomingLockedSub)
            ) {
                if appModel.membership?.premiumEnabled == true {
                    FlexrButton(title: s(.premiumShowOffer), action: onOpenPremium)
                        .frame(maxWidth: 260)
                }
            }
            .frame(maxHeight: .infinity)
        } else if let likes, !likes.profiles.isEmpty {
            ScrollView {
                LazyVStack(spacing: 10) {
                    ForEach(likes.profiles) { profile in
                        IncomingProfileRow(profile: profile)
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
}

/// Eine Zeile der Liste — dieselbe Form wie `MatchListItem`, damit die Ansicht
/// nicht wie ein fremder Teil der App wirkt.
///
/// Bewusst ohne Tippziel: Von hier aus gibt es (noch) nichts zu öffnen. Ein
/// Chat setzt ein Match voraus, und zurückliken passiert im Deck — die Leute
/// stehen dort ohnehin alle drin.
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
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .flexrSurface(radius: FlexrRadius.medium, fill: FlexrColor.surface, border: FlexrColor.hairline)
    }
}
