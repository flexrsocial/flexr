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
            isPremium: isPremium ?? false,
            distanceKm: distanceKm,
            photos: (photos ?? []).sorted { $0.position ?? 0 < $1.position ?? 0 }.map { $0.toDomain() }
        )
    }
}

extension IncomingLikesDTO {
    func toDomain() -> IncomingLikes {
        IncomingLikes(
            count: count ?? 0,
            profiles: (profiles ?? []).map { $0.toDomain() },
            premiumRequired: premiumRequired ?? false
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
                isPremium: isPremium ?? false,
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
            email: email ?? "",
            emailVerified: emailVerified ?? true,
            verificationRequired: verificationRequired ?? false,
            isAccountActivated: isAccountActivated ?? true,
            ageVerified: ageVerified ?? false,
            notifications: NotificationSettings(
                matchEmail: notifyMatchEmail ?? true,
                matchPush: notifyMatchPush ?? true,
                queueEmail: notifyQueueEmail ?? true,
                queuePush: notifyQueuePush ?? true,
                inactiveEmail: notifyInactiveEmail ?? true,
                inactivePush: notifyInactivePush ?? true,
                pendingLikesEmail: notifyPendingLikesEmail ?? true,
                pendingLikesPush: notifyPendingLikesPush ?? true
            ),
            language: language ?? "de"
        )
    }
}

extension MembershipStatusDTO {
    func toDomain() -> Membership {
        // Die Standardwerte gelten nur, wenn der Server ein Feld gar nicht
        // liefert. Sie beschreiben bewusst den zurückhaltendsten Fall: Premium
        // nicht kaufbar, keine Grenzen aktiv, Beta-Abzeichen an.
        //
        // `checkoutAvailable` hat Vorrang vor `premiumEnabled`; ein Server, der
        // es noch nicht kennt, fällt auf `premiumEnabled` zurück. Beide sind
        // für diese App ohnehin falsch, solange der Verkauf im Browser läuft.
        Membership(
            isPremium: isPremium ?? false,
            premiumEnabled: checkoutAvailable ?? premiumEnabled ?? false,
            limitsActive: limitsActive ?? premiumEnabled ?? false,
            storePurchaseAvailable: storePurchaseAvailable ?? false,
            storeProductID: storeProductId,
            betaActive: betaActive ?? true,
            hasStripeSubscription: hasStripeSubscription ?? isSubscribed ?? false,
            priceCents: priceCents ?? 1000,
            currency: currency ?? "EUR",
            freeDailyLikes: freeDailyLikes ?? 20,
            freeOpenChats: freeOpenChats ?? 3,
            freeMaxRadiusKm: freeMaxRadiusKm ?? 50,
            maxRadiusKm: maxRadiusKm ?? 250,
            likesRemaining: likesRemaining,
            openChatsRemaining: openChatsRemaining,
            nextLikeAt: nextLikeAt.flatMap(ServerTime.parse)
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
        VerificationState(
            status: VerificationStatus(raw: status),
            prompts: prompts ?? [],
            nextStep: VerificationNextStep(raw: nextStep),
            reason: reason,
            verificationRequired: verificationRequired ?? false,
            accountActivated: accountActivated ?? true,
            emailVerified: emailVerified ?? true,
            documentTypes: (documentTypes ?? []).map { $0.toDomain() }
        )
    }
}

extension EmailResendResponseDTO {
    func toDomain() -> EmailResendInfo {
        EmailResendInfo(email: email, validHours: validHours ?? 24)
    }
}

extension EmailConfirmResponseDTO {
    func toDomain() -> EmailConfirmation {
        EmailConfirmation(email: email, name: name, confirmed: confirmed ?? true)
    }
}

extension VerificationDocumentTypeDTO {
    func toDomain() -> VerificationDocumentType {
        VerificationDocumentType(
            value: value,
            label: label,
            needsBack: needsBack ?? false
        )
    }
}

extension PushNotificationDTO {
    func toDomain() -> PushNotification {
        PushNotification(id: id, topic: topic, title: title, body: body, target: target)
    }
}
