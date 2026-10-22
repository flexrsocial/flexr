import SwiftUI

/// Listeneintrag für Matches und Chats (`.match-item`).
///
/// Online-Zustand als oranger Ring um den Avatar, ungelesene Nachrichten als
/// leuchtender Rahmen plus Zähler — dieselbe Bildsprache wie im Web.
struct MatchListItem: View {
    @Environment(LanguageStore.self) private var languageStore
    private var s: FlexrStrings { languageStore.strings }

    let match: MatchSummary
    let onTap: () -> Void
    var ownUserID: String?
    var showsLastMessage = false
    /// Gesetzt: statt des Pfeils ein Knopf „Hallo sagen", der direkt in den Chat führt.
    var onSayHi: (() -> Void)? = nil

    private var isUnread: Bool { match.unreadCount > 0 }

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 13) {
                AvatarImage(
                    source: PhotoImageSource(match.profile.primaryPhoto?.avatarURL),
                    name: match.profile.name,
                    size: 54,
                    ringColor: match.isOnline ? FlexrColor.plateDim : nil,
                    accessibilityLabel: s(.commonProfilePhotoOf, match.profile.name)
                )

                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 6) {
                        Text("\(match.profile.name), \(match.profile.age)")
                            .flexrText(.titleMedium)
                            .foregroundStyle(FlexrColor.chalk)
                            .lineLimit(1)
                        if match.profile.isVerified { VerifiedBadge(size: 14) }
                        if match.profile.isPremium { PremiumBadge(size: 14) }
                        // Chatliste: Zeitpunkt der letzten Nachricht rechts,
                        // wie in der Web-App und auf Android.
                        if let lastTime {
                            Spacer(minLength: 8)
                            Text(lastTime)
                                .font(.flexrMono(11, weight: isUnread ? 600 : 500))
                                .foregroundStyle(isUnread ? FlexrColor.plate : FlexrColor.chalkDim)
                                .lineLimit(1)
                                .layoutPriority(1)
                        }
                    }
                    Text(secondaryLine)
                        .flexrText(.bodySmall)
                        .foregroundStyle(isUnread ? FlexrColor.chalk : FlexrColor.chalkDim)
                        .lineLimit(1)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                if isUnread {
                    Text(match.unreadCount > 9 ? "9+" : "\(match.unreadCount)")
                        .flexrText(.labelSmall)
                        .foregroundStyle(FlexrColor.plateInk)
                        .frame(width: 22, height: 22)
                        .background(Circle().fill(FlexrColor.plate))
                } else if let onSayHi {
                    Button(action: onSayHi) {
                        HStack(spacing: 6) {
                            Image(systemName: "bubble.left.fill")
                                .font(.system(size: 12, weight: .semibold))
                            Text(s(.matchesSayHi))
                                .font(.flexrMono(12, weight: 600))
                                .lineLimit(1)
                        }
                        .foregroundStyle(FlexrColor.plate)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Capsule().fill(FlexrColor.plate.opacity(0.08)))
                        .overlay(Capsule().strokeBorder(FlexrColor.plate.opacity(0.42), lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                } else {
                    Image(systemName: FlexrIcon.forward)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(FlexrColor.chalkDim.opacity(0.6))
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: FlexrRadius.medium, style: .continuous)
                    .fill(FlexrColor.listItemGradient)
            )
            .overlay(
                RoundedRectangle(cornerRadius: FlexrRadius.medium, style: .continuous)
                    .strokeBorder(
                        isUnread ? FlexrColor.plateDim : FlexrColor.hairline,
                        lineWidth: isUnread ? 1.5 : 1
                    )
            )
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    private var lastTime: String? {
        guard showsLastMessage, let sent = match.lastMessage?.createdAt else { return nil }
        if ServerTime.daysAgo(sent) == 1 { return s(.chatYesterday) }
        return ServerTime.formatChatListTime(sent, language: languageStore.language)
    }

    private var secondaryLine: String {
        if showsLastMessage {
            // lastMessage kann trotz inChats fehlen: Nach „Chatverlauf leeren"
            // ist der Chat weiterhin gelistet, aber (für einen selbst) leer.
            guard let message = match.lastMessage else { return s(.chatsHistoryCleared) }
            let prefix = message.senderID == ownUserID ? s(.chatsYouPrefix) : ""
            return prefix + message.content
        }
        var parts = [match.profile.city]
        if let distance = match.profile.distanceKm { parts.append(Entfernung.text(distance)) }
        if match.isOnline { parts.append(s(.matchesOnlineNow)) }
        return parts.joined(separator: " · ")
    }
}
