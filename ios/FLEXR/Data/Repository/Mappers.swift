import Foundation

/// DTO → Domäne. Bewusst an einer Stelle gebündelt, damit die Übersetzung des
/// Backend-Vertrags nachvollziehbar bleibt.

extension PhotoDTO {
    func toDomain() -> Photo {
        Photo(
            id: id,
            url: url,
            thumbURL: thumbUrl,
            position: position ?? 0,
            status: PhotoStatus(raw: status)
        )
    }
}

extension ProfileDTO {
    func toDomain() -> Profile {
        Profile(
            id: id,
            name: name,
            age: age,
            city: city,
            gender: Gender(raw: gender),
            gym: gym,
            bio: bio,
            isOnline: isOnline ?? false,
            isVerified: isVerified ?? false,
            distanceKm: distanceKm,
            photos: (photos ?? []).sorted { $0.position ?? 0 < $1.position ?? 0 }.map { $0.toDomain() }
        )
    }
}

extension MyProfileDTO {
    func toDomain() -> MyProfile {
        MyProfile(
            profile: Profile(
                id: id,
                name: name,
                age: age,
                city: city,
                gender: Gender(raw: gender),
                gym: gym,
                bio: bio,
                isOnline: isOnline ?? false,
                isVerified: isVerified ?? false,
                distanceKm: distanceKm,
                // Die eigene Ansicht zeigt bewusst ALLE Fotos inklusive Moderationsstatus.
                photos: (photos ?? [])
                    .sorted { $0.position ?? 0 < $1.position ?? 0 }
                    .map { $0.toDomain() }
            ),
            plz: plz,
            birthdate: ServerTime.parseDate(birthdate),
            searchRadiusKm: searchRadiusKm ?? 20,
            messagingMutedUntil: ServerTime.parse(messagingMutedUntil),
            notifications: NotificationSettings(
                matchEmail: notifyMatchEmail ?? true,
                matchPush: notifyMatchPush ?? true,
                queueEmail: notifyQueueEmail ?? true,
                queuePush: notifyQueuePush ?? true,
                inactiveEmail: notifyInactiveEmail ?? true,
                inactivePush: notifyInactivePush ?? true
            )
        )
    }
}

extension MembershipStatusDTO {
    func toDomain() -> Membership {
        Membership(
            isSubscribed: isSubscribed,
            trialEndsAt: ServerTime.parse(trialEndsAt) ?? Date(timeIntervalSince1970: 0),
            isActive: isActive
        )
    }
}

extension MessageDTO {
    func toDomain() -> Message {
        Message(
            id: id,
            matchID: matchId,
            senderID: senderId,
            content: content,
            createdAt: ServerTime.parse(createdAt) ?? Date(),
            readAt: ServerTime.parse(readAt),
            wasCensored: wasCensored ?? false
        )
    }
}

extension MatchDTO {
    func toDomain() -> MatchSummary {
        MatchSummary(
            matchID: matchId,
            profile: profile.toDomain(),
            lastMessage: lastMessage?.toDomain(),
            unreadCount: unreadCount ?? 0,
            isOnline: isOnline ?? false,
            inChats: inChats ?? (lastMessage != nil)
        )
    }
}

extension GymDTO {
    func toDomain() -> Gym {
        Gym(
            id: id,
            name: name,
            street: street,
            houseNumber: houseNumber,
            plz: plz,
            city: city,
            label: label
        )
    }
}

extension VerificationStatusDTO {
    func toDomain() -> VerificationState {
        VerificationState(status: VerificationStatus(raw: status), prompts: prompts ?? [])
    }
}

extension PushNotificationDTO {
    func toDomain() -> PushNotification {
        PushNotification(id: id, topic: topic, title: title, body: body, target: target)
    }
}
