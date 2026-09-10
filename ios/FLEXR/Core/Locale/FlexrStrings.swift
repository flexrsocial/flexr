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
    case plzLoading

    // Login
    case loginEyebrow, loginTitle, loginSubtitle, loginSubmit, loginRegisterHint
    case loginMissingFields, loginReactivateTitle, loginReactivateConfirm
    case loginFailed, loginReactivateFailed, loginEmailPlaceholder

    // Registrierung
    case registerTitle, registerSubtitle, registerPasswordPlaceholder
    case registerNamePlaceholder, registerPhotosLabel, registerPhotoPreparing
    case registerConsentPrefix, registerConsentLink, registerConsentSuffix
    case registerSubmit
    case registerErrRequired, registerErrUnder18, registerErrBirthdate
    case registerErrPostalCode, registerErrGender, registerErrGym, registerErrPhoto
    case registerErrConsents, registerDone, registerDoneNoPhoto, registerDonePartial
    case registerFailed
    case registerPhotoMax, registerPhotoLoadFailed, plzLookupFailed
    case registerBirthdateLabel, registerGenderLabel, genderMale, genderFemale
    case registerEyebrow, registerBirthdatePlaceholder, registerAgeYears
    case registerWaiverPrefix, registerWaiverLink, registerWaiverSuffix

    // Gym
    case gymLabel, gymSearchPlaceholder, gymSuggestRow, gymSuggestTitle
    case gymSuggestIntro, gymNameLabel, gymNamePlaceholder, gymStreetLabel
    case gymStreetPlaceholder, gymHouseNumberLabel, gymPostalCodeLabel
    case gymSuggestThanks, gymSuggestSubmit, gymSearching, gymNone, bioNone

    // Swipe
    case swipeTitle, swipeRadius, swipeEmptyTitle, swipeEmptySub, swipeLike
    case swipeBlockTitle, swipeBlockBody, swipeLoadFailed, swipeFailed
    case swipeStampMatch, swipeStampPass, swipeOwnName, unmatchAction

    // Match-Overlay
    case matchTitle, matchSub, matchContinue

    // Matches / Chats
    case matchesTitle, matchesEmptyTitle, matchesEmptySub, matchesLoadFailed
    case chatsEyebrow, chatsTitle, chatsEmptyTitle, chatsEmptySub, chatsYouPrefix

    // Match-Profil
    case matchProfileBlockTitle, matchProfileBlockBody, matchProfileUnmatchTitle
    case matchProfileUnmatchBody, matchProfileUnmatchConfirm, unmatchDone

    // Chat
    case chatEmptyTitle, chatEmptySub, chatBlockBody, chatClearTitle, chatClearBody, chatClearConfirm
    case chatDeleteTitle, chatDeleteBody, chatDeleteAction, chatClearAction, chatCleared
    case chatCensoredOut, chatCensoredIn, chatMutedBanner, chatInputPlaceholder
    case chatInputLocked, chatSendFailed, chatDeleted, chatOpenFailed

    // Melden
    case reportDialogTitle, reportDialogBody, reportReasonLabel, reportReasonPlaceholder
    case reportBlockTitleNamed

    // Fotos
    case photoRemove, photoAdd, photoPending, photoUploading, photoHintNone
    case photoHintOk, photoHintPending, photoHintRejected, photoMinOne
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
    case premiumLikeLimit, premiumChatLimit
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
    case verifyHintTitle, verifyHintUnderstood, verifyHintStart
    case blocksBlocked, blocksBlockedSince, commonDone, consentRevokedSuffix

    // Vor der Zahlung
    case checkoutTitle, checkoutConsentImmediate, checkoutConsentWithdrawal, checkoutContinue

    // Einwilligungen / Blockierungen
    case consentNone, consentGrantedVersion, consentRevokedOnDay, consentSensitive
    case consentVerification, consentTerms, consentBasisExplicit, consentBasisContract
    case consentRevokeTitle, consentRevokeBody, consentRevokeConfirm, consentRevokeLink
    case consentGrantLink, consentLoadFailed, consentRevokeFailed, consentGrantFailed
    case blocksEmpty, blocksNote, blocksLoadFailed, blocksUnblock

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
    case paywallFeatureCancel, paywallReturnNote, paywallSubscribe

    // Selfie-Verifizierung
    case verifyTitle, verifyShotOf, verifyShotIndex, verifyCameraNeeded
    case verifyPrivacyNote, verifyCaptureFailed, verifyStartFailed, verifyCameraDenied
    case verifySubmitted, verifySubmitFailed
    case verifyPreparing, verifyDone, verifyUploading, verifyRetrySubmit
    case verifyAllowCamera, verifyCapture

    // Statuspillen
    case statusBetaFree, statusPremium, statusFree, statusLikesLeft

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
