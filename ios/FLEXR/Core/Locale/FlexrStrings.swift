import Foundation

/// Schlüssel aller Oberflächentexte.
///
/// Geordnet nach Bildschirm, nicht nach Alphabet — so steht beisammen, was auch
/// auf dem Schirm beisammensteht. Ein Aufzählungstyp statt roher Zeichenketten,
/// damit ein Tippfehler beim Übersetzen gar nicht erst übersetzt.
enum L: Hashable, Sendable {
    // Allgemein
    case commonBack, commonCancel, commonClose, commonLoading
    case commonDelete, commonReport, commonBlock, commonApply, commonAccount
    case commonLogout, commonDeleteAccount, commonWriteMessage, commonProfile
    case commonVerifiedProfile, commonProfilePhotoOf, commonDeleteFailed
    case commonMoreOptions

    // Sprache
    case langLabel, langRowTitle, langRowHint

    // Navigation
    case navSwipe, navMatches, navChats, navAccount

    // Rechtsdokumente
    case legalFaq, legalImpressum, legalDatenschutz, legalAgb, legalSicherheit
    case legalNutzungsrichtlinien, legalStrafverfolgung

    // Felder
    case fieldEmail, fieldPassword, fieldPasswordShow, fieldPasswordHide
    case fieldName, fieldBio, fieldBioPlaceholder, emojiInsert, emojiClose
    case plzLoading, plzEnter, plzUnknown

    // Login
    case loginEyebrow, loginTitle, loginSubtitle, loginSubmit, loginRegisterHint
    case loginMissingFields, loginReactivateTitle, loginReactivateConfirm
    case loginFailed, loginReactivateFailed, loginEmailPlaceholder

    // Registrierung
    case registerTitle, registerSubtitle, registerPasswordPlaceholder
    case registerNamePlaceholder, registerPhotosLabel, registerPhotoPreparing
    case registerPasswordRepeat, registerPasswordRepeatPlaceholder
    case registerErrPasswordMismatch, registerErrPasswordMismatchShort
    case registerIncompleteHint
    case registerConsentPrefix, registerConsentLink, registerConsentSuffix
    case registerSubmit
    case registerErrRequired, registerErrUnder18, registerErrBirthdate
    case registerErrPostalCode, registerErrGender, registerErrGym, registerErrPhoto
    case registerErrConsents, registerDone, registerDoneNoPhoto, registerDonePartial
    case registerFailed
    case registerPhotoMax, registerPhotoLoadFailed, plzLookupFailed
    case registerBirthdateLabel, registerGenderLabel, genderMale, genderFemale
    case registerEyebrow, registerBirthdatePlaceholder, registerAgeYears

    // Gym
    case gymLabel, gymSearchPlaceholder, gymSuggestRow, gymSuggestTitle
    case gymSuggestIntro, gymNameLabel, gymNamePlaceholder, gymStreetLabel
    case gymStreetPlaceholder, gymHouseNumberLabel, gymPostalCodeLabel
    case gymSuggestThanks, gymSuggestSubmit, gymSearching, gymNone, bioNone

    // Swipe
    case swipeEyebrow, swipeTitle, swipeRadius, swipeEmptyTitle, swipeEmptySub
    case swipeLike, swipePass, swipeLoading, swipeErrorTitle, swipeRetry, swipeReload
    case blockDone
    case swipeBlockTitle, swipeBlockBody, swipeLoadFailed, swipeFailed
    case swipeStampMatch, swipeStampPass, swipeOwnName, unmatchAction

    // Match-Overlay
    case matchEyebrow, matchTitle, matchSub, matchContinue

    // Matches / Chats
    case matchesEyebrow, matchesTitle, matchesEmptyTitle, matchesEmptySub
    case matchesLoadFailed
    case chatsEyebrow, chatsTitle, chatsEmptyTitle, chatsEmptySub, chatsYouPrefix

    // Match-Profil
    case matchProfileBlockTitle, matchProfileBlockBody, matchProfileUnmatchTitle
    case matchProfileUnmatchBody, matchProfileUnmatchConfirm, unmatchDone

    // Chat
    case chatEmptyTitle, chatEmptySub, chatBlockBody, chatClearTitle, chatClearBody, chatClearConfirm
    case chatDeleteTitle, chatDeleteBody, chatDeleteAction, chatClearAction, chatCleared
    case chatCensoredOut, chatCensoredIn, chatMutedBanner, chatInputPlaceholder
    case chatInputLocked, chatSendFailed, chatDeleted, chatOpenFailed, chatMuteReason

    // Melden
    case reportDialogTitle, reportDialogBody, reportReasonLabel, reportReasonPlaceholder
    case reportBlockTitleNamed

    // Fotos
    case photoRemove, photoAdd, photoPending, photoRejected, photoUploading, photoHintNone
    case photoHintOk, photoHintPending, photoHintRejected, photoHintTooFew, photoMinCount
    case photoUploadFailed, photoLightboxPosition, photoTooSmall, photoReadFailed

