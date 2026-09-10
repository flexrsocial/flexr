/* FLEXR Landingpage - Woerterbuch Deutsch / Englisch
   ============================================================================
   Ergaenzt /i18n.js um die Texte der oeffentlichen Startseite.

   Was hier bewusst NICHT uebersetzt wird:

   * Die JSON-LD-Auszeichnung im <head>. Sie beschreibt die kanonische, deutsche
     Fassung dieser URL. Eine per JavaScript nachtraeglich umgeschriebene
     FAQPage-Auszeichnung waere gegenueber Google nur noch Rauschen.
   * Die Rechtstexte hinter den Links der Fussleiste - sie sind in der
     deutschen Fassung verbindlich.

   Titel, Beschreibung und og:-Angaben werden dagegen mitgeschaltet, damit ein
   geteilter Link in der Sprache erscheint, in der der Teilende die Seite
   gelesen hat.
   ========================================================================== */
(function(){
  'use strict';
  if(!window.FlexrI18n){ console.error('FlexrI18n fehlt - /i18n.js zuerst laden.'); return; }

  FlexrI18n.register({
  de: {
    'meta.title': 'FLEXR – Dating für Gym-People in Österreich',
    'meta.description': 'FLEXR ist die Dating-App für Gym-People in Österreich: Matches nach Fitnessstudio und Umkreis. Die Nutzung ist dauerhaft kostenlos; FLEXR Premium (10 €/Monat) ist freiwillig.',
    'meta.ogTitle': 'FLEXR – Dating für Gym-People in Österreich',
    'meta.ogDescription': 'Finde Menschen, die Training genauso ernst nehmen wie du – in deinem Gym und in deiner Nähe. Dauerhaft kostenlos nutzbar.',
    'meta.ogLocale': 'de_AT',

    'nav.aria': 'Hauptnavigation',
    'nav.home': 'FLEXR Startseite',
    'nav.how': 'So funktioniert’s',
    'nav.price': 'Preis',
    'nav.faq': 'FAQ',
    'nav.login': 'Einloggen',
    'common.skipToContent': 'Zum Inhalt springen',

    'hero.eyebrow': 'FLEXR · Dating für Gym-People',
    'hero.h1': 'Dating für<br>Gym-People<br>in <em>Österreich</em>',
    'hero.sub': 'Finde Menschen, die Training genauso ernst nehmen wie du – in deinem Gym und in deiner Nähe. Match. Train. Repeat.',
    'hero.ctaStart': 'Gratis loslegen',
    'hero.ctaNote': 'Kostenlos registrieren, kein Zahlungsmittel nötig. Ab 18.',
    'hero.cardSub': 'Krafttraining · Wien',
    'hero.badge': 'In deiner Nähe',
    'hero.usp1': 'Matches nach Gym und Umkreis — nicht am anderen Ende Österreichs',
    'hero.usp2': 'Dauerhaft gratis nutzbar — <b>nichts wird abgebucht</b>, Premium ist freiwillig',
    'hero.usp3': 'Jedes Konto wird vor der Freischaltung auf Volljährigkeit geprüft',

    'life.h2': 'Dating, das zu deinem Lifestyle passt',
    'life.p1': 'Wer regelmäßig trainiert, kennt das Gespräch: „Du gehst schon <i>wieder</i> ins Gym?“ Fünf Einheiten die Woche, das Abendessen nach dem Training statt davor, der Wecker am Sonntag um sieben – das ist kein Hobby, das man nebenbei erklärt. Es ist ein Teil des Tages, um den herum der Rest geplant wird.',
    'life.p2': 'FLEXR ist für Menschen, die sich das nicht erklären wollen. Nicht, weil Training das Einzige wäre, was zählt, sondern weil ein gemeinsames Verständnis für Zeitaufwand und Disziplin eine Menge Reibung wegnimmt. Wer selbst trainiert, fragt nicht, warum du am Freitagabend noch eine Einheit einschiebst – und schlägt vielleicht vor, mitzukommen.',
    'life.p3': 'Und damit das klar ist: Es geht <b>nicht</b> um einen bestimmten Körper. Kraftsport, Functional Fitness, Ausdauer, Kampfsport, Klettern, der dritte Monat nach dem Wiedereinstieg – alles zählt. FLEXR ist kein Wettbewerb um Körperfettanteile, sondern eine Plattform für Leute, die einen ähnlichen Alltag führen.',

    'gym.h2': 'Matches rund um dein Gym',
    'gym.p1': 'Die meisten Dating-Apps fragen dein Handy nach dem Standort und zeigen dir dann, wer gerade in der Nähe ist. FLEXR macht das anders – und zwar bewusst:',
    'gym.li1': '<b>Du wählst dein Studio.</b> Aus einer Liste österreichischer Fitnessstudios mit Adresse. Fehlt deins, reichst du es mit Adresse ein und kannst es sofort verwenden.',
    'gym.li2': '<b>Du stellst deinen Suchradius ein.</b> Von 2 bis 250 Kilometer. Größerer Radius heißt mehr Profile, dafür weitere Wege.',
    'gym.li3': '<b>Keine GPS-Ortung.</b> Weder Browser noch App fragen deine Geräteposition ab. Gerechnet wird ausschließlich mit der öffentlichen Adresse des Studios, das du selbst angegeben hast. Dein Wohnort wird niemandem angezeigt – andere sehen nur deine Stadt.',
    'gym.li4': '<b>Du siehst Leute aus Studios im Umkreis</b>, nicht nur aus deinem eigenen. Das Gym ist der Mittelpunkt, nicht der Zaun.',
    'gym.p2': 'Der praktische Vorteil: Ihr habt von Anfang an einen Ort, den ihr beide kennt, und einen naheliegenden Vorschlag fürs erste Treffen.',

    'sample.h2': 'So könnte dein Match aussehen',
    'sample.p1': 'Ein Ausschnitt aus dem Deck, wie es beim Swipen aussieht. Zieh die Karte oder probier X und Herz aus. Keine echten Mitglieder — die Gesichter sind KI-generiert.',
    'sample.deckAria': 'Interaktives Muster-Swipe-Deck',
    // Beschreibungen der KI-generierten Musterprofile. Keine echten
    // Mitglieder - siehe frontend/brand/demo/README.md.
    'sample.bio1': 'Push Day, Bergtouren und Kaffee nach dem Training.',
    'sample.bio2': 'Functional Fitness, Meal Prep und sonntags eine lange Runde.',
    'sample.bio3': 'Leg Day, Espresso und jedes Wochenende irgendwo draußen.',
    'sample.bio4': 'Krafttraining, Wandern und immer offen für einen Spotter.',
    'sample.bio5': 'Ganzkörper-Split, Runden um den Wörthersee und Kaffee danach.',
    'sample.bio6': 'Schwere Squats, Wiener Kaffee und sonntags Meal Prep.',
    'sample.bio7': 'Dumbbells, lange Spaziergänge und immer bereit für eine neue Playlist.',
    'sample.bio8': 'Pull Days, Sushi nach dem Training und klare Trainingspläne.',
    'sample.bio9': 'Langhantel, Leg Days und Kaffee an der Donau.',
    'sample.bio10': 'Intervalle, Halbmarathons und Frühstück nach dem Early-Bird-Workout.',
    'sample.bio11': 'Squats, Bergtouren und Sonnenuntergänge über Tirol.',
    'sample.bio12': 'Calisthenics, Sonnenuntergänge und Trainings draußen.',
    'sample.bio13': 'Functional Fitness, Skitage und Early-Bird-Workouts.',
    'sample.bio14': 'Cycling, Krafttraining und aktive Wochenenden in Tirol.',
    'sample.bio15': 'Battle Ropes, Team-Workouts und nie ohne gute Laune.',
    'sample.bio16': 'Deadlifts, Push Day und danach Wiener Schnitzel.',
    'sample.bio17': 'Men\'s Physique, Struktur und die beste Pasta nach dem Wettkampf.',
    'sample.bio18': 'Pull-ups, Basketball und Training vor dem Frühstück.',
    'sample.bio19': 'Upper Body, Fotografie und neue Restaurants in Linz.',
    'sample.bio20': 'Push Day, Meal Prep und der Shake direkt nach dem Training.',
    'sample.bio21': 'Functional Fitness, Fußball und spontane Wochenendtrips.',
    'sample.bio22': 'Intervalle, Trail Runs und Espresso vor sieben.',
    'sample.bio23': 'Schwere Grundübungen, Wandern und Espresso nach dem Training.',
    'sample.bio24': 'Shoulder Day, Donauinsel und aktive Wochenenden.',
    'sample.bio25': 'Calisthenics, Donauinsel und Sommerabende draußen.',
    'sample.pass': 'Beispielprofil ablehnen',
    'sample.like': 'Beispielprofil gefällt mir',
    'sample.hint': 'Ziehen, tippen oder Pfeiltasten verwenden',

    'how.h2': 'So funktioniert FLEXR',
    'how.step1': 'Schritt 1',
    'how.step1H3': 'Profil erstellen',
    'how.step1P': 'E-Mail, Geburtsdatum, Postleitzahl, mindestens ein Foto. Kostenlos und ohne Zahlungsmittel. Danach prüfen wir einmalig, ob du mindestens 18 bist – erst dann geht es weiter. Kosten entstehen dabei keine, auch später nicht.',
    'how.step2': 'Schritt 2',
    'how.step2H3': 'Gym und Radius wählen',
    'how.step2P': 'Such dein Studio nach Name, Ort oder Postleitzahl und stell ein, wie weit du fahren würdest. Beides kannst du jederzeit im Konto ändern.',
    'how.step3': 'Schritt 3',
    'how.step3H3': 'Liken, matchen, schreiben',
    'how.step3P': 'Du siehst passende Profile aus deinem Umkreis. Liken sich zwei Leute gegenseitig, entsteht ein Match – und erst dann könnt ihr schreiben. Vorher landet bei dir keine ungefragte Nachricht.',

    'at.h2': 'Für Gym-People in ganz Österreich',
    'at.p1': 'FLEXR funktioniert mit jeder österreichischen Postleitzahl – in <b>Wien</b> genauso wie in <b>Graz</b>, <b>Linz</b>, <b>Salzburg</b>, <b>Innsbruck</b>, <b>Klagenfurt</b>, <b>Villach</b>, <b>Wels</b>, <b>St. Pölten</b>, <b>Dornbirn</b> oder <b>Wiener Neustadt</b>.',
    'at.p2': 'Ehrlich dazu: Wie viele Profile du siehst, hängt davon ab, wie viele Leute in deinem Umkreis dabei sind. In Ballungsräumen sind es mehr als am Land. Wir nennen bewusst keine Nutzerzahlen und versprechen keine bestimmte Anzahl an Matches – wer das tut, hat sie meist erfunden. Wenn du am Land wohnst, stell den Radius größer ein; die nächste größere Stadt ist oft näher, als es sich anfühlt.',
    'at.p3': 'FLEXR ist derzeit auf Österreich beschränkt. Das ist keine Übergangslösung, sondern der Punkt: Eine Dating-App, die in einem überschaubaren Markt gut funktioniert, ist mehr wert als eine, die überall ein bisschen läuft.',

    'safe.h2': 'Geprüfte Profile und Sicherheit',
    'safe.p1': 'Dating-Apps ziehen Betrüger an. Dagegen tun wir Folgendes – und das sind keine Marketingversprechen, sondern das, was tatsächlich läuft:',
    'safe.li1': '<b>Ab 18, und das wird geprüft.</b> Das Alter wird serverseitig aus dem Geburtsdatum berechnet. Vor der Freischaltung vergleicht ein Mensch dein Profilbild, ein live aufgenommenes Selfie und ein amtliches Lichtbilddokument und gleicht das Geburtsdatum ab.',
    'safe.li2': '<b>Manuelle Prüfung, keine Gesichtserkennung.</b> Es kommt keine automatische biometrische Erkennung zum Einsatz, es werden keine Gesichtsmerkmale berechnet oder gespeichert, und die Aufnahmen werden nach der Prüfung gelöscht.',
    'safe.li3': '<b>Jedes Foto wird freigegeben, bevor es jemand sieht.</b> Von einem Menschen. Lehnen wir eines ab, sagen wir dir warum.',
    'safe.li4': '<b>Scam-Schutz im Chat.</b> Links und E-Mail-Adressen werden automatisch entfernt, auffällige Nachrichten der Moderation vorgelegt. Profiltexte mit Links, Telefonnummern oder typischen Scam-Begriffen werden gar nicht erst veröffentlicht.',
    'safe.li5': '<b>Melden und Blockieren.</b> Blockieren wirkt sofort und beidseitig. Beim Melden bekommst du ein Aktenzeichen und siehst die Entscheidung samt Begründung in deinem Konto.',
    'safe.p2': 'Was wir <b>nicht</b> behaupten: dass jedes Profil garantiert echt ist oder dass FLEXR vollständig sicher wäre. Eine Sichtprüfung erschwert Täuschungen, sie schließt sie nicht aus. Lies vor einem ersten Treffen bitte unsere <a href="/sicherheit.html">Sicherheitstipps</a> – sie sind kurz und ersparen im Zweifel eine Menge.',

    'price.h2': 'Was FLEXR kostet',
    'price.lead': '<b>FLEXR zu nutzen kostet nichts — dauerhaft, nicht nur in der Beta.</b> Registrieren, Profile ansehen, liken, matchen und schreiben sind und bleiben kostenlos. Es wird kein Zahlungsmittel abgefragt.',
    'price.freeEyebrow': 'FLEXR',
    'price.forever': '/ für immer',
    'price.free1': 'Profile ansehen und matchen',
    'price.free2': '20 Likes pro Tag',
    'price.free3': '3 Unterhaltungen gleichzeitig',
    'price.free4': 'Suchumkreis bis 50 km',
    'price.free5': 'Kein Zahlungsmittel, nichts zu kündigen',
    'price.premiumEyebrow': 'FLEXR Premium',
    'price.perMonth': '/ Monat',
    'price.prem1': 'Unbegrenzt liken',
    'price.prem2': 'Unbegrenzt viele Unterhaltungen',
    'price.prem3': 'Sehen, wer dich geliket hat',
    'price.prem4': 'Letzten Swipe zurücknehmen',
    'price.prem5': 'Voller Suchumkreis bis 250 km',
    'price.prem6': 'Premium-Abzeichen im Profil',
    'price.premiumSoon': 'Kommt nach der Beta-Phase',
    'price.cta': 'Kostenlos starten',
    'price.p1': '<b>Aus einem kostenlosen Konto wird nie von selbst ein Abo.</b> Bei der Registrierung wird kein Zahlungsmittel abgefragt und keines hinterlegt. Premium entsteht nur, wenn du es ausdrücklich abschließt — du musst sonst nichts kündigen und kannst keine Frist versäumen.',
    'price.p2': 'Während der Beta-Phase gibt es FLEXR Premium noch nicht: Bis dahin sind Likes, Unterhaltungen und Umkreis für alle unbegrenzt. Sobald Premium startet, sagen wir das vorher an. Die 10&nbsp;€ pro Monat sind der Endpreis; Umsatzsteuer wird nicht zusätzlich verrechnet, und gekündigt wird mit einem Klick zum Ende des laufenden Monats.',

    'faq.h2': 'Häufige Fragen',
    'faq.q1': 'Was ist FLEXR?',
    'faq.a1': 'Eine Dating-App für Menschen, denen Training und Gym wichtig sind. Du findest Matches nach deinem Fitnessstudio und deinem Umkreis — in ganz Österreich.',
    'faq.q2': 'Für wen ist FLEXR?',
    'faq.a2': 'Für alle ab 18, die Training ernst nehmen und jemanden mit ähnlichem Lifestyle kennenlernen wollen. Der gemeinsame Nenner ist nicht ein Körper, sondern ein Alltag, in dem das Studio fix eingeplant ist.',
    'faq.q3': 'Ist FLEXR nur für Bodybuilder?',
    'faq.a3': 'Nein. Kraftsport, Functional Fitness, Ausdauer, Kampfsport, Klettern — alles zählt, unabhängig vom Level. Es geht um den Lifestyle, nicht um ein bestimmtes Aussehen.',
    'faq.q4': 'Was kostet FLEXR?',
    'faq.a4': '<b>Nichts.</b> FLEXR zu nutzen ist dauerhaft kostenlos — Profile ansehen, liken, matchen und schreiben kosten kein Geld, auch nach der Beta nicht. Optional gibt es nach der Beta <b>FLEXR&nbsp;Premium</b> für 10&nbsp;€ pro Monat: unbegrenzt liken, unbegrenzt viele Unterhaltungen, sehen wer dich geliket hat, den letzten Swipe zurücknehmen und der volle Suchumkreis. Ohne Premium gelten 20 Likes pro Tag, 3 Unterhaltungen gleichzeitig und 50&nbsp;km Umkreis. Kostenpflichtig wird nichts, ohne dass du dich aktiv dafür entscheidest.',
    'faq.q5': 'Wird mein Konto automatisch kostenpflichtig?',
    'faq.a5': '<b>Nein.</b> Bei der Registrierung wird kein Zahlungsmittel hinterlegt, aus einem kostenlosen Konto kann also gar kein Abo werden. Du musst nichts kündigen und keine Frist beachten.',
    'faq.q6': 'Wie funktionieren Matches?',
    'faq.a6': 'Du wählst Gym und Suchradius und siehst passende Profile aus diesem Umkreis. Liken sich zwei Personen gegenseitig, entsteht ein Match und ihr könnt schreiben. Vorher kann euch niemand anschreiben.',
    'faq.q7': 'Muss mein Gym bereits gelistet sein?',
    'faq.a7': 'Nein. Fehlt dein Studio, reichst du es mit Adresse ein und kannst es sofort für dein Profil verwenden. Nach der Prüfung erscheint es für alle in der Auswahl.',
    'faq.q8': 'Wie funktioniert die Altersverifikation?',
    'faq.a8': 'Du bestätigst deine E-Mail-Adresse, nimmst ein Selfie live über die Kamera auf und lädst eine Aufnahme eines amtlichen Lichtbildausweises hoch — als Foto oder als Datei von deinem Gerät. Ein Mensch vergleicht Profilbild, Selfie und Ausweisfoto und prüft das Geburtsdatum — <b>keine automatische Gesichtserkennung</b>. Die Aufnahmen werden danach gelöscht.',
    'faq.q9': 'Speichert FLEXR meinen Standort?',
    'faq.a9': 'Nein. Weder Browser noch App fragen eine Geräteposition ab. Die Umkreissuche rechnet ausschließlich mit der öffentlichen Adresse des Studios, das du selbst auswählst.',
    'faq.q10': 'Ist FLEXR in ganz Österreich verfügbar?',
    'faq.a10': 'Ja, jede österreichische Postleitzahl funktioniert. Wie viele Profile du siehst, hängt davon ab, wie viele Leute in deinem Umkreis dabei sind — in Ballungsräumen mehr als am Land.',
    'faq.q11': 'Wie kündige ich?',
    'faq.a11': 'Im Konto-Bereich unter „Abo verwalten / kündigen“, jederzeit und ohne Frist. Der Zugang bleibt bis zum Ende der bezahlten Periode aktiv.',
    'faq.q12': 'Wie melde oder blockiere ich jemanden?',
    'faq.a12': 'Über das Flaggen-Symbol in jedem Profil und Chat. Blockieren wirkt sofort und beidseitig. Beim Melden bekommst du ein Aktenzeichen und siehst das Ergebnis unter „Meine Meldungen“. Ohne Konto geht es über das <a href="/meldung.html">öffentliche Meldeformular</a>.',
    'faq.more': 'Mehr Antworten stehen in den <a href="/faq.html">ausführlichen FAQ</a>.',

    'start.h2': 'Bereit?',
    'start.p': 'Profil erstellen, Gym auswählen, loslegen. Während der Beta kostet FLEXR nichts — ohne Zahlungsmittel, ohne Frist.',

    'foot.toApp': 'Zur App',
    'foot.safetyTitle': 'Sicherheit',
    'foot.safetyTips': 'Sicherheitstipps',
    'foot.authorities': 'Für Behörden',
    'foot.note': 'FLEXR ist eine Marke von Julian Pachernegg, Einzelunternehmer, 8232 Grafendorf, Österreich. Nutzung ab 18 Jahren. Vollständige Anbieterangaben im <a href="/impressum.html">Impressum</a>.',

    'beta.eyebrow': 'Beta-Phase',
    'beta.title': 'FLEXR ist noch im Aufbau',
    'beta.text': 'Du kannst FLEXR schon jetzt im Browser nutzen. Weil wir noch in der Beta sind, sind manche Regionen dünn besetzt und einzelne Funktionen ändern sich noch.',
    'beta.free': '<b>FLEXR zu nutzen kostet nichts — dauerhaft.</b> Kein Probemonat, keine Mitgliedsgebühr, kein Zahlungsmittel. Nach der Beta kommt <b class="inline">FLEXR&nbsp;Premium</b> für 10&nbsp;€ im Monat dazu: freiwillig, monatlich kündbar und nur für alle, die mehr wollen als die 20 Likes und 3 Unterhaltungen pro Tag, die dann für Standardkonten gelten. Während der Beta ist auch das unbegrenzt.',
    'beta.android': 'Veröffentlichung geplant für Ende September 2026',
    'beta.ios': 'folgt im Anschluss',
    'beta.outro': 'Mit dem Start der Android-App geht FLEXR dann richtig an den Start.',
    'beta.ok': 'Verstanden',
    'beta.closeAria': 'Hinweis schließen'
  },

  en: {
    'meta.title': 'FLEXR – dating for gym people in Austria',
    'meta.description': 'FLEXR is the dating app for gym people in Austria: matches by gym and radius. Using it is permanently free; FLEXR Premium (€10/month) is optional.',
    'meta.ogTitle': 'FLEXR – dating for gym people in Austria',
    'meta.ogDescription': 'Find people who take training as seriously as you do – at your gym and close to you. Free to use, permanently.',
    'meta.ogLocale': 'en',

    'nav.aria': 'Main navigation',
    'nav.home': 'FLEXR home',
    'nav.how': 'How it works',
    'nav.price': 'Pricing',
    'nav.faq': 'FAQ',
    'nav.login': 'Log in',
    'common.skipToContent': 'Skip to content',

    'hero.eyebrow': 'FLEXR · dating for gym people',
    'hero.h1': 'Dating for<br>gym people<br>in <em>Austria</em>',
    'hero.sub': 'Find people who take training as seriously as you do – at your gym and close to you. Match. Train. Repeat.',
    'hero.ctaStart': 'Start for free',
    'hero.ctaNote': 'Sign up free, no payment method needed. 18+.',
    'hero.cardSub': 'Strength training · Vienna',
    'hero.badge': 'Near you',
    'hero.usp1': 'Matches by gym and radius — not from the other end of Austria',
    'hero.usp2': 'Free to use, permanently — <b>nothing is charged</b>, Premium is optional',
    'hero.usp3': 'Every account is checked for being of age before it is unlocked',

    'life.h2': 'Dating that fits your lifestyle',
    'life.p1': 'Anyone who trains regularly knows the conversation: “You’re going to the gym <i>again</i>?” Five sessions a week, dinner after training instead of before, the alarm at seven on a Sunday – that is not a hobby you explain in passing. It is a part of the day that the rest gets planned around.',
    'life.p2': 'FLEXR is for people who would rather not have to explain that. Not because training is the only thing that counts, but because a shared understanding of the time and discipline involved removes a lot of friction. Someone who trains themselves does not ask why you squeeze in a session on a Friday evening – and might suggest coming along.',
    'life.p3': 'And to be clear: this is <b>not</b> about a particular body. Strength training, functional fitness, endurance, martial arts, climbing, the third month back after a break – all of it counts. FLEXR is not a contest about body fat percentages, it is a place for people who live a similar everyday life.',

    'gym.h2': 'Matches around your gym',
    'gym.p1': 'Most dating apps ask your phone for your location and then show you who happens to be nearby. FLEXR does it differently – deliberately:',
    'gym.li1': '<b>You choose your gym.</b> From a list of Austrian gyms with addresses. If yours is missing, submit it with its address and use it right away.',
    'gym.li2': '<b>You set your search radius.</b> From 2 to 250 kilometres. A larger radius means more profiles, but longer trips.',
    'gym.li3': '<b>No GPS tracking.</b> Neither the browser nor the app asks for your device location. Distances are calculated solely from the public address of the gym you entered yourself. Your home address is never shown to anyone – others only see your city.',
    'gym.li4': '<b>You see people from gyms in the area</b>, not only from your own. The gym is the centre, not the fence.',
    'gym.p2': 'The practical upside: from the start you both know a place, and there is an obvious suggestion for a first meeting.',

    'sample.h2': 'What your match could look like',
    'sample.p1': 'A slice of the deck as it looks when swiping. Drag the card or try X and the heart. No real members — the faces are AI-generated.',
    'sample.deckAria': 'Interactive sample swipe deck',
    'sample.bio1': 'Push day, mountain hikes and coffee after training.',
    'sample.bio2': 'Functional fitness, meal prep and a long run on Sundays.',
    'sample.bio3': 'Leg day, espresso and every weekend outdoors somewhere.',
    'sample.bio4': 'Strength training, hiking and always up for a spotter.',
    'sample.bio5': 'Full-body split, laps around Lake Wörth and coffee afterwards.',
    'sample.bio6': 'Heavy squats, Viennese coffee and meal prep on Sundays.',
    'sample.bio7': 'Dumbbells, long walks and always ready for a new playlist.',
    'sample.bio8': 'Pull days, sushi after training and clear training plans.',
    'sample.bio9': 'Barbell, leg days and coffee by the Danube.',
    'sample.bio10': 'Intervals, half marathons and breakfast after the early-bird workout.',
    'sample.bio11': 'Squats, mountain hikes and sunsets over Tyrol.',
    'sample.bio12': 'Calisthenics, sunsets and training outdoors.',
    'sample.bio13': 'Functional fitness, ski days and early-bird workouts.',
    'sample.bio14': 'Cycling, strength training and active weekends in Tyrol.',
    'sample.bio15': 'Battle ropes, team workouts and never without good spirits.',
    'sample.bio16': 'Deadlifts, push day and Wiener Schnitzel afterwards.',
    'sample.bio17': 'Men’s physique, structure and the best pasta after a competition.',
    'sample.bio18': 'Pull-ups, basketball and training before breakfast.',
    'sample.bio19': 'Upper body, photography and new restaurants in Linz.',
    'sample.bio20': 'Push day, meal prep and the shake straight after training.',
    'sample.bio21': 'Functional fitness, football and spontaneous weekend trips.',
    'sample.bio22': 'Intervals, trail runs and espresso before seven.',
    'sample.bio23': 'Heavy compound lifts, hiking and espresso after training.',
    'sample.bio24': 'Shoulder day, the Danube Island and active weekends.',
    'sample.bio25': 'Calisthenics, the Danube Island and summer evenings outdoors.',
    'sample.pass': 'Pass on example profile',
    'sample.like': 'Like example profile',
    'sample.hint': 'Drag, tap or use the arrow keys',

    'how.h2': 'How FLEXR works',
    'how.step1': 'Step 1',
    'how.step1H3': 'Create your profile',
    'how.step1P': 'Email, date of birth, postal code, at least one photo. Free and without a payment method. Then we check once that you are at least 18 – only then does it continue. No costs arise, now or later.',
    'how.step2': 'Step 2',
    'how.step2H3': 'Choose gym and radius',
    'how.step2P': 'Search for your gym by name, town or postal code and set how far you would travel. You can change both at any time in your account.',
    'how.step3': 'Step 3',
    'how.step3H3': 'Like, match, message',
    'how.step3P': 'You see matching profiles from your area. If two people like each other, a match is created – and only then can you message. Before that, no unsolicited message reaches you.',

    'at.h2': 'For gym people all across Austria',
    'at.p1': 'FLEXR works with every Austrian postal code – in <b>Vienna</b> just as in <b>Graz</b>, <b>Linz</b>, <b>Salzburg</b>, <b>Innsbruck</b>, <b>Klagenfurt</b>, <b>Villach</b>, <b>Wels</b>, <b>St. Pölten</b>, <b>Dornbirn</b> or <b>Wiener Neustadt</b>.',
    'at.p2': 'Honestly: how many profiles you see depends on how many people are on board within your radius. In urban areas there are more than in the countryside. We deliberately do not quote user numbers and do not promise a certain number of matches – those who do have usually made them up. If you live rurally, set the radius wider; the next larger town is often closer than it feels.',
    'at.p3': 'FLEXR is currently limited to Austria. That is not a stopgap, that is the point: a dating app that works well in a manageable market is worth more than one that runs a little bit everywhere.',

    'safe.h2': 'Checked profiles and safety',
    'safe.p1': 'Dating apps attract scammers. Here is what we do about it – these are not marketing promises but what actually happens:',
    'safe.li1': '<b>18+, and it is checked.</b> Age is calculated on the server from your date of birth. Before your account is unlocked, a person compares your profile picture, a live selfie and an official photo ID document and checks the date of birth.',
    'safe.li2': '<b>Manual review, no facial recognition.</b> No automated biometric recognition is used, no facial features are computed or stored, and the images are deleted after the review.',
    'safe.li3': '<b>Every photo is approved before anyone sees it.</b> By a person. If we reject one, we tell you why.',
    'safe.li4': '<b>Scam protection in chat.</b> Links and email addresses are removed automatically, and suspicious messages go to moderation. Profile texts containing links, phone numbers or typical scam wording are not published at all.',
    'safe.li5': '<b>Report and block.</b> Blocking takes effect immediately and both ways. When you report someone you get a reference number and see the decision with its reasons in your account.',
    'safe.p2': 'What we do <b>not</b> claim: that every profile is guaranteed genuine or that FLEXR is completely safe. A visual check makes deception harder, it does not rule it out. Before a first meeting, please read our <a href="/sicherheit.html">safety tips</a> (German) – they are short and can save you a lot.',

    'price.h2': 'What FLEXR costs',
    'price.lead': '<b>Using FLEXR costs nothing — permanently, not just during the beta.</b> Signing up, browsing profiles, liking, matching and chatting are and stay free. No payment method is requested.',
    'price.freeEyebrow': 'FLEXR',
    'price.forever': '/ forever',
    'price.free1': 'Browse profiles and match',
    'price.free2': '20 likes per day',
    'price.free3': '3 conversations at once',
    'price.free4': 'Search radius up to 50 km',
    'price.free5': 'No payment method, nothing to cancel',
    'price.premiumEyebrow': 'FLEXR Premium',
    'price.perMonth': '/ month',
    'price.prem1': 'Unlimited likes',
    'price.prem2': 'Unlimited conversations',
    'price.prem3': 'See who liked you',
    'price.prem4': 'Undo your last swipe',
    'price.prem5': 'Full search radius up to 250 km',
    'price.prem6': 'Premium badge on your profile',
    'price.premiumSoon': 'Arrives after the beta phase',
    'price.cta': 'Start for free',
    'price.p1': '<b>A free account never turns into a subscription by itself.</b> No payment method is requested or stored at sign-up. Premium only exists if you explicitly take it out — otherwise there is nothing to cancel and no deadline to miss.',
    'price.p2': 'FLEXR Premium does not exist yet during the beta: until then likes, conversations and radius are unlimited for everyone. We will announce it before Premium starts. The €10 per month is the final price; VAT is not charged on top, and cancelling takes one click, effective at the end of the current month.',

    'faq.h2': 'Frequently asked questions',
    'faq.q1': 'What is FLEXR?',
    'faq.a1': 'A dating app for people who care about training and the gym. You find matches by your gym and your radius — all across Austria.',
    'faq.q2': 'Who is FLEXR for?',
    'faq.a2': 'For everyone 18 and over who takes training seriously and wants to meet someone with a similar lifestyle. The common ground is not a body, it is a daily routine with the gym firmly in it.',
    'faq.q3': 'Is FLEXR only for bodybuilders?',
    'faq.a3': 'No. Strength training, functional fitness, endurance, martial arts, climbing — all of it counts, whatever your level. It is about the lifestyle, not about a particular look.',
    'faq.q4': 'What does FLEXR cost?',
    'faq.a4': '<b>Nothing.</b> Using FLEXR is permanently free — browsing profiles, liking, matching and chatting cost no money, after the beta too. Optionally, <b>FLEXR&nbsp;Premium</b> arrives after the beta at €10 per month: unlimited likes, unlimited conversations, see who liked you, undo your last swipe and the full search radius. Without Premium, 20 likes per day, 3 conversations at once and a 50&nbsp;km radius apply. Nothing becomes chargeable without you actively opting in.',
    'faq.q5': 'Will my account automatically become chargeable?',
    'faq.a5': '<b>No.</b> No payment method is stored at sign-up, so a free account cannot turn into a subscription. There is nothing to cancel and no deadline to watch.',
    'faq.q6': 'How do matches work?',
    'faq.a6': 'You choose a gym and a search radius and see matching profiles from that area. If two people like each other, a match is created and you can message. Before that, nobody can message you.',
    'faq.q7': 'Does my gym have to be listed already?',
    'faq.a7': 'No. If your gym is missing, submit it with its address and use it for your profile right away. Once reviewed it appears in the list for everyone.',
    'faq.q8': 'How does age verification work?',
    'faq.a8': 'You confirm your email address, take a selfie live with the camera and upload an image of an official photo ID — either as a photo you take now or as a file from your device. A person compares profile picture, selfie and ID photo and checks the date of birth — <b>no automated facial recognition</b>. The images are deleted afterwards.',
    'faq.q9': 'Does FLEXR store my location?',
    'faq.a9': 'No. Neither the browser nor the app asks for a device location. The radius search works solely with the public address of the gym you select yourself.',
    'faq.q10': 'Is FLEXR available all across Austria?',
    'faq.a10': 'Yes, every Austrian postal code works. How many profiles you see depends on how many people are on board within your radius — more in urban areas than in the countryside.',
    'faq.q11': 'How do I cancel?',
    'faq.a11': 'In the account area under “Manage / cancel subscription”, at any time and without notice periods. Access stays active until the end of the paid period.',
    'faq.q12': 'How do I report or block someone?',
    'faq.a12': 'Via the flag icon in every profile and chat. Blocking takes effect immediately and both ways. When you report someone you get a reference number and see the outcome under “My reports”. Without an account, use the <a href="/meldung.html">public reporting form</a> (German).',
    'faq.more': 'More answers are in the <a href="/faq.html">detailed FAQ</a> (German).',

    'start.h2': 'Ready?',
    'start.p': 'Create a profile, pick your gym, get going. During the beta FLEXR costs nothing — no payment method, no deadline.',

    'foot.toApp': 'To the app',
    'foot.safetyTitle': 'Safety',
    'foot.safetyTips': 'Safety tips',
    'foot.authorities': 'For authorities',
    'foot.note': 'FLEXR is a brand of Julian Pachernegg, sole trader, 8232 Grafendorf, Austria. Use from age 18. Full provider details in the <a href="/impressum.html">legal notice</a>.',

    'beta.eyebrow': 'Beta phase',
    'beta.title': 'FLEXR is still being built',
    'beta.text': 'You can already use FLEXR in your browser. Because we are still in beta, some regions are thinly populated and individual features are still changing.',
    'beta.free': '<b>Using FLEXR costs nothing — permanently.</b> No trial month, no membership fee, no payment method. After the beta, <b class="inline">FLEXR&nbsp;Premium</b> arrives at €10 a month: optional, cancellable any month, and only for those who want more than the 20 likes and 3 conversations a day that will then apply to standard accounts. During the beta even that is unlimited.',
    'beta.android': 'Release planned for end of September 2026',
    'beta.ios': 'to follow',
    'beta.outro': 'With the launch of the Android app, FLEXR really gets going.',
    'beta.ok': 'Got it',
    'beta.closeAria': 'Close notice'
  }
  });

  /* Titel und Social-Angaben mitschalten. Die kanonische URL und die
     JSON-LD-Auszeichnung bleiben unberuehrt - sie beschreiben die deutsche
     Fassung dieser Adresse. */
  function applyMeta(){
    document.title = FlexrI18n.t('meta.title');
    const set = (sel, value) => {
      const el = document.querySelector(sel);
      if(el) el.setAttribute('content', value);
    };
    set('meta[name="description"]', FlexrI18n.t('meta.description'));
    set('meta[property="og:title"]', FlexrI18n.t('meta.ogTitle'));
    set('meta[property="og:description"]', FlexrI18n.t('meta.ogDescription'));
    set('meta[property="og:locale"]', FlexrI18n.t('meta.ogLocale'));
    set('meta[name="twitter:title"]', FlexrI18n.t('meta.ogTitle'));
    set('meta[name="twitter:description"]', FlexrI18n.t('meta.ogDescription'));
  }
  FlexrI18n.onChange(applyMeta);
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', applyMeta);
  }else{
    applyMeta();
  }
})();
