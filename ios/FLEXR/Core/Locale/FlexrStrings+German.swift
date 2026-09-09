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

        // MARK: Login
        .loginEyebrow: "Willkommen zurück",
        .loginTitle: "Zurück ins\nGym-Date.",
        .loginSubtitle: "Melde dich mit deinen Zugangsdaten an.",
        .loginSubmit: "Einloggen",
        .loginRegisterHint: "Neu hier? Erstell dein Profil und teste FLEXR einen Monat gratis.",
        .loginMissingFields: "Bitte E-Mail und Passwort angeben.",
        .loginReactivateTitle: "Konto reaktivieren?",
        .loginReactivateConfirm: "Jetzt reaktivieren",
        .loginFailed: "Login fehlgeschlagen.",
        .loginReactivateFailed: "Reaktivierung fehlgeschlagen.",
        .loginEmailPlaceholder: "max@example.com",

        // MARK: Registrierung
        .registerTitle: "Dating für Leute,\ndie auch montags\nBeintag machen.",
        .registerSubtitle: """
            Erstell dein Profil. Während der Beta-Phase kostenlos — die \
            Mitgliedschaft von 5 €/Monat ist bis auf weiteres ausgesetzt. \
            Aktuell nur in Österreich verfügbar.
            """,
        .registerPasswordPlaceholder: "Mind. 8 Zeichen",
        .registerNamePlaceholder: "Max",
        .registerPhotosLabel: "Fotos (mind. 1, max. 6)",
        .registerPhotoPreparing: "Foto wird vorbereitet …",
        .registerConsentPrefix: """
            Ich willige ein, dass meine Angaben zu Geschlecht und gesuchtem \
            Geschlecht (daraus ableitbar: sexuelle Orientierung) gemäß \

            """,
        .registerConsentLink: "Datenschutzerklärung",
        .registerConsentSuffix: " verarbeitet werden.",
        .registerSubmit: "Profil erstellen & Probemonat starten",
        .registerErrRequired: "Bitte E-Mail, Passwort (min. %d Zeichen), Name und Geburtsdatum angeben.",
        .registerErrUnder18: "Du musst mindestens 18 Jahre alt sein.",
        .registerErrBirthdate: "Bitte ein gültiges Geburtsdatum angeben.",
        .registerErrPostalCode: "Bitte eine gültige österreichische Postleitzahl eingeben (Ort wird automatisch ermittelt).",
        .registerErrGender: "Bitte ein Geschlecht auswählen.",
        .registerErrGym: "Bitte ein Gym aus der Liste auswählen.",
        .registerErrPhoto: "Bitte lade mindestens ein Foto hoch.",
        .registerErrConsents: "Bitte beide Zustimmungen ankreuzen, um fortzufahren.",
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
        .registerWaiverPrefix: """
            Ich stimme zu, dass der Zugang sofort mit Registrierung beginnt, und \
            nehme zur Kenntnis, dass ich dadurch mein 14-tägiges Rücktrittsrecht \
            verliere (siehe \

            """,
        .registerWaiverLink: "AGB",
        .registerWaiverSuffix: ", §18 FAGG).",
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
        .swipeTitle: "Profile in deiner Nähe",
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
        .matchTitle: "Match!",
        .matchSub: "Du und %@ habt euch gegenseitig geliked.",
        .matchContinue: "Weiter swipen",

        // MARK: Matches / Chats
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
        .photoUploading: "Foto wird hochgeladen …",
        .photoHintNone: "Mindestens ein Foto ist nötig, damit dein Profil sichtbar ist.",
        .photoHintOk: "Dein Profil ist sichtbar. Neue Fotos werden kurz geprüft.",
        .photoHintPending: "Dein Foto wird geprüft.",
        .photoHintRejected: "Foto abgelehnt. Bitte lade ein anderes hoch.",
        .photoMinOne: "Mindestens ein Foto ist erforderlich. Lade zuerst ein weiteres hoch.",
        .photoUploadFailed: "Foto-Upload fehlgeschlagen.",
        .photoLightboxPosition: "Foto %d von %d",
        .photoTooSmall: "Foto zu klein (%d×%d). Mindestens %d×%d Pixel.",
        .photoReadFailed: "Foto konnte nicht geladen werden.",

        // MARK: Konto
        .accountSectionProfile: "Profil",
        .accountSectionPhotos: "Fotos",
        .accountStatusBetaFree: """
            FLEXR ist in der Beta-Phase kostenlos — die Mitgliedschaft von \
            5 €/Monat ist bis auf weiteres ausgesetzt. Es ist kein \
            Zahlungsmittel hinterlegt und es wird nichts abgebucht.
            """,
        .accountStatusActive: "Dein Abo ist aktiv (5 €/Monat).",
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
        .accountErrPhotoBeforeSave: "Bitte lade mindestens ein Foto hoch, bevor du speicherst.",
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
        .accountTrialDaysLeft: "Noch %d Tag(e) gratis Probemonat.",
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

        // MARK: Verifizierungs-Kurzstatus
        .verifyBadgeChecking: "Prüfung läuft …",
        .verifyBadgeConfirmAge: "Alter bestätigen",
        .verifyBadgeVerified: "Dein Profil ist verifiziert — andere sehen den blauen Haken neben deinem Namen.",
        .verifyBadgeReviewing: "Deine Verifizierung wird geprüft. Nach der Freigabe bekommst du den blauen Haken.",
        .verifyBadgeDocumentMissing: """
            Es fehlt noch die Aufnahme deines amtlichen Lichtbildausweises. \
            Diesen Schritt schließt du gerade noch unter flexr.social ab.
            """,
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
        .paywallTitle: "Probemonat vorbei",
        .paywallSub: "Dein kostenloser Monat ist abgelaufen. Schalte FLEXR wieder frei.",
        .paywallFeatureUnlimited: "Unbegrenzt swipen & matchen in deinem Umkreis",
        .paywallSubscribe: "Jetzt abonnieren",
        .paywallFeatureChat: "Chat mit allen Matches inklusive",
        .paywallFeatureCancel: "Monatlich kündbar, keine versteckten Kosten",
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
        .verifyDone: "Fertig!",
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
        .verifySubmitFailed: "Einreichen fehlgeschlagen. Bitte erneut versuchen.",

        // MARK: Statuspillen
        .statusBetaFree: "Beta · gratis",
        .statusSubscribed: "Abo aktiv",
        .statusTrialDays: "Testmonat: %dd",
        .statusExpired: "Abgelaufen",

        // MARK: Netz- und Serverfehler
        .errorTimeout: "Zeitüberschreitung. Bitte Verbindung prüfen und erneut versuchen.",
        .errorUnreachable: "Server nicht erreichbar.",
        .errorConnection: "Verbindung fehlgeschlagen. Bitte erneut versuchen.",
        .errorUnauthorized: "Ungültige oder abgelaufene Anmeldung.",
        .errorPaymentRequired: "Probemonat abgelaufen. Bitte Abo abschließen.",
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
