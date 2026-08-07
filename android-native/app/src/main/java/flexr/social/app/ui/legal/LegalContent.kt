package flexr.social.app.ui.legal

import flexr.social.app.ui.navigation.LegalDocument

/**
 * Rechtstexte als strukturierte Daten.
 *
 * Die Web-App lud Impressum, AGB, Datenschutz und FAQ als HTML-Seiten nach.
 * Nativ sind es Compose-Bausteine: kein Nachladen, offline verfügbar, mit der
 * Systemschriftgröße skalierbar und für TalkBack korrekt ausgezeichnet.
 * Inhaltlich sind die Texte unverändert übernommen — sie sind rechtsverbindlich.
 */
sealed interface LegalBlock {
    data class Heading(val text: String) : LegalBlock
    data class Paragraph(val text: String) : LegalBlock
    data class Bullets(val items: List<String>) : LegalBlock
    data class Lettered(val items: List<String>) : LegalBlock
    data class KeyValues(val rows: List<Pair<String, String>>) : LegalBlock
    data class Table(val headers: List<String>, val rows: List<List<String>>) : LegalBlock
    data class Faq(val question: String, val answer: String) : LegalBlock
    data class Note(val text: String) : LegalBlock
}

data class LegalPage(
    val document: LegalDocument,
    val intro: String? = null,
    val blocks: List<LegalBlock>,
)

object LegalContent {

    fun of(document: LegalDocument): LegalPage = when (document) {
        LegalDocument.FAQ -> faq
        LegalDocument.IMPRESSUM -> impressum
        LegalDocument.DATENSCHUTZ -> datenschutz
        LegalDocument.AGB -> agb
        LegalDocument.SICHERHEIT -> sicherheit
        LegalDocument.NUTZUNGSRICHTLINIEN -> nutzungsrichtlinien
        LegalDocument.STRAFVERFOLGUNG -> strafverfolgung
    }

    private val faq = LegalPage(
        document = LegalDocument.FAQ,
        intro = "Alles Wichtige zu FLEXR — der Dating-App für Gym-People in Österreich. " +
            "Tippe auf eine Frage, um die Antwort zu öffnen.",
        blocks = listOf(
            LegalBlock.Faq(
                "Was ist FLEXR?",
                "FLEXR ist eine Dating-App für Menschen, denen Training und Gym wichtig sind. " +
                    "Du findest Matches nach deinem Fitnessstudio und deiner Stadt — Leute in ganz " +
                    "Österreich, die einen ähnlichen Lifestyle leben wie du.",
            ),
            LegalBlock.Faq(
                "Was kostet FLEXR?",
                "Du testest FLEXR einen Monat gratis. Danach kostet es 5 € pro Monat, jederzeit " +
                    "kündbar — ohne Mindestlaufzeit.",
            ),
            LegalBlock.Faq(
                "In welchen Städten ist FLEXR verfügbar?",
                "FLEXR ist in ganz Österreich verfügbar. Die Matches richten sich nach deinem Gym " +
                    "und deinem Umkreis — von Wien über Graz, Linz und Salzburg bis Innsbruck und " +
                    "Klagenfurt.",
            ),
            LegalBlock.Faq(
                "Wie funktioniert das Matching?",
                "Du wählst dein Gym und deinen Suchradius. FLEXR zeigt dir passende Profile in der " +
                    "Nähe. Liken sich zwei Personen gegenseitig, entsteht ein Match und ihr könnt im " +
                    "Chat schreiben.",
            ),
            LegalBlock.Faq(
                "Ist FLEXR sicher und seriös?",
                "Ja. Jedes Konto durchläuft vor der Freischaltung eine manuelle Alters- und " +
                    "Identitätsprüfung mit Verifizierungs-Selfie und amtlichem Lichtbildausweis. " +
                    "Dazu kommen eine Melde- und Blockfunktion, der Verifizierungshaken im Profil " +
                    "sowie ein automatischer Schutz im Chat, der Scam-Nachrichten und externe " +
                    "Links erkennt und entfernt.",
            ),
            LegalBlock.Faq(
                "Für wen ist FLEXR gedacht?",
                "Für alle, die Training ernst nehmen und jemanden mit ähnlichem Lifestyle kennenlernen " +
                    "wollen — egal ob Kraftsport, Functional Fitness oder Ausdauer, und unabhängig vom Level.",
            ),
            LegalBlock.Faq(
                "Kann ich jederzeit kündigen?",
                "Ja. Es gibt keine Mindestlaufzeit. Du kannst dein Abo jederzeit in deinem Konto " +
                    "beenden — der Zugang bleibt bis zum Ende des bezahlten Zeitraums aktiv.",
            ),
        ),
    )

    private val impressum = LegalPage(
        document = LegalDocument.IMPRESSUM,
        intro = "Offenlegung gemäß §5 E-Commerce-Gesetz (ECG), §25 Mediengesetz und §14 UGB.",
        blocks = listOf(
            LegalBlock.Heading("Diensteanbieter und Inhaber"),
            LegalBlock.Paragraph(
                "flexr.social Kleinunternehmen\nJohann-Schrey-Weg 260\n8232 Grafendorf, Österreich",
            ),
            LegalBlock.Heading("Kontakt"),
            LegalBlock.KeyValues(listOf("E-Mail" to "flexr.social@proton.me")),
            LegalBlock.Heading("Unternehmensrechtliche Angaben"),
            LegalBlock.KeyValues(
                listOf(
                    "Rechtsform" to "Einzelunternehmen (Kleinunternehmerregelung)",
                    "Firmenbuchnummer" to "entfällt (nicht protokolliertes Einzelunternehmen)",
                    "UID-Nummer" to "entfällt (umsatzsteuerbefreit gem. Kleinunternehmerregelung, " +
                        "§ 6 Abs. 1 Z 27 UStG)",
                ),
            ),
            LegalBlock.Heading("Anwendbare Rechtsvorschriften"),
            LegalBlock.KeyValues(listOf("Gewerbeordnung" to "www.ris.bka.gv.at")),
            LegalBlock.Heading("Verbraucherbeschwerden und Streitbeilegung"),
            LegalBlock.Paragraph(
                "Unsere E-Mail-Adresse für Verbraucherbeschwerden: flexr.social@proton.me. " +
                    "Wir sind freiwillig bereit, an einem Streitbeilegungsverfahren vor einer " +
                    "Verbraucherschlichtungsstelle teilzunehmen.",
            ),
            LegalBlock.Paragraph(
                "Die Plattform der Europäischen Kommission zur Online-Streitbeilegung " +
                    "(„OS-Plattform“) wurde am 20. Juli 2025 eingestellt. Die Verordnung (EU) " +
                    "Nr. 524/2013 und die daraus folgende Pflicht, auf diese Plattform zu " +
                    "verlinken, wurden durch die Verordnung (EU) 2024/3228 aufgehoben; ein " +
                    "entsprechender Link entfällt daher.",
            ),
            LegalBlock.Heading("Haftung für Inhalte"),
            LegalBlock.Paragraph(
                "Als Diensteanbieter sind wir für eigene Inhalte auf diesen Seiten nach den " +
                    "allgemeinen Gesetzen verantwortlich. Für nutzergenerierte Inhalte (Profile, Fotos, " +
                    "Nachrichten) haften wir im Rahmen der §§16–19 ECG, insbesondere ohne Verpflichtung " +
                    "zur anlasslosen Überwachung. Bekannt gewordene rechtswidrige Inhalte werden nach " +
                    "Meldung (siehe Melde- und Blockfunktion in der App) unverzüglich entfernt.",
            ),
        ),
    )

