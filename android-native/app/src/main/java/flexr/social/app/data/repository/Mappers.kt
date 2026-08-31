package flexr.social.app.data.repository

import flexr.social.app.core.common.ServerTime
import flexr.social.app.data.remote.dto.AgeCheckResponseDto
import flexr.social.app.data.remote.dto.GymDto
import flexr.social.app.data.remote.dto.MatchDto
import flexr.social.app.data.remote.dto.MembershipStatusDto
import flexr.social.app.data.remote.dto.MessageDto
import flexr.social.app.data.remote.dto.MyProfileDto
import flexr.social.app.data.remote.dto.PhotoDto
import flexr.social.app.data.remote.dto.ProfileDto
import flexr.social.app.data.remote.dto.PushNotificationDto
import flexr.social.app.data.remote.dto.VerificationStatusDto
import flexr.social.app.domain.model.AgeCheck
import flexr.social.app.domain.model.Gender
import flexr.social.app.domain.model.Gym
import flexr.social.app.domain.model.MatchSummary
import flexr.social.app.domain.model.Membership
import flexr.social.app.domain.model.Message
import flexr.social.app.domain.model.MyProfile
import flexr.social.app.domain.model.Photo
import flexr.social.app.domain.model.PhotoStatus
import flexr.social.app.domain.model.NotificationSettings
import flexr.social.app.domain.model.Profile
import flexr.social.app.domain.model.PushNotification
import flexr.social.app.domain.model.VerificationDocumentType
import flexr.social.app.domain.model.VerificationState
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.domain.model.VerificationStep
import java.time.Instant

/** DTO → Domain. Bewusst an einer Stelle gebündelt, damit die Übersetzung des
 *  Backend-Vertrags nachvollziehbar bleibt. */

fun PhotoDto.toDomain() = Photo(
    id = id,
    url = url,
    thumbUrl = thumbUrl,
    position = position,
    status = PhotoStatus.from(status),
)

fun ProfileDto.toDomain() = Profile(
    id = id,
    name = name,
    age = age,
    city = city,
    gender = Gender.from(gender),
    gym = gym,
    bio = bio,
    isOnline = isOnline,
    isVerified = isVerified,
    distanceKm = distanceKm,
    photos = photos.sortedBy { it.position }.map { it.toDomain() },
)

fun MyProfileDto.toDomain() = MyProfile(
    profile = Profile(
        id = id,
        name = name,
        age = age,
        city = city,
        gender = Gender.from(gender),
        gym = gym,
        bio = bio,
        isOnline = isOnline,
        isVerified = isVerified,
        distanceKm = distanceKm,
        // Die eigene Ansicht zeigt bewusst ALLE Fotos inklusive Moderationsstatus.
        photos = photos.sortedBy { it.position }.map { it.toDomain() },
    ),
    plz = plz,
    birthdate = ServerTime.parseDate(birthdate),
    searchRadiusKm = searchRadiusKm,
    messagingMutedUntil = ServerTime.parse(messagingMutedUntil),
    verificationRequired = verificationRequired,
    isAccountActivated = isAccountActivated,
    email = email,
    emailVerified = emailVerified,
    ageVerified = ageVerified,
    notifications = NotificationSettings(
        matchEmail = notifyMatchEmail,
        matchPush = notifyMatchPush,
        queueEmail = notifyQueueEmail,
        queuePush = notifyQueuePush,
        inactiveEmail = notifyInactiveEmail,
        inactivePush = notifyInactivePush,
    ),
)

fun PushNotificationDto.toDomain() = PushNotification(
    id = id,
    topic = topic,
    title = title,
    body = body,
    target = target,
)

fun MembershipStatusDto.toDomain() = Membership(
    isSubscribed = isSubscribed,
    trialEndsAt = ServerTime.parse(trialEndsAt) ?: Instant.EPOCH,
    isActive = isActive,
)

fun MessageDto.toDomain() = Message(
    id = id,
    matchId = matchId,
    senderId = senderId,
    content = content,
    createdAt = ServerTime.parse(createdAt) ?: Instant.now(),
    readAt = ServerTime.parse(readAt),
    wasCensored = wasCensored,
)

fun MatchDto.toDomain() = MatchSummary(
    matchId = matchId,
    profile = profile.toDomain(),
    lastMessage = lastMessage?.toDomain(),
    unreadCount = unreadCount,
    isOnline = isOnline,
    inChats = inChats,
)

fun GymDto.toDomain() = Gym(
    id = id,
    name = name,
    street = street,
    houseNumber = houseNumber,
    plz = plz,
    city = city,
    label = label,
)

fun VerificationStatusDto.toDomain() = VerificationState(
    status = VerificationStatus.from(status),
    prompts = prompts.orEmpty(),
    nextStep = VerificationStep.from(nextStep),
    reason = reason,
    verificationRequired = verificationRequired,
    accountActivated = accountActivated,
    emailVerified = emailVerified,
    documentTypes = documentTypes.orEmpty().map {
        VerificationDocumentType(value = it.value, label = it.label, needsBack = it.needsBack)
    },
)

fun AgeCheckResponseDto.toDomain() = AgeCheck(
    eligible = eligible,
    age = age,
    message = message,
)
