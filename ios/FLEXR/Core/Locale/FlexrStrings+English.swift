import Foundation

/// Englische Übersetzung. Die Ausgangssprache steht in `FlexrStrings+German`;
/// fehlt hier ein Schlüssel, gilt der deutsche Text.
extension FlexrStrings {

    static let english: [L: String] = [
        // MARK: Allgemein
        .commonBack: "Back",
        .commonCancel: "Cancel",
        .commonClose: "Close",
        .commonDelete: "Delete",
        .commonReport: "Report",
        .commonLoading: "Loading …",
        .commonBlock: "Block",
        .commonApply: "Apply",
        .commonAccount: "Account",
        .commonLogout: "Log out",
        .commonDeleteAccount: "Delete account",
        .commonWriteMessage: "Send a message",
        .commonProfile: "Profile",
        .commonVerifiedProfile: "Verified profile",
        .commonProfilePhotoOf: "Profile photo of %@",
        .commonDeleteFailed: "Deletion failed.",

        // MARK: Sprache
        .langLabel: "Language",
        .langRowTitle: "Language",
        .langRowHint: "Applies to the whole app. Legal texts remain binding in their German version.",

        // MARK: Navigation
        .navSwipe: "Swipe",
        .navMatches: "Matches",
        .navChats: "Chats",
        .navAccount: "Account",

        // MARK: Rechtsdokumente
        .legalFaq: "Frequently asked questions",
        .legalImpressum: "Legal notice",
        .legalDatenschutz: "Privacy policy",
        .legalAgb: "Terms and conditions",
        .legalSicherheit: "Safety tips",
        .legalNutzungsrichtlinien: "Community guidelines",
        .legalStrafverfolgung: "Law enforcement",

        // MARK: Felder
        .fieldEmail: "Email",
        .fieldPassword: "Password",
        .fieldPasswordShow: "Show password",
        .fieldPasswordHide: "Hide password",
        .fieldName: "Name",
        .fieldBio: "Bio",
        .fieldBioPlaceholder: "What you are looking for, your training, emojis welcome 💪",
        .emojiInsert: "Insert emoji",
        .emojiClose: "Close emoji picker",
        .plzLoading: "Loading …",
        .plzEnter: "— enter postal code —",
        .plzUnknown: "— unknown postal code —",

        // MARK: Login
        .loginEyebrow: "Welcome back",
        .loginTitle: "Back to the\ngym date.",
        .loginSubtitle: "Sign in with your credentials.",
        .loginSubmit: "Log in",
        .loginRegisterHint: "New here? Create your profile and try FLEXR free for a month.",
        .loginMissingFields: "Please enter your email and password.",
        .loginReactivateTitle: "Reactivate account?",
        .loginReactivateConfirm: "Reactivate now",
        .loginFailed: "Login failed.",
        .loginReactivateFailed: "Reactivation failed.",
        .loginEmailPlaceholder: "alex@example.com",

        // MARK: Registrierung
        .registerTitle: "Dating for people\nwho do leg day\non Mondays.",
        .registerSubtitle: """
            Create your profile — free of charge, permanently. Using FLEXR costs \
            nothing; no payment method is requested. FLEXR Premium (€10/month, \
            cancel any time) arrives after the beta and is optional. Currently \
            available in Austria only.
            """,
        .registerPasswordPlaceholder: "At least 8 characters",
        .registerNamePlaceholder: "Alex",
        .registerPhotosLabel: "Photos (min. %d, max. %d)",
        .registerPhotoPreparing: "Preparing photo …",
        .registerConsentPrefix: """
            I consent to the processing of my gender and the gender I am looking \
            for (from which sexual orientation can be inferred) in accordance \
            with the \

            """,
        .registerConsentLink: "privacy policy",
        .registerConsentSuffix: ".",
        .registerSubmit: "Create profile for free",
        .registerErrRequired: "Please enter email, password (min. %d characters), name and date of birth.",
        .registerErrUnder18: "You must be at least 18 years old.",
        .registerErrBirthdate: "Please enter a valid date of birth.",
        .registerErrPostalCode: "Please enter a valid Austrian postal code (the town is filled in automatically).",
        .registerErrGender: "Please select a gender.",
        .registerErrGym: "Please select a gym from the list.",
        .registerErrPhoto: "Please upload at least %d photos.",
        .registerErrConsents: "Without your consent to processing your gender and the gender you are looking for we cannot suggest any profiles — it is the basis of matching.",
        .registerFailed: "Sign-up failed.",
        .registerDone: "Profile created. Welcome to FLEXR 💪",
        .registerDoneNoPhoto: "Profile created — photo upload failed. Please add a photo in your account.",
        .registerDonePartial: "Profile created — not all photos could be uploaded.",
        .registerPhotoMax: "Maximum %d photos.",
        .registerPhotoLoadFailed: "The photo could not be loaded.",
        .plzLookupFailed: "Could not determine the town. Please try again later.",
        .registerBirthdateLabel: "Date of birth",
        .registerEyebrow: "First rep",
        .registerBirthdatePlaceholder: "dd.mm.yyyy",
        .registerAgeYears: "%d years",
        .registerGenderLabel: "Gender",
        .genderMale: "Man",
        .genderFemale: "Woman",

        // MARK: Gym
        .gymLabel: "Gym",
        .gymSearchPlaceholder: "Search gym (name, town or postal code) …",
        .gymSuggestRow: "Gym missing? Suggest it now",
        .gymSuggestTitle: "Suggest a gym",
        .gymSuggestIntro: """
            Your gym is not in the list? Submit it with its address — you can \
            use it for your profile right away, and once reviewed it appears \
            for everyone.
            """,
        .gymNameLabel: "Gym name",
        .gymNamePlaceholder: "e.g. Eisenschmiede",
        .gymStreetLabel: "Street",
        .gymStreetPlaceholder: "e.g. Hauptstraße",
        .gymHouseNumberLabel: "Number",
        .gymPostalCodeLabel: "Postal code",
        .gymSearching: "Searching …",
        .gymSuggestSubmit: "Submit suggestion",
        .gymSuggestThanks: "Thanks! Suggestion submitted — you can use the gym right away.",
        .gymNone: "No gym given",
        .bioNone: "No bio given.",

        // MARK: Swipe
        .swipeTitle: "Profiles near you",
        .swipeRadius: "%d km around your gym",
        .swipeEmptyTitle: "All sets done",
        .swipeEmptySub: "No new profiles near you. Check back later.",
        .swipeLike: "Like",
        .swipeBlockTitle: "Block?",
        .swipeBlockBody: "You will no longer see each other — neither in the deck nor in your matches.",
        .swipeLoadFailed: "Profiles could not be loaded.",
        .swipeFailed: "Swipe failed.",
        .swipeStampMatch: "Match",
        .swipeStampPass: "Nope",
        .swipeOwnName: "You",
        .unmatchAction: "Remove match",

        // MARK: Match-Overlay
        .matchTitle: "It's a match!",
        .matchSub: "You and %@ liked each other.",
        .matchContinue: "Keep swiping",

        // MARK: Matches / Chats
        .matchesTitle: "Your matches",
        .matchesEmptyTitle: "No matches yet",
        .matchesEmptySub: "Keep swiping — your next training partner is already out there.",
        .matchesLoadFailed: "Matches could not be loaded.",
        .chatsEyebrow: "In conversation",
        .chatsTitle: "Your chats",
        .chatsEmptyTitle: "No chats yet",
        .chatsEmptySub: "Send one of your matches the first message.",
        .chatsYouPrefix: "You: ",

        // MARK: Match-Profil
        .matchProfileBlockTitle: "Block?",
        .matchProfileBlockBody: "You will no longer see each other — the match and the chat disappear.",
        .matchProfileUnmatchTitle: "Remove match with %@?",
        .matchProfileUnmatchBody: """
            The chat history will be deleted. That person can appear in your \
            deck again afterwards — this is explicitly not a block.
            """,
        .matchProfileUnmatchConfirm: "Remove",
        .unmatchDone: "Match with %@ removed.",

        // MARK: Chat
        .chatEmptyTitle: "No messages yet",
        .chatEmptySub: "Write the first one — you did match, after all.",
        .chatBlockBody: "You will no longer see each other. The match and the chat disappear.",
        .chatClearTitle: "Clear chat history?",
        .chatClearBody: "The history is only hidden for you — the other person still sees it.",
        .chatClearConfirm: "Clear",
        .chatDeleteTitle: "Delete chat?",
        .chatDeleteBody: "The chat disappears from your chats — your match stays.",
        .chatDeleteAction: "Delete chat",
        .chatClearAction: "Clear chat history",
        .chatCensoredOut: "🔒 Censored for safety — the recipient sees no links or contact details.",
        .chatCensoredIn: "🔒 A link or contact details were removed for your safety.",
        .chatMutedBanner: "Your chat function is temporarily blocked. You cannot send messages until %@.",
        .chatInputPlaceholder: "Write a message…",
        .chatInputLocked: "Chat temporarily blocked",
        .chatSendFailed: "The message could not be sent.",
        .chatCleared: "Chat history cleared.",
        .chatDeleted: "Chat deleted.",
        .chatOpenFailed: "The chat could not be opened.",

        // MARK: Melden
        .reportDialogTitle: "Report %@",
        .reportBlockTitleNamed: "Block %@?",
        .reportDialogBody: "What happened? We will review your report.",
        .reportReasonLabel: "Reason",
        .reportReasonPlaceholder: "Brief description",

        // MARK: Fotos
        .photoRemove: "Remove photo",
        .photoAdd: "Add photo",
        .photoPending: "Under review",
        .photoRejected: "Rejected",
        .photoUploading: "Uploading photo …",
        .photoHintNone: "At least %d photos are needed for your profile to be visible.",
        .photoHintOk: "Your profile is visible. New photos are reviewed briefly.",
        .photoHintPending: "Your photos are being reviewed.",
        .photoHintRejected: "Your photos were rejected. Please upload different ones.",
        .photoHintTooFew: "%d of %d required photos still missing. Without them your profile stays hidden.",
        .photoMinCount: "At least %d photos are required. Upload another one first.",
        .photoUploadFailed: "Photo upload failed.",
        .photoLightboxPosition: "Photo %d of %d",
        .photoTooSmall: "Photo too small (%d×%d). At least %d×%d pixels.",
        .photoReadFailed: "The photo could not be loaded.",

        // MARK: Konto
        .accountSectionProfile: "Profile",
        .accountSectionPhotos: "Photos",
        // MARK: FLEXR Premium
        .premiumStatusActive: """
            FLEXR Premium is running. Cancel any time, effective at the end of \
            the billing month.
            """,
        .premiumStatusBeta: """
            FLEXR is and stays free. Everything is unlimited during the beta; \
            FLEXR Premium comes afterwards and is optional.
            """,
        .premiumStatusFree: """
            Your account is free: %d likes per day and %d conversations at \
            once. Premium removes both limits.
            """,
        .premiumShowOffer: "See FLEXR Premium",
        .premiumTitle: "FLEXR Premium",
        .premiumSub: """
            Using FLEXR costs nothing — permanently. Premium is for everyone \
            who wants more: no like limit, no chat limit, full reach.
            """,
        .premiumEyebrow: "Cancel any month",
        .premiumFeatureLikes: "Unlimited likes instead of %d per day",
        .premiumFeatureChats: "As many conversations at once as you like (instead of %d)",
        .premiumFeatureIncoming: "See who already liked you",
        .premiumFeatureRewind: "Undo your last swipe",
        .premiumFeatureRadius: "Full search radius up to %d km instead of %d km",
        .premiumFeatureBadge: "Premium badge on your profile",
        .premiumBetaHint: """
            FLEXR Premium arrives after the beta. Until then everything is \
            unlimited — no cost, no payment method.
            """,
        .premiumLikesLeft: "%d of %d likes left today",
        .premiumLikesGone: "No likes left today",
        .premiumLikeLimit: """
            You have used your %d likes for today. FLEXR Premium lifts the limit.
            """,
        .premiumChatLimit: """
            You have %d conversations open — that is the limit at any one time. \
            Unmatch someone or get FLEXR Premium.
            """,
        .accountManageSubscription: "Manage / cancel subscription",
        .accountRadiusHint: """
            The starting point is your gym's address — not your home and not \
            your current location. Within the radius you set you also see people \
            from other gyms nearby.
            """,
        .accountSave: "Save profile",
        .accountSaved: "Profile saved ✓",
        .accountSaveFailed: "Saving failed.",
        .accountErrPostalCode: "Please enter a valid Austrian postal code (the town is filled in automatically).",
        .accountErrPhotoBeforeSave: "Please upload at least %d photos before saving.",
        .accountErrGym: "Please select a gym from the list.",
        .accountNotificationsRow: "Matches, profiles & reminders",
        .accountNotificationsSub: "Set email and app separately",
        .accountBlocksTitle: "Blocked people",
        .accountConsentsRow: "View and revoke",
        .accountBlocksRow: "Manage and lift blocks",
        .accountNotificationPermission: "Without permission no notifications can be shown.",
        .accountCheckoutConsentMissing: "Please confirm both statements to continue.",
        .accountCheckoutFailed: "Checkout could not be started.",
        .accountMessagesHint: "Notification when a match writes to you.",
        .accountNewMessages: "New messages",
        .accountRadiusLabel: "Search radius",
        .accountSubscribe: "Subscribe now",
        .accountSectionNotifications: "Notifications",
        .accountSectionPrivacy: "Privacy & safety",
        .accountConsentsTitle: "Consents",
        .accountSectionLegal: "Legal",
        .accountOwnPhoto: "Your profile photo",
        .verifyBadgeVerifiedShort: "Verified",
        .verifyHintTitle: "Verification",
        .verifyHintUnderstood: "Got it",
        .verifyHintStart: "Start verification",
        .blocksBlocked: "Blocked",
        .commonDone: "Done",
        .consentRevokedSuffix: "  — revoked",
        .blocksBlockedSince: "Blocked · since %@",

        // MARK: Vor der Zahlung
        .checkoutTitle: "Before payment",
        .checkoutConsentImmediate: """
            I expressly agree that FLEXR begins providing the paid service \
            before the 14-day withdrawal period has expired.
            """,
        .checkoutConsentWithdrawal: """
            I confirm that I have taken note that my right of withdrawal expires \
            once FLEXR has fully performed the contract, where the statutory \
            conditions for this are met.
            """,
        .checkoutContinue: "Continue to payment",

        // MARK: Einwilligungen / Blockierungen
        .consentNone: "No entries.",
        .consentGrantedVersion: "Granted on %@, version %@.",
        .consentRevokedOnDay: "Revoked on %@.",
        .consentSensitive: "Processing of gender and the gender you are looking for",
        .consentVerification: "Images for the age and identity check",
        .consentTerms: "Accepted version of the terms",
        .consentBasisExplicit: "Explicit consent under Art. 9(2)(a) GDPR.",
        .consentBasisContract: "Contract, not consent — therefore not revocable.",
        .consentRevokeTitle: "Revoke consent?",
        .consentRevokeBody: """
            Gender and the gender you are looking for are the basis of matching.

            Without this consent we no longer suggest profiles to you and you do \
            not appear in anyone's deck. Your account remains.

            If you want to leave entirely, delete your account instead.
            """,
        .consentRevokeConfirm: "Revoke consent",
        .consentRevokeLink: "Revoke consent",
        .consentGrantLink: "Give consent again",
        .consentLoadFailed: "Consents could not be loaded.",
        .consentRevokeFailed: "The revocation could not be saved.",
        .consentGrantFailed: "The renewed consent could not be saved.",
        .blocksEmpty: """
            You have not blocked anyone. You can block from the ban icon in any \
            profile and any chat.
            """,
        .blocksNote: """
            Blocking only hides an existing match, it does not remove it. If you \
            unblock, you see each other in the deck again — and an earlier match \
            comes back with its chat history.
            """,
        .blocksLoadFailed: "Your blocks could not be loaded.",
        .blocksUnblock: "Unblock",

        // MARK: Verifizierungs-Kurzstatus
        .verifyBadgeChecking: "Review running …",
        .verifyBadgeConfirmAge: "Confirm your age",
        .verifyBadgeVerified: "Your profile is verified — others see the blue check next to your name.",
        .verifyBadgeReviewing: "Your verification is being reviewed. Once approved you get the blue check.",
        .verifyBadgeDocumentMissing: """
            The image of your official photo ID is still missing. You complete \
            that step at flexr.social for now.
            """,
        .verifyBadgeFailed: "Your verification could not be completed. Questions: flexr.social@proton.me",
        .verifyBadgeStart: """
            Show with a live selfie and a photo ID that you really are you — and \
            get the blue check.
            """,

        // MARK: Benachrichtigungen
        .notifyMatchTitle: "New match",
        .notifyMatchHint: "When someone liked you back.",
        .notifyQueueTitle: "New profiles nearby",
        .notifyQueueHint: "From three waiting profiles, at most once a day.",
        .notifyInactiveTitle: "Inactivity reminder",
        .notifyInactiveHint: "When you have not been on FLEXR for seven days.",
        .notifyLikesTitle: "Open likes without a match",
        .notifyLikesHint: "When someone liked you, at most once a week.",
        .notifyEmail: "Email",
        .notifyPush: "App notification",
        .notifyLegalHint: """
            Legally required messages — about your subscription, withdrawal or \
            moderation decisions — cannot be switched off here.
            """,
        .notifyNewMessageFrom: "New message from %@",
        .notifyNewMessagesCount: "%d new messages",

        // MARK: Konto löschen
        .deleteBody: """
            Your account is deactivated immediately and is no longer visible to \
            others. All data including photos is permanently and irreversibly \
            deleted after 30 days (see the privacy policy).
            """,
        .deletePasswordLabel: "Your password to confirm",
        .deleteConfirm: "Delete permanently",
        .deletePasswordMissing: "Please enter your password to confirm.",
        .deleteDone: "Your account has been deactivated and will be permanently deleted in 30 days.",

        // MARK: Paywall
        .paywallTitle: "FLEXR Premium",
        .paywallSub: """
            Using FLEXR costs nothing — permanently. Premium lifts the limits \
            of the free account.
            """,
        .paywallFeatureUnlimited: "Unlimited likes instead of 20 per day",
        .paywallSubscribe: "Get Premium",
        .paywallPerMonth: " / month",
        .paywallFeatureChat: "Unlimited conversations at the same time",
        .paywallFeatureCancel: "Cancel monthly, no minimum term, no hidden costs",
        .paywallReturnNote: """
            After payment you return to the app automatically. If the status is \
            not right immediately: wait a moment and open it again.
            """,

        // MARK: Selfie-Verifizierung
        .verifyTitle: "Photo verification",
        .verifyShotOf: "Shot %d / %d",
        .verifyShotIndex: "Shot %d",
        .verifyCameraNeeded: "Camera access is required.",
        .verifyPreparing: "Preparing …",
        .verifyDone: "Done!",
        .verifyUploading: "Uploading …",
        .verifyRetrySubmit: "Retry submission",
        .verifyAllowCamera: "Allow camera access",
        .verifyCapture: "Capture",
        .verifyPrivacyNote: """
            The selfies are compared manually with your profile photos only and \
            deleted after the review. No automated biometric analysis.
            """,
        .verifyCaptureFailed: "Capture failed, please try again.",
        .verifyStartFailed: "Verification could not be started.",
        .verifyCameraDenied: "Camera access denied. Verification needs live camera images.",
        .verifySubmitted: "Selfies submitted — your verification is under review.",
        .verifySelfieExists: "We already have your selfie. Next up is your photo ID.",
        .verifyAlreadySubmitted: "Your verification is already under review.",
        .verifyNoneRunning: "No verification is currently running for this account.",
        .verifyContinueToDocument: "Continue to your ID",
        .verifySubmitFailed: "Submission failed. Please try again.",

        // MARK: Ausweis-Verifizierung
        .documentTitle: "Confirm your age",
        .documentLoading: "Loading …",
        .documentStatusLoadFailed: "Could not load status.",
        .documentWhyTitle: "Why we need this",
        .documentWhy: """
            To use FLEXR you must be at least 18 years old. Upload a valid \
            official photo ID once — either as a photo you take now or as a \
            file from your device. We use it solely for the age and identity \
            check and delete the image once the check is complete.
            """,
        .documentManualReview: """
            The check is done manually by a person — no automated facial \
            recognition is used.
            """,
        .documentTypeLabel: "Document type",
        .documentTypeIdCard: "Identity card",
        .documentTypePassport: "Passport",
        .documentTypeLicense: "Driving licence",
        .documentNeedsBoth: "Front and back",
        .documentNeedsFront: "Side with photo and date of birth",
        .documentRedactNote: """
            You may redact information that is not needed for the age check.
            """,
        .documentRedactNoteBold: """
            The photo, date of birth and the validity details required for the \
            check must remain visible.
            """,
        .documentShotsLabel: "Images",
        .documentSideFront: "Front",
        .documentSideBack: "Back",
        .documentSideOfId: "%@ of your ID",
        .documentSideDone: "%@ ✓ — tap to redo",
        .documentCaptureSide: "Capture %@",
        .documentActionCamera: "Take photo",
        .documentActionFile: "Choose file",
        .documentSourceHint: """
            Tap a slot to take a photo, or use “Choose file” to pick an \
            existing image from your device.
            """,
        .documentFrameHint: """
            Lay the ID flat and fill the frame as much as possible. Make sure \
            the photo and date of birth are sharp and readable.
            """,
        .documentCameraNeeded: "Camera access is required.",
        .documentCapture: "Capture",
        .documentAllowCamera: "Allow camera access",
        .documentCameraDenied: """
            Camera access denied. The camera is needed to photograph your ID.
            """,
        .documentCaptureFailed: "Capture failed, please try again.",
        .documentFileReadFailed: """
            That file could not be read as an image. Please choose a JPEG or PNG.
            """,
        .documentSubmit: "Submit for review",
        .documentSubmitting: "Submitting …",
        .documentSubmitted: "Verification submitted — we are reviewing your details.",
        .documentSubmitFailed: "Submission failed. Please try again.",
        .documentConsentNote: """
            The images are not publicly accessible and are deleted after the \
            review.
            """,

        // MARK: Statuspillen
        .statusBetaFree: "Beta · free",
        .statusPremium: "Premium",
        .statusFree: "Free",
        .statusLikesLeft: "%d likes",

        // MARK: Netz- und Serverfehler
        .errorTimeout: "Timed out. Please check your connection and try again.",
        .errorUnreachable: "Server unreachable.",
        .errorConnection: "Connection failed. Please try again.",
        .errorUnauthorized: "Invalid or expired sign-in.",
        .errorPaymentRequired: "This feature is not available right now.",
        .errorForbidden: "Access not possible.",
        .errorRateLimited: "Too many attempts. Please wait a moment.",
        .errorServer: "Server error. Please try again later.",
        .errorHttp: "Error (%d)",
        .errorCityLookup: "Could not determine the town.",
        .errorPostalCodeUnknown: "Postal code not found. Please check it.",
        .errorNoInternet: "No internet connection.",
        .errorCancelled: "Cancelled.",
        .errorUnexpectedResponse: "Unexpected response from the server.",
        .errorNotFound: "Not found.",
        .errorConflict: "Already exists.",
        .errorBadUploadURL: "Invalid upload address.",
        .errorBadURL: "Invalid address.",
        .errorBadRequest: "The request could not be created.",
    ]
}