    // Konto
    case accountSectionProfile, accountSectionPhotos
    case accountManageSubscription, accountRadiusHint

    // FLEXR Premium. Die Nutzung von FLEXR selbst ist dauerhaft kostenlos;
    // Preis und Grenzen kommen als Platzhalter vom Server.
    case premiumStatusActive, premiumStatusBeta, premiumStatusFree
    case premiumShowOffer, premiumTitle, premiumSub, premiumEyebrow
    case premiumFeatureLikes, premiumFeatureChats, premiumFeatureIncoming
    case premiumFeatureRewind, premiumFeatureRadius, premiumFeatureBadge
    case premiumBetaHint, premiumLikesLeft, premiumLikesGone
    // Kauf über den App Store, siehe StoreKitService.
    case purchaseSuccess, purchasePending, purchaseFailed, purchaseUnavailable
    case premiumLikeLimit, premiumChatLimit
    case premiumBadgeTitle, premiumLikesLeftOne, premiumMoreLikes
    case premiumRewindDone, premiumRewindFailed, swipeRewind

    // „Wer dich geliket hat" (Premium).
    case incomingTitleOne, incomingTitle, incomingSubFree, incomingSubPremium
    case incomingEyebrow, incomingHeadline, incomingLoading
    case incomingLockedTitleOne, incomingLockedTitle, incomingLockedSub
    case incomingNone, incomingLoadFailed
    case accountSave, accountSaved, accountSaveFailed, accountErrPostalCode
    case accountErrPhotoBeforeSave, accountErrGym, accountNotificationsRow
    case accountNotificationsSub, accountConsentsRow
    case accountBlocksRow, accountNotificationPermission, accountCheckoutConsentMissing
    case accountCheckoutFailed
    case accountBlocksTitle
    case accountMessagesHint, accountNewMessages, accountRadiusLabel
    case accountSubscribe, accountSectionNotifications
    case accountSectionPrivacy, accountConsentsTitle, accountSectionLegal
    case accountOwnPhoto, verifyBadgeVerifiedShort
    case verifyHintTitle, verifyHintUnderstood, verifyHintStart, verifyHintDocument
    case blocksBlocked, blocksBlockedSince, commonDone, consentRevokedSuffix

    // Vor der Zahlung
    case checkoutTitle, checkoutConsentImmediate, checkoutConsentWithdrawal, checkoutContinue

    // Einwilligungen / Blockierungen
    case consentNone, consentGrantedVersion, consentRevokedOnDay, consentSensitive
    case consentVerification, consentTerms, consentBasisExplicit, consentBasisContract
    case consentRevokeTitle, consentRevokeBody, consentRevokeConfirm, consentRevokeLink
    case consentGrantLink, consentLoadFailed, consentRevokeFailed, consentGrantFailed
    case blocksEmpty, blocksNote, blocksLoadFailed, blocksUnblock, blocksUnblockFailed

    // Verifizierungs-Kurzstatus
    case verifyBadgeChecking, verifyBadgeConfirmAge, verifyBadgeVerified
    case verifyBadgeReviewing, verifyBadgeDocumentMissing, verifyBadgeFailed
    case verifyBadgeStart

    // Benachrichtigungen
    case notifyMatchTitle, notifyMatchHint, notifyQueueTitle, notifyQueueHint
    case notifyInactiveTitle, notifyInactiveHint, notifyLikesTitle, notifyLikesHint
    case notifyEmail, notifyPush, notifyLegalHint
    case notifyNewMessageFrom, notifyNewMessagesCount

    // Konto löschen
    case deleteBody, deletePasswordLabel, deleteConfirm, deletePasswordMissing, deleteDone

    // Paywall
    case paywallTitle, paywallSub, paywallFeatureUnlimited, paywallFeatureChat
    case paywallFeatureCancel, paywallReturnNote, paywallSubscribe, paywallPerMonth

    // Selfie-Verifizierung
    case verifyTitle, verifyShotOf, verifyShotIndex, verifyCameraNeeded
    case verifyPrivacyNote, verifyCaptureFailed, verifyStartFailed, verifyCameraDenied
    case verifySubmitted, verifySubmitFailed
    case verifyPreparing, verifyUploading, verifyRetrySubmit
    case verifySelfieExists, verifyAlreadySubmitted
    case verifyNotStarted, verifyCannotStart, verifyRetry
    case verifySelfieEyebrow, verifySubmitting, verifyFrameHint, verifyCameraNotReady
    case verifyNoneRunning, verifyContinueToDocument
    case verifyAllowCamera, verifyCapture

