import SwiftUI

/// Zustand einer Swipe-Karte.
///
/// Ausgelagert, damit auch die Aktionsknöpfe unter dem Deck dieselbe
/// Wegflug-Animation auslösen wie eine echte Wischgeste.
@MainActor
@Observable
final class SwipeCardState {

    /// Grenzwert, ab dem losgelassen wird gewertet statt zurückgefedert.
    static let threshold: CGFloat = 96
    static let maxRotation: Double = 15
    static let flingVelocity: CGFloat = 900

    var offset: CGSize = .zero
    /// Oben angefasst kippt die Karte anders als unten, wie ein Blatt Papier.
    var gripSign: CGFloat = 1
    var containerWidth: CGFloat = 380

    var progress: CGFloat { min(abs(offset.width) / Self.threshold, 1) }

    var rotation: Double {
        min(max(offset.width / 12, -Self.maxRotation), Self.maxRotation) * gripSign
    }

    /// Wegflug nach links (Pass) oder rechts (Like).
    func flyOut(like: Bool, velocity: CGFloat = 0) async {
        let speed = min(abs(velocity), 4000)
        let direction: CGFloat = like ? 1 : -1
        let duration = max(0.26, (420 - speed / 20) / 1000)
        withAnimation(.easeOut(duration: duration)) {
            offset = CGSize(
                width: direction * (containerWidth * 1.6 + speed * 0.1),
                height: -160
            )
        }
        try? await Task.sleep(for: .seconds(duration))
    }

    func settleBack() {
        withAnimation(.interpolatingSpring(stiffness: 420, damping: 26)) {
            offset = .zero
        }
    }

    func reset() {
        offset = .zero
        gripSign = 1
    }
}

/// Profilkarte mit Wischgeste.
///
/// Verhalten wie in der Web- und Android-App: Die Rotation richtet sich nach
/// Auslenkung UND Griffpunkt. Ausgelöst wird ab einer Schwelle ODER bei genug
/// Schwung.
struct SwipeableCard: View {

    let profile: Profile
    /// Referenztyp — Änderungen wirken direkt, deshalb kein Binding nötig.
    let state: SwipeCardState
    let onSwiped: (Bool) -> Void
    let onOpenPhotos: (Int) -> Void
    let onReport: () -> Void
    let onBlock: () -> Void
    @Binding var photoIndex: Int
    var onUnmatch: (() -> Void)?
    /// Wischgeste aktiv. Im Match-Profil wird nicht gewischt, nur betrachtet.
    var isDraggable = true
    /// Melde-/Block-Knöpfe, Fotogalerie und Stempel.
    var isInteractive = true

    var body: some View {
        GeometryReader { geometry in
            CardContent(
                profile: profile,
                isInteractive: isInteractive,
                onOpenPhotos: onOpenPhotos,
                onReport: onReport,
                onBlock: onBlock,
                onUnmatch: onUnmatch,
                photoIndex: $photoIndex
            )
            .frame(width: geometry.size.width, height: geometry.size.height)
            .background(FlexrColor.cardGradient)
            .clipShape(RoundedRectangle(cornerRadius: FlexrRadius.large, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: FlexrRadius.large, style: .continuous)
                    .strokeBorder(FlexrColor.plate.opacity(0.3), lineWidth: 1.5)
            )
            .overlay(alignment: .topTrailing) {
                if isDraggable {
                    SwipeStamp(text: "Match", color: FlexrColor.lime, rotation: -10)
                        .padding(16)
                        .opacity(state.offset.width > 0 ? state.progress : 0)
                }
            }
            .overlay(alignment: .topLeading) {
                if isDraggable {
                    SwipeStamp(text: "Nope", color: FlexrColor.danger, rotation: 10)
                        .padding(16)
                        .opacity(state.offset.width < 0 ? state.progress : 0)
                }
            }
            .opacity(1 - state.progress * 0.15)
            .rotationEffect(.degrees(state.rotation))
            .offset(x: state.offset.width, y: state.offset.height * 0.55)
            .onAppear { state.containerWidth = geometry.size.width }
            .gesture(
                dragGesture(height: geometry.size.height),
                including: isDraggable ? .all : .subviews
            )
        }
    }

    private func dragGesture(height: CGFloat) -> some Gesture {
        DragGesture(minimumDistance: 8)
            .onChanged { value in
                if state.offset == .zero {
                    state.gripSign = value.startLocation.y < height / 2 ? 1 : -1
                }
                state.offset = value.translation
            }
            .onEnded { value in
                let velocityX = value.predictedEndTranslation.width - value.translation.width
                let flung = abs(velocityX) > SwipeCardState.flingVelocity / 4
                    && abs(state.offset.width) > 40
                if abs(state.offset.width) > SwipeCardState.threshold || flung {
                    let like = flung ? velocityX > 0 : state.offset.width > 0
                    Task {
                        await state.flyOut(like: like, velocity: velocityX * 4)
                        onSwiped(like)
                    }
                } else {
                    state.settleBack()
                }
            }
    }
}

/// Karte im Hintergrund des Stapels — wächst mit, während die obere weggezogen wird.
struct BackgroundCard: View {

    let profile: Profile
    let progress: CGFloat

    @State private var photoIndex = 0

    var body: some View {
        let scale = 0.92 + 0.08 * progress
        GeometryReader { geometry in
            CardContent(
                profile: profile,
                isInteractive: false,
                onOpenPhotos: { _ in },
                onReport: {},
                onBlock: {},
                onUnmatch: nil,
                photoIndex: $photoIndex
            )
            .frame(width: geometry.size.width, height: geometry.size.height)
            .background(FlexrColor.cardGradient)
            .clipShape(RoundedRectangle(cornerRadius: FlexrRadius.large, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: FlexrRadius.large, style: .continuous)
                    .strokeBorder(FlexrColor.hairline, lineWidth: 1)
            )
            .scaleEffect(scale)
            .offset(y: 14 * (1 - progress))
        }
    }
}

