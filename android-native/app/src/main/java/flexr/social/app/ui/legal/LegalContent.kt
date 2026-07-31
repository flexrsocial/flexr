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
                "Ja. FLEXR hat eine Melde- und Blockfunktion, eine Foto-Verifizierung (blauer Haken) " +
                    "sowie einen automatischen Schutz im Chat, der Scam-Nachrichten und externe Links " +
                    "erkennt und entfernt.",
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
            LegalBlock.Heading("EU-Streitschlichtung"),
            LegalBlock.Paragraph(
                "Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) " +
                    "bereit: ec.europa.eu/consumers/odr. Unsere E-Mail-Adresse für " +
                    "Verbraucherbeschwerden: flexr.social@proton.me. Wir sind freiwillig bereit, an " +
                    "einem Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.",
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
                    "Mindestalter 18 Jahre. Mit der Registrierung bestätigt der Nutzer aktiv, " +
                        "mindestens 18 Jahre alt zu sein. Es erfolgt aktuell keine Ausweis-/ID-" +
                        "Verifikation, sondern eine Selbstauskunft mit serverseitiger Altersgrenze " +
                        "(18–99 Jahre). Bei begründetem Verdacht auf Falschangabe behalten wir uns die " +
                        "Sperre des Accounts vor.",
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
            LegalBlock.Heading("6. Nutzungsregeln, Melde- und Blockfunktion"),
            LegalBlock.Paragraph(
                "Untersagt sind insbesondere: Belästigung anderer Nutzer, Hochladen rechtswidriger, " +
                    "beleidigender oder Rechte Dritter verletzender Inhalte, kommerzielle Werbung, " +
                    "Fake-Profile. Verstöße können über die Melde-Funktion in der App gemeldet werden; " +
                    "wir behalten uns vor, gemeldete oder blockierte Nutzer zu sperren.",
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
                    "OS-Plattform der EU: ec.europa.eu/consumers/odr.",
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
                        "Name, Geburtsdatum, Stadt, Gym, Bio",
                        "Registrierung / Profilbearbeitung",
                    ),
                    listOf(
                        "Präferenzdaten (Art. 9 DSGVO)",
                        "Geschlecht, gesuchtes Geschlecht (→ sexuelle Orientierung)",
                        "Registrierung",
                    ),
                    listOf("Fotos", "Profilbilder", "Upload durch Nutzer, gespeichert bei Cloudflare R2"),
                    listOf(
                        "Standortdaten",
                        "GPS-Position (nur bei aktiver Standortfreigabe am Gerät), ersatzweise die " +
                            "Koordinate der angegebenen PLZ, gewählter Suchradius",
                        "Gerät (Standortfreigabe) / Registrierung",
                    ),
                    listOf(
                        "Verifizierungs-Selfies",
                        "Selfie-Aufnahmen mit vorgegebenen Posen für die freiwillige Profil-" +
                            "Verifizierung (blauer Haken)",
                        "Live-Aufnahme über die Kamera, gespeichert bei Cloudflare R2",
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
                    "Standortdaten: Vertragserfüllung (Art. 6 Abs. 1 lit. b) für die Umkreissuche. Die " +
                        "GPS-Position wird nur verarbeitet, wenn die Standortfreigabe am Gerät aktiv " +
                        "ist; andernfalls wird ersatzweise die Koordinate der angegebenen PLZ " +
                        "verwendet. Bei deaktivierter oder widerrufener Standortfreigabe wird die " +
                        "gespeicherte GPS-Position gelöscht.",
                    "Verifizierungs-Selfies: Einwilligung (Art. 6 Abs. 1 lit. a). Die Verifizierung " +
                        "ist freiwillig und wird aktiv vom Nutzer gestartet. Die Selfies werden " +
                        "ausschließlich zur Echtheitsprüfung des Profils mit den Profilfotos " +
                        "verglichen; die Prüfung erfolgt manuell durch den Betreiber, es findet keine " +
                        "automatisierte biometrische Auswertung statt.",
                ),
            ),
            LegalBlock.Heading("4. Empfänger / Auftragsverarbeiter"),
            LegalBlock.Table(
                headers = listOf("Dienst", "Zweck", "Sitz / Übermittlung"),
                rows = listOf(
                    listOf(
                        "Cloudflare R2",
                        "Speicherung von Profilfotos",
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
                    "GPS-Standortdaten: werden bei jedem App-Start aktualisiert und bei deaktivierter " +
                        "Standortfreigabe gelöscht.",
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
            LegalBlock.Heading("8. Kein Tracking"),
            LegalBlock.Paragraph(
                "Die App setzt keine Analyse- oder Werbe-SDKs ein. Der Login-Token und ein zufällig " +
                    "erzeugter Gerätebezug (Mehrfachkonto-Erkennung) werden ausschließlich lokal auf " +
                    "dem Gerät gespeichert, vom Cloud-Backup ausgenommen und beim Deinstallieren " +
                    "gelöscht.",
            ),
        ),
    )
}
