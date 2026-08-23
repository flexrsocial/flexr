import SwiftUI

/// Listeneintrag für Matches und Chats (`.match-item`).
///
/// Online-Zustand als oranger Ring um den Avatar, ungelesene Nachrichten als
/// leuchtender Rahmen plus Zähler — dieselbe Bildsprache wie im Web.
struct MatchListItem: View {

    let match: MatchSummary
    let onTap: () -> Void
    var ownUserID: String?
    var showsLastMessage = false

    private var isUnread: Bool { match.unreadCount > 0 }

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 13) {
                AvatarImage(
                    source: PhotoImageSource(match.profile.primaryPhoto?.avatarURL),
                    name: match.profile.name,
                    size: 54,
                    ringColor: match.isOnline ? FlexrColor.plateDim : nil,
                    accessibilityLabel: "Profilfoto von \(match.profile.name)"
                )

                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 6) {
                        Text("\(match.profile.name), \(match.profile.age)")
                            .flexrText(.titleMedium)
                            .foregroundStyle(FlexrColor.chalk)
                            .lineLimit(1)
                        if match.profile.isVerified { VerifiedBadge(size: 14) }
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

    private var secondaryLine: String {
        if showsLastMessage {
            // lastMessage kann trotz inChats fehlen: Nach „Chatverlauf leeren"
            // ist der Chat weiterhin gelistet, aber (für einen selbst) leer.
            guard let message = match.lastMessage else { return "Chatverlauf geleert" }
            let prefix = message.senderID == ownUserID ? "Du: " : ""
            return prefix + message.content
        }
        var parts = [match.profile.city]
        if let distance = match.profile.distanceKm { parts.append("\(distance) km") }
        if match.isOnline { parts.append("gerade online") }
        return parts.joined(separator: " · ")
    }
}