    private val agb = LegalPage(
        document = LegalDocument.AGB,
        blocks = listOf(
            LegalBlock.Heading("1. Geltungsbereich"),
            LegalBlock.Paragraph(
                "Diese AGB gelten für die Nutzung der Plattform FLEXR („wir\", „FLEXR\"), betrieben " +
                    "von flexr.social Kleinunternehmen, Johann-Schrey-Weg 260, 8232 Grafendorf " +
                    "(siehe Impressum), durch registrierte Nutzer („Nutzer\").",
            ),
            LegalBlock.Heading("2. Registrierungsvoraussetzungen"),
            LegalBlock.Lettered(
                listOf(
                    "Mindestalter 18 Jahre. Bei der Registrierung gibt der Nutzer sein " +
                        "Geburtsdatum an; das Alter wird serverseitig berechnet (zulässig sind " +
                        "18–99 Jahre). Liegt es unter 18 Jahren, kann die Registrierung nicht " +
                        "abgeschlossen werden.",
                    "Alters- und Identitätsprüfung vor der Freischaltung. Zusätzlich zur Angabe " +
                        "des Geburtsdatums ist vor der Freischaltung des Accounts eine Prüfung zu " +
                        "durchlaufen: Der Nutzer nimmt Verifizierungs-Selfies mit vorgegebenen " +
                        "Posen auf und lädt einmalig eine Aufnahme eines gültigen amtlichen " +
                        "Lichtbildausweises (Personalausweis, Reisepass oder Führerschein) hoch. " +
                        "Die Prüfung erfolgt manuell durch FLEXR — Profilfoto, " +
                        "Verifizierungs-Selfie und Ausweisfoto werden von einem Menschen " +
                        "verglichen und das Geburtsdatum abgeglichen. Eine automatisierte " +
                        "biometrische Gesichtserkennung findet nicht statt. Es handelt sich um " +
                        "eine Sichtprüfung des vorgelegten Dokuments, nicht um ein behördliches " +
                        "Identifizierungsverfahren.",
                    "Freischaltung. Der Account wird erst nach erfolgreicher Prüfung " +
                        "freigeschaltet; erst dann sind Swipen, Matchen und Chatten möglich und " +
                        "erst dann beginnt der Probemonat (siehe Punkt 4). Verläuft die Prüfung " +
                        "nicht erfolgreich — etwa weil das Dokument nicht lesbar ist, die Person " +
                        "nicht übereinstimmt, das Geburtsdatum abweicht oder der Nutzer noch nicht " +
                        "18 Jahre alt ist — können wir eine neue Aufnahme anfordern oder die " +
                        "Registrierung ablehnen. Die Aufnahmen des Ausweises und die " +
                        "Verifizierungs-Selfies werden nach Abschluss der Prüfung gelöscht " +
                        "(Einzelheiten in der Datenschutzerklärung).",
                    "Bei begründetem Verdacht auf Falschangaben behalten wir uns die Sperre des " +
                        "Accounts vor. Bestehende Accounts können wir zur Alters- und " +
                        "Identitätsprüfung nachträglich auffordern.",
                    "Nutzung aktuell nur für Personen mit Wohnsitz/Aufenthalt in Österreich " +
                        "(Postleitzahl bei der Registrierung).",
                    "Ein Account pro Person; keine Erstellung von Fake-Profilen oder Profilen für Dritte.",
                ),
            ),
            LegalBlock.Heading("3. Leistungsbeschreibung"),
            LegalBlock.Paragraph(
                "FLEXR vermittelt Kontakte zwischen Nutzern anhand gegenseitiger Interessensbekundung " +
                    "(„Swipe\"). Bei beidseitigem Interesse entsteht ein „Match\"; die weitere " +
                    "Kontaktaufnahme erfolgt eigenverantwortlich zwischen den Nutzern. Wir garantieren " +
                    "keine Matches, keine bestimmte Anzahl an Matches und keinen Erfolg bei der " +
                    "Partnersuche.",
            ),
            LegalBlock.Heading("4. Preise, Probemonat, Kündigung"),
            LegalBlock.Lettered(
                listOf(
                    "Erster Monat ab Registrierung kostenlos (Trial). Danach 5 €/Monat, sofern nicht " +
                        "vor Ablauf des Probemonats gekündigt wird. Preis und Trial-Bedingungen werden " +
                        "bereits im Registrierungsformular unmittelbar vor dem Bestell-Button klar und " +
                        "unübersehbar angezeigt (§ 6 Abs. 1 Z 25 KSchG).",
                    "Automatische monatliche Verlängerung bis zur Kündigung.",
                    "Kündigung jederzeit zum Ende der laufenden Abrechnungsperiode selbstständig über " +
                        "„Abo verwalten / kündigen\" im Konto-Bereich der App (Stripe Billing Portal).",
                    "Zahlungsabwicklung über Stripe. Es gelten zusätzlich die Stripe-Nutzungsbedingungen.",
                ),
            ),
            LegalBlock.Heading("5. Widerrufsrecht (Verbraucher)"),
            LegalBlock.Paragraph(
                "Verbrauchern steht grundsätzlich ein 14-tägiges Rücktrittsrecht ohne Angabe von " +
                    "Gründen zu (§ 11 FAGG). Bei digitalen Dienstleistungen erlischt dieses Recht " +
                    "vorzeitig, wenn der Nutzer ausdrücklich zugestimmt hat, dass die Ausführung vor " +
                    "Ablauf der Rücktrittsfrist beginnt, und zur Kenntnis genommen hat, dass er dadurch " +
                    "sein Rücktrittsrecht verliert (§ 18 Abs. 1 Z 11 FAGG). Diese Zustimmung wird bei " +
                    "der Registrierung separat per Checkbox eingeholt und mit Zeitstempel gespeichert.",
            ),
            LegalBlock.Heading("6. Nutzungsregeln"),
            LegalBlock.Paragraph(
                "Welche Inhalte und Verhaltensweisen zulässig sind, regeln abschließend die " +
                    "Nutzungsrichtlinien (Acceptable Use Policy, im Konto-Bereich und unter " +
                    "flexr.social/nutzungsrichtlinien.html). Sie sind Bestandteil dieses Vertrags. " +
                    "Dort sind auch die Schutzprotokolle gegen Menschenhandel, strafbare Handlungen, " +
                    "Identitätsmissbrauch und Darstellungen sexuellen Kindesmissbrauchs sowie das " +
                    "Melde- und Beschwerdeverfahren beschrieben. Verstöße können über die " +
                    "Melde-Funktion in der App gemeldet werden; wir behalten uns vor, gemeldete " +
                    "Inhalte zu entfernen und Konten befristet oder dauerhaft zu sperren. " +
                    "Auskunftsersuchen von Behörden behandeln wir nach den Richtlinien für " +
                    "Strafverfolgungsbehörden.",
            ),
            LegalBlock.Paragraph(
                "Moderation, Beschwerde und Kontaktstelle (Art. 14 DSA): Inhalte werden auf " +
                    "zwei Wegen geprüft — automatisiert durch Filter, die Profiltexte mit Links, " +
                    "Telefonnummern oder Scam-Begriffen zurückweisen, Links und Kontaktdaten in " +
                    "Chatnachrichten unkenntlich machen und auffällige Nachrichten zur Prüfung " +
                    "vorlegen, und durch menschliche Prüfung, die über jede Fotofreigabe und " +
                    "jede Maßnahme gegen ein Konto entscheidet. Über eine Beschränkung " +
                    "informieren wir dich begründet; du kannst ihr formlos per E-Mail an " +
                    "flexr.social@proton.me widersprechen. Dieselbe Adresse ist unsere zentrale " +
                    "Kontaktstelle für Nutzer (Art. 12 DSA) und für Behörden (Art. 11 DSA), " +
                    "erreichbar auf Deutsch und Englisch.",
            ),
            LegalBlock.Heading("7. Haftungsbeschränkung"),
            LegalBlock.Paragraph(
                "Wir haften nicht für das Verhalten, die Angaben oder die Identität anderer Nutzer. " +
                    "Für Vorsatz und grobe Fahrlässigkeit sowie Personenschäden haften wir " +
                    "unbeschränkt; im Übrigen ist die Haftung auf den vertragstypisch vorhersehbaren " +
                    "Schaden beschränkt.",
            ),
            LegalBlock.Heading("8. Änderungen der AGB"),
            LegalBlock.Paragraph(
                "Änderungen werden 4 Wochen vor Inkrafttreten per E-Mail angekündigt; widerspricht der " +
                    "Nutzer nicht fristgerecht, gelten sie als angenommen.",
            ),
            LegalBlock.Heading("9. Anwendbares Recht, Gerichtsstand, Streitschlichtung"),
            LegalBlock.Lettered(
                listOf(
                    "Es gilt österreichisches Recht unter Ausschluss der Verweisungsnormen des IPR.",
                    "Für Verbraucher gelten die zwingenden Bestimmungen des Wohnsitzstaates.",
                    "Beschwerden richte bitte an flexr.social@proton.me; wir sind freiwillig " +
                        "bereit, an einem Streitbeilegungsverfahren vor einer " +
                        "Verbraucherschlichtungsstelle teilzunehmen. Die OS-Plattform der " +
                        "Europäischen Kommission wurde am 20. Juli 2025 eingestellt " +
                        "(siehe Impressum).",
                ),
            ),
        ),
    )