    // Ausweis-Verifizierung (Schritt 2)
    case documentTitle, documentLoading, documentStatusLoadFailed
    case documentWhyTitle, documentWhy, documentManualReview
    case documentTypeLabel, documentTypeIdCard, documentTypePassport, documentTypeLicense
    case documentNeedsBoth, documentNeedsFront
    case documentRedactNote, documentRedactNoteBold
    case documentShotsLabel, documentSideFront, documentSideBack
    case documentSideOfId, documentSideDone, documentCaptureSide
    case documentActionCamera, documentActionFile, documentSourceHint
    case documentFrameHint, documentCameraNeeded, documentCapture
    case documentAllowCamera, documentCameraDenied, documentCaptureFailed
    case documentFileReadFailed, documentSubmit, documentSubmitting
    case documentSubmitted, documentSubmitFailed, documentConsentNote

    // Verifizierungs-Gate: der einzige Bildschirm eines gesperrten Kontos
    case vgateLoading, vgateStep1of2, vgateStep2of2, vgateStep1of3
    case vgateUnlockTitle, vgateReworkEyebrow, vgateReworkTitle, vgateReworkChip
    case vgateIntro, vgateNeedTitle, vgateNeedSelfie, vgateNeedDocument
    case vgateMediaTitle, vgateMediaHuman, vgateMediaPrivate, vgateMediaDeleted
    case vgateStart, vgateRetry
    case vgateDocumentTitle, vgateDocumentBody, vgateDocumentBtn, vgateDocumentBtnRework
    case vgateSubmittedEyebrow, vgateSubmittedTitle, vgateSubmittedChip
    case vgateSubmittedBody, vgateSubmittedNote, vgateRefresh, vgateChecking
    case vgateReviewRunning
    case vgateMailTitle, vgateMailChip, vgateMailSentTo, vgateMailFallback
    case vgateMailBody, vgateMailResend, vgateMailSending, vgateMailResent
    case vgateMailSendFailed
    case vgatePhotoEyebrow, vgatePhotoTitle, vgatePhotoChip, vgatePhotoBody
    case vgatePhotoBody2, vgatePhotoMissing, vgatePhotoUploading, vgatePhotoUploadFailed
    case vgateDoneEyebrow, vgateUnlockedTitle, vgateUnlockedChip
    case vgateUnlockedBody, vgateUnlockedCta
    case vgateRejectedEyebrow, vgateRejectedTitle, vgateRejectedChip
    case vgateRejectedFallback, vgateRejectedBody, vgateRejectedDeleted

    // Statuspillen
    case statusBetaPrefix, statusPremium, statusFree, statusLikesLeft
    case statusNotUnlocked

    // Netz- und Serverfehler
    case errorTimeout, errorUnreachable, errorConnection, errorUnauthorized
    case errorPaymentRequired, errorForbidden, errorRateLimited, errorServer
    case errorHttp, errorPostalCodeUnknown, errorCityLookup
    case errorBadUploadURL, errorBadURL, errorBadRequest
    case errorNoInternet, errorCancelled, errorUnexpectedResponse
    case errorNotFound, errorConflict
}

/// Texttabelle in einer Sprache.
///
/// Wird von [LanguageStore] gehalten und über die SwiftUI-Umgebung
/// weitergereicht. Aufruf am Ort: `s(.loginSubmit)`.
///
/// Die Rechtstexte (AGB, Datenschutz, Nutzungsrichtlinien) stehen bewusst NICHT
/// hier: sie liegen in `UI/Legal/LegalContent.swift` und bleiben nur auf
/// Deutsch, weil sie in dieser Fassung verbindlich sind.
struct FlexrStrings: Sendable {

    /// Texte für Stellen ausserhalb der Oberfläche: den Netzwerkstapel
    /// ([APIErrorParser]) und die Benachrichtigungs-Dienste.
    ///
    /// Bewusst eine setzbare statische Eigenschaft und kein Konstruktorargument:
    /// beide Stellen kennen die Oberfläche nicht, und eine Abhängigkeit müsste
    /// durch APIClient, Repositories und Hintergrunddienste gefädelt werden,
    /// ohne dass irgendwo eine Entscheidung davon abhinge. Gesetzt wird sie vom
    /// [LanguageStore] — beim Start wie bei jedem Sprachwechsel.
    ///
    /// Voreingestellt ist Deutsch, die Ausgangssprache; in Unit-Tests bleibt es
    /// dabei.
    nonisolated(unsafe) static var current = FlexrStrings(language: .german)

    let language: AppLanguage

    /// Text zum Schlüssel. Fehlt die englische Fassung, gilt der deutsche
    /// Originaltext — nie ein leerer oder technischer Platzhalter.
    func callAsFunction(_ key: L) -> String {
        if language == .english, let text = Self.english[key] { return text }
        return Self.german[key] ?? ""
    }

    /// Text mit eingesetzten Platzhaltern (`%@`, `%d`).
    func callAsFunction(_ key: L, _ arguments: CVarArg...) -> String {
        String(format: self(key), arguments: arguments)
    }
}
