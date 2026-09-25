import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

/**
 * Release-Signing: wiederverwendet den bestehenden Upload-Key aus dem
 * TWA-Build (android/android.keystore), damit die Play-Store-App weiterhin
 * mit demselben Schlüssel aktualisiert werden kann. Passwort kommt aus
 * android/KEYSTORE-CREDENTIALS.txt (nicht im Git) oder aus -Pflexr.keystorePassword.
 */
val legacyKeystore = rootProject.file("../android/android.keystore")
val legacyCredentials = rootProject.file("../android/KEYSTORE-CREDENTIALS.txt")
val keystorePassword: String? = (findProperty("flexr.keystorePassword") as String?)
    ?: legacyCredentials.takeIf { it.isFile }
        ?.readLines()
        ?.firstOrNull { it.startsWith("Passwort (Store + Key):") }
        ?.substringAfter(": ")
        ?.trim()

android {
    namespace = "flexr.social.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "flexr.social.app"
        minSdk = 26
        targetSdk = 36
        // Am 10.09.2026 lehnte die Play Console nacheinander versionCode 43 UND
        // 50 mit "wurde bereits verwendet" ab. Beide waren nie zuvor gebaut
        // worden - die Console kannte sie trotzdem, weil ein Bundle schon in
        // der Bibliothek des Kontos lag. Was dort sonst noch liegt, ist von
        // hier aus nicht einsehbar, und jeder Fehlversuch kostet einen
        // kompletten Build.
        //
        // Deshalb jetzt 100 statt 51: reichlich Abstand nach oben. Luecken im
        // versionCode sind zulaessig, nur Rueckwaertsspruenge nicht - die
        // Nummer muss lediglich groesser sein als jede zuvor hochgeladene.
        // Bewusst KEIN datumsbasiertes Schema (20260910xx): Das liegt dicht
        // unter der harten Obergrenze von 2.100.000.000 und laesst sich nie
        // wieder verkleinern.
        //
        // versionName bleibt 2.6.0: Der Release IST 2.6.0, verbrannt sind nur
        // Build-Nummern. versionCode ist der Zaehler, versionName die Fassung.
        // 101/2.6.1 am 11.09.2026: 2.6.0 (versionCode 100) stuerzt beim Start ab.
        // Der Stapelabzug war nicht zu bekommen - kein Rechner am Geraet, und
        // ohne Ursache waere ein blosser Neubau derselben Quellen nur eine
        // Wette gewesen. Diese Fassung bringt deshalb zweierlei mit:
        //
        //   1. core/diagnostics/CrashLog.kt - schreibt den Stapelabzug in
        //      Android/data/flexr.social.app/files/. Stuerzt sie wieder ab,
        //      ist die Ursache danach ohne Rechner ablesbar.
        //   2. Die Korrektur an core/locale/ProvideAppLanguage.kt: Der dort
        //      untergeschobene LocalContext hatte keine Activity mehr in der
        //      baseContext-Kette. Das ist unabhaengig vom Absturz falsch und
        //      der plausibelste Verursacher - die Zweisprachigkeit kam mit
        //      2.6.0 herein, 2.5.5 lief noch.
        //
        // Siehe HANDOFF.md, Abschnitt "Absturz beim Start der Android-App".
        //
        // 102/2.6.2 am 11.09.2026 (Sitzung 3): 2.6.1 lief zwar an, hatte aber
        // zwei eigene Fehler - den Sprachregler doppelt (auch oben in der
        // Kopfzeile statt nur im Profil) und einen Sprachwechsel, der den
        // Reglerzustand umstellte, aber keinen einzigen Text (siehe HANDOFF,
        // Sitzung 11.09.2026 (3)). Beide sind hier behoben; dabei zusaetzlich
        // ein reiner Build-Fehler gefunden (KSP2 verdoppelte Hilt-Klassen im
        // Release-Build) und mit ksp.useKSP2=false umgangen. Ab hier bekommt
        // jeder tatsaechlich gebaute und ausgelieferte Stand eine eigene
        // Versionsnummer statt denselben Code unter derselben Nummer neu zu
        // bauen - so bleibt am Dateinamen erkennbar, welcher Fix schon drin
        // ist.
        //
        // 103/2.6.3 am 12.09.2026: In 2.6.2 aenderte der Sprachregler weiterhin
        // keinen einzigen Text, und auf dem Login-Schirm gab es ueberhaupt
        // keinen mehr. Diese Fassung schaltet die Sprache am Basis-Context der
        // Activity um (MainActivity.attachBaseContext) statt zur Laufzeit an
        // den Ressourcen zu drehen, stellt den Regler im ausgeloggten Graphen
        // wieder auf, und schaltet unten die Sprach-Splits des App Bundles ab.
        //
        // 104/2.6.4 am 12.09.2026: Statuspille nur noch "Beta", der Hinweis
        // unter "Sprache" enger gesetzt, und mindestens drei Profilfotos beim
        // Anlegen eines Kontos. 2.6.3 war zu diesem Zeitpunkt schon gebaut und
        // aufs Geraet gespielt - deshalb eine eigene Nummer statt eines zweiten
        // Bundles unter 103 mit anderem Inhalt.
        //
        // 105/2.6.5 am 12.09.2026: Die Leerzustaende von Matches und Chats
        // stehen jetzt mittig wie der im Swipe-Deck. 2.6.4 war zu diesem
        // Zeitpunkt schon gebaut und hochgeladen.
        //
        // 106/2.6.6 am 12.09.2026: Auch der Leerzustand im Chatverlauf steht
        // mittig - als einziger im Projekt fehlte dem EmptyState dort das
        // align(Center), er klebte deshalb oben an der Kopfzeile.
        //
        // 107/2.6.7 am 12.09.2026: Der Benachrichtigungs-Schalter im Konto
        // stand fuer neue Konten von Anfang an auf "an", ohne dass je die
        // POST_NOTIFICATIONS-Laufzeitberechtigung eingeholt wurde - der Screen
        // fragt sie jetzt beim ersten Laden einmalig nach und stellt den
        // Schalter bei Ablehnung zurueck auf "aus".
        //
        // 108/2.6.8 am 16.09.2026: Zwei Fehler derselben Bauart. Ein 401 von
        // /api/auth/login galt als abgelaufene Sitzung, weil der Interceptor
        // pauschal alles unter /api/auth/ ausnahm bzw. nicht ausnahm - wer
        // sich vertippte, las "Sitzung abgelaufen" statt "E-Mail oder Passwort
        // falsch". Und der Chat-Poll lief im ViewModel-Umfang weiter, auch wenn
        // der Chat nicht zu sehen war, und quittierte dabei Nachrichten als
        // gelesen, die niemand angesehen hatte.
        // 109/2.6.9 am 16.09.2026: FLEXR Premium bekommt seine drei
        // Zusatzfunktionen (Abzeichen, letzten Swipe zuruecknehmen, "Wer dich
        // geliket hat"). Sie sind unsichtbar, solange PREMIUM_ENABLED am
        // Server aus steht - dann ist is_premium fuer jeden falsch. Dazu der
        // ersetzte Login-Hinweis: Der versprochene Probemonat existiert seit
        // dem 10.09.2026 nicht mehr.
        // 110/2.6.10 am 17.09.2026: Befunde der Durchsicht vor der
        // iOS-Einreichung. Die Rechtstexte nannten in dieser App noch 5 € und
        // einen Probemonat - beides gibt es seit dem 10.09.2026 nicht mehr,
        // iOS und Web waren laengst richtig. Dazu die Folge der endgueltigen
        // Ablehnung (alle Profilfotos werden geloescht) in der
        // Datenschutzerklaerung ergaenzt, und der 403 "verification_required"
        // wird endlich behandelt: Bisher blieb der Nutzer auf dem Deck mit
        // "Zugriff nicht moeglich" stehen, statt ins Verifizierungs-Gate
        // geleitet zu werden - auf iOS laeuft das seit jeher richtig.
        // 111/2.7.0 am 17.09.2026: FLEXR Premium ist scharf geschaltet. Fuer
        // diese App heisst das zweierlei. Erstens gelten die Grenzen des
        // kostenlosen Kontos jetzt auch hier - die App hat bis 2.6.10 "Beta,
        // alles unbegrenzt" angezeigt und waere an der ersten Grenze ohne
        // Erklaerung stehen geblieben. Zweitens wird hier trotzdem **nichts
        // verkauft**: Ein Abschluss ausserhalb von Play Billing verstiesse
        // gegen die Payments-Policy, also bietet der Server App-Clients gar
        // keinen an (siehe backend/app/clients.py). Gekauft wird im Browser,
        // die Leistung daraus wirkt auch hier.
        // 112/2.7.1 am 17.09.2026: Das Beta-Abzeichen zeigte seit dem
        // Scharfschalten "Beta · n Likes" - der Like-Zaehler war der Kopfzeile
        // zu viel, die Restzahl steht ohnehin im Konto. Zurueck auf "Beta".
        // 113/2.7.1 am 18.09.2026: Kein Quellcode-Unterschied zu 112 - erst
        // jetzt stehen die vier Firebase-Werte in gradle.properties (Block A
        // der Einrichtungsanleitung), FCM_SERVICE_ACCOUNT_FILE auf dem Server.
        // 112 wurde nie in die Play Console geladen; trotzdem eine neue
        // Nummer statt derselben wiederzuverwenden, damit spaeter zweifelsfrei
        // feststeht, welche .aab tatsaechlich Push zustellen kann.
        // 114/2.7.2 am 18.09.2026: 2.7.1 gab es schon (112, 113) - eigener
        // Versionsname, damit in der Play Console keine Verwechslung entsteht.
        // Quellcode weiterhin unveraendert zu 113.
        // 115/2.7.3 am 18.09.2026: 114 startet auf einem echten Geraet nicht
        // mehr (sofortiger Absturz, generischer Systemdialog "FLEXR
        // geschlossen"). Kein Code-Fehler gefunden, der das erklaeren wuerde -
        // Unit-Tests und ein sauberer clean-Build mit R8 laufen unveraendert
        // durch. Deckt sich stattdessen mit dem 2.6.0-Muster (11.09.2026):
        // release-2.6.6 bis 2.7.1 haben allesamt NUR ein .aab exportiert,
        // keine installierbare Universal-APK mehr - wer ein .aab direkt (oder
        // umbenannt) aufspielt statt es ueber Play zu installieren, bekommt
        // eine Installation ohne die passenden Splits, und Android beendet
        // die App beim Start sofort wieder. Deshalb diesmal wieder beides
        // exportiert. Bleibt der Absturz bestehen, braucht es den
        // Absturzbericht vom Geraet (Android/data/flexr.social.app/files/) -
        // dann ist es doch ein echter Code-Fehler.
        // 116/2.7.4 am 18.09.2026: 115 stuerzt weiterhin sofort beim Start ab -
        // die Universal-APK war also doch nicht die Ursache, es ist ein
        // echter Code-Fehler. Nur ist der Absturzbericht unter
        // Android/data/flexr.social.app/files/ auf dem betroffenen Geraet
        // nicht mehr zu holen: Weder "Eigene Dateien" noch X-plore (auch
        // nicht mit dessen SAF-Grant-Trick) kommen seit Android 11 noch an
        // Android/data heran, und Rechner (USB, gleiches WLAN fuer
        // kabelloses ADB) steht keiner zur Verfuegung. Deshalb rein
        // diagnostisch: CrashLog.kt legt den Bericht jetzt zusaetzlich in
        // Downloads/ ab (ueber MediaStore, ohne Sonderrechte erreichbar).
        // Quellcode sonst unveraendert - dieser Build dient nur dazu, den
        // naechsten Absturz tatsaechlich einsehen zu koennen.
        // 117/2.7.5 am 18.09.2026: Die Downloads-Kopie aus 116 hat den
        // Absturzbericht tatsaechlich geliefert - der eigentliche Fehler,
        // gefunden und behoben. PlayBillingService baute den BillingClient
        // mit einem LEEREN PendingPurchasesParams; seit Billing Library 7
        // verlangt das build() zwingend enableOneTimeProducts(), sonst wirft
        // es "Pending purchases for one-time products must be supported." -
        // und das synchron als Property-Initializer, also bei jedem
        // App-Start, sobald Hilt PlayBillingService konstruiert. Weder
        // Firebase noch die .aab/.apk-Distribution (115/116) waren die
        // Ursache - beides Fehlspuren ohne Absturzbericht.
        // 118/2.7.6 am 18.09.2026: Bug-Durchgang (c5582aa). Suchumkreis endet
        // jetzt dort, wo der Server kappt (50 km ohne Premium statt 250 am
        // Regler), die Karte kommt bei aufgebrauchtem Like-Kontingent zurueck
        // statt verschluckt zu werden, das Schlosssymbol ist vom
        // Premium-Bildschirm verschwunden (der Zurueck-Knopf passte sonst
        // nicht aufs Bild), und die Aboverwaltung sitzt unten in den
        // Einstellungen statt unter dem Profilbild.
        // 119/2.7.7 am 18.09.2026: Benachrichtigungen bei **beendeter** App.
        // Das Firebase-SDK zeichnet sie in diesem Fall selbst - es bekommt
        // jetzt Symbol, Farbe und Kanal ueber das Manifest mit, und ein Tipp
        // darauf fuehrt wieder in die Chats. Dazu der Hinweis auf die
        // Akku-Ausnahme in den Benachrichtigungseinstellungen (ohne sie legt
        // Android die App schlafen, und dann kommt gar nichts) und zwei
        // Einblendungen weniger beim Zuruecknehmen eines Swipes.
        // 120/2.7.8 am 19.09.2026: Feinschliff im Konto-Bereich. "Profil
        // gespeichert" verschwindet jetzt von selbst nach 2s statt auf einen
        // Klick zu warten; die Statuskarte "FLEXR Premium laeuft ..." ist fuer
        // Premium-Konten komplett weg (Profil ruekt nach); "Aboverwaltung"
        // heisst nur noch "Abo verwalten" und steht in normaler weisser
        // Schrift statt als Link. Die beiden Rewind-Einblendungen aus 2.7.7
        // waren in den gemeldeten Screenshots noch zu sehen, weil dort ein
        // aelterer Build lief - der Code dafuer ist unveraendert seit 2.7.7.
        // 121/2.7.9 am 19.09.2026: Zweiter Feinschliff im Konto-Bereich, auf
        // Screenshots hin. Die Statuskarte "Dein Konto ist kostenlos ..."
        // faellt jetzt auch fuer Nicht-Premium-Konten weg - "Profil" ruekt
        // direkt unter den Kopf bzw. den Verifizierungs-Hinweis nach. Der
        // blaue Haken haengt jetzt an der Grundlinie von Name+Alter
        // (alignByBaseline) statt an der Zeilenhoehe box-zentriert zu sein -
        // er sass dadurch sichtbar zu hoch, auf Hoehe der Versalienoberkante.
        // Alle Popup-Meldungen verschwinden jetzt nach zwei Sekunden von
        // selbst, wie schon zuvor in der Web-App - einzige Ausnahme bleibt die
        // Empfangsbestaetigung mit Aktenzeichen beim Melden eines Profils
        // (Art. 16 Abs. 4 DSA), die bleibt stehen. Auf dem Premium-Bildschirm
        // sind die beiden erklaerenden Absaetze ("FLEXR zu nutzen kostet
        // nichts ..." und "Nach der Zahlung kehrst du automatisch ...") weg;
        // der Zurueck-Knopf ruekt dadurch weiter nach oben.
        // 122/2.7.10 am 19.09.2026: Die alignByBaseline()-Korrektur aus 2.7.9
        // hat den Haken/Stern sichtbar schlimmer gemacht (viel zu weit oben) -
        // Oswald's Grundlinie liegt in der Zeile ungewoehnlich tief, die
        // Row-Baseline-Verteilung hat den Haken dadurch weit nach oben
        // gezogen. Stattdessen wird jetzt die Zeilenbox des Namens selbst auf
        // ihre tatsaechlichen Schriftmetriken zusammengezogen (kein
        // Android-Legacy-"Font Padding", Zeilenhoehe mittig getrimmt) - das
        // macht die Box um Text und Abzeichen so eng wie moeglich an das
        // sichtbare Schriftbild, wodurch die normale Row-Zentrierung von
        // selbst passt, ganz ohne Sonderbehandlung der Abzeichen. Dazu ein
        // neuer "Premium aktivieren"-Knopf im Kopf, links von der
        // Beta/Status-Pille, analog zum Web - fuehrt auf den Premium-Screen.
        // 123/2.7.11 am 20.09.2026: Feinschliff auf Screenshots hin. Im
        // Benachrichtigungen-Dialog waren die Anlass-Ueberschriften ("Bei
        // geschlossener App", "Neues Match" usw.) klein und grau (labelMedium)
        // gesetzt, waehrend "E-Mail"/"App-Benachrichtigung" darunter gross und
        // weiss standen - optisch genau verkehrt herum. Ueberschriften stehen
        // jetzt gross und weiss (titleMedium/chalk), die Schalter-Beschriftung
        // kleiner (bodyMedium); nach jeder Ueberschrift ist jetzt ein
        // Abstand, bevor der erklaerende Text folgt. Im Impressum unter
        // "Unternehmensrechtliche Angaben" fehlte der Wert-Spalte in der
        // Schluessel-Wert-Tabelle ein weight(1f) - ohne das wurde sie mit der
        // vollen Zeilenbreite statt der Restbreite gemessen, wodurch der Wert
        // bei einer mehrzeilig umbrechenden Beschriftung (z. B.
        // "Firmenbuchnummer:") an deren letzter Zeile statt an deren erster
        // ausgerichtet erschien.
        // 124/2.7.12 am 20.09.2026: Im Benachrichtigungen-Dialog steht der
        // Rechtstext ("Rechtlich noetige Nachrichten...") jetzt als Blocksatz
        // (TextAlign.Justify) statt linksbuendig mit unterschiedlich langen
        // Zeilenenden; "Moderationsentscheidungen" traegt dafuer einen
        // weichen Trennstrich (U+00AD) nach "Moderations", damit das Wort bei
        // Bedarf dort umbricht statt als Ganzes in die naechste Zeile zu
        // rutschen und eine Luecke zu hinterlassen. Zwischen der "E-Mail"/
        // "App-Benachrichtigung"-Beschriftung und dem erklaerenden Text
        // darunter ist jetzt ebenfalls ein kleiner Abstand (3dp).
        // 125/2.7.13 am 20.09.2026: "Wenn du sieben Tage nicht in FLEXR
        // warst" hiess korrekt "... nicht AUF FLEXR warst"; der Rechtstext
        // im Benachrichtigungen-Dialog ist jetzt auf einen Satz gekuerzt
        // ("Rechtlich noetige Nachrichten lassen sich nicht deaktivieren.").
        // Im Konto-Header sass der blaue Verifiziert-Haken neben Name/Alter
        // sichtbar zu hoch (Oswalds Versal-/Ascent-Luecke, siehe Kommentar
        // in AccountScreen.kt) - analog zum Web-Haken jetzt mit einem
        // kleinen manuellen Offset nach unten korrigiert.
        // 126/2.7.14 am 20.09.2026: Gym laesst sich nur noch alle 3 Monate
        // aendern (Umgehungsschutz fuer den per Gym-Adresse berechneten
        // FLEXR-Premium-Suchumkreis), mit erklaerendem Info-Dialog am
        // Gym-Feld. Ausserdem derselbe Oswald-Offset wie beim Haken oben
        // jetzt auch am Premium-Stern daneben (sass sichtbar hoeher) und an
        // den Kopf-Badges "Premium"/"Beta"-Pille neben der FLEXR-Wortmarke.
        // 127/2.7.15 am 20.09.2026: Premium-Vorteilsliste auf der Paywall
        // vereinheitlicht (feste Texte ohne Vergleich zu den Server-Zahlen,
        // z. B. "Unbegrenzt liken" statt "Unbegrenzt liken statt X pro Tag").
        // 128/2.7.16 am 20.09.2026: "Hilfe & Rechtliches" im Konto-Bereich
        // hatte keinen Eintrag fuer das Ruecktrittsrecht - neue Zeile
        // "Ruecktrittsrecht" oeffnet flexr.social/widerruf.html im Custom
        // Tab (die Online-Ruecktrittsfunktion dort ist ein Formular mit
        // Server-Anbindung, keine reine Textseite wie die uebrigen nativ
        // nachgebauten Rechtstexte).
        // 129/2.7.17 am 21.09.2026: Der Custom Tab aus 128 faellt wieder weg -
        // das Ruecktrittsrecht ist jetzt LegalDocument.WIDERRUF und oeffnet
        // wie alle anderen Rechtstexte nativ in der LegalScreen, inklusive der
        // eingebetteten Online-Ruecktrittsfunktion (LegalBlock.WithdrawalForm,
        // POST /api/withdrawal direkt aus der App statt ueber den Browser).
        // 130/2.7.18 am 22.09.2026: "Passwort vergessen?" im Login, Passwort
        // und E-Mail-Adresse im Konto aenderbar, Accept-Language mit der
        // App-Sprache (Server-Fehlermeldungen zweisprachig), eigenes Bild und
        // Loeschbarkeit der Fotos vom Server (abgelehnte Fotos blockierten
        // das Loeschen), Lint-Fehler behoben.
        // 131/2.7.19 am 25.09.2026: Start ohne Netz fuehrt nicht mehr auf den
        // Login (AppState.Unreachable mit Neuversuch), Chatnachrichten mit
        // Datum, Schrittanzeige bis zum ersten Swipe (JourneyBar),
        // Datenschutz-Kurzfassung um Push-Mitteilungen ergaenzt.
        versionCode = 131
        versionName = "2.7.19"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        // Nur die Sprachen ausliefern, die es wirklich gibt: Deutsch als
        // Ausgangssprache, Englisch als Uebersetzung (res/values-en).
        resourceConfigurations += listOf("de", "en")
    }

    signingConfigs {
        if (legacyKeystore.isFile && keystorePassword != null) {
            create("release") {
                storeFile = legacyKeystore
                storePassword = keystorePassword
                keyAlias = "flexr"
                keyPassword = keystorePassword
            }
        }
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
            isMinifyEnabled = false
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = signingConfigs.findByName("release")
            // Die Play Console warnt seit versionCode 35, das Bundle enthalte
            // nativen Code ohne Debug-Symbole. Diese Einstellung behebt das
            // NICHT, und nichts an unserem Build kann es beheben:
            //
            // Der native Code stammt ausschliesslich aus Fremdbibliotheken
            // (androidx.graphics.path, datastore_shared_counter sowie CameraX'
            // image_processing_util_jni und surface_util_jni). Alle vier .so
            // liefert Google fertig gestripped aus - mit llvm-readelf geprueft:
            // weder .debug_* noch .symtab. extractNativeDebugMetadata laeuft
            // durch und schreibt ein leeres Verzeichnis, weil es nichts zu
            // extrahieren gibt. Am 31.08.2026 eigens ein NDK (r27d) nachinstalliert
            // und sauber neu gebaut: byte-identisches Bundle, Warnung unveraendert.
            //
            // Die Warnung ist damit hinzunehmen. Sie kostet nur die Lesbarkeit
            // von Abstuerzen INNERHALB dieser vier Google-Bibliotheken.
            // FULL bleibt stehen, damit eigener nativer Code - falls je welcher
            // dazukommt - seine Symbole automatisch mitbringt. Ein NDK ist dafuer
            // aktuell nicht noetig; ohne eines ist die Zeile ein No-Op.
            ndk {
                debugSymbolLevel = "FULL"
            }
        }
    }

    /**
     * Keine Sprach-Splits im App Bundle.
     *
     * Standardmaessig legt das Bundle jede Sprache in ein eigenes Split-APK,
     * und Play liefert dem Geraet nur die Splits seiner Systemsprache aus. Auf
     * einem deutsch eingestellten Telefon waere `res/values-en` damit gar nicht
     * installiert — die App kann dann umschalten, worauf sie will, und faellt
     * trotzdem auf die deutschen Texte zurueck.
     *
     * Genau dieses Bild hat der Nutzer zweimal gemeldet (2.6.1 und 2.6.2: der
     * Regler sprang um, kein Text aenderte sich). Vom Rechner aus war es nicht
     * zu sehen, weil das direkt aufgespielte APK aus `assembleProdRelease`
     * immer alle Sprachen enthaelt; nur der Weg ueber die Play Console
     * schneidet sie weg.
     *
     * Der Aufpreis sind ein paar Kilobyte Downloadgroesse fuer zwei Sprachen.
     * Das ist die Bedingung dafuer, dass eine App ihre Sprache selbst
     * umstellen darf.
     */
    bundle {
        language {
            enableSplit = false
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        isCoreLibraryDesugaringEnabled = false
    }

    kotlin {
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        }
    }

    packaging {
        resources {
            excludes += setOf(
                "/META-INF/{AL2.0,LGPL2.1}",
                "/META-INF/DEPENDENCIES",
                "/META-INF/LICENSE*",
            )
        }
    }

    /**
     * Firebase-Zugangsdaten fuer Push.
     *
     * Bewusst ueber gradle.properties statt google-services.json: Mit dem
     * google-services-Plugin liesse sich die App ohne diese Datei gar nicht
     * bauen, und sie gehoert nicht ins Repository. So baut jeder Stand, und wo
     * die vier Werte fehlen, bleibt Push schlicht aus - die App faellt dann auf
     * den Hintergrundabgleich zurueck, so wie vor dem 17.09.2026.
     *
     * Zu setzen in ~/.gradle/gradle.properties oder per -P:
     *   flexr.firebase.projectId, flexr.firebase.appId,
     *   flexr.firebase.apiKey, flexr.firebase.senderId
     */
    defaultConfig {
        val firebase = listOf(
            "FIREBASE_PROJECT_ID" to "flexr.firebase.projectId",
            "FIREBASE_APP_ID" to "flexr.firebase.appId",
            "FIREBASE_API_KEY" to "flexr.firebase.apiKey",
            "FIREBASE_SENDER_ID" to "flexr.firebase.senderId",
        )
        firebase.forEach { (feld, eigenschaft) ->
            buildConfigField("String", feld, "\"${findProperty(eigenschaft) ?: ""}\"")
        }
    }

    /** API-Endpunkte pro Build-Typ — Debug kann gegen die lokale Testumgebung laufen. */
    flavorDimensions += "backend"
    productFlavors {
        create("prod") {
            dimension = "backend"
            buildConfigField("String", "API_BASE_URL", "\"https://flexr.social/\"")
        }
        create("local") {
            dimension = "backend"
            applicationIdSuffix = ".local"
            versionNameSuffix = "-local"
            // 10.0.2.2 = Host-Rechner aus Sicht des Android-Emulators
            buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000/\"")
        }
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.core.splashscreen)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.browser)
    implementation(libs.billing.ktx)
    implementation(libs.firebase.messaging)
    implementation(libs.coroutines.play.services)

    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)

    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons.extended)
    implementation(libs.compose.animation)
    implementation(libs.compose.foundation)
    debugImplementation(libs.compose.ui.tooling)

    implementation(libs.androidx.navigation.compose)

    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.hilt.navigation.compose)
    implementation(libs.hilt.work)
    ksp(libs.hilt.ext.compiler)

    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)

    implementation(libs.retrofit)
    implementation(libs.retrofit.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)

    implementation(libs.coil.compose)

    implementation(libs.camera.core)
    implementation(libs.camera.camera2)
    implementation(libs.camera.lifecycle)
    implementation(libs.camera.view)

    implementation(libs.androidx.datastore.preferences)
    implementation(libs.androidx.work.runtime)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.okhttp.mockwebserver)
    testImplementation(libs.turbine)
    androidTestImplementation(libs.androidx.test.junit)
    androidTestImplementation(libs.androidx.test.espresso)
}