    // Sicherheitstipps. Inhaltsgleich mit flexr.social/sicherheit.html.
    private val sicherheit = LegalPage(
        document = LegalDocument.SICHERHEIT,
        intro = "Worauf du beim Daten achten solltest — und was wir im Hintergrund tun.",
        blocks = listOf(
            LegalBlock.Heading("1. Vor dem ersten Treffen"),
            LegalBlock.Bullets(
                listOf(
                    "Bleib bis dahin im Chat. Es gibt keinen guten Grund, sofort auf WhatsApp, " +
                        "Telegram oder Instagram wechseln zu müssen. Wer darauf drängt, will " +
                        "meist raus aus einem Bereich, in dem du melden und blockieren kannst.",
                    "Sieh dir das Profil genau an: nur ein Foto, auffällig professionelle " +
                        "Aufnahmen, keine Angaben zum Studio — das muss nichts heißen, ist aber " +
                        "ein Grund, genauer hinzusehen. Der Verifizierungshaken bedeutet, dass " +
                        "wir Selfies in zufällig vorgegebenen Posen mit den Profilfotos " +
                        "verglichen haben.",
                    "Telefoniert oder macht einen Videocall, bevor ihr euch trefft.",
                    "Sag jemandem Bescheid, wen du triffst, wo und wie lange.",
                ),
            ),
            LegalBlock.Heading("2. Beim Treffen"),
            LegalBlock.Bullets(
                listOf(
                    "Trefft euch öffentlich — im Studio, im Café, im Park. Nicht bei dir oder " +
                        "bei der anderen Person zuhause.",
                    "Komm und geh selbstständig. Lass dich beim ersten Mal nicht abholen und " +
                        "gib deine Adresse noch nicht heraus.",
                    "Behalte Getränk und Handy bei dir und achte auf einen geladenen Akku.",
                    "Trink in Maßen — du willst klar entscheiden können, wie der Abend weitergeht.",
                    "Geh, wenn es sich falsch anfühlt. Du schuldest niemandem eine Erklärung.",
                ),
            ),
            LegalBlock.Heading("3. Betrugsmaschen erkennen"),
            LegalBlock.Note(
                "Jede Bitte um Geld, Gutscheine, Paysafe-Codes oder Krypto ist ein " +
                    "Betrugsversuch — auch die rührendste Notlage, auch nach Wochen Chat.",
            ),
            LegalBlock.Bullets(
                listOf(
                    "Anlagetipps: „Ich zeig dir, wie ich mit Trading verdiene\" ist die " +
                        "häufigste Masche auf Dating-Plattformen.",
                    "Zu schnell, zu viel: Liebeserklärungen nach drei Tagen, ständige " +
                        "Erreichbarkeitsforderungen, Eifersucht vor dem ersten Treffen.",
                    "Nie erreichbar: Videocalls scheitern immer, Treffen platzen kurzfristig, " +
                        "die Person arbeitet „auf einer Bohrinsel\" oder „im Auslandseinsatz\".",
                    "Intime Aufnahmen: Wer schnell Nacktbilder will, will sie manchmal, um dich " +
                        "damit zu erpressen (Sextortion).",
                    "Links: Wir entfernen Links und E-Mail-Adressen automatisch aus Nachrichten. " +
                        "Umgeht jemand das mit „Punkt\" statt „.\", ist das ein deutliches Signal.",
                ),
            ),
            LegalBlock.Paragraph(
                "Wenn du erpresst wirst: nicht zahlen — Zahlungen führen praktisch immer zu " +
                    "weiteren Forderungen. Kontakt abbrechen, blockieren, melden. Screenshots " +
                    "von Profil, Chat und Zahlungsaufforderung sichern und Anzeige bei der " +
                    "nächsten Polizeidienststelle erstatten.",
            ),
            LegalBlock.Heading("4. Melden und Blockieren"),
            LegalBlock.Bullets(
                listOf(
                    "Blockieren wirkt sofort und beidseitig: Das Match verschwindet, Nachrichten " +
                        "sind nicht mehr möglich, ihr seht euch nicht mehr im Deck.",
                    "Melden geht in jedem Profil und in jedem Chat. Du bekommst ein " +
                        "Aktenzeichen, wir prüfen binnen 72 Stunden — bei Gefahr für eine Person " +
                        "sofort — und du siehst das Ergebnis unter „Meine Meldungen\".",
                    "Ohne Konto erreichst du uns unter flexr.social@proton.me, etwa wenn deine " +
                        "Fotos hier ohne dein Wissen verwendet werden.",
                ),
            ),
            LegalBlock.Heading("5. Was wir tun"),
            LegalBlock.Bullets(
                listOf(
                    "Jedes Foto wird von einem Menschen geprüft, bevor es jemand zu sehen bekommt.",
                    "Profiltexte mit Links, Telefonnummern oder Scam-Begriffen werden gar nicht " +
                        "erst veröffentlicht.",
                    "In Nachrichten machen wir Links und E-Mail-Adressen unkenntlich und legen " +
                        "auffällige Nachrichten der Moderation vor.",
                    "Mindestalter 18, serverseitig aus dem Geburtsdatum geprüft.",
                    "Verifizierung über drei zufällig vorgegebene Selfie-Posen.",
                ),
            ),
            LegalBlock.Heading("6. Im Notfall"),
            LegalBlock.Note("Bei akuter Gefahr: Polizei 133 oder Euronotruf 112."),
            LegalBlock.KeyValues(
                listOf(
                    "Opfer-Notruf" to "0800 112 112 (rund um die Uhr, kostenlos)",
                    "Frauenhelpline gegen Gewalt" to "0800 222 555",
                    "Männerinfo" to "0800 400 777",
                    "Rat auf Draht" to "147 (für junge Menschen)",
                ),
            ),
            LegalBlock.Paragraph(
                "Wenn dir hier auf FLEXR etwas zugestoßen ist, melde es uns zusätzlich unter " +
                    "flexr.social@proton.me. Wir sichern die Daten zu deinem Fall, damit sie für " +
                    "eine Anzeige verfügbar bleiben.",
            ),
        ),
    )

