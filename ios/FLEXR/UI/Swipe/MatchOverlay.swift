import SwiftUI

/// „Match!"-Overlay nach beidseitigem Like.
///
/// Die beiden Avatare fahren beim Erscheinen zusammen — dieselbe Choreografie
/// wie im Web, hier aber mit SwiftUI-Animationen statt CSS-Keyframes.
struct MatchOverlay: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let matchedProfile: Profile
    let ownAvatarURL: String?
    let ownName: String
    let onWriteMessage: () -> Void
    let onKeepSwiping: () -> Void

    @State private var isVisible = false

    var body: some View {
        ZStack {
            // Verwischt und fast deckend wie im Web (backdrop-filter): Mit
            // reinem Schwarz zu 0,88 schien das leere Deck dahinter ("Alle
            // Sätze absolviert", "Neu laden") zwischen Text und Knöpfen durch.
            ZStack {
                Rectangle().fill(.ultraThinMaterial)
                Color.black.opacity(0.9)
            }
            .ignoresSafeArea()

            VStack(spacing: 0) {
                Eyebrow(text: s(.matchEyebrow))
                Text(s(.matchTitle))
                    .flexrText(.displayLarge)
                    .foregroundStyle(FlexrColor.plate)

                HStack(spacing: -18) {
                    AvatarImage(
                        source: PhotoImageSource(ownAvatarURL),
                        name: ownName,
                        size: 104,
                        ringColor: FlexrColor.plate,
                        ringWidth: 3,
                        accessibilityLabel: s(.accountOwnPhoto)
                    )
                    AvatarImage(
                        source: PhotoImageSource(matchedProfile.primaryPhoto?.avatarURL),
                        name: matchedProfile.name,
                        size: 104,
                        ringColor: FlexrColor.plate,
                        ringWidth: 3,
                        accessibilityLabel: s(.commonProfilePhotoOf, matchedProfile.name)
                    )
                }
                .padding(.top, 24)

                Text(s(.matchSub, matchedProfile.name))
                    .flexrText(.bodyMedium)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .multilineTextAlignment(.center)
                    .padding(.top, 20)

                FlexrButton(title: s(.commonWriteMessage), icon: .symbol(FlexrIcon.chats)) {
                    onWriteMessage()
                }
                .padding(.top, 26)

                FlexrSecondaryButton(title: s(.matchContinue), action: onKeepSwiping)
                    .padding(.top, 10)
            }
            .frame(maxWidth: 380)
            .padding(28)
            .scaleEffect(isVisible ? 1 : 0.7)
        }
        .onAppear {
            withAnimation(.interpolatingSpring(stiffness: 320, damping: 20)) { isVisible = true }
        }
    }
}
