import Foundation

/// Die Ausgangssprache. Was in `FlexrStrings+English` fehlt, fällt hierher
/// zurück — eine vergessene Übersetzung sieht dann nach deutschem Text aus und
/// nicht nach einem Fehler.
extension FlexrStrings {

    static let german: [L: String] = [
        // MARK: Allgemein
        .commonBack: "Zurück",
        .commonCancel: "Abbrechen",
        .commonClose: "Schließen",
        .commonDelete: "Löschen",
        .commonReport: "Melden",
        .commonLoading: "Lädt …",
        .commonBlock: "Blockieren",
        .commonApply: "Übernehmen",
        .commonAccount: "Konto",
        .commonLogout: "Ausloggen",
        .commonDeleteAccount: "Konto löschen",
        .commonWriteMessage: "Nachricht schreiben",
        .commonProfile: "Profil",
        .commonVerifiedProfile: "Verifiziertes Profil",
        .commonProfilePhotoOf: "Profilfoto von %@",
        .commonDeleteFailed: "Löschen fehlgeschlagen.",
        .commonMoreOptions: "Weitere Optionen",

        // MARK: Sprache
        .langLabel: "Sprache",
        .langRowTitle: "Sprache",
        .langRowHint: "Gilt für die gesamte App. Rechtstexte bleiben auf Deutsch verbindlich.",

        // MARK: Navigation
        .navSwipe: "Swipe",
        .navMatches: "Matches",
        .navChats: "Chats",
        .navAccount: "Konto",

        // MARK: Rechtsdokumente
        .legalFaq: "Häufige Fragen",
        .legalImpressum: "Impressum",
        .legalDatenschutz: "Datenschutzerklärung",
        .legalAgb: "Allgemeine Geschäftsbedingungen",
        .legalSicherheit: "Sicherheitstipps",
        .legalNutzungsrichtlinien: "Nutzungsrichtlinien",
        .legalStrafverfolgung: "Strafverfolgungsbehörden",

        // MARK: Felder
        .fieldEmail: "E-Mail",
        .fieldPassword: "Passwort",
        .fieldPasswordShow: "Passwort anzeigen",
        .fieldPasswordHide: "Passwort verbergen",
        .fieldName: "Name",
        .fieldBio: "Bio",
        .fieldBioPlaceholder: "Was du suchst, dein Training, gerne mit Emojis 💪",
        .emojiInsert: "Emoji einfügen",
        .emojiClose: "Emoji-Auswahl schließen",
        .plzLoading: "Lädt …",
        .plzEnter: "— PLZ eingeben —",
        .plzUnknown: "— unbekannte PLZ —",

        // MARK: Login
        .loginEyebrow: "Willkommen zurück",
        .loginTitle: "Zurück ins\nGym-Date.",
        .loginSubtitle: "Melde dich mit deinen Zugangsdaten an.",
        .loginSubmit: "Einloggen",
        .loginRegisterHint: "Neu hier? Erstell dein Profil — FLEXR zu nutzen kostet nichts.",
        .loginMissingFields: "Bitte E-Mail und Passwort angeben.",
        .loginReactivateTitle: "Konto reaktivieren?",
        .loginReactivateConfirm: "Jetzt reaktivieren",
        .loginFailed: "Login fehlgeschlagen.",
        .loginReactivateFailed: "Reaktivierung fehlgeschlagen.",
        .loginEmailPlaceholder: "max@example.com",

        // MARK: Registrierung
        .registerTitle: "Dating für Leute,\ndie auch montags\nBeintag machen.",
        .registerSubtitle: """
            Erstell dein Profil — kostenlos, und das dauerhaft. FLEXR zu nutzen \
            kostet nichts; es wird kein Zahlungsmittel abgefragt. FLEXR Premium \
            (10 €/Monat, jederzeit kündbar) kommt nach der Beta und ist \
            freiwillig. Aktuell nur in Österreich verfügbar.
            """,
        .registerPasswordPlaceholder: "Mind. 8 Zeichen",
        .registerNamePlaceholder: "Max",
        .registerPasswordRepeat: "Passwort wiederholen",
        .registerPasswordRepeatPlaceholder: "Passwort erneut eingeben",
        .registerErrPasswordMismatch: "Die beiden Passwörter stimmen nicht überein.",
        .registerErrPasswordMismatchShort: "Die Passwörter stimmen nicht überein.",
        .registerIncompleteHint: """
            Noch nicht vollständig — tippe auf den Knopf, dann zeigen wir dir, \
            was fehlt.
            """,
        .registerPhotosLabel: "Fotos (mind. %d, max. %d)",
        .registerPhotoPreparing: "Foto wird vorbereitet …",
        .registerConsentPrefix: """
            Ich willige ein, dass meine Angaben zu Geschlecht und gesuchtem \
            Geschlecht (daraus ableitbar: sexuelle Orientierung) gemäß \

            """,
        .registerConsentLink: "Datenschutzerklärung",
        .registerConsentSuffix: " verarbeitet werden.",
        .registerSubmit: "Profil kostenlos erstellen",
        .registerErrRequired: "Bitte E-Mail, Passwort (min. %d Zeichen), Name und Geburtsdatum angeben.",
        .registerErrUnder18: "Du musst mindestens 18 Jahre alt sein.",
        .registerErrBirthdate: "Bitte ein gültiges Geburtsdatum angeben.",
        .registerErrPostalCode: "Bitte eine gültige österreichische Postleitzahl eingeben (Ort wird automatisch ermittelt).",
        .registerErrGender: "Bitte ein Geschlecht auswählen.",
        .registerErrGym: "Bitte ein Gym aus der Liste auswählen.",
        .registerErrPhoto: "Bitte lade mindestens %d Fotos hoch.",
        .registerErrConsents: "Ohne die Einwilligung zur Verarbeitung von Geschlecht und gesuchtem Geschlecht können wir dir keine Profile vorschlagen — sie ist die Grundlage des Matchings.",
        .registerFailed: "Registrierung fehlgeschlagen.",
        .registerDone: "Profil erstellt. Willkommen bei FLEXR 💪",
        .registerDoneNoPhoto: "Profil erstellt — Foto-Upload fehlgeschlagen. Bitte im Konto ein Foto hinzufügen.",
        .registerDonePartial: "Profil erstellt — nicht alle Fotos konnten hochgeladen werden.",
        .registerPhotoMax: "Maximal %d Fotos.",
        .registerPhotoLoadFailed: "Foto konnte nicht geladen werden.",
        .plzLookupFailed: "Ort konnte nicht ermittelt werden. Bitte später erneut versuchen.",
        .registerBirthdateLabel: "Geburtsdatum",
        .registerEyebrow: "Erste Wiederholung",
        .registerBirthdatePlaceholder: "tt.mm.jjjj",
        .registerAgeYears: "%d Jahre",
        .registerGenderLabel: "Geschlecht",
        .genderMale: "Mann",
        .genderFemale: "Frau",

        // MARK: Gym
        .gymLabel: "Gym",
        .gymSearchPlaceholder: "Gym suchen (Name, Ort oder PLZ) …",
        .gymSuggestRow: "Gym nicht dabei? Jetzt vorschlagen",
        .gymSuggestTitle: "Gym vorschlagen",
        .gymSuggestIntro: """
            Dein Gym fehlt in der Liste? Reich es mit Adresse ein — du kannst es \
            sofort für dein Profil verwenden, nach Prüfung erscheint es für alle.
            """,
        .gymNameLabel: "Name des Gyms",
        .gymNamePlaceholder: "z. B. Eisenschmiede",
        .gymStreetLabel: "Straße",
        .gymStreetPlaceholder: "z. B. Hauptstraße",
        .gymHouseNumberLabel: "Hausnummer",
        .gymPostalCodeLabel: "Postleitzahl",
        .gymSearching: "Suche …",
        .gymSuggestSubmit: "Vorschlag einreichen",
        .gymSuggestThanks: "Danke! Vorschlag eingereicht — du kannst das Gym sofort verwenden.",
        .gymNone: "Kein Gym angegeben",
        .bioNone: "Keine Bio angegeben.",

        // MARK: Swipe
        .swipeEyebrow: "Entdecken",
        .swipeTitle: "Profile in deiner Nähe",
        .swipeLoading: "Lade Profile …",
        .swipeErrorTitle: "Nicht geladen",
        .swipeRetry: "Erneut versuchen",
        .swipeReload: "Neu laden",
        .swipePass: "Ablehnen",
        .blockDone: "%@ blockiert.",
        .swipeRadius: "%d km rund um dein Gym",
        .swipeEmptyTitle: "Alle Sätze absolviert",
        .swipeEmptySub: "Keine neuen Profile in deiner Nähe. Schau später nochmal vorbei.",
        .swipeLike: "Gefällt mir",
        .swipeBlockTitle: "Blockieren?",
        .swipeBlockBody: "Ihr seht euch danach nicht mehr — weder im Deck noch in den Matches.",
        .swipeLoadFailed: "Profile konnten nicht geladen werden.",
        .swipeFailed: "Swipe fehlgeschlagen.",
        .swipeStampMatch: "Match",
        .swipeStampPass: "Nope",
        .swipeOwnName: "Du",
        .unmatchAction: "Match auflösen",

        // MARK: Match-Overlay
        .matchEyebrow: "Beide interessiert",
        .matchTitle: "Match!",
        .matchSub: "Du und %@ habt euch gegenseitig geliked.",
        .matchContinue: "Weiter swipen",

        // MARK: Matches / Chats
        .matchesEyebrow: "Trefferquote",
        .matchesTitle: "Deine Matches",
        .matchesEmptyTitle: "Noch keine Matches",
        .matchesEmptySub: "Weiter swipen — dein nächster Trainingspartner wartet schon.",
        .matchesLoadFailed: "Matches konnten nicht geladen werden.",
        .chatsEyebrow: "Im Gespräch",
        .chatsTitle: "Deine Chats",
        .chatsEmptyTitle: "Noch keine Chats",
        .chatsEmptySub: "Schreib einem deiner Matches die erste Nachricht.",
        .chatsYouPrefix: "Du: ",

        // MARK: Match-Profil
        .matchProfileBlockTitle: "Blockieren?",
        .matchProfileBlockBody: "Ihr seht euch danach nicht mehr — das Match und der Chat verschwinden.",
        .matchProfileUnmatchTitle: "Match mit %@ auflösen?",
        .matchProfileUnmatchBody: """
            Der Chatverlauf wird gelöscht. Die Person kann dir danach erneut im \
            Deck begegnen — eine Sperre ist das ausdrücklich nicht.
            """,
        .matchProfileUnmatchConfirm: "Auflösen",
        .unmatchDone: "Match mit %@ aufgelöst.",

        // MARK: Chat
        .chatEmptyTitle: "Noch keine Nachrichten",
        .chatEmptySub: "Schreib die erste — ihr habt schließlich gematcht.",
        .chatBlockBody: "Ihr seht euch danach nicht mehr. Das Match und der Chat verschwinden.",
        .chatClearTitle: "Chatverlauf leeren?",
        .chatClearBody: "Der Verlauf wird nur für dich ausgeblendet — die andere Person sieht ihn weiterhin.",
        .chatClearConfirm: "Leeren",
        .chatDeleteTitle: "Chat löschen?",
        .chatDeleteBody: "Der Chat verschwindet aus deinen Chats — euer Match bleibt aber bestehen.",
        .chatDeleteAction: "Chat löschen",
        .chatClearAction: "Chatverlauf leeren",
        .chatCensoredOut: "🔒 Zum Schutz zensiert — der Empfänger sieht keine Links/Kontaktdaten.",
        .chatCensoredIn: "🔒 Ein Link oder Kontaktdaten wurden zu deinem Schutz entfernt.",
        .chatMutedBanner: "Deine Chat-Funktion ist vorübergehend gesperrt. Du kannst bis %@ Uhr keine Nachrichten senden.",
        .chatInputPlaceholder: "Nachricht schreiben…",
        .chatInputLocked: "Chat vorübergehend gesperrt",
        .chatMuteReason: "Grund: %@",
        .chatSendFailed: "Nachricht konnte nicht gesendet werden.",
        .chatCleared: "Chatverlauf geleert.",
        .chatDeleted: "Chat gelöscht.",
        .chatOpenFailed: "Chat konnte nicht geöffnet werden.",

        // MARK: Melden
        .reportDialogTitle: "%@ melden",
        .reportBlockTitleNamed: "%@ blockieren?",
        .reportDialogBody: "Was ist vorgefallen? Deine Meldung wird von uns geprüft.",
        .reportReasonLabel: "Grund",
        .reportReasonPlaceholder: "Kurze Beschreibung",

        // MARK: Fotos
        .photoRemove: "Foto entfernen",
        .photoAdd: "Foto hinzufügen",
        .photoPending: "In Prüfung",
        .photoRejected: "Abgelehnt",
        .photoUploading: "Foto wird hochgeladen …",
        .photoHintNone: "Mindestens %d Fotos sind nötig, damit dein Profil sichtbar ist.",
        .photoHintOk: "Dein Profil ist sichtbar. Neue Fotos werden kurz geprüft.",
        .photoHintPending: "Deine Fotos werden geprüft.",
        .photoHintRejected: "Deine Fotos wurden abgelehnt. Bitte lade andere hoch.",
        .photoHintTooFew: "Noch %d von %d Pflichtfotos. Ohne sie bleibt dein Profil unsichtbar.",
        .photoMinCount: "Mindestens %d Fotos sind erforderlich. Lade zuerst ein weiteres hoch.",
        .photoUploadFailed: "Foto-Upload fehlgeschlagen.",
        .photoLightboxPosition: "Foto %d von %d",
        .photoTooSmall: "Foto zu klein (%d×%d). Mindestens %d×%d Pixel.",
        .photoReadFailed: "Foto konnte nicht geladen werden.",

        // MARK: Konto
        .accountSectionProfile: "Profil",
        .accountSectionPhotos: "Fotos",
        // MARK: FLEXR Premium
        .premiumStatusActive: """
            FLEXR Premium läuft. Jederzeit zum Ende des Abrechnungsmonats \
            kündbar.
            """,
        .premiumStatusBeta: """
            FLEXR ist und bleibt kostenlos. Während der Beta ist alles \
            unbegrenzt; FLEXR Premium kommt danach und ist freiwillig.
            """,
        .premiumStatusFree: """
            Dein Konto ist kostenlos: %d Likes pro Tag und %d Unterhaltungen \
            gleichzeitig. Mit Premium fällt beides weg.
            """,
        .premiumShowOffer: "FLEXR Premium ansehen",
        .premiumTitle: "FLEXR Premium",
        .premiumSub: """
            FLEXR zu nutzen kostet nichts — dauerhaft. Premium ist für alle, \
            die mehr wollen: ohne Like-Grenze, ohne Chat-Grenze, mit voller \
            Reichweite.
            """,
        .premiumEyebrow: "Monatlich kündbar",
        .premiumFeatureLikes: "Unbegrenzt liken statt %d pro Tag",
        .premiumFeatureChats: "So viele Unterhaltungen gleichzeitig, wie du willst (statt %d)",
        .premiumFeatureIncoming: "Sehen, wer dich schon geliket hat",
        .premiumFeatureRewind: "Den letzten Swipe zurücknehmen",
        .premiumFeatureRadius: "Voller Suchumkreis bis %d km statt %d km",
        .premiumFeatureBadge: "Premium-Abzeichen in deinem Profil",
        .premiumBetaHint: """
            FLEXR Premium kommt nach der Beta-Phase. Bis dahin ist alles \
            unbegrenzt — ohne Kosten und ohne Zahlungsmittel.
            """,
        .premiumLikesLeft: "Noch %d von %d Likes heute",
        .premiumLikesGone: "Likes für heute aufgebraucht",
        .premiumLikeLimit: """
            Deine %d Likes für heute sind aufgebraucht. Mit FLEXR Premium \
            likest du ohne Grenze.
            """,
        .premiumBadgeTitle: "FLEXR Premium",
        .premiumLikesLeftOne: "Noch 1 von %d Likes heute",
        .premiumMoreLikes: "Unbegrenzt liken",
        .premiumRewindDone: "Swipe zurückgenommen.",
        .premiumRewindFailed: "Zurücknehmen hat nicht geklappt.",
        .swipeRewind: "Letzten Swipe zurücknehmen",
        .incomingTitleOne: "Jemand hat dich geliket",
        .incomingTitle: "Leute haben dich geliket",
        .incomingSubFree: "Mit FLEXR Premium siehst du, wer",
        .incomingSubPremium: "Ansehen und zurückliken",
        .incomingEyebrow: "Offene Likes",
        .incomingHeadline: "Wer dich geliket hat",
        .incomingLoading: "Lade …",
        .incomingLockedTitleOne: "Eine Person wartet auf dich",
        .incomingLockedTitle: "%d Leute warten auf dich",
        .incomingLockedSub: """
            Wer genau, siehst du mit FLEXR Premium. Ohne Premium tauchen sie \
            ganz normal in deinem Deck auf.
            """,
        .incomingNone: "Gerade wartet niemand.",
        .incomingLoadFailed: "Die offenen Likes konnten nicht geladen werden.",
        .premiumChatLimit: """
            Du hast %d Unterhaltungen offen — mehr gehen gleichzeitig nicht. \
            Löse ein Match auf oder hol dir FLEXR Premium.
            """,
        .accountManageSubscription: "Abo verwalten / kündigen",
        .accountRadiusHint: """
            Ausgangspunkt ist die Adresse deines Gyms — nicht dein Wohnort und \
            nicht dein aktueller Standort. Im eingestellten Umkreis siehst du \
            auch Leute aus anderen Studios in der Nähe.
            """,
        .accountSave: "Profil speichern",
        .accountSaved: "Profil gespeichert ✓",
        .accountSaveFailed: "Speichern fehlgeschlagen.",
        .accountErrPostalCode: "Bitte eine gültige österreichische Postleitzahl eingeben (Ort wird automatisch ermittelt).",
        .accountErrPhotoBeforeSave: "Bitte lade mindestens %d Fotos hoch, bevor du speicherst.",
        .accountErrGym: "Bitte ein Gym aus der Liste auswählen.",
        .accountNotificationsRow: "Matches, Profile & Erinnerungen",
        .accountNotificationsSub: "E-Mail und App getrennt einstellen",
        .accountBlocksTitle: "Blockierte Personen",
        .accountConsentsRow: "Einsehen und widerrufen",
        .accountBlocksRow: "Blockierungen verwalten und aufheben",
        .accountNotificationPermission: "Ohne Berechtigung können keine Benachrichtigungen angezeigt werden.",
        .accountCheckoutConsentMissing: "Bitte bestätige beide Erklärungen, um fortzufahren.",
        .accountCheckoutFailed: "Checkout konnte nicht gestartet werden.",
        .accountMessagesHint: "Benachrichtigung, wenn dir ein Match schreibt.",
        .accountNewMessages: "Neue Nachrichten",
        .accountRadiusLabel: "Suchumkreis",
        .accountSubscribe: "Jetzt abonnieren",
        .accountSectionNotifications: "Benachrichtigungen",
        .accountSectionPrivacy: "Datenschutz & Sicherheit",
        .accountConsentsTitle: "Einwilligungen",
        .accountSectionLegal: "Rechtliches",
        .accountOwnPhoto: "Dein Profilfoto",
        .verifyBadgeVerifiedShort: "Verifiziert",
        .verifyHintTitle: "Verifizierung",
        .verifyHintUnderstood: "Verstanden",
        .verifyHintStart: "Zur Verifizierung",
        .verifyHintDocument: "Ausweis aufnehmen",
        .blocksBlocked: "Blockiert",
        .commonDone: "Fertig",
        .consentRevokedSuffix: "  — widerrufen",
        .blocksBlockedSince: "Blockiert · seit %@",

        // MARK: Vor der Zahlung
        .checkoutTitle: "Vor der Zahlung",
        .checkoutConsentImmediate: """
            Ich stimme ausdrücklich zu, dass FLEXR bereits vor Ablauf der \
            14-tägigen Rücktrittsfrist mit der Erbringung der kostenpflichtigen \
            Dienstleistung beginnt.
            """,
        .checkoutConsentWithdrawal: """
            Ich bestätige, dass ich zur Kenntnis genommen habe, dass mein \
            Rücktrittsrecht nach vollständiger Vertragserfüllung durch FLEXR \
            erlischt, wenn die gesetzlichen Voraussetzungen dafür erfüllt sind.
            """,
        .checkoutContinue: "Weiter zur Zahlung",

        // MARK: Einwilligungen / Blockierungen
        .consentNone: "Keine Einträge.",
        .consentGrantedVersion: "Erteilt am %@, Fassung %@.",
        .consentRevokedOnDay: "Widerrufen am %@.",
        .consentSensitive: "Verarbeitung von Geschlecht und gesuchtem Geschlecht",
        .consentVerification: "Aufnahmen für die Alters- und Identitätsprüfung",
        .consentTerms: "Angenommene AGB-Fassung",
        .consentBasisExplicit: "Ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a DSGVO.",
        .consentBasisContract: "Vertragsschluss, keine Einwilligung — daher nicht widerrufbar.",
        .consentRevokeTitle: "Einwilligung widerrufen?",
        .consentRevokeBody: """
            Geschlecht und gesuchtes Geschlecht sind die Grundlage des Matchings.

            Ohne diese Einwilligung schlagen wir dir keine Profile mehr vor und \
            du erscheinst in keinem Deck. Dein Konto bleibt bestehen.

            Willst du ganz weg, lösche stattdessen dein Konto.
            """,
        .consentRevokeConfirm: "Widerruf erklären",
        .consentRevokeLink: "Einwilligung widerrufen",
        .consentGrantLink: "Einwilligung erneut erteilen",
        .consentLoadFailed: "Einwilligungen konnten nicht geladen werden.",
        .consentRevokeFailed: "Der Widerruf konnte nicht gespeichert werden.",
        .consentGrantFailed: "Die erneute Einwilligung konnte nicht gespeichert werden.",
        .blocksEmpty: """
            Du hast niemanden blockiert. Blockieren geht über das Verbots-Symbol \
            in jedem Profil und in jedem Chat.
            """,
        .blocksNote: """
            Eine Blockierung blendet ein bestehendes Match nur aus, sie löst es \
            nicht auf. Hebst du sie auf, seht ihr einander wieder im Deck — und \
            ein früheres Match ist samt Chatverlauf wieder da.
            """,
        .blocksLoadFailed: "Deine Blockierungen konnten nicht geladen werden.",
        .blocksUnblock: "Aufheben",
        .blocksUnblockFailed: "Aufheben fehlgeschlagen.",

        // MARK: Verifizierungs-Kurzstatus
        .verifyBadgeChecking: "Prüfung läuft …",
        .verifyBadgeConfirmAge: "Alter bestätigen",
        .verifyBadgeVerified: "Dein Profil ist verifiziert — andere sehen den blauen Haken neben deinem Namen.",
        .verifyBadgeReviewing: "Deine Verifizierung wird geprüft. Nach der Freigabe bekommst du den blauen Haken.",
        .verifyBadgeDocumentMissing: "Selfie erledigt. Jetzt noch den Ausweis aufnehmen.",
        .verifyBadgeFailed: "Deine Verifizierung konnte nicht abgeschlossen werden. Bei Fragen: flexr.social@proton.me",
        .verifyBadgeStart: """
            Zeig mit einem Live-Selfie und einem Lichtbildausweis, dass du \
            wirklich du bist — und hol dir den blauen Haken.
            """,

        // MARK: Benachrichtigungen
        .notifyMatchTitle: "Neues Match",
        .notifyMatchHint: "Wenn jemand dich zurückgeliked hat.",
        .notifyQueueTitle: "Neue Profile im Umkreis",
        .notifyQueueHint: "Ab drei wartenden Profilen, höchstens einmal am Tag.",
        .notifyInactiveTitle: "Erinnerung bei Inaktivität",
        .notifyInactiveHint: "Wenn du sieben Tage nicht in FLEXR warst.",
        .notifyLikesTitle: "Offene Likes ohne Match",
        .notifyLikesHint: "Wenn dich jemand geliked hat, höchstens einmal pro Woche.",
        .notifyEmail: "E-Mail",
        .notifyPush: "App-Benachrichtigung",
        .notifyLegalHint: """
            Rechtlich nötige Nachrichten — etwa zu Abo, Rücktritt oder \
            Moderationsentscheidungen — lassen sich hier nicht abschalten.
            """,
        .notifyNewMessageFrom: "Neue Nachricht von %@",
        .notifyNewMessagesCount: "%d neue Nachrichten",

        // MARK: Konto löschen
        .deleteBody: """
            Dein Konto wird sofort deaktiviert und ist für andere nicht mehr \
            sichtbar. Alle Daten inklusive Fotos werden nach 30 Tagen endgültig \
            und unwiderruflich gelöscht (siehe Datenschutzerklärung).
            """,
        .deletePasswordLabel: "Zur Bestätigung dein Passwort",
        .deleteConfirm: "Endgültig löschen",
        .deletePasswordMissing: "Bitte gib zur Bestätigung dein Passwort ein.",
        .deleteDone: "Dein Konto wurde deaktiviert und wird in 30 Tagen endgültig gelöscht.",

        // MARK: Paywall
        // Der Bildschirm heißt weiter paywall*, ist aber keine Bezahlwand mehr,
        // sondern ein Angebot, das man von sich aus aufruft.
        .paywallTitle: "FLEXR Premium",
        .paywallSub: """
            FLEXR zu nutzen kostet nichts — dauerhaft. Premium hebt die Grenzen \
            des kostenlosen Kontos auf.
            """,
        .paywallFeatureUnlimited: "Unbegrenzt liken statt 20 pro Tag",
        .paywallSubscribe: "Premium holen",
        .paywallPerMonth: " / Monat",
        .paywallFeatureChat: "Unbegrenzt viele Unterhaltungen gleichzeitig",
        .paywallFeatureCancel: "Monatlich kündbar, keine Mindestlaufzeit, keine versteckten Kosten",
        .paywallReturnNote: """
            Nach der Zahlung kehrst du automatisch in die App zurück. Falls der \
            Status nicht sofort stimmt: kurz warten und erneut öffnen.
            """,

        // MARK: Selfie-Verifizierung
        .verifyTitle: "Foto-Verifizierung",
        .verifyShotOf: "Aufnahme %d / %d",
        .verifyShotIndex: "Aufnahme %d",
        .verifyCameraNeeded: "Kamerazugriff wird benötigt.",
        .verifyPreparing: "Wird vorbereitet …",
        .verifyUploading: "Wird hochgeladen …",
        .verifyRetrySubmit: "Einreichen wiederholen",
        .verifyAllowCamera: "Kamerazugriff erlauben",
        .verifyCapture: "Aufnehmen",
        .verifyPrivacyNote: """
            Die Selfies werden ausschließlich manuell mit deinen Profilfotos \
            verglichen und nach der Prüfung gelöscht. Keine automatisierte \
            biometrische Auswertung.
            """,
        .verifyCaptureFailed: "Aufnahme fehlgeschlagen, bitte erneut.",
        .verifyStartFailed: "Verifizierung konnte nicht gestartet werden.",
        .verifyCameraDenied: "Kamerazugriff abgelehnt. Die Verifizierung braucht Live-Aufnahmen über die Kamera.",
        .verifySubmitted: "Selfies eingereicht — deine Verifizierung ist in Prüfung.",
        .verifySelfieExists: "Dein Selfie liegt bereits vor. Weiter geht es mit dem Ausweis.",
        .verifyNotStarted: "Nicht gestartet",
        .verifyCannotStart: "Die Verifizierung kann gerade nicht beginnen.",
        .verifyRetry: "Erneut versuchen",
        .verifySelfieEyebrow: "Verifizierungs-Selfie",
        .verifySubmitting: "Aufnahme wird eingereicht …",
        .verifyFrameHint: "Gesicht mittig im Rahmen halten und unten auf „Aufnehmen“ tippen.",
        .verifyCameraNotReady: "Die Kamera ist noch nicht bereit, bitte gleich erneut.",
        .verifyAlreadySubmitted: "Deine Verifizierung ist bereits in Prüfung.",
        .verifyNoneRunning: "Für dieses Konto läuft gerade keine Verifizierung.",
        .verifyContinueToDocument: "Weiter zum Ausweis",
        .verifySubmitFailed: "Einreichen fehlgeschlagen. Bitte erneut versuchen.",

        // MARK: Ausweis-Verifizierung
        .documentTitle: "Alter bestätigen",
        .documentLoading: "Wird geladen …",
        .documentStatusLoadFailed: "Status konnte nicht geladen werden.",
        .documentWhyTitle: "Warum wir das brauchen",
        .documentWhy: """
            Um FLEXR nutzen zu können, musst du mindestens 18 Jahre alt sein. \
            Lade einmalig einen gültigen amtlichen Lichtbildausweis hoch — als \
            Foto oder als Datei von deinem Gerät. Wir verwenden ihn \
            ausschließlich zur Alters- und Identitätsprüfung und löschen die \
            Aufnahme nach Abschluss der Prüfung.
            """,
        .documentManualReview: """
            Die Prüfung erfolgt manuell durch einen Menschen — es kommt keine \
            automatische Gesichtserkennung zum Einsatz.
            """,
        .documentTypeLabel: "Dokumenttyp",
        .documentTypeIdCard: "Personalausweis",
        .documentTypePassport: "Reisepass",
        .documentTypeLicense: "Führerschein",
        .documentNeedsBoth: "Vorder- und Rückseite",
        .documentNeedsFront: "Seite mit Foto und Geburtsdatum",
        .documentRedactNote: """
            Du kannst Informationen schwärzen, die für die Altersprüfung nicht \
            benötigt werden.
            """,
        .documentRedactNoteBold: """
            Foto, Geburtsdatum und die zur Prüfung erforderlichen \
            Gültigkeitsinformationen müssen sichtbar bleiben.
            """,
        .documentShotsLabel: "Aufnahmen",
        .documentSideFront: "Vorderseite",
        .documentSideBack: "Rückseite",
        .documentSideOfId: "%@ des Ausweises",
        .documentSideDone: "%@ ✓ — tippen zum Wiederholen",
        .documentCaptureSide: "%@ aufnehmen",
        .documentActionCamera: "Foto aufnehmen",
        .documentActionFile: "Datei wählen",
        .documentSourceHint: """
            Tippe auf einen Platz, um zu fotografieren, oder wähle über „Datei \
            wählen“ eine bestehende Aufnahme von deinem Gerät.
            """,
        .documentFrameHint: """
            Lege den Ausweis flach hin und füll den Rahmen möglichst aus. Achte \
            darauf, dass Foto und Geburtsdatum scharf zu lesen sind.
            """,
        .documentCameraNeeded: "Kamerazugriff wird benötigt.",
        .documentCapture: "Aufnehmen",
        .documentAllowCamera: "Kamerazugriff erlauben",
        .documentCameraDenied: """
            Kamerazugriff abgelehnt. Für die Aufnahme des Ausweises wird die \
            Kamera gebraucht.
            """,
        .documentCaptureFailed: "Aufnahme fehlgeschlagen, bitte erneut.",
        .documentFileReadFailed: """
            Die Datei konnte nicht als Bild gelesen werden. Bitte wähle ein \
            JPEG oder PNG.
            """,
        .documentSubmit: "Zur Prüfung einreichen",
        .documentSubmitting: "Wird übermittelt …",
        .documentSubmitted: "Verifizierung eingereicht — wir prüfen deine Angaben.",
        .documentSubmitFailed: "Einreichen fehlgeschlagen. Bitte erneut versuchen.",
        .documentConsentNote: """
            Die Aufnahmen sind nicht öffentlich abrufbar und werden nach der \
            Prüfung gelöscht.
            """,

        // MARK: Verifizierungs-Gate
        .vgateLoading: "Status wird geladen …",
        .vgateStep1of2: "Schritt 1 von 2",
        .vgateStep2of2: "Schritt 2 von 2",
        .vgateStep1of3: "Schritt 1 von 3",
        .vgateUnlockTitle: "Konto freischalten",
        .vgateReworkEyebrow: "Nachbesserung",
        .vgateReworkTitle: "Wir konnten deine Verifizierung noch nicht abschließen.",
        .vgateReworkChip: "Neue Aufnahme nötig",
        .vgateIntro: """
            FLEXR ist ab 18. Damit hier keine Minderjährigen und keine \
            Fake-Profile landen, prüfen wir einmalig, ob du wirklich du bist \
            und mindestens 18 Jahre alt.
            """,
        .vgateNeedTitle: "Das brauchst du",
        .vgateNeedSelfie: """
            Ein Live-Selfie, frontal in die Kamera — die Kamera öffnet sich \
            erst, wenn du startest
            """,
        .vgateNeedDocument: """
            Eine Aufnahme deines Personalausweises, Reisepasses oder \
            Führerscheins
            """,
        .vgateMediaTitle: "Was mit den Aufnahmen passiert",
        .vgateMediaHuman: """
            Ein Mensch vergleicht Profilfotos, Selfie und Ausweisfoto — keine \
            automatische Gesichtserkennung
            """,
        .vgateMediaPrivate: "Die Aufnahmen sind nicht öffentlich abrufbar",
        .vgateMediaDeleted: "Nach Abschluss der Prüfung werden sie gelöscht",
        .vgateStart: "Verifizierung starten",
        .vgateRetry: "Verifizierung wiederholen",
        .vgateDocumentTitle: "Alter bestätigen",
        .vgateDocumentBody: """
            Dein Selfie liegt vor. Jetzt fehlt noch eine Aufnahme deines \
            amtlichen Lichtbildausweises, damit wir dein Alter bestätigen \
            können.
            """,
        .vgateDocumentBtn: "Ausweis aufnehmen",
        .vgateDocumentBtnRework: "Erneut hochladen",
        .vgateSubmittedEyebrow: "In Prüfung",
        .vgateSubmittedTitle: "Verifizierung wird geprüft",
        .vgateSubmittedChip: "Prüfung läuft",
        .vgateSubmittedBody: """
            Deine Angaben wurden übermittelt. Wir prüfen jetzt, ob du \
            mindestens 18 Jahre alt bist und ob die Verifizierung zu deinem \
            Profil gehört. Sobald die Prüfung abgeschlossen ist, kannst du \
            FLEXR vollständig nutzen.
            """,
        .vgateSubmittedNote: """
            Die Aufnahmen deines Ausweises werden nach Abschluss der Prüfung \
            gelöscht. Die Wartezeit kostet dich nichts — die Nutzung von FLEXR \
            ist ohnehin kostenlos.
            """,
        .vgateRefresh: "Status aktualisieren",
        .vgateChecking: "Wird geprüft …",
        .vgateReviewRunning: "Die Prüfung läuft noch.",
        .vgateMailTitle: "Bestätige deine E-Mail",
        .vgateMailChip: "Bestätigung offen",
        .vgateMailSentTo: "Wir haben dir eine Mail geschickt an:",
        .vgateMailFallback: "deine E-Mail-Adresse",
        .vgateMailBody: """
            Klick den Link darin, dann geht es hier weiter. Nichts angekommen? \
            Schau im Spam-Ordner nach. Der Link gilt 24 Stunden.
            """,
        .vgateMailResend: "Mail erneut senden",
        .vgateMailSending: "Wird gesendet …",
        .vgateMailResent: "Neue Mail an %@ unterwegs. Der Link gilt %d Stunden.",
        .vgateMailSendFailed: "Mail konnte nicht gesendet werden.",
        .vgatePhotoEyebrow: "Profilfotos fehlen",
        .vgatePhotoTitle: "Zuerst deine Profilfotos",
        .vgatePhotoChip: "Fotos fehlen",
        .vgatePhotoBody: """
            Für die Prüfung vergleicht ein Mensch deine Profilfotos mit deinem \
            Selfie und deinem Ausweis. Ohne mindestens %d Fotos kann sie nicht \
            starten.
            """,
        .vgatePhotoBody2: """
            Beim Anlegen deines Profils hat der Upload nicht geklappt. Hol ihn \
            hier nach — danach geht es normal weiter.
            """,
        .vgatePhotoMissing: "Noch %d von %d Pflichtfotos.",
        .vgatePhotoUploading: "Foto wird hochgeladen …",
        .vgatePhotoUploadFailed: "Foto konnte nicht hochgeladen werden.",
        .vgateDoneEyebrow: "Geschafft",
        .vgateUnlockedTitle: "Konto freigeschaltet",
        .vgateUnlockedChip: "Freigeschaltet",
        .vgateUnlockedBody: """
            Deine Prüfung ist durch. Wir laden gerade dein Profil — gleich \
            steht dir FLEXR vollständig offen.
            """,
        .vgateUnlockedCta: "Weiter zu FLEXR",
        .vgateRejectedEyebrow: "Abgeschlossen",
        .vgateRejectedTitle: "Verifizierung nicht erfolgreich",
        .vgateRejectedChip: "Nicht freigeschaltet",
        .vgateRejectedFallback: "Wir konnten deine Verifizierung nicht abschließen.",
        .vgateRejectedBody: """
            Dein Konto wurde nicht freigeschaltet. Wenn du glaubst, dass das \
            ein Fehler ist, schreib uns an flexr.social@proton.me.
            """,
        .vgateRejectedDeleted: """
            Alle Aufnahmen deines Ausweises und dein Verifizierungs-Selfie \
            wurden gelöscht.
            """,

        // MARK: Statuspillen
        .statusBetaFree: "Beta · gratis",
        .statusPremium: "Premium",
        .statusFree: "Gratis",
        .statusNotUnlocked: "Nicht freigeschaltet",
        .statusLikesLeft: "%d Likes",

        // MARK: Netz- und Serverfehler
        .errorTimeout: "Zeitüberschreitung. Bitte Verbindung prüfen und erneut versuchen.",
        .errorUnreachable: "Server nicht erreichbar.",
        .errorConnection: "Verbindung fehlgeschlagen. Bitte erneut versuchen.",
        .errorUnauthorized: "Ungültige oder abgelaufene Anmeldung.",
        .errorPaymentRequired: "Diese Funktion steht gerade nicht zur Verfügung.",
        .errorForbidden: "Zugriff nicht möglich.",
        .errorRateLimited: "Zu viele Versuche. Bitte kurz warten.",
        .errorServer: "Serverfehler. Bitte später erneut versuchen.",
        .errorHttp: "Fehler (%d)",
        .errorCityLookup: "Ort konnte nicht ermittelt werden.",
        .errorPostalCodeUnknown: "Postleitzahl nicht gefunden. Bitte prüfen.",
        .errorNoInternet: "Keine Internetverbindung.",
        .errorCancelled: "Abgebrochen.",
        .errorUnexpectedResponse: "Unerwartete Antwort des Servers.",
        .errorNotFound: "Nicht gefunden.",
        .errorConflict: "Bereits vorhanden.",
        .errorBadUploadURL: "Ungültige Upload-Adresse.",
        .errorBadURL: "Ungültige Adresse.",
        .errorBadRequest: "Anfrage konnte nicht erstellt werden.",
    ]
}