    // Acceptable Use Policy. Inhaltsgleich mit
    // flexr.social/nutzungsrichtlinien.html — beide Fassungen zusammen pflegen.
    private val nutzungsrichtlinien = LegalPage(
        document = LegalDocument.NUTZUNGSRICHTLINIEN,
        intro = "Verbindliche Verhaltens- und Inhaltsregeln für alle Nutzer von FLEXR. " +
            "Stand: 3. August 2026.",
        blocks = listOf(
            LegalBlock.Heading("1. Geltung"),
            LegalBlock.Paragraph(
                "Diese Nutzungsrichtlinien gelten für jede Nutzung von FLEXR, betrieben von " +
                    "flexr.social Kleinunternehmen, Johann-Schrey-Weg 260, 8232 Grafendorf. Sie " +
                    "ergänzen die AGB und sind Bestandteil des Nutzungsvertrags. Ein Verstoß " +
                    "berechtigt uns zur Sperre oder Löschung des Kontos, unabhängig von einer " +
                    "bestehenden Zahlungsverpflichtung.",
            ),
            LegalBlock.Heading("2. Grundregeln"),
            LegalBlock.Bullets(
                listOf(
                    "FLEXR ist ausschließlich für Personen ab 18 Jahren. Das Geburtsdatum wird bei " +
                        "der Registrierung serverseitig geprüft; Konten unter 18 Jahren werden " +
                        "technisch nicht angelegt.",
                    "Ein Konto pro Person. Konten dürfen nicht geteilt, verkauft, vermietet oder " +
                        "für Dritte betrieben werden.",
                    "Alle Angaben im Profil müssen der Wahrheit entsprechen und die eigene Person " +
                        "betreffen.",
                    "Jedes hochgeladene Foto muss die anmeldende Person selbst zeigen. Fotos " +
                        "Dritter, Prominenter, aus dem Internet oder von Minderjährigen sind " +
                        "unzulässig.",
                    "FLEXR ist eine Kontaktplattform, kein Marktplatz. Kommerzielle Angebote, " +
                        "Werbung, Anwerbung und Vermittlung jeder Art sind untersagt.",
                ),
            ),
            LegalBlock.Heading("3. Verbotene Inhalte und Verhaltensweisen"),
            LegalBlock.Bullets(
                listOf(
                    "Menschenhandel, Zwangsprostitution, sexuelle Ausbeutung sowie jede Form der " +
                        "Anwerbung dafür (Abschnitt 4).",
                    "Alle sonstigen strafbaren Handlungen, insbesondere Betrug, Erpressung, " +
                        "Sextortion, Drogen- und Waffenhandel, Geldwäsche (Abschnitt 5).",
                    "Identitätsmissbrauch, Fake-Profile, Auftreten im Namen einer anderen realen " +
                        "oder juristischen Person (Abschnitt 6).",
                    "Darstellungen sexuellen Kindesmissbrauchs (CSAM) und jede Sexualisierung " +
                        "Minderjähriger (Abschnitt 7).",
                    "Belästigung, Stalking, Drohungen, Hassrede, Diskriminierung.",
                    "Weitergabe fremder personenbezogener Daten oder von Chatinhalten Dritter ohne " +
                        "deren Einwilligung.",
                    "Unaufgeforderte sexuell explizite Bilder.",
                    "Kommerzielle Werbung, Spam, Weiterleitung auf externe Bezahl-, Cam-, Krypto- " +
                        "oder Investmentangebote.",
                    "Automatisierter Zugriff (Bots, Scraper) sowie Umgehung von Sperren, etwa durch " +
                        "Neuanmeldung nach einem Ausschluss.",
                ),
            ),
            LegalBlock.Heading("4. Protokoll: Menschenhandel und sexuelle Ausbeutung"),
            LegalBlock.Note("Nulltoleranz — bei Verdacht wird ohne Abstufung sofort gesperrt."),
            LegalBlock.Bullets(
                listOf(
                    "Verboten: das Anbieten, Bewerben, Vermitteln oder Nachfragen sexueller " +
                        "Handlungen gegen Geld oder geldwerte Leistungen.",
                    "Verboten: das Anwerben von Personen für Prostitution, Cam-Angebote, Escort-, " +
                        "Sugar- oder Modelagenturen, auch als vorgebliches Jobangebot.",
                    "Verboten: das Betreiben eines Profils für oder unter der Kontrolle einer " +
                        "anderen Person (Betreuer, Manager, Agentur).",
                    "Verboten: jede Kommunikation, die auf Zwang, Schuldknechtschaft, Einbehalten " +
                        "von Ausweisdokumenten, Isolation oder Transport zum Zweck der Ausbeutung " +
                        "hindeutet.",
                ),
            ),
            LegalBlock.Paragraph(
                "Erkennung: Öffentliche Profiltexte werden serverseitig geprüft — Bios mit Links, " +
                    "Telefonnummern oder einschlägigen Begriffen werden beim Speichern abgewiesen " +
                    "und gar nicht erst veröffentlicht. Chatnachrichten mit denselben Signalen " +
                    "werden zugestellt, aber mit Grund markiert und der Moderation vorgelegt; " +
                    "externe Links und E-Mail-Adressen werden dem Empfänger gegenüber automatisch " +
                    "unkenntlich gemacht. Jedes Foto wird vor Veröffentlichung von einem Menschen " +
                    "freigegeben; Agentur- oder Studioaufnahmen mit Werbecharakter werden " +
                    "abgelehnt. Dazu kommen Meldungen aus Profil und Chat.",
            ),
            LegalBlock.Lettered(
                listOf(
                    "Sofortmaßnahme innerhalb von 24 Stunden nach Kenntnis: Konto gesperrt, Profil " +
                        "nicht mehr sichtbar, laufende Chats unterbunden.",
                    "Beweissicherung: Profil, Fotos, Chatverlauf und Zeitstempel werden vor der " +
                        "Löschroutine gesichert.",
                    "Manuelle Bewertung durch die Betreiberin anhand des gesicherten Materials.",
                    "Bei erhärtetem Verdacht: Anzeige bei der zuständigen österreichischen " +
                        "Strafverfolgungsbehörde (Bundeskriminalamt, Zentralstelle zur Bekämpfung " +
                        "der Schlepperkriminalität und des Menschenhandels) und endgültige Löschung " +
                        "des Kontos.",
                    "Bei akuter Gefahr für eine Person: unverzüglich Polizeinotruf 133 bzw. 112.",
                    "Betroffene werden auf Hilfsangebote hingewiesen, in Österreich insbesondere " +
                        "LEFÖ-IBF und den Opfer-Notruf 0800 112 112.",
                ),
            ),
            LegalBlock.Heading("5. Protokoll: Illegale Handlungen"),
            LegalBlock.Bullets(
                listOf(
                    "Verboten: Betrug jeder Art, insbesondere Romance Scam, Vorschussbetrug, " +
                        "angebliche Notlagen mit Geldforderung, gefälschte Investment- und " +
                        "Krypto-Angebote, Weiterleitung auf Phishing-Seiten.",
                    "Verboten: Erpressung und Sextortion, also das Androhen der Veröffentlichung " +
                        "intimer Aufnahmen.",
                    "Verboten: Handel mit Betäubungsmitteln, Waffen, gestohlenen Daten oder " +
                        "gefälschten Dokumenten.",
                    "Verboten: Geldwäsche, Weiterleitung von Zahlungen für Dritte, Missbrauch der " +
                        "Plattform zur Anbahnung von Finanztransaktionen.",
                    "Verboten: Zahlungsbetrug gegenüber FLEXR, insbesondere die Nutzung fremder " +
                        "oder gestohlener Zahlungsmittel.",
                ),
            ),
            LegalBlock.Paragraph(
                "Erkennung: serverseitige Scam-Begriffsprüfung in Bios (harte Ablehnung) und in " +
                    "Chatnachrichten (Markierung zur Prüfung), automatische Entfernung externer " +
                    "Links und E-Mail-Adressen aus zugestellten Nachrichten, Blocklist für " +
                    "Wegwerf-E-Mail-Adressen bei der Registrierung, Ratenbegrenzung auf allen " +
                    "sicherheitsrelevanten Endpunkten. Die Zahlungsabwicklung läuft ausschließlich " +
                    "über Stripe; FLEXR verarbeitet und speichert keine Kartendaten.",
            ),
            LegalBlock.Lettered(
                listOf(
                    "Meldung oder Systemmarkierung erreicht die Prüfliste der Moderation.",
                    "Sichtung binnen 72 Stunden, bei Gefahr im Verzug unverzüglich.",
                    "Abgestufte Maßnahme: befristete Chat-Sperre bei einmaligem, leichterem " +
                        "Verstoß — sofortige Kontosperre bei Betrugs-, Erpressungs- oder " +
                        "Handelsversuchen.",
                    "Beweissicherung und Anzeige bei der Kriminalpolizei, wenn ein Anfangsverdacht " +
                        "auf eine gerichtlich strafbare Handlung besteht.",
                    "Geschädigte erhalten auf Anfrage die zu ihrem Fall gehörenden Daten für eine " +
                        "eigene Anzeige, soweit datenschutzrechtlich zulässig.",
                ),
            ),
            LegalBlock.Heading("6. Protokoll: Identitätsmissbrauch und Fake-Profile"),
            LegalBlock.Bullets(
                listOf(
                    "Verboten: das Auftreten unter dem Namen, mit den Fotos oder mit der Identität " +
                        "einer anderen realen Person, eines Unternehmens oder einer Behörde.",
                    "Verboten: die Verwendung fremder, generierter oder aus dem Internet " +
                        "entnommener Fotos.",
                    "Verboten: falsche Angaben zu Alter, Geschlecht, Wohnort oder Studio, soweit " +
                        "sie zur Täuschung anderer Nutzer dienen.",
                    "Verboten: das Anlegen von Zweit- oder Ersatzkonten, insbesondere nach einer " +
                        "Sperre.",
                ),
            ),
            LegalBlock.Paragraph(
                "Vorbeugend: Ohne mindestens ein freigegebenes Foto ist ein Profil für andere " +
                    "nicht sichtbar. Jedes hochgeladene Foto steht zunächst auf ausstehend und " +
                    "wird erst nach menschlicher Prüfung ausgeliefert. Bei der Alters- und " +
                    "Identitätsprüfung verlangt der Server drei zufällig gezogene Posen als " +
                    "Selfie — da die Posen erst bei der Anfrage feststehen, lassen sie sich mit " +
                    "fremdem oder vorbereitetem Material nicht bedienen; dazu kommt der Abgleich " +
                    "mit einem vorgelegten amtlichen Lichtbildausweis. Nach der Prüfung werden " +
                    "Selfies und Ausweisaufnahmen gelöscht. Dazu kommen die Telefonprüfung per SMS-Einmalcode, die " +
                    "E-Mail-Eindeutigkeit je Konto und die Sperrliste für Wegwerf-Adressen.",
            ),
            LegalBlock.Lettered(
                listOf(
                    "Meldung über die Melden-Funktion oder per E-Mail an flexr.social@proton.me — " +
                        "auch von Betroffenen ohne eigenes Konto.",
                    "Prüfung binnen 72 Stunden. Beanstandete Fotos werden für die Dauer der " +
                        "Prüfung aus der Auslieferung genommen.",
                    "Bei begründetem Verdacht fordern wir eine Foto-Verifizierung nach dem " +
                        "Posen-Verfahren an.",
                    "Wird sie nicht binnen sieben Tagen erbracht oder besteht sie die Prüfung " +
                        "nicht, werden die Fotos entfernt und das Konto gesperrt.",
                    "Bei gewerbsmäßigem oder wiederholtem Identitätsmissbrauch folgen endgültige " +
                        "Löschung und, bei Anhaltspunkten für Betrug, eine Anzeige.",
                ),
            ),
            LegalBlock.Heading("7. Protokoll: Schutz Minderjähriger und CSAM"),
            LegalBlock.Note(
                "Nulltoleranz — Meldungen zu diesem Bereich haben unbedingten Vorrang vor allen " +
                    "anderen Vorgängen.",
            ),
            LegalBlock.Bullets(
                listOf(
                    "Verboten: jede Darstellung sexuellen Kindesmissbrauchs (CSAM) in " +
                        "Profilfotos, Chatnachrichten oder Profiltexten.",
                    "Verboten: jede Sexualisierung von Minderjährigen, auch in Text-, Zeichnungs-, " +
                        "Comic- oder KI-generierter Form.",
                    "Verboten: das Anbahnen sexueller Kontakte zu Minderjährigen (Grooming) sowie " +
                        "das Erfragen oder Anbieten entsprechender Inhalte.",
                    "Verboten: die Nutzung der Plattform durch Personen unter 18 Jahren.",
                    "Verboten: das Hochladen von Fotos, auf denen Minderjährige erkennbar " +
                        "abgebildet sind — auch als Beiwerk oder Familienfoto.",
                ),
            ),
            LegalBlock.Paragraph(
                "Vorbeugend: Die Registrierung verlangt ein Geburtsdatum; der Server weist jeden " +
                    "Wert unter 18 Jahren ab, und das Alter wird laufend aus dem Geburtsdatum " +
                    "berechnet statt als frei änderbare Zahl geführt. Vor der Freischaltung des " +
                    "Kontos prüft ein Mensch zusätzlich einen vorgelegten amtlichen " +
                    "Lichtbildausweis gegen die Angabe bei der Registrierung. Kein Foto wird ohne manuelle " +
                    "Freigabe ausgeliefert; bei Zweifeln an der Volljährigkeit der abgebildeten " +
                    "Person wird im Zweifel gegen die Freigabe entschieden und das Konto geprüft. " +
                    "Der Chat überträgt ausschließlich Text — die Verbreitung von Bildmaterial " +
                    "über die Plattform ist damit auf den vorab moderierten Profilbereich " +
                    "beschränkt.",
            ),
            LegalBlock.Lettered(
                listOf(
                    "Sofortige Entfernung des Inhalts aus der Auslieferung und sofortige Sperre " +
                        "des Kontos — ohne vorherige Anhörung, ohne Wartefrist.",
                    "Beweissicherung: Das Material wird gegen automatische Löschung gesperrt, der " +
                        "Zugriff auf die Betreiberin beschränkt und ausschließlich zur Weitergabe " +
                        "an die Strafverfolgung aufbewahrt. Es wird nicht weiter angesehen, " +
                        "kopiert oder verbreitet.",
                    "Meldung binnen 24 Stunden nach Kenntnis an das Bundeskriminalamt, Meldestelle " +
                        "für Kinderpornografie und Kindersextourismus, und Anzeige bei der " +
                        "Kriminalpolizei. Bei akuter Gefahr für ein Kind zusätzlich sofort " +
                        "Polizeinotruf 133 bzw. 112.",
                    "Endgültige Löschung des Kontos; ein erneuter Zugang wird dauerhaft verweigert.",
                    "Bei einem Konto, das eine minderjährige Person betreibt: Sperre und Löschung; " +
                        "die Daten werden nur so lange aufbewahrt, wie es zur Erfüllung einer " +
                        "behördlichen Anordnung erforderlich ist.",
                ),
            ),
            LegalBlock.Paragraph(
                "Meldungen zu diesem Bereich bitte mit dem Betreff CSAM an " +
                    "flexr.social@proton.me. Bitte fügen Sie keine Bilddateien an, sondern nur " +
                    "Profil-Links, Namen und Zeitpunkte.",
            ),
            LegalBlock.Heading("8. Durchsetzung"),
            LegalBlock.Table(
                headers = listOf("Maßnahme", "Wirkung", "Anlass"),
                rows = listOf(
                    listOf(
                        "Inhalt abgelehnt",
                        "Bio oder Foto wird nicht veröffentlicht",
                        "Regelverstoß im Inhalt, ohne Täuschungsabsicht",
                    ),
                    listOf(
                        "Befristete Chat-Sperre",
                        "Lesen möglich, Senden gesperrt",
                        "Belästigung, Spam, erster leichterer Verstoß",
                    ),
                    listOf(
                        "Kontosperre",
                        "Kein Zugang, Profil unsichtbar",
                        "Wiederholung, Betrug, Identitätsmissbrauch",
                    ),
                    listOf(
                        "Endgültige Löschung",
                        "Konto und Inhalte entfernt, Zugang dauerhaft verweigert",
                        "Menschenhandel, CSAM, schwere Straftaten",
                    ),
                ),
            ),
            LegalBlock.Paragraph(
                "Die Maßnahme richtet sich nach Schwere, Vorsatz und Wiederholung. In den Fällen " +
                    "der Abschnitte 4 und 7 entfällt die Abstufung: Es wird sofort gesperrt.",
            ),
            LegalBlock.Heading("9. Melden, Entscheidung und Beschwerde"),
            LegalBlock.Paragraph(
                "Das Meldeverfahren ist auf Art. 16 der Verordnung (EU) 2022/2065 (DSA) " +
                    "ausgelegt: Melden geht elektronisch, jede Meldung wird bestätigt, und der " +
                    "Melder erfährt, was daraus geworden ist.",
            ),
            LegalBlock.Bullets(
                listOf(
                    "In der App: Melden- und Blockieren-Funktion in jedem Profil und in jedem " +
                        "Chat. Blockieren wirkt sofort und beidseitig.",
                    "Per E-Mail: flexr.social@proton.me, auch ohne eigenes Konto — etwa wenn " +
                        "die eigene Identität hier missbraucht wird.",
                ),
            ),
            LegalBlock.Lettered(
                listOf(
                    "Empfangsbestätigung sofort: Jede Meldung bekommt beim Absenden ein " +
                        "Aktenzeichen, das dir angezeigt wird.",
                    "Prüfung binnen 72 Stunden — bei Gefahr im Verzug sowie in den Fällen der " +
                        "Abschnitte 4 und 7 unverzüglich, spätestens binnen 24 Stunden. Es prüft " +
                        "ein Mensch; kein Automatismus entscheidet über eine Sperre.",
                    "Entscheidung mit Begründung: Unter „Meine Meldungen\" im Konto-Bereich " +
                        "steht zu jeder Meldung, ob wir eingeschritten sind oder keinen Verstoß " +
                        "feststellen konnten — samt Begründung im Wortlaut.",
                    "Widerspruch: Wer mit der Entscheidung nicht einverstanden ist, kann ihr " +
                        "formlos per E-Mail widersprechen. Wir prüfen erneut und antworten " +
                        "begründet.",
                ),
            ),
            LegalBlock.Paragraph(
                "Wenn wir gegen dein Konto vorgehen, bekommst du nach Art. 17 DSA eine " +
                    "Begründung: bei einer befristeten Chat-Sperre im Chat, bei einer " +
                    "Kontosperre beim Anmeldeversuch. Beides nennt Grund, Dauer und den Weg zum " +
                    "Widerspruch. Der Rechtsweg bleibt unberührt; ebenso die Möglichkeit, sich " +
                    "an den österreichischen Koordinator für digitale Dienste (KommAustria/RTR) " +
                    "zu wenden.",
            ),
            LegalBlock.Heading("10. Kontakt und Kontaktstellen"),
            LegalBlock.Paragraph(
                "flexr.social Kleinunternehmen, Johann-Schrey-Weg 260, 8232 Grafendorf, " +
                    "Österreich. E-Mail: flexr.social@proton.me. Dieselbe Adresse ist die " +
                    "zentrale Kontaktstelle für Nutzer (Art. 12 DSA) und für Behörden " +
                    "(Art. 11 DSA), elektronisch erreichbar auf Deutsch und Englisch. FLEXR ist " +
                    "ein Kleinstunternehmen und daher nach Art. 19 DSA von den zusätzlichen " +
                    "Pflichten für Online-Plattformen ausgenommen; die Pflichten für " +
                    "Hostingdienste erfüllen wir wie oben beschrieben.",
            ),
        ),
    )

