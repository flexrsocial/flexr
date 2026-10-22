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
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let profile: Profile
    /// Referenztyp — Änderungen wirken direkt, deshalb kein Binding nötig.
    let state: SwipeCardState
    let onSwiped: (Bool) -> Void
    let onOpenPhotos: (Int) -> Void
    let onReport: () -> Void
    let onBlock: () -> Void
    @Binding var photoIndex: Int
    var onUnmatch: (() -> Void)?
    /// Like/Pass-Wischgeste aktiv. Im Match-Profil blättert Wischen stattdessen die Fotos.
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
                photoIndex: $photoIndex,
                // Im Deck gehoert das waagrechte Wischen dem Like/Pass, sonst
                // blaettert es durch die Fotos.
                swipesPhotos: !isDraggable,
                textBottomInset: isDraggable ? CardContent.deckButtonsInset : CardContent.textBottom
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
                    SwipeStamp(text: s(.swipeStampMatch), color: FlexrColor.lime, rotation: -10)
                        .padding(16)
                        .opacity(state.offset.width > 0 ? state.progress : 0)
                }
            }
            .overlay(alignment: .topLeading) {
                if isDraggable {
                    SwipeStamp(text: s(.swipeStampPass), color: FlexrColor.danger, rotation: 10)
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
                photoIndex: $photoIndex,
                swipesPhotos: false,
                // Gleiche Aufteilung wie die obere Karte, sonst springt das
                // Foto, sobald diese Karte nach vorn rueckt.
                textBottomInset: CardContent.deckButtonsInset
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

// MARK: - Fotos blaettern

/// Foto nach einer Wischgeste im Match-Profil: nach links (negativ) das
/// naechste, nach rechts das vorige. Am ersten und letzten Foto bleibt es
/// stehen, wie in der Vollbildansicht. Eher senkrechte Bewegungen zaehlen
/// nicht. Gleiche Schwelle wie Android (`PHOTO_SWIPE_THRESHOLD_DP`).
/// Entfernung zwischen den Gyms. Der Server rundet auf ganze Kilometer;
/// „0 km" (bis 2.4.13 so angezeigt, meist dasselbe Gym) heißt unter 500 m.
enum Entfernung {
    static func text(_ km: Int) -> String {
        km < 1 ? "< 1 km" : "\(km) km"
    }
}

enum FotoWischen {
    static let threshold: CGFloat = 40

    static func photoIndex(after current: Int, count: Int, translation: CGSize,
                           threshold: CGFloat = FotoWischen.threshold) -> Int {
        guard count > 1, abs(translation.width) > abs(translation.height) else { return current }
        if translation.width <= -threshold { return min(current + 1, count - 1) }
        if translation.width >= threshold { return max(current - 1, 0) }
        return current
    }
}

// MARK: - Karteninhalt

private struct CardContent: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    /// Abstand des Textes zum unteren Kartenrand.
    static let textBottom: CGFloat = 16
    /// Im Deck liegen X und Herz ueber dem unteren Kartenrand (64 pt Knopf,
    /// 14 pt Abstand, siehe SwipeView). Der Text endet darueber, statt unter
    /// den Knoepfen zu verschwinden.
    static let deckButtonsInset: CGFloat = 88

    let profile: Profile
    let isInteractive: Bool
    let onOpenPhotos: (Int) -> Void
    let onReport: () -> Void
    let onBlock: () -> Void
    let onUnmatch: (() -> Void)?
    @Binding var photoIndex: Int
    let swipesPhotos: Bool
    let textBottomInset: CGFloat

    private var canSwipePhotos: Bool {
        swipesPhotos && isInteractive && profile.photos.count > 1
    }

    var body: some View {
        // Foto mindestens 58 % der Karte ueber dem Abstand unten (im Deck:
        // ueber X und Herz), den Rest bekommt es, soweit der Text darunter ihn
        // nicht braucht (Web: .card .photo, Android: CardContent). Mit fester
        // 58/42-Teilung stand im Match-Profil unter einer kurzen Bio - dem
        // Regelfall - ein leeres Stueck Karte.
        PhotoOverDetailLayout(maxDetailShare: 0.42, bottomInset: textBottomInset) {
            // `Color.clear` ist genau so gross, wie das Layout vorschlaegt, und
            // ein `overlay` wirkt nicht auf diese Groesse zurueck (wie in
            // PhotoImage). `.clipped()` schneidet damit an der Fotoflaeche.
            Color.clear
                .overlay { photoSection }
                .clipped()
            detailSection
        }
    }

    private var photoSection: some View {
        ZStack(alignment: .bottomLeading) {
            PhotoImage(
                source: PhotoImageSource(profile.photos[safe: photoIndex]?.url),
                verticalFocus: 0.2,
                accessibilityLabel: s(.commonProfilePhotoOf, profile.name)
            )
                .contentShape(Rectangle())
                .onTapGesture {
                    if isInteractive, !profile.photos.isEmpty { onOpenPhotos(photoIndex) }
                }
                // Im Match-Profil war Blaettern bis 2.4.12 nur ueber die
                // Vollbildansicht oder die Striche moeglich. `.subviews` laesst
                // den Tipp aktiv, wenn die Wischgeste aus ist (Deck).
                .gesture(photoSwipeGesture, including: canSwipePhotos ? .all : .subviews)
                // VoiceOver sagt, welches Foto zu sehen ist; der UI-Test prueft
                // daran das Blaettern.
                .accessibilityValue(
                    profile.photos.count > 1
                        ? s(.photoLightboxPosition, photoIndex + 1, profile.photos.count)
                        : ""
                )

            if profile.photos.isEmpty {
                // Profil ohne freigegebenes Foto (z. B. ein Match, dessen Fotos
                // spaeter abgelehnt wurden): Umriss statt leerer Flaeche.
                Image(systemName: "person.fill")
                    .font(.system(size: 80))
                    .foregroundStyle(FlexrColor.chalkDim.opacity(0.35))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .allowsHitTesting(false)
            }

            // Abdunkelung oben und unten, damit Text auf jedem Foto lesbar bleibt.
            // Unten laeuft sie in die Kartenfarbe aus statt in Schwarz - vorher
            // stand zwischen Foto und Textbereich eine harte dunkle Kante.
            LinearGradient(
                stops: [
                    .init(color: .black.opacity(0.38), location: 0),
                    .init(color: .clear, location: 0.16),
                    .init(color: .clear, location: 0.46),
                    .init(color: Color(hex: 0x121212).opacity(0.8), location: 0.84),
                    .init(color: Color(hex: 0x1C1C1C), location: 1),
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
        // Kein `.clipped()` hier: Es schnitte an der Groesse dieses Stapels,
        // nicht an der Fotoflaeche, die er bekommen soll. Geschnitten wird
        // oben in `body` an `Color.clear`, das die Flaeche vorgibt. Am Stapel
        // geschnitten lief der Name in die Merkmale darunter (18.09.2026).
    }

    /// Nach links das naechste, nach rechts das vorige Foto (Android:
    /// `detectHorizontalDragGestures` in `CardContent`).
    private var photoSwipeGesture: some Gesture {
        DragGesture(minimumDistance: 12)
            .onEnded { value in
                photoIndex = FotoWischen.photoIndex(
                    after: photoIndex,
                    count: profile.photos.count,
                    translation: value.translation
                )
            }
    }

    /// Die Striche sind die Foto-Auswahl: ein Tipp auf einen Strich (bzw. den
    /// Bereich darunter) schaltet direkt auf dieses Foto — ohne Umweg über die
    /// Vollbildansicht. Der Trefferbereich ist bewusst 44 pt hoch, die Striche
    /// selbst wären zu schmal.
    private var photoSelector: some View {
        GeometryReader { geometry in
            HStack(spacing: 4) {
                // Mit Schatten und kräftigerem Weiß: Bis 2.4.13 waren die
                // übrigen Striche (Weiß 28 %) auf hellen Fotos - weiße Wand,
                // Fenster - praktisch unsichtbar.
                ForEach(profile.photos.indices, id: \.self) { offset in
                    Capsule()
                        .fill(offset == photoIndex ? FlexrColor.plate : Color.white.opacity(0.55))
                        .frame(height: 3)
                        .shadow(color: .black.opacity(0.45), radius: 1.5, y: 0.5)
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
                CardActionButton(icon: FlexrIcon.unmatch, label: s(.unmatchAction), action: onUnmatch)
            }
            CardActionButton(icon: FlexrIcon.report, label: s(.commonReport), action: onReport)
            CardActionButton(icon: FlexrIcon.block, label: s(.commonBlock), action: onBlock)
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
                if profile.isPremium { PremiumBadge() }
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
        if let distance = profile.distanceKm { parts.append(Entfernung.text(distance)) }
        return parts.joined(separator: " · ")
    }

    private var gymChip: some View {
        StatChip(text: profile.gym.isEmpty ? s(.gymNone) : profile.gym, icon: .dumbbell)
    }

    private var onlineChip: some View {
        StatChip(text: s(.commonOnline), isAccent: true, hasPulsingDot: true)
    }

    /// Ein `ScrollView` nimmt immer die ganze angebotene Hoehe. Deshalb erst
    /// der Text ohne Scrollen; nur wenn er nicht in den Platz passt, den
    /// `PhotoOverDetailLayout` anbietet, die scrollende Fassung.
    private var detailSection: some View {
        ViewThatFits(in: .vertical) {
            detailContent
            ScrollView { detailContent }
        }
    }

    private var detailContent: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Umbrechend wie im Web (flex-wrap) und auf Android (FlowRow):
            // Passt der Gym-Chip nicht neben "Online", kommt "Online" in
            // die naechste Zeile, statt die Adresse abzuschneiden.
            ViewThatFits(in: .horizontal) {
                HStack(spacing: 8) {
                    gymChip
                    if profile.isOnline { onlineChip }
                    Spacer(minLength: 0)
                }
                VStack(alignment: .leading, spacing: 8) {
                    gymChip
                    if profile.isOnline { onlineChip }
                }
            }
            Text(profile.bio?.isEmpty == false ? profile.bio! : s(.bioNone))
                .flexrText(.bodyMedium)
                .foregroundStyle(FlexrColor.chalkDim)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 16)
        .padding(.top, 14)
        // Kein Abstand nach unten: Den haelt `PhotoOverDetailLayout` frei.
        // Bis 2.4.12 lag er hier und damit im `ScrollView`; wurde gekappt,
        // endete der sichtbare Text unter X und Herz (17.10.2026).
    }
}

/// Foto oben, Text unten, darunter `bottomInset` frei (im Deck Platz fuer
/// X und Herz). Der Text (zweite Unteransicht) bekommt die Hoehe, die er
/// braucht, hoechstens `maxDetailShare` der Karte ueber dem Abstand; das Foto
/// den Rest.
///
/// Der Abstand zaehlt nicht zu den 42 %, wie im Web, wo die Knoepfe unter der
/// Karte stehen (Android: `(maxHeight - bottomInset) * 0.42f`). Und er liegt
/// ausserhalb des Textes, also auch ausserhalb des `ScrollView`: Gekappter
/// Text endet so immer ueber den Knoepfen.
///
/// Ein `VStack` mit `.frame(maxHeight:)` ginge nicht: Ein Rahmen mit
/// Hoechstwert waechst bis zu diesem Wert, sobald mehr angeboten wird, und
/// meldet dann wieder starre 42 %.
private struct PhotoOverDetailLayout: Layout {

    let maxDetailShare: CGFloat
    let bottomInset: CGFloat

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        proposal.replacingUnspecifiedDimensions()
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        guard subviews.count == 2 else { return }
        let photo = subviews[0]
        let detail = subviews[1]
        let maxDetailHeight = max(bounds.height - bottomInset, 0) * maxDetailShare
        // Bei diesem Angebot waehlt `ViewThatFits` den Text ohne Scrollen
        // (meldet seine eigene Hoehe) oder den scrollenden (meldet das
        // Angebot) - also nie mehr als `maxDetailHeight`.
        let needed = detail.sizeThatFits(
            ProposedViewSize(width: bounds.width, height: maxDetailHeight)
        ).height
        let detailHeight = min(needed, maxDetailHeight)
        let photoHeight = max(bounds.height - bottomInset - detailHeight, 0)
        photo.place(
            at: bounds.origin,
            anchor: .topLeading,
            proposal: ProposedViewSize(width: bounds.width, height: photoHeight)
        )
        detail.place(
            at: CGPoint(x: bounds.minX, y: bounds.minY + photoHeight),
            anchor: .topLeading,
            proposal: ProposedViewSize(width: bounds.width, height: detailHeight)
        )
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
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

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