// MARK: - Karteninhalt

private struct CardContent: View {

    let profile: Profile
    let isInteractive: Bool
    let onOpenPhotos: (Int) -> Void
    let onReport: () -> Void
    let onBlock: () -> Void
    let onUnmatch: (() -> Void)?
    @Binding var photoIndex: Int

    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                photoSection
                    .frame(height: geometry.size.height * 0.58)
                detailSection
                    .frame(height: geometry.size.height * 0.42)
            }
        }
    }

    private var photoSection: some View {
        ZStack(alignment: .bottomLeading) {
            PhotoImage(
                source: PhotoImageSource(profile.photos[safe: photoIndex]?.url),
                accessibilityLabel: "Profilfoto von \(profile.name)"
            )
                .contentShape(Rectangle())
                .onTapGesture {
                    if isInteractive, !profile.photos.isEmpty { onOpenPhotos(photoIndex) }
                }

            // Abdunkelung oben und unten, damit Text auf jedem Foto lesbar bleibt.
            LinearGradient(
                stops: [
                    .init(color: .black.opacity(0.38), location: 0),
                    .init(color: .clear, location: 0.16),
                    .init(color: .clear, location: 0.42),
                    .init(color: .black.opacity(0.88), location: 1),
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .allowsHitTesting(false)

            if profile.photos.count > 1 {
                photoSelector
            }

            if isInteractive {
                actionButtons
            }

            nameBlock
        }
        .clipped()
    }

    /// Die Striche sind die Foto-Auswahl: ein Tipp auf einen Strich (bzw. den
    /// Bereich darunter) schaltet direkt auf dieses Foto — ohne Umweg über die
    /// Vollbildansicht. Der Trefferbereich ist bewusst 44 pt hoch, die Striche
    /// selbst wären zu schmal.
    private var photoSelector: some View {
        GeometryReader { geometry in
            HStack(spacing: 4) {
                ForEach(profile.photos.indices, id: \.self) { offset in
                    Capsule()
                        .fill(offset == photoIndex ? FlexrColor.plate : Color.white.opacity(0.28))
                        .frame(height: 3)
                }
            }
            .padding(10)
            .frame(width: geometry.size.width, height: 44, alignment: .top)
            .contentShape(Rectangle())
            .onTapGesture { location in
                guard isInteractive else { return }
                let segment = geometry.size.width / CGFloat(profile.photos.count)
                photoIndex = min(max(Int(location.x / segment), 0), profile.photos.count - 1)
            }
        }
        .frame(height: 44)
        .frame(maxHeight: .infinity, alignment: .top)
    }

    private var actionButtons: some View {
        HStack(spacing: 6) {
            if let onUnmatch {
                CardActionButton(icon: FlexrIcon.unmatch, label: "Match auflösen", action: onUnmatch)
            }
            CardActionButton(icon: FlexrIcon.report, label: "Melden", action: onReport)
            CardActionButton(icon: FlexrIcon.block, label: "Blockieren", action: onBlock)
        }
        .padding(.top, 22)
        .padding(.trailing, 10)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
    }

    private var nameBlock: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 6) {
                Text("\(profile.name), \(profile.age)")
                    .font(.flexrOswald(26, weight: 500))
                    .foregroundStyle(.white)
                    .lineLimit(1)
                if profile.isVerified { VerifiedBadge() }
            }
            Text(subtitle.uppercased())
                .flexrText(.mono)
                .foregroundStyle(FlexrColor.chalkDim)
                .lineLimit(1)
        }
        .padding(.horizontal, 16)
        .padding(.bottom, 12)
        .allowsHitTesting(false)
    }

    private var subtitle: String {
        var parts = [profile.city]
        if !profile.gymName.isEmpty { parts.append(profile.gymName) }
        if let distance = profile.distanceKm { parts.append("\(distance) km") }
        return parts.joined(separator: " · ")
    }

    private var detailSection: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 8) {
                    StatChip(
                        text: profile.gym.isEmpty ? "Kein Gym angegeben" : profile.gym,
                        icon: .dumbbell
                    )
                    if profile.isOnline {
                        StatChip(text: "Online", isAccent: true, hasPulsingDot: true)
                    }
                    Spacer(minLength: 0)
                }
                Text(profile.bio?.isEmpty == false ? profile.bio! : "Keine Bio angegeben.")
                    .flexrText(.bodyMedium)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
        }
    }
}

private struct CardActionButton: View {

    let icon: String
    let label: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(.white.opacity(0.85))
                .frame(width: 30, height: 30)
                .background(Circle().fill(.black.opacity(0.5)))
                .overlay(Circle().strokeBorder(.white.opacity(0.22), lineWidth: 1))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(label)
    }
}

/// MATCH-/NOPE-Stempel, der beim Ziehen sichtbar wird.
private struct SwipeStamp: View {

    let text: String
    let color: Color
    let rotation: Double

    var body: some View {
        Text(text.uppercased())
            .flexrText(.headlineMedium)
            .foregroundStyle(color)
            .padding(.horizontal, 14)
            .padding(.vertical, 6)
            .background(
                RoundedRectangle(cornerRadius: FlexrRadius.small, style: .continuous)
                    .fill(.black.opacity(0.35))
            )
            .overlay(
                RoundedRectangle(cornerRadius: FlexrRadius.small, style: .continuous)
                    .strokeBorder(color, lineWidth: 3)
            )
            .rotationEffect(.degrees(rotation))
    }
}

extension Array {
    /// Zugriff ohne Absturz, wenn der Index danebenliegt.
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