    // Law Enforcement Guidelines. Inhaltsgleich mit
    // flexr.social/strafverfolgung.html — beide Fassungen zusammen pflegen.
    private val strafverfolgung = LegalPage(
        document = LegalDocument.STRAFVERFOLGUNG,
        intro = "Verfahren für behördliche Auskunfts-, Sicherungs- und Notfallersuchen. " +
            "Stand: 3. August 2026.",
        blocks = listOf(
            LegalBlock.Heading("1. Wer wir sind"),
            LegalBlock.Paragraph(
                "Verantwortlich für FLEXR ist flexr.social Kleinunternehmen, " +
                    "Johann-Schrey-Weg 260, 8232 Grafendorf, Österreich. Der Dienst wird aus " +
                    "Österreich betrieben; es gilt österreichisches Recht. FLEXR ist ein " +
                    "Kleinunternehmen ohne eigene Rechtsabteilung — Anfragen bearbeitet die " +
                    "Betreiberin persönlich.",
            ),
            LegalBlock.Heading("2. Zustellung von Anfragen"),
            LegalBlock.Paragraph(
                "Behördliche Ersuchen an flexr.social@proton.me, Betreff Behördenanfrage, bei " +
                    "Gefahr im Verzug NOTFALL — Behördenanfrage. Postalisch an die oben genannte " +
                    "Anschrift. Ersuchen sind auf Behördenpapier einzureichen; wir antworten " +
                    "ausschließlich an eine dienstliche Adresse der ersuchenden Behörde. Anfragen " +
                    "von Privatpersonen, Anwaltskanzleien oder Detekteien werden über dieses " +
                    "Verfahren nicht beantwortet.",
            ),
            LegalBlock.Heading("3. Erforderliche Angaben"),
            LegalBlock.Bullets(
                listOf(
                    "Ersuchende Behörde, Aktenzeichen, Name und dienstliche Kontaktdaten der " +
                        "sachbearbeitenden Person.",
                    "Rechtsgrundlage und, soweit erforderlich, gerichtliche Bewilligung bzw. " +
                        "staatsanwaltschaftliche Anordnung.",
                    "Möglichst genaue Bezeichnung der betroffenen Person: E-Mail-Adresse des " +
                        "Kontos, Profilname, Telefonnummer oder Konto-ID.",
                    "Präzise Bezeichnung der angeforderten Daten und des Zeitraums.",
                    "Frist, bis zu der die Auskunft benötigt wird.",
                ),
            ),
            LegalBlock.Heading("4. Rechtsgrundlage"),
            LegalBlock.Bullets(
                listOf(
                    "Österreichische Behörden: auf Grundlage der Strafprozessordnung, insbesondere " +
                        "auf staatsanwaltschaftliche Anordnung bzw. gerichtliche Bewilligung, sowie " +
                        "sonstiger gesetzlicher Auskunftspflichten.",
                    "Behörden anderer EU-Mitgliedstaaten: über die justizielle Zusammenarbeit, " +
                        "insbesondere die Europäische Ermittlungsanordnung, sowie die europäische " +
                        "Herausgabeanordnung (Verordnung (EU) 2023/1543), sobald anwendbar.",
                    "Behörden aus Drittstaaten: über den Rechtshilfeweg (MLAT) unter Einbindung " +
                        "der österreichischen Justizbehörden.",
                    "Freiwillige Auskünfte über die gesetzlichen Pflichten hinaus erteilen wir " +
                        "nicht — ausgenommen Notfälle nach Abschnitt 6.",
                ),
            ),
            LegalBlock.Heading("5. Welche Daten überhaupt vorhanden sind"),
            LegalBlock.Paragraph(
                "Wir können nur herausgeben, was tatsächlich gespeichert ist. FLEXR betreibt keine " +
                    "Vorratsdatenspeicherung und protokolliert keine Verbindungsdaten je " +
                    "Nutzerkonto.",
            ),
            LegalBlock.Table(
                headers = listOf("Datenart", "Vorhanden?", "Anmerkung"),
                rows = listOf(
                    listOf(
                        "Bestandsdaten (E-Mail, Name, Geburtsdatum, PLZ/Ort, Geschlecht, Studio, " +
                            "Registrierungszeitpunkt)",
                        "ja",
                        "Selbstangaben, nicht ausweisgeprüft",
                    ),
                    listOf("Telefonnummer", "nur wenn hinterlegt", "per SMS-Einmalcode bestätigt"),
                    listOf("Profilfotos", "ja", "inkl. Freigabestatus"),
                    listOf(
                        "Verifizierungs-Selfies",
                        "nein",
                        "werden nach der Prüfung gelöscht",
                    ),
                    listOf(
                        "Chatnachrichten (Inhalt, Zeitstempel, Absender)",
                        "ja",
                        "Klartext in der Datenbank, keine Ende-zu-Ende-Verschlüsselung; Original " +
                            "und bereinigte Fassung liegen getrennt vor",
                    ),
                    listOf(
                        "Matches, Swipes, Blockierungen, Meldungen",
                        "ja",
                        "mit Zeitstempel",
                    ),
                    listOf(
                        "Systemseitig markierte Nachrichten",
                        "ja",
                        "inkl. Markierungsgrund",
                    ),
                    listOf(
                        "IP-Adressen je Konto oder Login",
                        "nein",
                        "nicht kontobezogen gespeichert; kurzlebige Server-Logs können IP und " +
                            "Zeitstempel ohne Kontozuordnung enthalten",
                    ),
                    listOf(
                        "Zahlungs- und Kartendaten",
                        "nein",
                        "ausschließlich bei Stripe; bei uns nur die Stripe-Kennungen des Kontos",
                    ),
                    listOf("Passwörter", "nicht lesbar", "nur als Hash gespeichert"),
                ),
            ),
            LegalBlock.Heading("6. Notfallanfragen"),
            LegalBlock.Note(
                "Bei unmittelbarer Gefahr für Leben oder körperliche Unversehrtheit erteilen wir " +
                    "die zur Abwehr erforderliche Auskunft ohne vorherige gerichtliche Anordnung.",
            ),
            LegalBlock.Bullets(
                listOf(
                    "Betreff: NOTFALL — Behördenanfrage.",
                    "Bitte schildern Sie die konkrete Gefahrenlage und die betroffene Person.",
                    "Bitte begründen Sie, warum die Auskunft zur Abwehr erforderlich und dringlich " +
                        "ist, und benennen Sie die benötigten Daten.",
                    "Bitte geben Sie eine dienstliche Rückrufnummer an.",
                    "Wir bearbeiten Notfallanfragen vorrangig, können als Kleinunternehmen aber " +
                        "keinen Rund-um-die-Uhr-Bereitschaftsdienst zusichern.",
                ),
            ),
            LegalBlock.Heading("7. Sicherungsersuchen"),
            LegalBlock.Lettered(
                listOf(
                    "Ersuchen per E-Mail mit Betreff Sicherung, unter Angabe des Kontos und des " +
                        "Zeitraums.",
                    "Wir sichern die betroffenen Daten und bestätigen dies schriftlich.",
                    "Die Sicherung gilt 90 Tage und wird auf Ersuchen einmalig um 90 Tage " +
                        "verlängert.",
                    "Geht innerhalb dieser Frist keine förmliche Anordnung ein, wird die Sicherung " +
                        "aufgehoben und die reguläre Löschfrist läuft weiter.",
                ),
            ),
            LegalBlock.Heading("8. Aufbewahrung und Löschung"),
            LegalBlock.Bullets(
                listOf(
                    "Gelöschte Konten werden sofort deaktiviert und nach 30 Tagen Karenzzeit " +
                        "endgültig gelöscht, einschließlich der Fotos im Objektspeicher. Danach " +
                        "sind die Daten nicht wiederherstellbar.",
                    "Ein rechtzeitiges Sicherungsersuchen hemmt die endgültige Löschung.",
                    "Zahlungsbezogene Aufzeichnungen unterliegen den gesetzlichen " +
                        "Aufbewahrungspflichten (in der Regel sieben Jahre, § 132 BAO).",
                    "Material zu CSAM-Fällen wird unabhängig davon zur Übergabe an die " +
                        "Strafverfolgung gesichert.",
                ),
            ),
            LegalBlock.Heading("9. Benachrichtigung der betroffenen Person"),
            LegalBlock.Paragraph(
                "Datenschutzrechtlich sind wir grundsätzlich verpflichtet, betroffene Personen zu " +
                    "informieren. Wir sehen davon ab, wenn die Behörde ein gesetzlich vorgesehenes " +
                    "Auskunftsverbot mitteilt, eine gerichtliche Anordnung dies untersagt oder die " +
                    "Benachrichtigung eine Ermittlung gefährden oder eine Person in Gefahr bringen " +
                    "würde. Bitte weisen Sie im Ersuchen ausdrücklich darauf hin.",
            ),
            LegalBlock.Heading("10. Bearbeitung, Form und Kosten"),
            LegalBlock.Bullets(
                listOf(
                    "Eingangsbestätigung in der Regel binnen drei Werktagen, Notfälle vorrangig.",
                    "Auskünfte erteilen wir schriftlich in strukturierter Form (Text oder CSV).",
                    "Für die Bearbeitung stellen wir keine Kosten in Rechnung.",
                    "Wir prüfen jedes Ersuchen auf Zuständigkeit, Rechtsgrundlage und " +
                        "Verhältnismäßigkeit und widersprechen offensichtlich unzulässigen oder " +
                        "unverhältnismäßig weiten Ersuchen.",
                ),
            ),
        ),
    )

    private val datenschutz = LegalPage(
        document = LegalDocument.DATENSCHUTZ,
        blocks = listOf(
            LegalBlock.Heading("1. Verantwortlicher"),
            LegalBlock.Paragraph(
                "flexr.social Kleinunternehmen\nJohann-Schrey-Weg 260, 8232 Grafendorf\n" +
                    "E-Mail: flexr.social@proton.me",
            ),
            LegalBlock.Note(
                "Ein gesonderter Datenschutzbeauftragter wurde nicht bestellt; " +
                    "datenschutzrechtliche Anfragen werden von flexr.social Kleinunternehmen direkt " +
                    "bearbeitet (siehe Kontakt oben).",
            ),
            LegalBlock.Heading("2. Welche Daten wir verarbeiten"),
            LegalBlock.Table(
                headers = listOf("Kategorie", "Beispiele", "Quelle"),
                rows = listOf(
                    listOf("Kontodaten", "E-Mail, Passwort-Hash (bcrypt, nie im Klartext)", "Registrierung"),
                    listOf(
                        "Profildaten",
                        "Name, Geburtsdatum, Stadt, Gym (Studio aus der öffentlichen Liste), " +
                            "Suchradius, Bio",
                        "Registrierung / Profilbearbeitung",
                    ),
                    listOf(
                        "Präferenzdaten (Art. 9 DSGVO)",
                        "Geschlecht, gesuchtes Geschlecht (→ sexuelle Orientierung)",
                        "Registrierung",
                    ),
                    listOf("Fotos", "Profilbilder", "Upload durch Nutzer, gespeichert bei Cloudflare R2"),
                    listOf(
                        "Verifizierungs-Selfies",
                        "Selfie-Aufnahmen mit vorgegebenen Posen für die Alters- und " +
                            "Identitätsprüfung",
                        "Live-Aufnahme über die Kamera, temporär bei Cloudflare R2",
                    ),
                    listOf(
                        "Ausweisaufnahmen",
                        "Aufnahme eines amtlichen Lichtbildausweises (Personalausweis, Reisepass " +
                            "oder Führerschein) für die Alters- und Identitätsprüfung",
                        "Upload durch Nutzer, temporär in einem nicht öffentlich abrufbaren " +
                            "Bereich bei Cloudflare R2",
                    ),
                    listOf(
                        "Verifizierungs-Status",
                        "Ergebnis der Prüfung, Prüfgrund aus einer festen Liste, Zeitpunkt der " +
                            "Prüfung und der Freischaltung, Prüfkennung",
                        "Ergebnis der manuellen Prüfung",
                    ),
                    listOf(
                        "Registrierungsversuche unter 18",
                        "Zufällige Geräte-ID und Zeitpunkt — kein Name, keine E-Mail, kein " +
                            "Geburtsdatum",
                        "Registrierungsformular",
                    ),
                    listOf("Nutzungsdaten", "Swipes, Matches, Reports/Blocks", "App-Nutzung"),
                    listOf(
                        "Zahlungsdaten",
                        "Abo-Status, Stripe-Kunden-/Abo-ID (keine Kartendaten bei uns)",
                        "Stripe Checkout",
                    ),
                    listOf(
                        "Technische Daten",
                        "IP-Adresse (Server-Logs), Zeitstempel",
                        "Automatisch beim Zugriff",
                    ),
                ),
            ),
            LegalBlock.Heading("3. Zwecke und Rechtsgrundlagen (Art. 6 DSGVO)"),
            LegalBlock.Bullets(
                listOf(
                    "Vertragserfüllung (Art. 6 Abs. 1 lit. b): Bereitstellung des Matching-Dienstes, " +
                        "Abo-Abwicklung.",
                    "Berechtigtes Interesse (Art. 6 Abs. 1 lit. f): Betrugs-/Missbrauchsprävention, " +
                        "Sicherheit (Report/Block-Funktion).",
                    "Einwilligung (Art. 6 Abs. 1 lit. a i. V. m. Art. 9 Abs. 2 lit. a): Verarbeitung " +
                        "der sexuellen Orientierung über das Präferenzfeld.",
                ),
            ),
            LegalBlock.Heading("3a. Alters- und Identitätsprüfung"),
            LegalBlock.Paragraph(
                "Was geprüft wird. Vor der Freischaltung eines Accounts prüfen wir einmalig, ob " +
                    "der Nutzer mindestens 18 Jahre alt ist und ob die Verifizierung zu seinem " +
                    "Profil gehört. Verarbeitet werden dafür: die Verifizierungs-Selfies, eine " +
                    "temporäre Aufnahme eines amtlichen Lichtbildausweises, das bei der " +
                    "Registrierung angegebene Geburtsdatum sowie der Verifizierungs-Status samt " +
                    "Prüfzeitpunkt.",
            ),
            LegalBlock.Paragraph(
                "Zwecke. Altersprüfung und Verhinderung von Accounts Minderjähriger, Prüfung der " +
                    "Plausibilität von Identität und Profil sowie Missbrauchs- und " +
                    "Fake-Profil-Prävention.",
            ),
            LegalBlock.Paragraph(
                "Art der Prüfung — kein biometrisches Verfahren. Die Prüfung erfolgt " +
                    "ausschließlich manuell: Ein Mensch vergleicht Profilbild, " +
                    "Verifizierungs-Selfie und Ausweisfoto durch Sichtvergleich und gleicht das " +
                    "Geburtsdatum ab. Es kommt keine automatisierte biometrische " +
                    "Gesichtserkennung zum Einsatz, es werden keine Gesichtsmerkmale berechnet, " +
                    "gespeichert oder mit einer Datenbank abgeglichen, und es ist kein externer " +
                    "Identifizierungsdienstleister eingebunden. Es findet keine automatisierte " +
                    "Entscheidung im Sinne des Art. 22 DSGVO statt.",
            ),
            LegalBlock.Paragraph(
                "Datenminimierung. Es wird nur verlangt, was für die Prüfung nötig ist: " +
                    "Lichtbild, Geburtsdatum, Dokumenttyp und die zur Plausibilitätsprüfung " +
                    "erforderlichen Gültigkeitsangaben. Nicht benötigte Angaben auf dem Dokument " +
                    "dürfen vor dem Hochladen geschwärzt werden. Ausweisnummer, maschinenlesbare " +
                    "Zone und der übrige Dokumentinhalt werden nicht ausgelesen und nicht " +
                    "gespeichert; es wird auch keine zusätzliche Kopie des Geburtsdatums aus dem " +
                    "Ausweis angelegt.",
            ),
            LegalBlock.Paragraph(
                "Zugriff und Speicherort. Die Ausweisaufnahmen liegen in einem eigenen, nicht " +
                    "öffentlich abrufbaren Bereich des Objektspeichers. Sie erhalten keine " +
                    "öffentliche Adresse; für die Prüfung werden ausschließlich Links mit sehr " +
                    "kurzer Gültigkeit erzeugt, die nur angemeldeten Prüfern angezeigt werden.",
            ),
            LegalBlock.Paragraph(
                "Rechtsgrundlage. Die Prüfung ist Voraussetzung für die Nutzung von FLEXR und " +
                    "dient der Einhaltung des Mindestalters sowie der Sicherheit der Plattform " +
                    "(Art. 6 Abs. 1 lit. b und lit. f DSGVO). Für die Aufnahmen von Gesicht und " +
                    "Ausweis holen wir zusätzlich eine ausdrückliche Einwilligung ein, die vor " +
                    "der Aufnahme erteilt wird (Art. 6 Abs. 1 lit. a DSGVO); ohne sie kann der " +
                    "Account nicht freigeschaltet werden. Die Einwilligung kann jederzeit mit " +
                    "Wirkung für die Zukunft widerrufen werden — noch nicht geprüfte Aufnahmen " +
                    "lassen sich in der App selbst zurückziehen und werden dann sofort gelöscht.",
            ),
            LegalBlock.Paragraph(
                "Registrierungsversuche unter 18. Wird bei der Registrierung ein Geburtsdatum " +
                    "unter 18 Jahren angegeben, halten wir zum Schutz vor systematischem " +
                    "Ausprobieren der Altersgrenze fest, dass ein solcher Versuch stattgefunden " +
                    "hat — gespeichert werden dabei nur die zufällige Geräte-ID und der " +
                    "Zeitpunkt, keine Namens-, Kontakt- oder Geburtsdaten. Diese Einträge werden " +
                    "nur für ein kurzes Zeitfenster ausgewertet.",
            ),
            LegalBlock.Heading("4. Empfänger / Auftragsverarbeiter"),
            LegalBlock.Table(
                headers = listOf("Dienst", "Zweck", "Sitz / Übermittlung"),
                rows = listOf(
                    listOf(
                        "Cloudflare R2",
                        "Speicherung von Profilfotos; temporäre Speicherung von " +
                            "Verifizierungs-Selfies und Ausweisaufnahmen",
                        "Eastern Europe (EEUR) — EU, kein Drittstaatentransfer",
                    ),
                    listOf(
                        "Stripe",
                        "Zahlungsabwicklung, Abo-Verwaltung",
                        "USA/EU, Standardvertragsklauseln (SCC)",
                    ),
                    listOf(
                        "Contabo GmbH, Welfenstraße 22, 81541 München, Deutschland",
                        "Serverbetrieb (VPS)",
                        "Deutschland/EU",
                    ),
                ),
            ),
            LegalBlock.Note(
                "Mit allen Auftragsverarbeitern bestehen Auftragsverarbeitungsverträge (Art. 28 DSGVO).",
            ),
            LegalBlock.Heading("5. Speicherdauer"),
            LegalBlock.Bullets(
                listOf(
                    "Kontodaten: bis zur Löschung des Profils durch den Nutzer.",
                    "Nach Löschung: 30 Tage Karenzzeit, danach vollständige und unwiderrufliche " +
                        "Löschung aller Daten inklusive Fotos aus Cloudflare R2.",
                    "Verifizierungs-Selfies: werden unmittelbar nach Abschluss der Prüfung (Freigabe " +
                        "oder Ablehnung) gelöscht.",
                    "Zahlungsbezogene Daten: gemäß gesetzlicher Aufbewahrungspflichten " +
                        "(i. d. R. 7 Jahre, §132 BAO).",
                ),
            ),
            LegalBlock.Heading("6. Betroffenenrechte"),
            LegalBlock.Paragraph(
                "Auskunft (Art. 15), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung " +
                    "(Art. 18), Datenübertragbarkeit (Art. 20), Widerspruch (Art. 21), Widerruf einer " +
                    "Einwilligung mit Wirkung für die Zukunft (Art. 7 Abs. 3). Kontakt dafür: " +
                    "flexr.social@proton.me.",
            ),
            LegalBlock.Heading("7. Beschwerderecht"),
            LegalBlock.Paragraph(
                "Österreichische Datenschutzbehörde (DSB), Barichgasse 40–42, 1030 Wien, www.dsb.gv.at.",
            ),
            LegalBlock.Heading("8. Keine Standortdaten"),
            LegalBlock.Paragraph(
                "FLEXR erhebt keine Standortdaten. Die Umkreissuche rechnet ausschließlich mit " +
                    "der öffentlichen Adresse des Studios, das du selbst im Profil auswählst, und " +
                    "dem von dir eingestellten Suchradius. Die App fragt keine Geräteposition ab " +
                    "und verlangt dafür auch keine Berechtigung.",
            ),
            LegalBlock.Heading("9. Kein Tracking"),
            LegalBlock.Paragraph(
                "Die App setzt keine Analyse- oder Werbe-SDKs ein. Der Login-Token und ein zufällig " +
                    "erzeugter Gerätebezug (Mehrfachkonto-Erkennung) werden ausschließlich lokal auf " +
                    "dem Gerät gespeichert, vom Cloud-Backup ausgenommen und beim Deinstallieren " +
                    "gelöscht.",
            ),
        ),
    )
}
