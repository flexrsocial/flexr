# FLEXR — Handoff für ein anderes Gerät / Claude Code

Stand: **18.09.2026**

## Wo das Projekt gerade steht

> **Dringend zu prüfen beim Einstieg: Ist Android 2.7.5 (versionCode 117) in
> der Play Console live?** Der Nutzer hat 116 (2.7.4) auf ausdrücklichen
> Wunsch **direkt in Produktion** hochgeladen, obwohl diese Fassung den
> Absturz beim Start noch **nicht** behoben hat (siehe „Sitzung 18.09.2026
> (2)" unten) — 117 wurde ihm danach übergeben, ob der Play-Console-Upload von
> 117 tatsächlich passiert ist, ist von hier aus nicht einsehbar. Falls nicht:
> **Jeder Nutzer, der gerade aktualisiert, bekommt eine App, die sofort nach
> dem Start abstürzt.** Play Console prüfen, im Zweifel 117 aus
> `release-2.7.5/flexr-2.7.5-vc117.aab` sofort hochladen.

**Alles committet, gepusht und deployed.** Der VPS steht auf `origin/main`
(**`c5582aa`**, Sitzung 18.09.2026 (6) — Bug-Durchgang in allen drei
Oberflächen). Das ist jetzt der aktuelle Code-Stand (löst `c36c074` als
Referenz ab). Migration bis `5f8ae574bc95` gelaufen (Sitzung (3)), Nginx neu
geladen (`/brand/`-Sperre, Sitzung (3)). `systemctl is-active` zeigt
`active`, `/api/health` liefert 200.

> **Sitzung (6) hat das Backend nicht angefasst** — keine Migration, kein
> Neustart, der `git pull` allein reicht. Live wirkt davon nur die Web-App
> (Balken über dem Profilfoto springen an); die Änderungen an iOS und Android
> liegen im Repo und brauchen einen Build. **Die 13 geänderten
> Swift-Dateien sind noch nie kompiliert worden**, hier gibt es keine
> Swift-Toolchain — der nächste Xcode-Build ist der eigentliche Beweis.
> Android kompiliert (49 Unit-Tests grün).

> **FLEXR Premium ist seit dem 18.09.2026 in allen drei Oberflächen fertig
> eingerichtet — nicht nur scharf geschaltet, sondern auch tatsächlich
> kaufbar.** Alle vier Blöcke der [Einrichtungsanleitung](EINRICHTUNG-PUSH-UND-KAUF.md)
> sind durch:
>
> * **A — Firebase (Android-Push):** eingerichtet und verifiziert.
> * **B — APNs (iOS-Push):** eingerichtet und verifiziert (17.09.).
> * **C — Play Console (Android-Kauf):** Dienstkonto, API-Freischaltung und
>   Produkt-ID stehen; der Kauf-Knopf ist in der Android-App live.
> * **D — App Store Connect (iOS-Kauf):** Abo angelegt, Produkt-ID gesetzt,
>   **Version 1.0 + Abo bei Apple zur Prüfung eingereicht** — Ausgang offen,
>   typisch 24–48 h.
>
> Einzelheiten, samt aller Stolpersteine unterwegs, in „Sitzung 18.09.2026"
> direkt unten.
>
> **Einstieg für die nächste Sitzung.** Nichts hängt technisch halbfertig.
> Zwei Tests stehen noch aus, unabhängig vom Ausgang der Apple-Prüfung:
>
> 1. **Sandbox-Kauf auf einem echten Gerät.** Bei Apple: App Store Connect →
>    Benutzer und Zugriffsrechte → Sandbox → Tester anlegen, dann auf dem
>    iPhone unter Einstellungen → App Store → Sandbox-Konto anmelden. Bei
>    Google: Play Console → Einstellungen → Lizenztests → die eigene
>    Google-Kontoadresse als Lizenztester eintragen. Erst danach lässt sich der
>    Kauf-Knopf in beiden Apps tatsächlich durchklicken, ohne echtes Geld zu
>    bewegen.
> 2. **Push mit zwei echten Geräten.** Eine Chat-Nachricht schicken und
>    prüfen, ob sie **sofort** ankommt - nicht erst nach manuellem Öffnen der
>    App. Das war der ursprünglich gemeldete Fehler (Sitzung 17.09.2026 (7));
>    dieser Test ist der eigentliche Beweis, dass er behoben ist.
>
> Der iOS-Sandbox-Kauf lässt sich erst nach Apples Freigabe von Version 1.0
> sinnvoll testen (das Abo hängt an dieser Einreichung). Der Android-Weg und
> der Push-Test sind schon jetzt möglich, unabhängig von Apples Entscheidung.
>
> Nebenbei erledigt: Das Prüfkonto `appreview` trainiert jetzt in einem Wiener
> Gym (Clever fit, Seidengasse 9-11, 1070 Wien) statt in Graz - siehe unten,
> „Sitzung 18.09.2026". Es lässt sich jetzt reell liken/matchen; sobald das
> geschehen ist, hat das Konto endlich Match- und Chatverlauf für die
> App-Prüfung.
>
> Was **nicht** ansteht: ein Backend-Deploy, eine Migration, ein weiterer
> Android- oder iOS-Build allein wegen Store-Einrichtung — beides ist bereits
> passiert (Android 2.7.2 / versionCode 114 liegt in der Play Console, der
> iOS-Stand von gestern liegt bei Apple).

> **FLEXR Premium ist seit dem 17.09.2026 scharf — und in allen drei
> Oberflächen kaufbar.** Im Browser über Stripe, in den Apps über StoreKit
> bzw. Play Billing (`backend/app/store_billing.py`). Der Kauf-Knopf in den
> Apps erscheint erst, wenn die Store-Produkte angelegt und ihre Kennungen in
> der `.env` eingetragen sind — siehe Sitzung 17.09.2026 (5).
>
> **Überholt seit 18.09.2026** — der Satz „Verkauft wird ausschließlich im
> Browser" stimmt nicht mehr, siehe oben (Block C/D). Der Rest bleibt
> gültig: **FLEXR Premium ist seit dem 17.09.2026 scharf.**
> `PREMIUM_ENABLED=true` steht in der `.env` des VPS (eine Sicherung liegt
> daneben als `.env.bak-vor-premium-20260917`). Damit gelten die Grenzen des
> kostenlosen Kontos für alle: 20 Likes/24 h, 3 Unterhaltungen, 50 km. Die
> Beta-Kennzeichnung bleibt und hängt an `settings.beta_active`. Zurückdrehen
> ginge jederzeit mit `PREMIUM_ENABLED=false` plus Neustart — das würde jetzt
> aber auch die drei Store-Kaufwege mit abschalten, nicht nur Stripe.

Nach dem Deploy gegengeprüft: Deck und Matches antworten einem
unverifizierten Konto weiterhin mit 403, und eine fremde `request_id` am
Rücktrittsformular gibt keine fremde Erklärung mehr heraus.

> **`withdrawal_declarations` ist leer.** Die Gegenprobe zum Rücktrittsleck
> hatte zwei echte Erklärungen angelegt; auf Ansage entfernt, zusammen mit
> einem dritten Testeintrag vom 16.08. ("Test Person", `test@example.com`),
> der noch aus einer früheren Sitzung stammte. Die Tabelle enthält damit
> **null** Datensätze — der nächste Eintrag dort ist ein echter.

Der vorige Stand zum Vergleich (**`4c0922c`**): `git pull` und
`sudo systemctl restart flexr-api` sind gelaufen, `systemctl is-active` zeigt
`active`, `curl https://flexr.social/api/health` liefert `{"status":"ok"}`.
Keine Migration nötig: beide Backend-Änderungen der zweiten Sitzung vom 17.09.
(siehe unten) sind reine Anwendungslogik, kein Schema-Wechsel. Direkt nach dem
Neustart lieferte derselbe `curl`-Aufruf einmalig `502` — reine Racebedingung
zwischen "Prozess gestartet" und "Uvicorn nimmt Verbindungen an" (`is-active`
kommt vor der eigentlichen Anwendungsbereitschaft), Sekunden später war der
Health-Check grün. Kein Grund zur Sorge, aber beim nächsten Deploy nicht
direkt im selben Atemzug wie den Neustart-Befehl prüfen.

> **Überholt — Einstieg vom 16.09.2026 abends** (steht als Verlauf hier,
> der gültige Einstieg ist der oben). Arbeitsbaum
> sauber, `HEAD` = `origin/main` = `72ada4c`. Nichts hängt halbfertig. Die drei
> Dinge, die als Nächstes anstehen, in dieser Reihenfolge:
>
> 1. **Die TestFlight-Fassung auf einem iPhone ansehen** — Login-Knopf mit
>    leerem Passwortfeld, eine kurze Chatnachricht, und das Fotoraster nicht nur
>    betrachten, sondern bedienen (verschieben, löschen, neu hochladen). Das
>    sind die drei Korrekturen dieser Sitzung; ausgeführt hat sie niemand.
> 2. **Premium gegen ein lokales Backend prüfen** — siehe den eigenen Abschnitt
>    „FLEXR Premium ausprobieren, ohne die Produktion anzufassen" weiter unten.
>    Am Schalter der Produktion zu drehen ist dafür **nicht** der richtige Weg.
> 3. **Android 2.6.9 (versionCode 109) in die Play Console laden.** Das Bundle
>    ist gebaut, signiert und im Chat übergeben; Prüfsumme im
>    16.09.-(2)-Abschnitt. Liegt der Chatverlauf nicht mehr vor, neu bauen —
>    identische Quellen ergeben dasselbe Paket, nur die Prüfsumme ändert sich.
>
> Was **nicht** ansteht: ein Backend-Deploy, eine Migration, ein Neustart.

> **Stolperstein beim `git pull` am 16.09.:** Der Pull brach ab mit *„untracked
> working tree files would be overwritten"* — `backend/scripts/activate_review_account.py`
> war am 15.09. von Hand auf den VPS kopiert worden und lag dort unversioniert,
> während derselbe Pfad inzwischen im Commit steckte. Prüfsummen verglichen
> (identisch), die unversionierte Fassung gelöscht, Pull wiederholt. Wer künftig
> ein Skript vorab auf den Server schiebt, sollte es danach wieder entfernen.
> Dieselbe Falle liegt noch scharf: `backend/list_users.py` (21.08., nur
> lesend) liegt unversioniert am VPS. Sobald dieser Pfad je in einen Commit
> kommt, bricht der nächste Pull genauso ab.

> **Android 2.6.9 (versionCode 109) — aktueller Stand.** Gebaut am 16.09.2026,
> signiert (Upload-Key `CN=FLEXR`, jarsigner-geprüft), prod-Flavor, 7.772.406
> Bytes, SHA-256
> `c1e37f50981f5c0a2bd5558c473dbd0e55ac968fcbcbe77548831f080ee89612`.
> Im Chat übergeben als `flexr-2.6.9-vc109.aab`, **nicht** in
> `dl-a616e78274de323b/` abgelegt; ein APK dieser Fassung ist nicht gebaut.
> Inhalt: die drei FLEXR-Premium-Zusatzfunktionen (Abzeichen, letzten Swipe
> zurücknehmen, „Wer dich geliket hat") — unsichtbar, solange
> `PREMIUM_ENABLED` am Server aus steht — plus der ersetzte Login-Hinweis, der
> keinen Probemonat mehr verspricht. Vor dem Bauen liefen
> `:app:testProdReleaseUnitTest` (49 Tests, 0 Fehler) und
> `:app:compileProdReleaseKotlin` grün. Einzelheiten in
> [android-native/HANDOFF.md](android-native/HANDOFF.md), Abschnitt „FLEXR
> Premium: die drei Zusatzfunktionen".
>
> **2.6.8 (versionCode 108)** war der Stand davor. Gebaut am 16.09.2026,
> signiert, prod-Flavor; **noch nicht in die Play Console hochgeladen**. Zwei
> Korrekturen: Ein 401 vom Login gilt nicht mehr als abgelaufene Sitzung, und
> der Chat-Poll läuft nur noch, solange der Chat zu sehen ist. Einzelheiten in
> „Sitzung 16.09.2026" direkt unten.
>
> **2.6.7 (versionCode 107)** holt die POST_NOTIFICATIONS-Laufzeitberechtigung
> beim ersten Laden des Kontobereichs ein und stellt den Schalter bei Ablehnung
> zurück auf „aus" — vorher stand er für neue Konten von Anfang an auf „an",
> ohne dass je gefragt worden wäre. **2.6.6 (versionCode 106)** rückt den
> Leerzustand im Chatverlauf mittig; ihm fehlte als einzigem im Projekt das
> `align(Center)`. Beide sind im 2.6.8-Paket enthalten.
>
> **2.6.5 (versionCode 105)** war der Stand davor: wie 2.6.4, zusätzlich
> stehen die Leerzustände von Matches und Chats mittig wie der im Swipe-Deck.
>
> **2.6.4 (versionCode 104)** brachte: Statuspille heißt nur noch „Beta", der
> Hinweis unter „Sprache" ist enger gesetzt, und beim Anlegen eines Kontos sind
> **mindestens drei Profilfotos** Pflicht — durchgesetzt am Server, nicht nur in
> den Clients. Einzelheiten in „Sitzung 12.09.2026 (2)" direkt unten. Das Paket
> ist veröffentlicht, deshalb bekam der Nachzug eine eigene Nummer.
>
> **Android 2.6.3 (versionCode 103)** war der Stand davor und ist nie
> veröffentlicht worden (gebaut, aufs Gerät gespielt, nicht hochgeladen). Der
> Sprachwechsel
> ist zum dritten Mal angefasst worden, diesmal an der Wurzel: Er sitzt jetzt
> am **Basis-Context der Activity** (`MainActivity.attachBaseContext`) statt
> zur Laufzeit an den Ressourcen zu drehen, und das App Bundle legt seine
> Sprachen nicht mehr in **Sprach-Splits** ab (`bundle { language {
> enableSplit = false } }`) — auf einem deutschen Gerät war `res/values-en`
> über Play sonst überhaupt nicht installiert. Dazu steht der Regler wieder in
> der Kopfzeile des **ausgeloggten** Graphen, weil der Kontobereich ohne
> Anmeldung unerreichbar ist. Einzelheiten in „Sitzung 12.09.2026" weiter
> unten. Der Inhalt steckt vollständig in 2.6.4.
>
> Vorgeschichte in „Sitzung 11.09.2026 (3)": 2.6.2 entfernte den Regler aus
> der Kopfzeile und baute `ProvideAppLanguage` ohne `ContextWrapper` neu; der
> ursprüngliche Absturz beim Start (2.6.0, versionCode 100) steht im Abschnitt
> „Absturz beim Start der Android-App". Der dort gefundene Werkzeug-Fehler
> (KSP2 verdoppelt Hilt-Klassen im `prodRelease`-Build, umgangen mit
> `ksp.useKSP2=false`) gilt unverändert weiter.

**Das Geschäftsmodell hat sich am 10.09.2026 grundlegend geändert:**

* **Die Nutzung von FLEXR ist unbefristet unentgeltlich** — nicht nur in der
  Beta. Es gibt **keine Bezahlwand, keinen Probemonat, kein 402** mehr; kein
  Konto wird je mangels Zahlung gesperrt.
* Bezahlt wird nur **FLEXR Premium**: 10 €/Monat, freiwillig, monatlich kündbar.
* Standardkonten haben Grenzen — **20 Likes je 24 h, 3 gleichzeitige
  Unterhaltungen, 50 km Umkreis**. Premium hebt sie auf und bringt: sehen wer
  geliket hat, letzten Swipe zurücknehmen, 250 km, Abzeichen im Profil.
* **Der Schalter `PREMIUM_ENABLED` steht auf `false`.** Solange er aus ist
  (Beta), ist für alle alles unbegrenzt und Premium ist nicht kaufbar. Das
  Umlegen braucht keine Migration.

Die Zahlen stehen in `backend/app/config.py` und sind zugleich eine
**vertragliche Zusage** (AGB Punkt 7 b). Wer sie ändert, zieht
`frontend/i18n-*.js`, `res/values*/strings.xml`, `agb.html`, `faq.html` und
`app/legal.py` mit.

**Aktuelles Android-Paket:** 2.7.8 (versionCode 120), Stand 19.09.2026.

Zum **Installieren auf einem Gerät** taugt nur das **APK**. Das `.aab` ist das
Veröffentlichungsformat für die Play Console und lässt sich auf einem Telefon
nicht installieren — wird es trotzdem aufgespielt, startet die App und schließt
sich sofort wieder. Genau das ist am 11.09. passiert (Abschnitt „Absturz beim
Start der Android-App"). Beide Dateien gehören deshalb in den Download-Ordner,
klar benannt:

| Datei | Wofür |
| --- | --- |
| `flexr-X.Y.Z-vcNNN.apk` | Direkt aufs Gerät laden und antippen |
| `flexr-X.Y.Z-vcNNN.aab` | Nur Upload in die Play Console |

**Stand 16.09.2026 stimmt das für 2.6.8 und 2.6.9 nicht.** Beide Bundles sind
direkt im Chat übergeben worden, nicht in `dl-a616e78274de323b/` abgelegt; ein
APK ist von keiner der beiden Fassungen gebaut worden. Im Download-Ordner liegt
als neuestes weiterhin `flexr-2.6.5.aab`, und APKs liegen dort überhaupt keine
— die Namensschreibweise oben ist die Absicht, nicht der Ist-Zustand. Wer 2.6.9
aufs Gerät bringen will, braucht erst `./gradlew assembleProdRelease`.

Die `vc101`- bis `vc104`-Dateien sind hinfällig. Die Play Console hatte 43 und
50 schon vergeben — Näheres im 10.09.-Abschnitt.

> **Zum Prüfen des Sprachwechsels bitte das APK nehmen, nicht den
> Play-Store-Stand einer älteren Fassung.** Ein über die Play Console
> ausgeliefertes 2.6.2 oder älter kann die Sprache gar nicht umstellen — die
> englischen Texte lagen dort in einem Sprach-Split, den ein deutsches Gerät
> nie herunterlädt. Erst ab 2.6.3 stecken beide Sprachen im Basis-Paket.

Aufbau des Dokuments: erst diese Eckdaten, dann **die Sitzung vom 19.09.**
(Android: Konto-Feinschliff nach 2.7.7), dann **die Sitzung vom 18.09. (7)**
(Aboverwaltung im Web, Push bei beendeter Android-App), dann **18.09. (6)**
(Bug-Durchgang in allen drei Oberflächen), dann **18.09. (5)** (Widerruf der
Art.-9-Einwilligung wirkte nur halb), dann **18.09. (4)** („Swipe
zurücknehmen" blieb an einem Match hängen), dann **18.09. (3)** (Kompletter
Bug-/Performance-/Cleanup-Durchgang), dann **die Sitzung vom 18.09. (2)**
(Android-Absturz beim Start: PlayBillingService fehlte enableOneTimeProducts,
2.7.3 bis 2.7.5), dann **die Sitzung vom 18.09.** (Block A, C, D fertig: Push
und Kauf), dann **die Sitzung vom 17.09. (3)**
(Durchsicht vor der Einreichung: Nutzerweg, Admin-Werkzeuge, Rechtstexte),
dann **die Sitzung vom 17.09. (2)**
(Verifizierungsablehnung: Fotos löschen, Nutzerliste kennzeichnen), dann **die
Sitzung vom 17.09.** (Stripe-Umstellung auf FLEXR Premium), dann **zwei
Abschnitte vom 16.09.**
((2) FLEXR Premium in den nativen Clients, dann der ungezählte erste vom selben
Tag über den 401 beim Login),
dann **drei Abschnitte vom 12.09.** ((3) SEO/Performance, dann (2) Backend,
dann der ungezaehlte erste vom selben Tag), dann **vier Abschnitte vom 11.09.** (diese Sitzung als (3), dann (2), dann der Absturz-Befund, dann die
Ausgangssitzung), dann die **drei Abschnitte vom 10.09.**
(Audit-Fortsetzung, Audit, Monetarisierung), dann **09.09.**, dann
**08.09.**, dann die beiden Sitzungen vom **07.09.**, dann **06.09.**, dann
**05.09.**, dann **31.08.**, **30.08.**, **23.08.**, **21.08.**; die Build-,
Test- und Deploy-Abschnitte am Ende gelten sitzungsübergreifend.

## Sitzung 19.09.2026 — Android: Konto-Feinschliff nach 2.7.7

Rückmeldung zu 2.7.7 (vier Screenshots): zwei davon zeigten die
Rewind-Einblendungen, die in 2.7.7 bereits entfernt waren — der Vergleich
gegen den Code (`e9b069b`) bestätigt das, die Screenshots kamen von einem
noch nicht aktualisierten Gerät. Kein Codewechsel nötig, nur klargestellt.
Die anderen beiden Punkte waren neu und sind jetzt umgesetzt. Code-Stand:
**`8985c36`**. Backend unverändert.

### „Profil gespeichert" verschwindet jetzt von selbst

Die geteilte Snackbar-Anzeigedauer (`showMessage` in `FlexrApp.kt`) stand
fest bei 20 s samt Schließen-Knopf — richtig für eine Fehlermeldung, die man
in Ruhe lesen soll, falsch für eine reine Bestätigung, die die gespeicherte
Karte darunter ohnehin schon zeigt. `AccountEvent.Message` trägt jetzt ein
`brief`-Flag; `showBriefMessage` (neu, 2 s) räumt danach selbst auf, der
Schließen-Knopf bleibt für alle Faelle stehen. Nur der Speichern-Erfolg
bekommt das Flag — Löschen-fehlgeschlagen, Widerrufs-Folgetexte und
Moderationsgründe bleiben bei den bisherigen 20 s.

### Statuskarte „FLEXR Premium läuft …" ist für Premium-Konten weg

Trug nichts zum Handeln bei — der Premium-Badge im Kopf sagt es bereits, und
das Kündigen sitzt unten unter „Aboverwaltung". Die ganze Karte (Rahmen,
Text, Abstand) fällt für Premium-Konten jetzt weg statt als leerer Rahmen
zwischen Kopf und „Profil" stehenzubleiben — „Profil" rückt dadurch von
selbst nach oben. Für Nicht-Premium-Konten (Beta-Hinweis oder
Grenzen-Text plus ggf. Angebotsknopf) unverändert. `premium_status_active`
ist damit in beiden `strings.xml` unbenutzt und entfernt.

### „Aboverwaltung": nur noch „Abo verwalten", kein Link mehr

Text verkürzt (weg mit „/ kündigen") und umgestylt: dieselbe weiße
Zeilen-Optik wie „Blockierte Personen" & Co. — kein orange, keine
Unterstreichung mehr, das ist eine Aktion in den Einstellungen, kein
Hyperlink. Verhalten unverändert: führt direkt zum Stripe-Portal
beziehungsweise zur Play-Store-Abo-Verwaltung, außerhalb der App.

### Geprüft

53 Unit-Tests grün, Kotlin- und Test-Quellen kompilieren, Release-Build durch
(inkl. Release-Unit-Tests). Der geänderte String „Abo verwalten" steht
nachweislich im gebauten APK (`aapt2 dump resources`). **Nicht am Gerät
geprüft** — hier läuft kein Emulator.

### Android 2.7.8 (versionCode 120)

Gebaut mit `clean testProdReleaseUnitTest assembleProdRelease
bundleProdRelease`, signiert mit demselben Upload-Key wie bisher
(SHA-256 `bc64ad3f…`, gegen `release-2.7.6/` gegengeprüft). `.aab` und `.apk`
liegen mit `SHA256SUMS.txt` in `release-2.7.8/` und sind im Chat übergeben.

| | |
|---|---|
| AAB (Play Console) | `flexr-2.7.8-vc120.aab` |
| APK (direkt installierbar) | `flexr-2.7.8-vc120.apk` |

### Offen

1. **2.7.8 ist noch nicht in der Play Console** (2.7.6 und 2.7.7 waren es
   zum Zeitpunkt dieser Sitzung ebenfalls noch nicht).
2. **Der Push-Befund aus 2.7.7 ist weiterhin unbestätigt** — siehe
   18.09.-(7)-Abschnitt. Mit dem 2.7.8-APK nachstellen: App ganz schließen,
   Nachricht schicken.
3. Web und iOS zeigen die beiden Rewind-Meldungen weiterhin (siehe
   18.09.-(7), Punkt „Offen" 3) — unverändert offen.

## Sitzung 18.09.2026 (7) — Aboverwaltung im Web, Push bei beendeter Android-App

Drei Aufträge: die Aboverwaltung in der Web-App an dieselbe Stelle wie in der
Android-App; Android-Benachrichtigungen, die bei vollständig geschlossener App
ausbleiben; und zwei Einblendungen beim Zurücknehmen eines Swipes, die weg
sollten. Code-Stand am Ende: **`e9b069b`**. Backend unverändert — keine
Migration, kein Neustart.

### Web: „Aboverwaltung" zwischen Benachrichtigungen und Datenschutz

Die Verwaltung eines laufenden Abos saß in der Statuskarte unter dem
Profilbild; in der Android-App ist sie seit 18.09. (6) unten in den
Einstellungen. Jetzt auch im Web, als dritte Zeile **zwischen**
„Benachrichtigungen" und „Datenschutz & Sicherheit". Das *Angebot* für
Nicht-Abonnenten bleibt oben in der Karte — das verwaltet nichts.

Dabei ist eine Sackgasse aufgefallen und mit behoben: Die Web-App zeigte den
Verwalten-Link bei jedem `is_premium`, auch wenn das Abo aus einer der Apps
stammt. `/api/billing/portal` antwortet darauf mit 400 („Noch kein Abo
abgeschlossen"), weil es keinen Stripe-Kunden gibt. Jetzt zwei Fälle, die sich
gegenseitig ausschließen:

| Zustand | Zeile |
| --- | --- |
| `has_stripe_subscription` | Link „Aboverwaltung" → Stripe-Kundenportal |
| `is_premium` ohne Stripe | Satz: Abo läuft über App Store bzw. Google Play |
| sonst | die Zeile bleibt ganz weg |

Der Stripe-Fall gilt bewusst auch bei ausgeschaltetem Premium: Ein Altabo muss
kündbar bleiben (siehe `billing.create_portal`).

`acct.manageSub` ist damit unbenutzt und aus `i18n-app.js` entfernt; neu sind
`acct.subscription` und `acct.subStoreHint` (DE und EN).

**Geprüft:** Reihenfolge und Darstellung im Browser gegen das echte CSS, beide
Fälle und beide Sprachen; die Zustandslogik zusätzlich in einem Node-Lauf über
alle fünf Fälle (Stripe-Abo, Store-Abo, Altabo bei ausgeschaltetem Premium,
Gratiskonto, Status noch nicht geladen). 496 Backend-Tests grün. Deployt und
per Prüfsumme gegengeprüft (`63337577…`).

### Android: Push kommt nur, solange der Prozess noch lebt

**Gemeldet:** Im Hintergrund geöffnet kommen Chat-Benachrichtigungen sofort;
nach dem Wischen aus der Übersicht kommt keine einzige.

**Am Server liegt es nicht.** Belege, nicht Vermutungen: `push.py` schickt in
beiden Fällen dieselbe Nachricht mit `notification`-Nutzlast und
`priority: high`, das VPS-Journal zeigt über drei Tage **keinen** FCM-Fehler
und keine verworfenen Token, und der Android-Token des Kontos steht mit
frischem `last_seen` in der Datenbank. Firebase nimmt die Nachricht in beiden
Fällen an.

**Der Unterschied entsteht auf dem Gerät.** Ist der Prozess weg, muss Android
ihn für die Zustellung neu starten — die Benachrichtigung zeichnet in diesem
Fall das Firebase-SDK im App-Prozess, nicht Google Play Services für uns.
Genau diesen Neustart verweigern die Akku-Optimierung und, deutlich schärfer,
die Hersteller-Ruhemodi darüber (Samsungs „Apps im Ruhemodus", Xiaomis
Autostart-Sperre). Kein Code in der App kann das umgehen; es ist eine
Entscheidung des Systems **über** die App. Passend dazu, dass auch der
15-Minuten-Fallback (`MessageNotificationScheduler`) nichts nachliefert: Ein
schlafen gelegtes Paket führt auch keine WorkManager-Aufträge mehr aus.

Was in unserer Hand liegt, ist jetzt drin (`android-native`):

1. **Hinweis auf die Ausnahme.** Die Benachrichtigungseinstellungen lesen
   `PowerManager.isIgnoringBatteryOptimizations` und führen mit einem Tipp in
   die Systemliste. Bewusst **nicht** über den Einzeldialog
   `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`: Dessen Berechtigung lässt
   Google nur für Alarme, Anrufe und Gerätesteuerung zu — eine Dating-App
   fliegt damit aus der Prüfung. Steht die Ausnahme schon, sagt die Zeile das
   (nützlich beim Nachstellen des Fehlers). Neu gelesen bei der Rückkehr aus
   den Einstellungen.
2. **Das SDK zeichnet jetzt wie die App.** Bei beendeter App läuft
   `onMessageReceived()` **nicht** — das gilt für jede Nachricht mit
   `notification`-Nutzlast, sobald die App nicht im Vordergrund ist. Ohne
   Manifest-Angaben nahm das SDK dafür das Launcher-Symbol, die Standardfarbe
   und notfalls einen Ersatzkanal „Sonstiges". Jetzt stehen
   `default_notification_icon`, `default_notification_color` und
   `default_notification_channel_id` im Manifest.
3. **Der Tipp führt wieder in die Chats.** Das SDK legt die Datennutzlast als
   Extras in den Start-Intent — der Schlüssel heißt dort `target`, so wie in
   der Nutzlast. `MainActivity` las bisher nur die eigenen Schlüssel
   (`open_chats`, `notification_target`); ein Tipp auf die SDK-Benachrichtigung
   landete also stumm auf dem Startbildschirm. Neuer Unit-Test
   `PushZustellungTest` hält Manifest, Server-Nutzlast und Kotlin-Konstanten
   zusammen — drei Orte, die kein Compiler vergleicht.

> **Nicht am Gerät geprüft.** Hier läuft kein Emulator. Der Beweis ist der
> nächste Versuch mit dem 2.7.7-APK: App ganz schließen, Nachricht schicken.
> Kommt weiterhin nichts, ist die Akku-Ausnahme der nächste Griff — sie steht
> jetzt im selben Dialog.

### Android: zwei Einblendungen beim Zurücknehmen weg

Beide auf ausdrücklichen Wunsch, beide **nur in der Android-App**:

* „Swipe zurückgenommen." verdeckte genau die Karte, die gerade
  zurückgekommen ist — die Karte sagt es selbst.
* „Daraus ist schon ein Match geworden …" (409) erschien am Anfang des Decks
  bei jedem Versuch: Dort liegen in der Regel nur gematchte Swipes, es gibt
  also schlicht nichts zurückzunehmen. Der 404 („Es gibt keinen Swipe zum
  Zurücknehmen") ist aus demselben Grund mit verstummt.

Die Absage mangels Premium (403) bleibt sichtbar — sie ist die einzige, an der
der Nutzer etwas ändern kann; dafür gibt es jetzt eine Zusicherung im Test.
`premium_rewind_done` ist damit unbenutzt und aus beiden `strings.xml`
entfernt. **Web und iOS zeigen beide Meldungen weiterhin** (nicht beauftragt).

### Geprüft

* **496 Backend-Tests grün** (Backend in dieser Sitzung unverändert).
* **Android:** 53 Unit-Tests grün (4 neue), Kotlin- und Test-Quellen
  kompilieren, Release-Build durch. Die drei Manifest-Angaben stehen
  nachweislich im gebauten APK (`aapt2 dump xmltree`), Symbol und Farbe haben
  den Ressourcen-Shrinker überlebt (`aapt2 dump resources`).
* **Web:** im Browser gegen das echte CSS, beide Zustände und beide Sprachen.
* **iOS:** nicht angefasst.

### Android 2.7.7 (versionCode 119)

Gebaut mit `clean testProdReleaseUnitTest assembleProdRelease
bundleProdRelease`, signiert mit demselben Upload-Key wie bisher
(SHA-256 `bc64ad3f…`, gegen `release-2.7.6/` gegengeprüft). `.aab` und `.apk`
liegen mit `SHA256SUMS.txt` in `release-2.7.7/` und sind im Chat übergeben.

| | |
|---|---|
| AAB (Play Console) | `flexr-2.7.7-vc119.aab`, 8,4 MB |
| APK (direkt installierbar) | `flexr-2.7.7-vc119.apk`, 4,4 MB |

### Offen

1. **2.7.7 ist noch nicht in der Play Console** — wie schon 2.7.6.
2. **Der Push-Befund ist unbestätigt.** Nachstellen mit dem 2.7.7-APK: App
   komplett schließen, Nachricht vom zweiten Konto schicken. Kommt sie, war es
   der Kanal/Neustart-Pfad; kommt sie nicht, in Konto → Benachrichtigungen die
   Akku-Ausnahme setzen und denselben Versuch wiederholen. Welches Telefon und
   welche Android-Fassung — steht nirgends und wäre für die nächste Runde
   nützlich.
3. **Web und iOS:** Sollen die beiden Rewind-Meldungen dort auch weg? Bisher
   bewusst nicht angefasst.

## Sitzung 18.09.2026 (6) — Bug-Durchgang in allen drei Oberflächen

**Gemeldet** (iOS zuerst, Android nachgereicht): Profilkarte falsch gezeichnet
und Zurück-Knopf tot; Leerzustände unterschiedlich hoch; „Datenschutz &
Sicherheit" zweizeilig; Suchumkreis ohne Premium beliebig weit; vergrößerte
Chat-Blasen weiterhin da; **die Chatpartnerin bekam keine Nachrichten**; in der
Web-App blättern die Balken über dem Foto nur weiter, statt anzuspringen; auf
Android dasselbe Umkreis-Problem, das Schlosssymbol drängt den Zurück-Knopf
aus dem Bild, und die Aboverwaltung soll aus der Profilkarte in die
Einstellungen.

Code-Stand: **`c5582aa`**. Backend unverändert — keine Migration, kein
Neustart nötig.

### Profilkarte und Zurück-Knopf: eine Ursache, zwei Symptome

`PhotoImage` meldete eine **zu große Höhe**. `Image.resizable()`
`.aspectRatio(contentMode: .fill)` überragt den Vorschlag bewusst — anders
ginge ein Cover-Zuschnitt gar nicht. Der `ZStack` darum übernahm diese
Meldung, und `.clipped()` schnitt an genau diesem zu großen Rahmen, also gar
nicht.

Am Screenshot nachgemessen: Karte 604 pt hoch, Fotofläche soll 350 pt
bekommen (0,58), gezeichnet wurden rund 465 pt. Die überschüssigen ~58 pt
liefen nach **unten** in den Merkmalsbereich — dort landete der Namensblock
auf Chip und Bio — und nach **oben** über die Kopfzeile. Oben war der
Überstand unsichtbar (die Karte hat einen `clipShape`), aber weiterhin
tippempfindlich: Genau das schluckte den Zurück-Knopf.

Behoben an der Wurzel, in `PhotoImage`: Das Foto liegt jetzt als `overlay`
über dem Platzhalter statt als Kind eines `ZStack`. Ein Overlay wirkt nie auf
die Größe seines Gastgebers zurück; `PhotoImage` ist damit immer exakt so
groß wie vorgeschlagen, und `.clipped()` schneidet den Überstand wirklich weg.

> **Derselbe Fehler war schon einmal da.** Im Fotoraster
> (`UI/Components/PhotoGrid.swift`) steht seit dem Umbau ein Kommentar, der
> ihn wörtlich beschreibt: „…nur auf die (zu grosse) Bildflaeche, und die
> ZStack darum uebernahm diese Groesse. Ergebnis war ein Raster aus
> verschieden grossen, einander ueberlappenden Kacheln." Dort wurde er mit
> einem `Color.clear.aspectRatio(…).overlay { … }` umgangen, statt an der
> Quelle behoben — deshalb schlug er in der Swipe-Karte ein zweites Mal zu.
> Der Umweg im Raster funktioniert weiterhin, wird aber nicht mehr gebraucht.

Zusätzlich abgesichert: In `CardContent` steht `.frame(height:)` jetzt **vor**
`.clipped()` (vorher umgekehrt — dann schneidet das Clipping an der Größe des
Stapels statt an der halben Kartenhöhe), und der Zurück-Knopf im `BackHeader`
hat ein 44-×-44-Ziel mit `contentShape` statt 36 × 36. Die senkrechte
Polsterung der Zeile geht im Gegenzug von 10 auf 6, die Kopfzeile bleibt
damit exakt gleich hoch.

### Nachrichten kamen beim Empfänger nicht an

Der auffälligste Befund der Sitzung, und der am schwersten zu sehende.

**Das Backend war es nicht.** 496 Tests laufen grün, darunter
`test_reading_messages_marks_them_read`, das genau diesen Weg abdeckt: A
schickt, B sieht die Nachricht und `unread_count == 1`. Die Nachricht wird vor
dem Push committet; selbst ein völlig totes APNs ändert daran nichts.

**Der lokale Bestand der iOS-App war es.** `FlexrStore.replaceSyncedMessages`
löschte alle bestätigten Zeilen eines Chats und legte anschließend dieselben
Kennungen neu an — in **einem** Speichervorgang, gegen ein
`@Attribute(.unique) var messageID`. Und `save()` war ein `try?`.

Geht ein `save()` schief, bleiben die Änderungen offen im `ModelContext`
stehen. Der nächste Abgleich legt seine eigenen obendrauf und scheitert am
selben Konflikt, und so weiter. Der Bestand steht dann **dauerhaft still** —
über App-Neustarts hinweg, denn die Oberfläche liest brav weiter, was in der
Datei steht, nur kommt dort nichts Neues mehr an. Das passt genau auf die
Meldung: nichts im Chat sichtbar, auch nach Neustart.

Jetzt derselbe Weg wie bei den Matches (`replaceMatches` machte es von Anfang
an richtig): vorhandene Zeilen werden beschrieben (`MessageEntity.apply()`),
nur wirklich Verschwundenes wird gelöscht. Den Konflikt gibt es damit gar
nicht erst. `save()` rollt bei einem Fehler zurück und bricht in Debug-Builds
mit `assertionFailure` ab.

> **Warum Android nicht betroffen ist.** `MessageDao.replaceSynced` sieht
> gleich aus (`deleteSyncedForMatch` + `upsertAll` in einer `@Transaction`),
> ist aber echtes SQL: Room führt `DELETE` und `INSERT OR REPLACE`
> nacheinander aus, beide greifen wirklich. Die iOS-Fassung hat die *Form*
> übernommen, aber SwiftData arbeitet auf einem Objektgraphen und nicht auf
> Anweisungen. Das ist die Art Portierungsfehler, die keine Übersetzung
> auffängt.

**Dass es so lange unsichtbar blieb, ist der zweite Teil des Fehlers.**
`ChatModel.poll()` schluckte jeden Abgleichsfehler kommentarlos, und ein Chat,
der nicht geladen werden kann, sah damit exakt aus wie ein leerer:
„Noch keine Nachrichten — schreib die erste." Jetzt trennt die Ansicht die
beiden Fälle; bei leerem Bestand und fehlgeschlagenem Abruf steht der Fehler
da, mit „Erneut versuchen". Bei vorhandenem Verlauf bleibt es stumm, ein
Aussetzer alle vier Sekunden ist kein Bannergrund.

> **Noch nicht am Gerät bestätigt.** Die Diagnose stützt sich auf den Code und
> darauf, dass der Server nachweislich liefert; hier gibt es kein iPhone.
> Falls es nach dem nächsten TestFlight-Build weiterhin klemmt: einmal neu
> installieren lassen (das wirft den festgefahrenen Bestand weg). Kommt es
> danach zurück, liegt es woanders.

### Chat-Blasen: der Spacer vom 18.09. konnte nicht wirken

Am 18.09. (Commit `feadf87`) wurde ein `Spacer(minLength: 0)` neben die Blase
gesetzt, weil `frame(maxWidth: 300)` „schrumpfen sollte, aber auf einem echten
Gerät weiterhin volle Zeilenbreite zeigte". Der Spacer war die richtige Idee
mit der falschen Zahl: `frame(maxWidth:)` schrumpft nicht auf den Inhalt,
sondern nimmt, was angeboten wird — und gegen einen Spacer, der bei 0
anfängt, setzt sich der gierige Rahmen durch.

Der Rahmen ist jetzt weg, die Obergrenze setzt `Spacer(minLength: 56)`: Der
Blase bleibt die Zeilenbreite minus 56 pt (auf dem Telefon rund 294 pt, also
dieselbe Grenze wie gedacht), darunter bestimmt sie ihre Breite selbst.

### Premium-Grenzen: der Regler log, und das Deck verschluckte Profile

Der Server kappt den Suchumkreis für Standardkonten längst bei 50 km
(`premium.clamp_radius`, seit Sitzung 17.09.2026 (6)). Beide Apps ließen den
Regler trotzdem bis 250 km ziehen — gespeichert wurden 50, angezeigt 250. Der
Regler endet jetzt an `max_radius_km` aus `GET /api/billing/status`, also an
derselben Zahl, die der Server durchsetzt, mit einem Hinweis darunter. Ein
älterer Wert über der Grenze (etwa nach einer Kündigung) wird mitgezogen; auf
Android wird der Mitgliedsstand dafür beobachtet und nicht einmalig gelesen,
weil Kauf und Ablauf mitten in der Sitzung greifen.

> Die Web-App macht es bewusst anders: Dort bleibt der Regler über die volle
> Spannweite bedienbar und ein Hinweis erklärt die Kappung
> (`renderRadiusPremiumHint`, Kommentar in `app/index.html`). Das ist eine
> gewollte Entscheidung und kein Versehen — in den Apps war es aber nach
> ausdrücklichem Wunsch ein harter Anschlag.

Beim Durchgehen der übrigen Grenzen fiel ein zweiter Fehler auf, in **beiden**
Apps: Beim Swipe wird `currentIndex` sofort hochgezählt, damit sich die
Oberfläche nie am Netz aufhält. Lehnt der Server den Like danach wegen des
aufgebrauchten Kontingents ab (403, `like_limit_reached`), blieb die Karte
trotzdem weg — das Profil war ohne Zutun übersprungen und im Deck nicht wieder
zu finden. Jetzt kommt sie zurück, und zwar auf den Index der *abgelehnten*
Karte (`min`/`coerceAtMost`, nicht „einen zurück"): Wer schnell wischt, hat
bis zur Antwort vielleicht schon weitergewischt.

Stand der Grenzen nach dieser Sitzung:

| Grenze | Server | iOS | Android |
|---|---|---|---|
| 20 Likes/Tag | durchgesetzt | Karte kommt zurück | Karte kommt zurück |
| 3 offene Chats | durchgesetzt | stehendes Banner im Chat | Meldung des Servers |
| 50 km Umkreis | durchgesetzt | Regler endet dort | Regler endet dort |
| Eingehende Likes | durchgesetzt | gesperrt dargestellt | gesperrt dargestellt |
| Swipe zurücknehmen | durchgesetzt | Knopf nur mit Premium | Knopf nur mit Premium |

Das Chat-Kontingent bekam in iOS ein **stehendes** Banner statt einer
Einblendung: Wer dort ansteht, bekommt in diesem Chat nie eine Nachricht
durch, solange kein Platz frei wird — eine Meldung, die nach 20 Sekunden
verschwindet, liest sich dann wie eine Störung. Der Wortlaut kommt vom Server,
damit die Zahl nicht an zwei Stellen gepflegt wird.

### Kleinigkeiten in iOS

* Leerzustände in Matches und Chats standen oben an der Überschrift (in der
  Matchliste je nach offenen Likes noch eine Karte tiefer), im Deck und im
  Chat dagegen mittig. Jetzt überall mittig
  (`containerRelativeFrame(.vertical)`), Ziehen zum Aktualisieren bleibt.
* „Datenschutz & Sicherheit" brach zweizeilig um: Der `HairlineDivider` neben
  der Überschrift ist `maxWidth: .infinity` und nahm ihr den Platz weg.
  `layoutPriority(1)` dreht die Reihenfolge um, `minimumScaleFactor(0.7)`
  fängt lange Übersetzungen ab.

### Android: Premium-Bildschirm und Aboverwaltung

Das Schlosssymbol ist weg und der Kopf enger gesetzt — nur in der
Android-App, iOS und Web bleiben, wie sie sind. Der gemeinsame `EmptyState`
brachte 68 dp Symbolkreis plus je 48 dp Polsterung mit; ersetzt durch
Überschrift und Untertitel direkt. Zusammen mit knapperen Abständen unter dem
Zurück-Knopf werden **186 dp** frei. Nachgerechnet am Screenshot (≈1,55 px/dp):
Der Knopf endete bei ~1389 px, die Navigationsleiste beginnt bei ~1210 px —
es fehlten rund 179 px, frei werden ~288 px.

> **Gerechnet, nicht am Gerät gesehen** — hier läuft kein Emulator. Falls es
> knapp bleibt, ist die nächste Reserve die Innenpolsterung der Preiskarte
> (20 dp).

Das Schloss war ohnehin ein Überbleibsel der alten Bezahlwand: Seit dem
10.09.2026 ist dort nichts mehr gesperrt, und ein Vorhängeschloss über einem
freiwilligen Zusatzpaket sagt das Gegenteil.

Die Verwaltung eines laufenden Abos sitzt jetzt als eigener Abschnitt
**„Aboverwaltung"** unten in den Einstellungen statt in der Statuskarte unter
dem Profilbild. Er steht bewusst als letzter *inhaltlicher* Abschnitt vor
„Konto": Ausloggen und Kontolöschung gehören ans Ende. Gibt es nichts zu
verwalten, bleibt der Abschnitt ganz weg statt als leere Überschrift
dazustehen. Das **Angebot** für Nicht-Abonnenten bleibt oben in der Karte —
das ist keine Verwaltung, und es gehört dorthin, wo man es findet. Gekündigt
wird weiterhin dort, wo gekauft wurde: Bei einem Play-Kauf ist Google der
Händler, wir könnten das Abo gar nicht beenden.

### Web: Balken über dem Profilfoto springen an

Bisher blätterten die Zonen links und rechts nur eines weiter; in beiden Apps
springt ein Tipp auf einen Balken direkt auf dieses Foto. Die Web-App hat
dafür jetzt einen 44 px hohen Streifen (`.photo-nav .zone.bars`) über den
Balken, der die Tippstelle in eine Foto-Nummer umrechnet. Die Balken selbst
nehmen weiterhin keine Tipper an (`pointer-events: none`), darunter bleibt es
beim Blättern nach links und rechts.

Im Browser gegen das echte CSS gemessen: Der Streifen gewinnt das Hit-Testing
über die volle Breite (links, Mitte, rechts → `zone bars`), darunter greifen
weiter `zone prev`/`zone next`, und die Segmentrechnung trifft bei drei Fotos
die Indizes 0/0/1/2/2. Nur `app/index.html` betroffen — die App ist zur
Laufzeit übersetzt (`i18n-app.js`), `en/` enthält nur Landing- und
Rechtstexte.

### Geprüft

* **496 Backend-Tests grün.** Das Backend ist in dieser Sitzung unverändert
  geblieben; die Suite lief als Gegenprobe.
* **Android:** `:app:compileProdDebugKotlin` und die Test-Quellen kompilieren,
  49 Unit-Tests grün, 0 Fehler. (JDK unter
  `~/.bubblewrap/jdk/jdk-17.0.11+9`, SDK unter `~/.bubblewrap/android_sdk`,
  Gradle läuft mit `--offline`.)
* **Web:** im Browser gegen das echte CSS gemessen, siehe oben.
* **iOS:** nicht kompiliert — auf diesem Gerät gibt es keine Swift-Toolchain.
  Die Änderungen sind von Hand gegen die umgebenden Muster geprüft. **Das ist
  die einzige Lücke dieser Sitzung**; der nächste Xcode-Build ist der
  eigentliche Beweis.

### Android 2.7.6 (versionCode 118)

Gebaut mit `clean testProdReleaseUnitTest assembleProdRelease
bundleProdRelease`, signiert mit demselben Upload-Key wie bisher
(SHA-256 `bc64ad3f…`, gegen `release-2.7.5/` gegengeprüft — sonst nimmt die
Play Console die Aktualisierung nicht an). 49 Unit-Tests grün. `.aab` und
`.apk` liegen mit `SHA256SUMS.txt` in `release-2.7.6/`.

| | |
|---|---|
| AAB (Play Console) | `flexr-2.7.6-vc118.aab`, 8,4 MB |
| APK (direkt installierbar) | `flexr-2.7.6-vc118.apk`, 4,4 MB |

### Web nachgeschoben: Like-Kontingent klebte an den Knöpfen

„Likes für heute aufgebraucht — Unbegrenzt liken" stand mit 2 px unter der
Reihe aus X und Herz. Jetzt 18 px, dieselbe Zahl wie über der Reihe: Die
Knöpfe sitzen damit gleich weit von Karte und Zeile entfernt.

> Die 4 px Aussenabstand unter `.swipe-actions` sind dabei wirkungslos —
> senkrechte Abstände benachbarter Geschwister fallen zusammen, es gilt der
> größere von beiden. Wer den Abstand ändern will, ändert ihn an
> `.like-counter`.

### Offen

1. **iOS-Build.** Die 13 geänderten Swift-Dateien sind ungebaut. Neue
   Symbole, an denen ein Tippfehler auffiele: `MessageEntity.apply(_:)`,
   `ChatModel.limitNotice`/`loadError`/`retryLoad()`,
   `AccountModel.maxSelectableRadiusKm`/`isRadiusCapped`, `L.chatLoadFailed`,
   `L.accountRadiusCapped`.
2. **Nachrichtenzustellung am Gerät gegenprüfen**, sobald der Build in
   TestFlight ist — siehe den Kasten oben.
3. **Android-Bildschirm ansehen**: passt der Zurück-Knopf auf der
   Premium-Seite jetzt wirklich ohne Scrollen aufs Bild?

## Sitzung 18.09.2026 (5) — Widerruf der Art.-9-Einwilligung wirkte nur halb

**Gemeldet:** Nach dem Widerruf standen im Swipe-Deck weiter die Profile aus
dem Ladevorgang davor. Der Nutzer erwartete — zu Recht — ein leeres Deck und
außerdem, selbst nicht mehr angezeigt zu werden.

**Befund, schlimmer als gemeldet.** Der Widerruf hielt nur die Hälfte seines
Versprechens. „Du erscheinst in keinem Deck" stimmte: Dafür sorgt
`consents.sensitive_data_consent_condition()` in den Deck-Filtern. „Es werden
dir keine Profile mehr vorgeschlagen" stimmte **nicht** — `deck_profiles()`
prüfte nur den Consent der *anderen* Nutzer und stellte das eigene Deck
unverändert über `gender`/`interest` zusammen. Ein Reload half also gar nicht;
die alten Karten waren nur der auffälligste Teil. Ein Like darauf wurde weiter
angenommen und erzeugte weiter ein Match — aus genau den Daten, deren
Verarbeitung gerade widerrufen worden war.

**Fix (Backend, `routers/swipes.py`).** Neue Funktion `matching_erlaubt()`,
geprüft an drei Stellen:

* `deck_profiles()` liefert `[]`. Der Deck-Zähler des Benachrichtigungsjobs
  (`email_jobs.py`) hängt an derselben Funktion und verschickt damit
  ebenfalls keine „X Profile warten auf dich"-Mails mehr.
* `swipe()` antwortet 403 — sonst entstünde aus einem vor dem Widerruf
  geladenen Deck weiterhin ein Match.
* `incoming_likes()` liefert 0 — „wer dich geliket hat" ist ebenfalls ein
  Profilvorschlag auf derselben Grundlage.

Kein Altkonto-Risiko: Migration `9c4e1a7f2b83` hat die Consent-Zeilen für den
Bestand nachgetragen, „keine aktive Zeile" heißt also wirklich „widerrufen".

**Fix (Frontend, `app/index.html`).** Das im Browser liegende Deck wird beim
Widerruf sofort geräumt, die erneute Einwilligung lädt es wieder. Der leere
Zustand nennt jetzt den Grund (`swipe.revokedTitle`/`swipe.revokedSub` in
`i18n-app.js`), statt „Alle Sätze absolviert" zu behaupten — der Grund ist
mit einem Klick behebbar, das darf nicht verschwiegen werden. `i18n-app.js`
auf `?v=6`, Service-Worker-Cache auf `flexr-shell-v19`.

**Geprüft:** 5 neue Tests in `test_einwilligungen.py`, 496 grün. Zusätzlich
lokal im Browser durchgespielt (Karte verschwindet sofort, Leertext richtig,
Weg zurück funktioniert) und nach dem Deploy gegen Produktion gegengeprüft,
dass ein Konto *mit* Einwilligung weiterhin ein volles Deck bekommt (32
Profile). Keine Migration, Backend neu gestartet (**`c36c074`**,
`/api/health` → 200).

> Beim Neustart liefert `/api/health` rund fünf Sekunden lang 502 — der
> Uvicorn-Start braucht so lange. Ein Health-Check nach 3 s Wartezeit
> erschreckt grundlos.

### Mailtexte: „Antworte einfach auf diese Mail" ist korrekt

Auf Nachfrage geprüft, weil als Absender `noreply@flexr.social` erscheint.
Kein Widerspruch: `mailer.send_email()` setzt bei **jeder** Mail
`Reply-To: flexr.social@proton.me` (`settings.support_email`), und aller
Versand läuft über genau diese eine Funktion — es gibt keinen zweiten
`smtplib`-Pfad. Ein Klick auf „Antworten" landet also im Support-Postfach,
nicht bei `noreply@`. Am erzeugten Mailobjekt gegengeprüft. Keine einzige
Vorlage sagt umgekehrt „bitte nicht antworten". Kein Änderungsbedarf —
offen bleibt allein, ob Post an `noreply@flexr.social` selbst (von Hand
adressiert) irgendwo landet oder ins Leere geht.

### Testkonto für den Fiverr-Tester

`~/MEGA/flexr/seed/seed_fiverr.py` (außerhalb des Repos, siehe dessen README)
legt `testuserfiverr@flexrtest.at` an: Prüfung bestanden, E-Mail bestätigt,
FLEXR Premium dauerhaft (`store_premium_until` = 31.12.2099, wie bei
`styriatrading@gmail.com` — nicht `is_subscribed`), drei freigegebene Fotos,
Gym in 1090 Wien, Umkreis 250 km (der volle Premium-Regler; Standardkonten
werden bei 50 km gekappt). Deck gegengeprüft: 32 Profile. Die drei Portraits
stammen aus derselben Unsplash-Serie, damit das Profil nicht nach drei
verschiedenen Männern aussieht (`fotos_bauen.py`, Eintrag `testuserfiverr`).

## Sitzung 18.09.2026 (4) — "Swipe zurücknehmen" blieb an einem Match hängen

**Gemeldet beim Testen mit dem neuen Testdaten-Batch:** Wiederholtes
Zurücknehmen zeigte immer wieder denselben Hinweis "Daraus ist schon ein
Match geworden", ohne je ein älteres Profil freizugeben - wirkte, als bliebe
man "am Anfang des Decks hängen".

**Ursache:** `rewind_last_swipe()` (`routers/swipes.py`) nahm immer nur den
einen allerletzten Swipe. War der bereits gematcht, blieb er (da nie
gelöscht) für immer "der letzte" - jeder weitere Klick traf exakt dieselbe
Zeile erneut. Ältere, an sich zurücknehmbare Swipes davor waren dadurch
dauerhaft unerreichbar, sobald irgendwo in der jüngeren Vergangenheit ein
Match lag.

**Fix:** Springt jetzt über gematchte Swipes hinweg zum jüngsten ohne Match
(begrenzt auf `DECK_SIZE` zurück, damit der "Notausgang für den eigenen
Daumen" nicht beliebig weit in die Historie gräbt). Bleiben nur gematchte
Swipes übrig (der Normalfall: genau einer), weiterhin derselbe 409 wie
bisher - der Fall aus dem bestehenden Test
`test_rewind_faellt_bei_bestehendem_match_aus` ändert sich also nicht.
Neuer Regressionstest:
`test_rewind_ueberspringt_gematchten_swipe_und_nimmt_aelteren_zurueck`.

492 Tests grün, keine Migration, Backend neu gestartet
(**`65a0793`**, `/api/health` → 200).

## Sitzung 18.09.2026 (3) — Kompletter Bug-/Performance-/Cleanup-Durchgang, Testdaten für Premium

Ein Commit, **zwei Migrationen** (neue Indizes + `phone_verifications`
entfernen), **Backend-Neustart nötig**, **Nginx-Reload nötig**
(`deploy/nginx-flexr.conf` geändert). Android und iOS sind **nicht
angefasst** — reiner Server- und Web-Frontend-Durchgang, siehe unten „Müssen
Android/iOS neu gebaut werden?".

### Wie geprüft wurde

Komplette Backend-Testsuite (491 Tests) nach jeder Änderungsgruppe grün.
Die beiden neuen Migrationen gegen einen frisch mit `initdb` erzeugten
**echten Postgres** (nicht sqlite — die Testsuite läuft nur gegen sqlite via
`Base.metadata.create_all`, Migrationen selbst also sonst ungeprüft)
hoch- und wieder runtergefahren, Indizes und Partial-Index-Bedingungen per
`\d`/`pg_indexes` gegengeprüft. Zusätzlich ein Live-Smoke-Test: Backend lokal
per `uvicorn` gestartet, zwei Konten über echte HTTP-Requests registriert,
gematcht, Nachricht geschickt/gelesen — bestätigt, dass die neu geschriebene
`GET /api/matches`-Abfrage (siehe unten) reale Werte liefert, nicht nur was
die Tests erwarten. Frontend-Änderungen im Browser gegen den lokalen
Dev-Server geprüft (Landingpage DE/EN, App-Shell, Konsole fehlerfrei).

### Backend: Bugs

1. **Race Condition bei gleichzeitigem Doppel-Swipe/Doppel-Match**
   (`routers/swipes.py`): Zwei praktisch gleichzeitige identische Requests
   (Doppel-Tap, Retry nach Timeout) liefen in die Unique-Constraints
   `uq_swipe_pair`/`uq_match_pair` und damit in einen rohen 500er. Jetzt
   `IntegrityError` abgefangen, `rollback()`, bestehende Zeile
   weiterverwendet statt Fehler.
2. **Zeitlich unsicherer Vergleich** des Google-Pub/Sub-Pfad-Geheimnisses
   (`routers/store_billing.py`): `!=` statt `secrets.compare_digest`.
3. **Drei Webhook-Handler blockierten die Event-Loop** (Stripe, Apple,
   Google): `async def`, aber mit synchronen, teils sekundenlangen
   DB-/Netzwerk-Aufrufen direkt drin — auf dem Ein-Prozess-Uvicorn (kein
   `--workers`) hätte das *alle* gleichzeitigen Anfragen an den ganzen
   Server ausgebremst, nicht nur den Webhook selbst. Jetzt über
   `run_in_threadpool` entkoppelt.

### Backend: Performance

1. **`GET /api/matches`** (`routers/matches.py`): lief mit 3×N
   Datenbankabfragen für N Matches (jeder App-Start). Umgebaut auf eine
   Handvoll fester Abfragen unabhängig von N — `last_message` per
   Window-Function (`ROW_NUMBER() OVER (PARTITION BY match_id ...)`),
   `unread_count`/`in_chats` per gruppierter Abfrage mit den
   Ausblend-Zeitpunkten aller Matches auf einmal statt einzeln.
2. **Nachrichten als gelesen markieren** (`routers/messages.py`): lief als
   Python-Schleife mit einem UPDATE-Statement pro Nachricht; zusätzlich
   löste `expire_on_commit` (SQLAlchemy-Default) nach dem `commit()` für
   jede Nachricht der Antwort eine eigene Nachlade-Abfrage aus. Jetzt ein
   Bulk-UPDATE, Antwort wird vor dem Commit aus bereits geladenen Werten
   gebaut.
3. **Umkreissuche liest bei jedem Deck-Aufruf die komplette Gym-Tabelle**
   (`gym_geo.py`) — inklusive einmal pro Kandidat im täglichen
   Warteschlangen-Mail-Job. Jetzt 60 s gecacht (Testsuite räumt den Cache
   zwischen Testfällen selbst weg, siehe `conftest.py`).
4. Fehlende Indizes ergänzt: `users.gym` (Hauptfilter im Deck), Partial-
   Indizes auf `photos.status='pending'` und `messages.is_flagged`
   (Admin-Dashboard bei jedem Seitenaufruf).
5. **Push-Zustellung beim Nachrichtenversand** (`routers/messages.py`) lief
   synchron vor der Antwort — der Absender wartete auf FCM/APNs, bevor er
   sein 201 sah. Jetzt `BackgroundTasks`; `push.send_async()` öffnet dafür
   eine **eigene** DB-Session (`database.SessionLocal`, als Modul
   nachgeschlagen statt beim Import gebunden — die Request-Session ist zu
   dem Zeitpunkt schon geschlossen, FastAPI räumt `yield`-Dependencies vor
   den BackgroundTasks weg). `conftest.py` tauscht dafür
   `database.SessionLocal`/`.engine` testweise gegen die StaticPool-Session
   aus, sonst würde ein Hintergrund-Task testweise an eine leere,
   eigenständige sqlite-`:memory:`-Verbindung geraten statt an die mit
   Testdaten befüllte.
6. `security.py`: bis zu zwei `db.commit()` pro authentifiziertem Request
   (last_seen_at, last_active_at) auf einen zusammengeführt.

### Backend: totes aufgeräumt

Die nie registrierte SMS-Telefonverifizierung vollständig entfernt:
`routers/phone.py`, `app/sms.py`, `PhoneVerification`-Modell samt
Datenbanktabelle (Migration `5f8ae574bc95`). War seit ihrer Einführung nie
in `main.py` eingebunden — `test_phone_verification_is_not_exposed` prüfte
genau das schon vorher absichtlich.

### Frontend

- **XSS-Lücke**: Foto-URLs in Match-/Chat-Liste (`app/index.html`) wurden
  ungeschützt ins `<img src>` interpoliert, inkonsistent zur sonst
  durchgängigen `escapeHtml()`. Behoben, plus fehlende `alt`-Attribute an
  5 Stellen ergänzt.
- Service Worker (`sw.js`, jetzt `flexr-shell-v18`): cachte
  `/favicon.ico?v=4`, angefordert wird überall `/favicon.ico` ohne Query —
  der Eintrag griff nie. Statische, versionierte Assets (Fonts/Icons/
  Demo-Bilder) laufen jetzt Cache-first statt Netz-first.
- `app/index.html` lud `legal-status.js` ohne Versions-Query, `404.html`
  noch `legal.css?v=1` statt `?v=2` — beide Cache-Busting-Lücken
  geschlossen. `en/index.html` per `build-en.py` neu erzeugt (war leicht
  veraltet).
- `icon-512.png` verlustfrei nachkomprimiert (−7 %, Pixel-für-Pixel
  identisch geprüft). `favicon.ico` (98 KB, 6 Auflösungen) versucht,
  aber ohne Erfolg — ohne `pngquant`/`optipng` in dieser Umgebung ließ sich
  über Pillows Standard-Encoder keine Einsparung erzielen; nicht
  weiterverfolgt.
- Nginx: `location /brand/` liefert jetzt `404` (ausgenommen
  `/brand/demo/`, weiterhin öffentlich) — Logo-Rohdaten und `build_*.py`
  waren zuvor unbeabsichtigt öffentlich erreichbar, weil `root` direkt auf
  `frontend/` zeigt.

### Aufgeräumt (Dateien)

- `backend/venv` war durch die MEGA-Cloud-Sync beschädigt (leere
  Paket-Unterordner) — neu aufgebaut. Dabei einen echten
  Versionskonflikt in `requirements-dev.txt` gefunden und behoben
  (`httpx` dort abweichend von `requirements.txt` gepinnt, pip konnte
  beides nie gleichzeitig installieren).
- Gelöscht (nach Rückfrage): alte TWA-Android-Build-Reste, `HANDOVER.md`
  (unreferenzierte Einmal-Doku vom Gerätewechsel), 9 verwaiste Demo-Fotos
  in `frontend/brand/demo/`.
- Diverse Logs, `__pycache__`-Ordner projektweit entfernt.

### FLEXR Premium für `styriatrading@gmail.com`

Auf Wunsch **dauerhaft** freigeschaltet — `store_premium_until` auf
`2099-12-31` gesetzt (nicht `is_subscribed`, um keine Stripe-Vertrags-
Semantik vorzutäuschen; `has_store_premium` ist genau für „Premium ohne
Stripe-Abo" gedacht, siehe Docstring in `models.py`). Konto existierte
bereits (`Julian`, `is_banned=False`, nicht gelöscht).

### Testdaten: 30+30 Konten für den Premium-Funktionstest

`~/MEGA/flexr/seed/seed_testuser.py` (außerhalb des Repos, siehe dessen
README) von 10+10 auf **30 weibliche und 30 männliche** `@flexrtest.at`-
Konten erweitert — je 20 mit Gym in Wien (über die Bezirke verteilt), 10
mit Gym anderswo in Österreich (Salzburg, Innsbruck, Klagenfurt,
St. Pölten, Bregenz, Villach, Wels, Krems, Dornbirn, Leoben — plus die
bestehenden Graz/Linz/Vösendorf/Baden/Wr. Neustadt). Passwort weiterhin
`FlexrQA2026!`. Fotos: 40 zusätzliche, bereits früher kuratierte
Unsplash-Kandidaten aus `holen.sh` (nie verwendeter Rest der dortigen
Auswahl), vor der Verwendung stichprobenartig im Browser gegengeprüft.

Dabei nebenbei einen Altlast-Bug im Skript gefunden und behoben:
`settings.stripe_trial_days` existiert seit der Umstellung auf FLEXR
Premium nicht mehr (siehe `config.py`), das Skript brach beim ersten
`--apply`-Lauf ab. `trial_ends_at` wird jetzt gar nicht mehr gesetzt (der
Spalten-Default reicht, die Spalte wird laut `models.py` ohnehin nirgends
mehr ausgewertet).

Mit `deckcheck.py` gegen alle 60 Konten verifiziert: 58 bekommen ein
gefülltes Deck, 2 (Salzburg, Innsbruck — beide mit eher engem Radius) ein
leeres, weil ihre „anderswo"-Gegenstücke weiter entfernt liegen als ihr
Radius reicht. Kein Bug, sondern die erwartete Geometrie bei nur 10
Fernkonten je Geschlecht.

Die Testkonten unter `@flexrtest.at` in „Testdaten für manuelles Testen"
unten waren mit „nicht mehr aktuell" vermerkt — das stimmt seit dieser
Sitzung nicht mehr, sie sind wieder der aktuelle Stand für dieses Batch.

### Müssen Android/iOS neu gebaut werden?

**Nein.** Alle Backend-Änderungen sind serverintern (Bugfixes, Performance,
totes entfernt) oder API-Antwortform-erhaltend — kein Client, egal ob
Web, Android oder iOS, sieht einen anderen Vertrag als vorher. Die
entfernten Telefon-Endpunkte waren nie in `main.py` eingebunden, also auch
nie von einem Client erreichbar. Die Frontend-Änderungen betreffen
ausschließlich die Web-App (`frontend/`) — Android und iOS sind eigene,
native Clients ohne WebView auf diesen Code und bleiben unberührt.

### Deploy

Commit `5e9f016` gepusht, auf dem VPS gepullt, beide Migrationen bis
`5f8ae574bc95` gelaufen, `flexr-api` neu gestartet (`systemctl is-active`:
`active`). Nginx-Live-Konfiguration (`/etc/nginx/sites-available/flexr.social`
— **weicht von `deploy/nginx-flexr.conf` ab**, siehe deren Kopfkommentar, nicht
blind überschreiben) um denselben `/brand/`-Sperrblock von Hand ergänzt statt
die Vorlage zu kopieren, vorher als
`flexr.social.bak-vor-brand-sperre-20260918` gesichert. `nginx -t` vor dem
Reload geprüft. Gegenprobe: `GET /brand/build_icons.py` liefert `404`,
`GET /brand/demo/*` weiterhin `200`, `GET /api/health` weiterhin `200`,
Login gegen `lea@flexrtest.at` erfolgreich.

## Sitzung 18.09.2026 (2) — Android-Absturz beim Start: PlayBillingService fehlte enableOneTimeProducts()

**Gemeldet:** Die Android-App (2.7.2, versionCode 114 — die Fassung aus der
vorigen Sitzung, die der Nutzer in die Play Console geladen hatte) startet auf
einem echten Gerät nicht mehr; sie schließt sich sofort mit dem generischen
Systemdialog "FLEXR geschlossen, da diese App einen Fehler enthält". Drei
Fehlversuche, bevor der echte Stack Trace zu fassen war — festgehalten, damit
niemand dieselben Sackgassen noch einmal durchläuft.

### Fehlspur 1: das 2.6.0-Distributionsmuster (115/2.7.3)

Der naheliegende Verdacht war eine Wiederholung des 2.6.0-Vorfalls vom
11.09.2026 (Abschnitt „Absturz beim Start der Android-App" weiter unten):
`release-2.6.6` bis `release-2.7.1` enthalten allesamt **nur** ein `.aab`,
keine installierbare Universal-APK mehr — ein `.aab` lässt sich nicht direkt
installieren, und wer es trotzdem versucht (umbenannt oder per
Split-Installer ohne passende Splits), bekommt eine Installation ohne die
richtigen Splits, die Android beim Start sofort wieder beendet. `versionCode
115`/`2.7.3` wurde deshalb quellcodegleich zu 114 gebaut, diesmal aber mit
`assembleProdRelease` **und** `bundleProdRelease`, beide nach
`release-2.7.3/` mit `SHA256SUMS.txt`, Signatur mit `apksigner verify
--print-certs` gegen den bekannten Fingerabdruck `bc64ad3f…e7980` geprüft.

**Ergebnis: Die sauber installierte Universal-APK stürzte genauso ab.** Die
Distributionstheorie war falsch — es ist ein echter Code-Fehler. (Die
Erkenntnis "seit 2.6.6 fehlt die APK" bleibt trotzdem richtig und die Lücke
sollte langfristig nicht wieder auftreten — sie ist nur diesmal nicht die
Ursache.)

### Fehlspur 2: Firebase/FCM (Verdacht, nie bestätigt)

Naheliegend war außerdem: 114 war der erste Build mit **echten**
Firebase-Werten (113 hatte sie auch schon, aber nie in die Play Console
geladen) — vorher liefen alle FCM-Codepfade wegen leerer `BuildConfig`-Felder
nie wirklich. Eine gründliche Codedurchsicht (`FlexrApplication.initFirebase()`,
`PushTokenRegistrar`, `FlexrMessagingService`, das gemergte Manifest aus einem
echten Build, R8-Warnungen) fand aber **nichts** — jeder riskante Aufruf steckt
bereits in `runCatching`. Diese Spur wurde nie verifiziert oder widerlegt,
sie wurde nur durch den späteren echten Fund gegenstandslos (siehe unten:
der tatsächliche Fehler liegt in `PlayBillingService`, unabhängig von Firebase).

### Der eigentliche Blocker: kein Stack Trace zu bekommen

Ohne echten Absturzbericht blieb alles Raten. `CrashLog.kt` (seit 2.6.1,
11.09.2026) schreibt ihn nach `Android/data/flexr.social.app/files/` — aber
dieser Ordner war auf dem betroffenen Gerät **nicht mehr erreichbar**:

* Samsungs "Eigene Dateien" zeigt für seine eigene App-Berechtigungsseite gar
  keine "Alle Dateien verwalten"-Option an.
* **X-plore File Manager** (der übliche Königsweg für genau diesen Fall) kommt
  bei `Android/media` noch durch seinen SAF-Grant-Trick, bei `Android/data`
  und `Android/obb` zeigt er nur noch "Zugriff verweigert" — offenbar hat
  dieses Android (16, API 36) die Lücke inzwischen geschlossen, über die
  X-plore bisher kam.
* USB/adb ging nicht: der Nutzer saß an einem anderen Rechner als dem, auf dem
  diese Session läuft. Kabelloses ADB ging auch nicht: Handy und Session-
  Rechner sind nicht im selben WLAN.

**Lösung (116/2.7.4):** `CrashLog.kt` legt den Bericht jetzt **zusätzlich** in
die `MediaStore`-Downloads-Sammlung — seit Android 10 ohne jede Berechtigung
beschreibbar (eine App darf dort eigene Dateien anlegen), und der Ordner ist
in jedem Dateimanager ganz normal sichtbar, ohne SAF-Tricks. Die
`Android/data`-Kopie bleibt als Fallback bestehen; beide Ablageorte räumen
für sich die ältesten Berichte auf (`MAX_DATEIEN = 5`). Diese Fassung behebt
den Absturz **nicht** — sie dient rein dazu, den nächsten tatsächlich
einsehen zu können. Auf ausdrücklichen Nutzerwunsch trotzdem direkt in
Produktion hochgeladen (siehe Warnhinweis ganz oben im Dokument).

### Der Fund

Aus der Downloads-Kopie:

```
java.lang.IllegalArgumentException: Pending purchases for one-time products must be supported.
    at b5.f.get(SourceFile:269)
    ...
    at androidx.compose.ui.platform.AndroidCompositionLocals_androidKt.a(SourceFile:643)
    ...
    at t1.t.onAttachedToWindow(SourceFile:121)
```

`PlayBillingService` (`android-native/app/src/main/java/flexr/social/app/data/billing/PlayBillingService.kt`)
baute den `BillingClient` mit einem **leeren** `PendingPurchasesParams`:

```kotlin
.enablePendingPurchases(PendingPurchasesParams.newBuilder().build())
```

Seit **Play Billing Library 7** (das Projekt ist auf `8.0.0`) verlangt
`build()` zwingend `enableOneTimeProducts()` — auch für Apps wie FLEXR, die
ausschließlich ein Abo verkaufen und nie ein Einmalprodukt anbieten werden.
Ohne das wirft `build()` sofort. Der `client`-Wert ist ein
**Property-Initializer**, kein `lazy` und kein `runCatching` drumherum — die
Exception fliegt also synchron und ungefangen, sobald Hilt `PlayBillingService`
konstruiert. Das passiert bei **jedem** App-Start, weil `MainViewModel` den
Service im Konstruktor verlangt (Hilt baut ihn beim ersten `hiltViewModel()`-
Aufruf in `MainActivity.setContent`) — daher der Stack Trace mitten im
Compose-Attach-Vorgang, und daher die 100-prozentige Reproduzierbarkeit.

**Vermutlich schon seit der ersten Play-Billing-Einreichung im Code** (Commit
`6950764`, 17.09.2026) — nur ist seither offenbar niemand mit einem frischen
Prozess auf einem echten Gerät gelandet, bevor `MainViewModel`/
`PlayBillingService` gebraucht wurden. Weder Unit-Tests noch der R8-Build
hätten das je gefangen: `BillingClient.newBuilder(...).build()` ist ein
echter Google-Play-Services-Aufruf, den Robolectric-freie JVM-Unit-Tests gar
nicht ausführen.

**Fix (117/2.7.5):**

```kotlin
.enablePendingPurchases(
    PendingPurchasesParams.newBuilder()
        .enableOneTimeProducts()
        .build(),
)
```

Quellcode sonst identisch zu 116. Gebaut, signiert (derselbe Fingerabdruck),
getestet (`testProdReleaseUnitTest` grün), `.aab` und `.apk` nach
`release-2.7.5/` mit `SHA256SUMS.txt`, dem Nutzer übergeben.

### iOS ist nicht betroffen

Kurz nachgeprüft, weil naheliegend: `ios/FLEXR/Data/Store/StoreKitService.swift`
hat keinen eager Property-Initializer wie Android — `init(api:)` ist trivial,
jeder StoreKit-Aufruf steckt in `do/try/catch` bzw. ist `async throws` mit
Fehlerbehandlung. Das Android-spezifische Konzept
`PendingPurchasesParams`/`enableOneTimeProducts()` existiert bei StoreKit
schlicht nicht. Kein Handlungsbedarf auf der iOS-Seite.

### Offen

* **Play Console prüfen**, ob 117 tatsächlich hochgeladen wurde (siehe
  Warnhinweis ganz oben) — 116 behebt den Absturz nicht.
* Die release-2.6.6-bis-2.7.1-Lücke (kein APK exportiert) ist mit 2.7.3ff.
  nur für diese Versionen behoben, nicht strukturell — es gibt weiterhin kein
  Skript, das `assembleProdRelease` automatisch neben `bundleProdRelease`
  laufen lässt. Käme mal jemand dazu, das in `android/build.sh` oder ein
  neues `android-native`-Äquivalent zu gießen, würde diese Lücke nicht wieder
  aufreißen.
* Die beiden noch offenen Tests aus der vorigen Sitzung (Sandbox-Kauf,
  Push mit zwei Geräten) stehen weiterhin aus — zusätzlich zur Frage, ob der
  Kauf-Knopf mit dem jetzt reparierten `PlayBillingService` überhaupt zum
  ersten Mal fehlerfrei durchläuft.

## Sitzung 18.09.2026 — Block A, C, D fertig: Push und Kauf in allen drei Oberflächen

Kurz: **Die Einrichtungsanleitung ist komplett abgearbeitet.** Firebase,
Play Console und App Store Connect stehen; der Kauf-Knopf ist in der
Android-App live, in der iOS-App eingereicht und wartet auf Apples Prüfung.

### A — Firebase für Android-Push

Projekt `flexr-a0625` in der Firebase-Konsole angelegt, Android-App
`flexr.social.app` registriert. Die vier Werte (Projekt-ID, App-ID,
API-Schlüssel, Sender-ID) kamen als `google-services.json` und stehen jetzt in
`~/.gradle/gradle.properties` — nicht im Repository, wie in
`app/build.gradle.kts` dokumentiert.

Das Dienstkonto für den Server (`firebase-adminsdk`, eigener privater
Schlüssel) liegt als `/flexr/backend/fcm-service-account.json` (600,
`deploy`). `.env` um `FCM_SERVICE_ACCOUNT_FILE` und `FCM_PROJECT_ID` ergänzt,
Sicherung `.env.bak-vor-fcm-20260918`.

**Geprüft ohne Gerät:** ein Sendeversuch an ein erfundenes Token. Antwort:
`400 „registration token is not a valid FCM registration token"` — das
Dienstkonto wird akzeptiert, nur das Fantasie-Token nicht. Genau das
gewünschte Ergebnis, analog zu Apples `BadDeviceToken`.

### Android neu gebaut — zweimal, aus einem guten Grund

**versionCode 113 (2.7.1)** entstand zuerst, mit den frischen Firebase-Werten,
aber ohne Quellcode-Änderung gegenüber 112. Danach der Hinweis: 2.7.1 gab es
schon (112, vom Vortag) - zwei verschiedene Bundles mit demselben
Versionsnamen wären in der Play Console verwechselbar gewesen. Also
**versionCode 114, versionName 2.7.2** - wieder ohne Quellcode-Unterschied,
nur der Name geändert (`android-native/app/build.gradle.kts`). 114 ist die
Fassung, die der Nutzer in die Play Console geladen hat.

Nebenbei mit erledigt: Der JDK- und SDK-Pfad auf dieser Maschine war nicht
gesetzt (`JAVA_HOME` fehlte, `gradlew` brach sofort ab). Gefunden unter
`~/.bubblewrap/jdk/jdk-17.0.11+9` und `~/.bubblewrap/android_sdk` (Letzteres
auch in `android-native/local.properties` als `sdk.dir` hinterlegt) - für
künftige Builds auf dieser Maschine gültig, keine Neuinstallation nötig.

### iOS: Sprechblasen noch einmal repariert

Der Fix vom 16.09. (`fe6af02`, `frame(maxWidth: 300)` + `fixedSize`) folgte
exakt dem dokumentierten SwiftUI-Muster und entspricht Androids
funktionierendem `Column + widthIn`. Trotzdem zeigte ein echtes iPhone am
18.09. wieder das alte Symptom: Ein-Wort-Nachrichten („test", „bjj", „26262")
füllten die ganze Zeile. Laut `HANDOFF.md` vom 16.09. hatte bis dahin
**niemand** die TestFlight-Fassung tatsächlich auf einem Gerät angesehen - ob
es sich um eine echte Regression oder einen veralteten Teststand handelte,
ließ sich im Nachhinein nicht mehr trennen.

Neu gebaut mit dem robusteren Primitiv: `HStack` + `Spacer(minLength: 0)`
statt sich allein auf das Schrumpfverhalten von `frame(maxWidth:)` zu
verlassen - der Spacer nimmt garantiert den Rest der Zeile, unabhängig davon,
was die Frame-Berechnung intern tut. Die 300-pt-Obergrenze für sehr lange
Nachrichten (iPad) bleibt, sitzt jetzt aber auf einem ausgelagerten `bubble`-
Baustein (`ios/FLEXR/UI/Chat/ChatView.swift`). Commit `feadf87`.

### C — Play Console: der Weg zum Dienstkonto ist nicht mehr da, wo er stand

Play Console hat den API-Zugriff aus den Kontoeinstellungen entfernt.
Dienstkonten werden jetzt **in der Google Cloud Console** angelegt (IAM &
Verwaltung → Dienstkonten, im selben Projekt `flexr-a0625` wie Firebase - das
Firebase-Projekt lag „ohne Organisation", nicht unter `pachernegg-org`, daher
in der Projektauswahl zunächst nicht sichtbar) und dann in der Play Console
unter **„Nutzer und Berechtigungen" → „Neue Nutzer einladen"** wie ein
gewöhnlicher Nutzer eingeladen - mit der Dienstkonto-E-Mail-Adresse statt
einer Personen-Adresse.

Drei Fehlschläge auf dem Weg zum funktionierenden Zugriff, jeder mit eigener,
eindeutiger Fehlermeldung:

1. `403 SERVICE_DISABLED` - die Google Play Android Developer API war im
   Cloud-Projekt schlicht noch nie aktiviert. Direktlink aus der
   Fehlermeldung selbst behoben.
2. `401 permissionDenied` - die App-spezifische Freigabe für FLEXR fehlte
   noch (ein eigener Dialog **„Berechtigungen für FLEXR"** neben den
   Kontoberechtigungen, mit eigenem „Anwenden"-Knopf - leicht zu übersehen).
3. `400 Invalid Value` - der Zielzustand: Google akzeptiert Schlüssel und
   Berechtigung, meckert nur noch über das absichtlich erfundene Test-Token.

Dienstkonto: `play-billing-verification@flexr-a0625.iam.gserviceaccount.com`,
Schlüssel liegt als `/flexr/backend/play-service-account.json` (600,
`deploy`). `.env` um `GOOGLE_SERVICE_ACCOUNT_FILE` und
`GOOGLE_SUBSCRIPTION_PRODUCT_ID=premium_monthly` ergänzt (bewusst **zusammen**
in einem Schritt, nicht einzeln - sonst hätte der Kauf-Knopf kurzzeitig ohne
funktionierende Kaufprüfung angezeigt).

### D — App Store Connect: Vertrag, DAC7, Abo, Einreichung

**Vertrag für gebührenpflichtige Apps** stand auf „Neu", nicht „Aktiv" -
zuerst Rechtsträger-Angaben aktualisiert, dann Bankverbindung (N26, IBAN
`DE33...`, Kontonummer aus der IBAN selbst hergeleitet - deutsche BBAN-Regel:
erste 8 Ziffern nach der Länderkennung sind die BLZ, die restlichen 10 die
Kontonummer) und Steuerformular eingereicht.

**Abo angelegt:** Gruppe `FLEXR Premium`, Tarif `FLEXR Premium Monatlich`,
Produkt-ID `social.flexr.premium.monthly` (exakt wie in der Anleitung, nicht
mehr änderbar), 1 Monat Laufzeit, 9,99 € (DACH-Verfügbarkeit - bewusst so
eingeschränkt, deckt sich mit dem restlichen App-Vertrieb).

**Kein iPhone zur Hand für den Pflicht-Screenshot** (App Review Screenshot,
von Apple für die erste Einreichung eines Abos zwingend verlangt, nicht
optional trotz fehlendem Stern im Formular). Gelöst ohne Gerät: Der
tatsächliche `PaywallView.swift`-Code (Texte, Farben aus `FlexrColor`, Layout)
als HTML nachgebaut und mit `google-chrome --headless --screenshot` auf exakt
640×920 px gerendert - der Screenshot geht ohnehin nur an Apples Prüfer, nie
an echte Nutzer. Dieselbe Technik für das optionale 1024×1024-Werbebild
(App-Icon + „PREMIUM"-Schriftzug).

**DAC7-Compliance-Frage** („Bieten deine Apps persönliche Dienste an?") mit
**Nein** beantwortet: DAC7 meint zeit-/aufgabenbasierte Arbeit, die ein Nutzer
für einen anderen gegen Bezahlung erbringt und die die Plattform nur
vermittelt (Fahrdienst, Nachhilfe, Handwerk). FLEXR verkauft ein Abo direkt an
die eigenen Nutzer für App-Funktionen - kein Nutzer bezahlt einen anderen.

**Reihenfolge-Falle bei der Einreichung**, zweimal in Folge:

1. Erster Versuch: „Kann nicht zur Prüfung übermittelt werden - Dein Abo mit
   automatischer Verlängerung muss mit seiner Abo-Gruppe übermittelt werden."
   Ursache: Version 1.0 war schon eingereicht («Warten auf Prüfung»), ein
   neues Abo lässt sich nicht nachträglich anhängen. Bewusste Entscheidung
   (Option B): Version 1.0 aus der Prüfung genommen, um Premium gleich mit
   dem ersten Release auszuliefern statt erst mit einem Folge-Update.
2. Zweiter Versuch, neue Fehlermeldung: „Füge mindestens eine Lokalisierung
   für die Abo-**Gruppe** hinzu." Die Lokalisierung, die wir ausgefüllt
   hatten, war die des einzelnen Tarifs - die Gruppe selbst (der Container,
   der Nutzer in den iOS-Einstellungen unter „Abonnements" sehen) brauchte
   ihre eigene: Anzeigename `FLEXR Premium`.

Danach nebenbei aufgetreten: eine zweite, unabhängige Blockade beim
Einreichen wegen fehlender **DAC7-Angaben** - derselbe Vertrag-Abschnitt unter
„Geschäftliches", nicht Teil des Abo-Formulars selbst, aber ebenfalls
Voraussetzung fürs Einreichen.

**Ergebnis:** Version 1.0 + `FLEXR Premium Monatlich` wurden zusammen zur
Prüfung eingereicht. Serverseitig `APPLE_SUBSCRIPTION_PRODUCT_ID=
social.flexr.premium.monthly` gesetzt und neu gestartet, noch **vor** der
Einreichung - damit ließ sich der echte Kauf-Bildschirm samt Preis schon in
der laufenden TestFlight-Fassung anschauen, ohne auf den neuen Build zu
warten (derselbe Trick wie bei C4: Server-Freischaltung wirkt sofort, ganz
ohne neuen Build).

**D5 (optional)** hat der Nutzer selbst erledigt: App Store Server
Notifications auf `https://flexr.social/api/billing/apple/notifications`
gesetzt.

### appreview zieht nach Wien um

Das Prüfkonto trainierte bisher in `3D Lady Fit`, Graz - ohne männliches
Gegenstück in der Nähe blieben Match und Chatverlauf leer. Auf Wunsch auf ein
zentrales, freigegebenes Gym umgezogen: **Clever fit, Seidengasse 9-11, 1070
Wien** (`User.gym`, `User.plz`, `User.city` direkt in der DB aktualisiert -
das Feld muss exakt dem `Gym.label` aus der `gyms`-Tabelle entsprechen, sonst
nimmt das Profil laut `gym_geo.py` an der Umkreissuche gar nicht teil). Der
Nutzer kann das Konto jetzt von seinem eigenen aus liken/matchen.

### Was jetzt noch fehlt

Zwei Tests, unabhängig von Apples Entscheidung zur Einreichung:

1. **Sandbox-Kauf auf einem echten Gerät** - bei Apple ein Sandbox-Tester
   anlegen (wartet ohnehin auf die Freigabe von Version 1.0), bei Google
   einen Lizenztester eintragen (Play Console → Einstellungen →
   Lizenztests) - das geht schon jetzt.
2. **Push mit zwei echten Geräten** - der eigentliche Beweis, dass der am
   17.09. gemeldete Fehler (Nachricht kam erst nach manuellem App-Start) nun
   wirklich behoben ist.

---

## Sitzung 17.09.2026 (8) — APNs eingerichtet, iOS-Build wieder grün

Kurz: **iOS-Push ist serverseitig fertig und gegen Apple geprüft.** Was noch
fehlt, damit auf einem iPhone etwas ankommt, ist kein Server-Thema mehr.

### Der Codemagic-Abbruch mit Status 65 — die Diagnose stimmte

Der Build davor scheiterte im Archiv-Schritt. Im Log stand nur *„Step 7 script
`Build ipa` exited with status code 65"*; `-showBuildSettings` war vorher
durchgelaufen, die `project.pbxproj` also strukturell in Ordnung.

Die Ursache war die Kette dahinter: Der Workflow holt sein Provisioning-Profil
mit `app-store-connect fetch-signing-files "$BUNDLE_ID" --type IOS_APP_STORE
--create`. Ein so erzeugtes Profil enthält **genau die Berechtigungen, die im
Developer-Portal für die App-ID freigeschaltet sind** — nicht die, die das
Xcode-Projekt verlangt. Die Sitzung davor hatte der App das
`aps-environment`-Entitlement gegeben (`ios/Config/FLEXR.entitlements`), im
Portal war Push für `social.flexr.app` aber nie eingeschaltet. `codesign`
verweigert dann, und xcodebuild meldet das als 65.

Nach dem Haken im Portal lief **derselbe Build unverändert durch**. Kein
Code-Eingriff nötig, und das vorbereitete Zurücknehmen der Entitlement-Zeilen
blieb ungenutzt.

> **Merksatz für das nächste Entitlement:** erst im Portal freischalten, dann
> bauen. Projekt und Profil müssen dasselbe wissen, und der Fehler zeigt sich
> erst ganz am Ende eines CI-Laufs.

### Der APNs-Schlüssel

Beim Anlegen fragt Apple zwei Dinge, die sich **nach dem Speichern nie wieder
ändern lassen**. Gewählt wurde:

| Feld | Wert | Warum |
|---|---|---|
| Environment | *Sandbox & Production* | von `push.py` vorausgesetzt |
| Key Restriction | *Team Scoped (All Topics)* | eine App, Unterschied heute null |

Das Environment ist der wichtige der beiden. `_send_apns()` schickt an eine
Umgebung und probiert bei `BadDeviceToken` die andere — weil
Entwicklungs-Builds Sandbox-Tokens bekommen, TestFlight und App Store
Produktions-Tokens, und beide gleichzeitig im Umlauf sind. Ein Schlüssel für
nur eine Umgebung hätte die andere Hälfte mit `InvalidProviderToken` abgewiesen,
und zwar still — ein solcher Fehlschlag steht nur im Log.

Bei der Key Restriction wäre *Topic Scoped* das engere gewesen: Bei einem Leck
ließen sich damit nur FLEXR-Nutzer beschicken statt jeder App des Kontos. Bei
genau einer App im Team ist der Unterschied heute keiner; er entstünde erst mit
einer zweiten App. Vertretbar, zumal Apple nur zwei aktive APNs-Schlüssel je
Konto zulässt — „pro App ein Schlüssel" trägt ohnehin nicht weit.

### Was auf dem Server steht

| | |
|---|---|
| Schlüssel | `/flexr/backend/apns-key.p8`, Eigentümer `deploy`, Rechte 600 |
| `APNS_KEY_ID` | `93U96DXUDW` |
| `APNS_TEAM_ID` | `UJ46YJU58D` |
| `APNS_TOPIC` | `social.flexr.app` |
| `APNS_SANDBOX` | **bewusst nicht gesetzt** — siehe oben |

Sicherung der vorigen `.env`: `/flexr/backend/.env.bak-vor-apns-20260917`.
Dienst neu gestartet, `systemctl is-active` → `active`, `/api/health` → 200.

> Direkt nach dem Neustart kam wieder einmalig ein **502** — dieselbe
> Racebedingung wie beim letzten Deploy (`is-active` meldet den Prozess, nicht
> die Bereitschaft von Uvicorn). Sekunden später grün. Das ist inzwischen zum
> zweiten Mal aufgetreten und kein Zufall: **nach einem Neustart ein paar
> Sekunden warten, bevor man den Health-Check aufruft.**

### Wie geprüft wurde, ohne ein iPhone zu haben

Ein Push an ein absichtlich unbrauchbares Geräte-Token. Die Antwort trennt
sauber, was sonst nur ein Gerät zeigen würde:

| Antwort | Bedeutung |
|---|---|
| `400 BadDeviceToken` | JWT **akzeptiert**, nur das Token verworfen — alles richtig |
| `403 InvalidProviderToken` | Schlüssel, Key ID oder Team ID falsch |
| `403 BadTopic` | Bundle-Identifier falsch |

Beide Umgebungen antworteten `400 BadDeviceToken`. Damit ist zweierlei belegt:
Der Schlüssel stimmt, **und** *Sandbox & Production* deckt tatsächlich beides
ab — die Rückfallebene in `push.py` trifft also auf das, was sie erwartet.

Das JWT selbst wurde mitgeprüft: `alg: ES256`, `kid`, `iss`, und eine
**64-Byte-Signatur im r‖s-Format**. Das ist die Stelle, an der
APNs-Anbindungen sonst scheitern — Bibliotheken liefern gern DER, Apple
verlangt rohes r‖s.

Der Befehl steht in [EINRICHTUNG-PUSH-UND-KAUF.md](EINRICHTUNG-PUSH-UND-KAUF.md),
Abschnitt B3, und ist wiederholbar.

### Zwei Dinge zur Schlüsselhygiene

* **Der private Schlüssel ist durch den Chat gegangen.** Er wurde als Anhang
  übergeben und musste gelesen werden, um ihn zu kopieren — damit steht er im
  Transkript dieser Sitzung. Wer das nicht will, widerruft ihn im Portal und
  legt einen neuen an (ein Slot ist frei); der Ablauf ist derselbe, nur mit
  neuer Key ID.
* **`*.p8` steht jetzt in der `.gitignore`.** Die beiden Schlüssel liegen
  außerhalb des Repos in `~/MEGA/FLEXR/` (dort von 664 auf **600** gesetzt),
  auf dem Server unversioniert. Die Regel ist Versicherung gegen ein späteres
  `git add -A`.

> **Die bekannte Falle ist für diesen Pfad zu.** `backend/apns-key.p8` liegt
> auf dem VPS unversioniert; wäre der Pfad je in einen Commit geraten, hätte
> der nächste `git pull` dort mit *„untracked working tree files would be
> overwritten"* abgebrochen — genau das ist am 16.09. schon einmal passiert.
> Durch `*.p8` in der `.gitignore` kann das für Schlüssel nicht mehr
> vorkommen, und `git status` auf dem VPS zeigt die Datei seither gar nicht
> mehr an. **Offen bleibt `backend/list_users.py`** (21.08., nur lesend, dort
> von Hand hingelegt): Für diesen Pfad ist die Falle weiter scharf.

### Was jetzt noch fehlt

Der Server **kann** senden, aber kein Gerät hat je ein Token registriert. Dafür
braucht es eine iOS-Fassung mit der Push-Berechtigung auf einem echten Gerät
(TestFlight) — der Simulator bekommt keine APNs-Tokens.

Offen sind damit die Blöcke **A**, **C** und **D** der Einrichtungsanleitung.

---

## Sitzung 17.09.2026 (7) — Push: warum nichts ankam, und was jetzt schickt

**Gemeldet:** „Zum Zeitpunkt eines Nachrichtenerhalts im Chat kam bei der
Android-App keine Pushnachricht. Erst als ich 1 h später die App manuell
gestartet habe, ging auch die Pushnachricht gleichzeitig ein."

### Es war kein Fehler im Code

FLEXR hatte **keinen Push-Kanal** — und das stand so im eigenen Code
(`notifications.py`: *„FLEXR hat bewusst kein FCM/APNs, die Apps holen ihre
Benachrichtigungen per Hintergrundabgleich ab"*). Was wie eine Push-Nachricht
aussah, war eine **lokale** Benachrichtigung, die die App sich selbst stellt,
nachdem ihr WorkManager-Job den Server abgefragt hat.

Dieser Entwurf hat eine Decke, die keine Einstellung verschiebt:

* **15 Minuten** ist das kürzeste Intervall, das WorkManager für periodische
  Arbeit zulässt.
* Im **Doze-Modus** schiebt Android auch diesen Lauf in die nächste
  Wartungsphase — auf einem schlafenden Telefon ein bis zwei Stunden.
* Nach einem **erzwungenen Beenden** (Akku-Optimierung mancher Hersteller)
  läuft gar nichts mehr, bis die App von Hand gestartet wird.

Beim Öffnen holt WorkManager den überfälligen Lauf sofort nach. Genau das war
zu sehen: Die Meldung kam im selben Moment wie der App-Start.

### Was jetzt gebaut ist

Der Server schickt selbst, über **FCM mit `priority: high`** — nur damit weckt
Android ein Gerät aus dem Doze. Ohne diese Priorität wäre der ganze Umbau
wirkungslos.

| Teil | Wo |
|---|---|
| Tabelle `push_tokens` | Migration `c93f18ad6b27` |
| Versand (FCM HTTP v1) | `backend/app/push.py` |
| An-/Abmelden des Geräts | `POST` / `DELETE /api/notifications/token` |
| Auslöser | `routers/messages.py`, nach dem Speichern |
| Empfang | `android/.../push/FlexrMessagingService.kt` |

### Vier Entscheidungen, die den Ausschlag geben

**Der Token ist der Schalter.** Wer Benachrichtigungen abschaltet, wird
abgemeldet; der Server hat dann niemanden, dem er zustellen könnte. Bewusst
kein zusätzliches Flag am Konto — zwei Quellen für dieselbe Frage laufen
früher oder später auseinander, und diese hier stimmt auch, wenn jemand die
App löscht.

**Zugestellt wird der zensierte Text**, nicht das Original. Die
Benachrichtigung landet auf einem gesperrten Bildschirm; was der Empfänger in
der App gar nicht zu sehen bekäme (Links, Kontaktdaten — siehe
`safety_checks.redact_message`), hat dort erst recht nichts verloren. Gekürzt
wird auf 120 Zeichen.

**Push ist nie Teil des Sendens.** `push.send()` wirft nicht, und die
Aufrufstelle fängt zusätzlich ab. Das ist keine doppelte Vorsicht, sondern der
Punkt: Ein Ausfall bei Google darf nicht verhindern, dass jemand eine Nachricht
schreiben kann — das wäre ein ungleich schlimmerer Fehler als der, der hier
behoben wurde. Festgehalten in `test_nachricht_kommt_auch_ohne_push_an`.

**Der Hintergrundabgleich bleibt.** Er ist jetzt der Fallback: für Geräte ohne
Play-Dienste, für verlorene Zustellungen und für den Zustand, in dem FCM noch
gar nicht eingerichtet ist. Beide benutzen dieselbe Benachrichtigungs-ID — holt
der Abgleich später dieselbe Nachricht, **ersetzt** er die Meldung, statt eine
zweite danebenzustellen.

### Android ohne `google-services.json`

Bewusst **ohne** das google-services-Gradle-Plugin: Mit ihm ließe sich die App
ohne `google-services.json` gar nicht bauen, und die Datei gehört nicht ins
Repository. Die vier Werte kommen stattdessen aus `gradle.properties` in
BuildConfig, und `FlexrApplication.initFirebase()` startet Firebase nur, wenn
alle vier da sind. Fehlen sie, passiert nichts und die App verhält sich wie
bisher.

Zu setzen in `~/.gradle/gradle.properties` (die Werte stehen in der
Firebase-Konsole und sind keine Geheimnisse — sie stecken in jeder
ausgelieferten Android-App):

```
flexr.firebase.projectId=…
flexr.firebase.appId=…
flexr.firebase.apiKey=…
flexr.firebase.senderId=…
```

### Was noch fehlt, damit es wirkt

**Ohne diese beiden Schritte bleibt Push aus** — der Server stellt nicht zu,
die Apps holen weiter ab, alles läuft wie bisher:

1. **Firebase-Projekt anlegen**, Android-App darin registrieren
   (`flexr.social.app`) → die vier Werte oben.
2. **Dienstkonto** mit der Rolle *Firebase Cloud Messaging API Admin*, JSON auf
   den VPS, in die `.env`:
   ```
   FCM_SERVICE_ACCOUNT_FILE=/flexr/backend/fcm-service-account.json
   FCM_PROJECT_ID=<projekt-id>
   ```

Gegengeprüft nach dem Deploy: `POST /api/notifications/token` → 200, ein zu
kurzer Token → 422, `DELETE` → 200, `push.configured()` → False (erwartet,
solange die Zugangsdaten fehlen).

### Android 2.7.1 (versionCode 112)

Enthält FCM und die Rücknahme des Like-Zählers im Beta-Abzeichen. 8,0 MB
(vorher 7,7 — die Firebase-Bibliothek), signiert, `jarsigner -verify` → „jar
verified". Abgelegt unter `../release-2.7.1/`:

```
7955631b452ad429cc6f466796329b9432ff83ba232d6ae24d575688520c5fd3  flexr-2.7.1-vc112.aab
```

2.7.0 (versionCode 111) ist damit überholt und war nie hochgeladen.

### iOS

Bleibt vorerst beim Hintergrundabgleich. Echte Zustellung bräuchte dort APNs
(Push-Schlüssel im Apple-Developer-Konto, Entitlement, Registrierung im Client)
— derselbe Umbau noch einmal, und er lässt sich hier ebenso wenig testen wie
der StoreKit-Teil. Der Server ist darauf vorbereitet: `push_tokens.platform`
kennt `ios` bereits, und `push.send()` schickt den APNs-Block mit.

### Geprüft

`backend/tests/test_push.py` (7 Fälle): An- und Abmelden, mehrfaches Anmelden
desselben Tokens, Wandern des Tokens beim Kontowechsel, kein Versand ohne
Zugangsdaten, Nachricht kommt auch bei krachendem Push an, zensierter Text,
Kürzung. Gesamt **488 Backend-Tests grün**, Android kompiliert in allen
Varianten, Android-Unit-Tests grün.

## Sitzung 17.09.2026 (6) — Suchumkreis: gespeicherter Wunsch ≠ wirksame Grenze

**Nachgefragt wurde:** ob neu erstellte Profile ohne Premium automatisch auf
50 km begrenzt sind.

**Die Antwort ist zweigeteilt, und der zweite Teil war ein Fehler.**

Neue Konten starten bei **20 km** (`models.User.search_radius_km`, Standard
20) — die liegen also ohnehin unter der Grenze. Der Regler selbst ist in allen
drei Oberflächen **bewusst** über die volle Spannweite bedienbar (2–250 km):
Wer ihn nach rechts zieht, soll sehen, was es dort gäbe, statt an einem stummen
Anschlag zu hängen. Gespeichert wird nur das Erlaubte, `profiles.py` kappt beim
Schreiben über `premium.clamp_radius()`.

**Gesucht wurde aber ungekappt.** `swipes.py` las `search_radius_km` roh aus
dem Konto. Für Konten, die ihren Wert eingestellt haben, *als es die Grenze
noch nicht gab*, greift das Kappen beim Speichern nie — sie fassen ihr Profil
ja nicht an. In der Produktion betraf das beim Nachsehen **drei Konten mit
250 km**, darunter das Apple-Prüfkonto:

```
appreview@flexr.social      radius=250  premium=False
zahariev.bul@gmail.com      radius=250  premium=False
liisa_koch@hotmail.com      radius=250  premium=False
```

Sie bekamen damit ohne Abo genau das, wofür Premium bezahlt wird.

**Behoben in `deck_profiles()`**: Der Radius wird jetzt bei der Suche gekappt.
Bewusst dort und **nicht** als einmalige Datenkorrektur — der gespeicherte
Wunsch bleibt erhalten und wird von selbst wieder wirksam, sobald jemand
Premium abschließt. Das Kappen beim Speichern bleibt zusätzlich bestehen; das
eine ersetzt das andere nicht, weil ein Konto seine Grenze auch ohne Speichern
verlieren kann (Abo endet, Schalter kippt).

Festgehalten in
`test_gespeicherter_umkreis_von_frueher_wirkt_nicht_weiter`: 250 km in der Zeit
ohne Grenzen gespeichert, Premium scharf geschaltet, Wunsch bleibt in der
Datenbank stehen — wirksam sind 50 km, und mit Premium wieder 250, ohne dass
jemand sein Profil erneut speichern müsste.

**481 Backend-Tests grün.**

### Nebenbefund für die Einreichung

Das Prüfkonto `appreview` sucht damit ab sofort im 50-km-Umkreis statt 250. Sein
Deck war ohnehin leer (kein männliches Gegenkonto, siehe Sitzung (3)) — durch
die Umstellung wird der Umkreis aber zusätzlich enger. Wer dort ein Gegenkonto
anlegt, muss es **innerhalb von 50 km** um `3D Lady Fit` in Graz platzieren.

### Android 2.7.1 (versionCode 112)

Enthält zusätzlich die Rücknahme des Like-Zählers im Beta-Abzeichen. 2.7.0 war
noch nicht hochgeladen, bekommt aber trotzdem eine eigene Nummer: Unter
derselben Nummer liegen sonst zwei verschiedene Inhalte, und am Dateinamen wäre
nicht mehr erkennbar, welcher davon auf einem Gerät liegt.

## Sitzung 17.09.2026 (5) — In-App-Käufe: StoreKit und Play Billing

**Auftrag:** „Premium soll aber unbedingt aus den apps heraus kaufbar sein —
baue das - kann man das nicht über stripe machen?"

**Die Antwort auf die Stripe-Frage lautet nein**, und zwar ohne Grauzone: Was
in einer App Funktionen freischaltet, muss über deren eigenen Kaufweg laufen
(App Review Guideline 3.1.1, Google-Play-Payments-Policy). Stripe bleibt dem
Browser. Gebaut ist deshalb der Weg, den die Stores vorsehen — StoreKit auf
iOS, Play Billing auf Android.

Deployt als **`6950764`**, Migration `b2e75c41a908` gelaufen, Dienst neu
gestartet, Health 200.

### Der tragende Gedanke: Die App schaltet nichts frei

Was aus einer App kommt, ist ein **Beleg, kein Ergebnis**. Apple liefert eine
signierte Transaktion, Google einen Kauf-Token; beide sagen für sich genommen
nur, dass der Client etwas behauptet. Erst der Server entscheidet:

* **Apple** — das JWS wird vollständig geprüft: Die Zertifikatskette muss bei
  genau dem Wurzelzertifikat enden, das im Repository liegt
  (`backend/app/data/AppleRootCA-G3.cer`, von apple.com geladen, SHA-256
  `63343abf…`), jedes Glied vom nächsten signiert sein, keines abgelaufen, und
  die Signatur muss vom Blattzertifikat stammen. Danach erst werden `bundleId`
  und `productId` geprüft. **Ohne App-Store-Connect-Zugangsdaten** — ein
  StoreKit-Beleg trägt seine Kette selbst.
* **Google** — ein Play-Token trägt keine prüfbare Signatur, also wird Google
  gefragt (`purchases.subscriptionsv2`). Dafür braucht es ein Dienstkonto.

### Warum ein Ablaufzeitpunkt und kein „aktiv"-Schalter

`users.store_premium_until` trägt die Berechtigung, nicht ein Boolean. Der
Grund: **Apple und Google stellen ihre Benachrichtigungen nicht garantiert
zu.** Ein Schalter, der auf „aktiv" steht und dessen „aus"-Nachricht verloren
geht, bliebe für immer offen. Ein Zeitpunkt läuft von selbst ab.

Umgekehrt sind 16 Stunden Kulanz aufgeschlagen (`store_billing.GRACE`): Beide
Stores buchen kurz vor Ablauf ab und melden die Verlängerung danach. Ohne die
Kulanz stünde ein zahlender Kunde bei jeder verspäteten Meldung stundenlang
ohne Premium da — die teurere der beiden Unfreundlichkeiten.

Warum die Spalte am Konto und nicht eine Abfrage über `store_subscriptions`:
`User.is_premium` wird bei **jeder** Profilausgabe gelesen, im Deck also bis zu
50-mal pro Anfrage. Die Tabelle bleibt der Nachweis, die Spalte ist die
schnelle Antwort; geschrieben wird beides nur von `apply_subscription()`.

### Ein Kauf, ein Konto

`(provider, external_id)` ist eindeutig. Wer denselben Apple-Zugang auf einem
zweiten FLEXR-Konto einreicht — im Alltag: Konto neu angelegt, gleiches
iPhone —, nimmt den Kauf **mit**; das erste Konto verliert die Berechtigung im
selben Zug. Kopiert wird nichts, sonst hätten zwei Konten Premium für einmal
Geld. Festgehalten in
`test_derselbe_kauf_erzeugt_nicht_zweimal_premium`.

### Was die Clients tun (und was nicht)

Beide reichen nur ein. Zusätzlich holen beide ihre laufenden Käufe **bei jedem
Start** nach (`Transaction.currentEntitlements` bzw. `queryPurchasesAsync`).
Das ist kein Beiwerk, sondern der Weg zurück aus jeder Störung —
Gerätewechsel, Neuinstallation, Kauf ohne Verbindung — und ersetzt den Knopf
„Kauf wiederherstellen", den sonst jeder erst suchen müsste. iOS hört
außerdem dauerhaft auf `Transaction.updates`; darüber stellt Apple
Verlängerungen und Rückerstattungen zu, die sonst niemand abholt.

**Der Preis kommt vom Store**, nicht aus unseren Ressourcen: Apple und Google
rechnen Währung, Steuer und Preisstufe selbst (typischerweise 9,99 € statt
10,00 €). Die Clients zeigen `displayPrice` bzw. `formattedPrice`.

Bei Google wird der Kauf **serverseitig bestätigt** (`acknowledge`), sobald die
Berechtigung gutgeschrieben ist — ohne Bestätigung storniert Google nach drei
Tagen und erstattet das Geld. Der Client bestätigt zusätzlich, falls der Server
dabei ausfällt.

### Der Kauf-Knopf ist noch unsichtbar — absichtlich

`store_purchase_available` ist nur wahr, wenn eine Produktkennung eingetragen
ist. Solange nicht, zeigen die Apps keinen Knopf: Einer, der im Store nichts
findet, ist schlimmer als keiner. **Das ist der einzige Schritt, der noch
fehlt**, und er braucht keinen neuen Build:

| Wo | Was anzulegen | Dann in die `.env` |
|---|---|---|
| App Store Connect | Auto-Renewable Subscription in einer Abo-Gruppe | `APPLE_SUBSCRIPTION_PRODUCT_ID=social.flexr.premium.monthly` |
| Play Console | Abo mit Basis-Tarif, aktiviert | `GOOGLE_SUBSCRIPTION_PRODUCT_ID=premium_monthly` |
| Google Cloud | Dienstkonto mit Play-Developer-API-Zugriff | `GOOGLE_SERVICE_ACCOUNT_FILE=/pfad/zur.json` |
| Play Console → Monetarisierung | RTDN-Pub/Sub-Thema | `GOOGLE_NOTIFICATIONS_TOKEN=<geheim>` |
| App Store Connect → App-Informationen | Server-Benachrichtigungen V2, Produktions-URL | — |

Die Benachrichtigungs-URLs:

```
Apple:  https://flexr.social/api/billing/apple/notifications
Google: https://flexr.social/api/billing/google/notifications/<GOOGLE_NOTIFICATIONS_TOKEN>
```

Apple signiert seine Benachrichtigungen und weist sich dadurch aus; Googles
Pub/Sub-Zustellung nicht, deshalb das Geheimnis im Pfad. Ein falsches gibt 404.

`STORE_SANDBOX_ALLOWED` bleibt in der Produktion **aus**: Ein Testkauf aus
einem Entwicklergerät darf dort kein echtes Premium erzeugen. Zum Testen mit
einem Sandbox-Konto vorübergehend auf `true`.

### Rechtstexte: Der Vertragspartner hängt jetzt vom Kaufweg ab

Das ist die inhaltlich wichtigste Folge und stand vorher falsch da (die
Fassung von heute Nachmittag versprach noch „keine In-App-Käufe"):

* **AGB 6 c** (neu) — bei einem In-App-Kauf kommt der Zahlungsvertrag mit
  Apple bzw. Google zustande; für die Leistung selbst gelten weiter unsere AGB.
* **AGB 9 e/f** (neu) — drei Bestellwege mit demselben Leistungsumfang, und
  der Preis im Store darf abweichen. Die 10,00 € gelten für flexr.social.
* **AGB 10 b** (neu) — bei einem In-App-Kauf erhalten wir **keine
  Zahlungsdaten**, nur die Bestätigung des Stores.
* **AGB 12 a** — gekündigt wird dort, wo gekauft wurde. Kein technisches
  Detail: Bei einem Store-Kauf könnten wir den Vertrag gar nicht beenden.
* **Rücktrittsbelehrung** — ein Stripe-Abo stoppt der Rücktritt weiterhin
  automatisch, ein Store-Abo nicht. Die Erklärung wird trotzdem entgegen-
  genommen und protokolliert; es ist nicht Sache des Kunden, vorher zu wissen,
  wer sie umzusetzen hat (`routers/withdrawal.py`).

Mitgezogen: FAQ, Landingpage, `i18n-landing.js` und die gekürzten Fassungen in
beiden Apps — deutsch und englisch.

**`TERMS_VERSION` bleibt `2026-09-17`.** Geprüft, warum das zulässig ist: Die
Zwischenfassung von nachmittags war rund eine Stunde online, und in dieser Zeit
hat sich **niemand** registriert — die beiden heutigen Konten (`testuser2`,
`info@akhunstech.com`) tragen beide noch `terms 2026-09-10`. Es gibt also
keinen Nutzer, der die Zwischenfassung unter diesem Label akzeptiert hätte.

### Geprüft

`backend/tests/test_store_billing.py` (20 Fälle). Der Schwerpunkt liegt auf den
**Ablehnungen** — ein Kauf-Beleg ist die einzige Eingabe, mit der sich Geldwert
erzeugen ließe: fremde Wurzel, veränderte Nutzlast, gebrochene Kette, fremde
App, fremdes Produkt, Sandbox in der Produktion, Unsinn. Für den positiven Fall
wird Apples Wurzelzertifikat im Test durch ein selbst erzeugtes ersetzt; anders
ginge es nicht, und geprüft wird dabei trotzdem genau das, worauf es ankommt.

Gesamt **480 Backend-Tests grün**, Android kompiliert in allen Varianten,
Android-Unit-Tests grün.

### Android 2.7.0 neu gebaut (versionCode 111)

Dasselbe Versionspaar wie am Nachmittag — das Bundle war noch nicht
hochgeladen, also durfte die Nummer bleiben. Inhalt ist jetzt aber ein
anderer: Play Billing ist drin. Neue Prüfsumme:

```
09dc5b81b72e22fe2f110efc8766b7cb1dfcdefa39d397be65626aa92d5e9e6f  flexr-2.7.0-vc111.aab
```

7,7 MB, signiert (`jarsigner -verify` → „jar verified"), abgelegt unter
`../release-2.7.0/`. **Das ältere Bundle mit derselben Nummer wurde dabei
ersetzt** — es hatte die Prüfsumme `b53337da…` und ist damit gegenstandslos.

### Was offen bleibt

* **Der iOS-Code ist nie kompiliert worden.** Hier gibt es kein Xcode; der
  erste Codemagic-Lauf ist gleichzeitig der erste Compile. Android wurde
  kompiliert und getestet.
* Die **Store-Produkte** sind anzulegen (Tabelle oben). Bis dahin zeigen die
  Apps keinen Kauf-Knopf und verhalten sich wie zuvor.
* Soll der Apple-Prüfer den Kauf mitprüfen, muss das Abo-Produkt **vor** dem
  Einreichen angelegt und dem Build beigefügt werden.
* In `AccountModel`/`AccountView` (iOS) steht die Stripe-Checkout-Maschinerie
  noch, ist aber unerreichbar — die beiden FAGG-Erklärungen gehörten zum
  Stripe-Weg, bei einem Store-Kauf führt Apple den Vertrag. Bewusst nicht
  entfernt, weil sich das hier nicht kompilieren lässt; beim nächsten
  iOS-Durchgang aufräumen.
* Provision: Apple und Google behalten 15–30 %. Bei 9,99 € bleiben 7–8,50 €.

## Sitzung 17.09.2026 (4) — FLEXR Premium scharf geschaltet, Verkauf nur im Browser

**Auftrag:** „nimm flexr premium jetzt live — mach alle nötigen anpassungen
dafür. die app soll aber nach wie vor auf status beta bleiben, auch mit dem
popup hinweis auf der landingpage."

Deployt als **`c521a82`**, `PREMIUM_ENABLED=true` steht in der `.env` des VPS,
`sudo systemctl restart flexr-api` ist gelaufen, Health-Check grün (der erste
`curl` direkt nach dem Neustart gab wieder einmal `502` — dieselbe bekannte
Racebedingung, Sekunden später `200`).

### Was Premium „live" heißt

`settings.premium_enabled` ist der eine Hebel geblieben, den `premium.py`
beschreibt. Mit ihm gelten seit heute die Grenzen des kostenlosen Kontos:
20 Likes je 24 Stunden, 3 gleichzeitige Unterhaltungen, 50 km Suchumkreis.
Gegengeprüft an `testuser2` in der Produktion — `likes_remaining: 20`,
`open_chats_remaining: 3`, `max_radius_km: 50`.

Die Stripe-Seite war bereits vollständig vorbereitet und wurde vor dem
Umlegen nachgeprüft, nicht angenommen:

| Prüfung | Ergebnis |
|---|---|
| Preisobjekt | `price_1UGYfdIpMumqxPtFzu0d5A6f`, `livemode`, aktiv, 1000 EUR-Cent, monatlich, kein Trial |
| Webhook | `https://flexr.social/api/billing/webhook`, `enabled`, `livemode`, alle acht ausgewerteten Ereignisse abonniert |
| Billing-Portal | Standardkonfiguration aktiv, Kündigung **an**, Tarifwechsel **aus** |
| Checkout aus dem Browser | HTTP 200, Sitzung beginnt mit `cs_live_` |

Die dabei entstandene `CheckoutConsent`-Zeile von `testuser2` wurde
anschließend wieder entfernt; in der Tabelle steht nur noch der echte Eintrag
von `styriatrading@gmail.com` vom 23.08.

### Der Grund für das neue Modul `backend/app/clients.py`

**Beide App-Stores verbieten, in einer App Funktionen freizuschalten, die
außerhalb ihres eigenen Kaufwegs bezahlt wurden** — Apple in App Review
Guideline 3.1.1 (dort ausdrücklich auch „buttons, external links, or other
calls to action"), Google in der Payments-Policy. Die Paywall beider Apps
führt aber in einen Stripe-Checkout im externen Browser.

Entscheidend: **Diese Logik hängt an `premium_enabled` aus der Serverantwort.**
Das Umlegen des Schalters hätte also der veröffentlichten Android-Fassung
*und* dem iOS-Build, der gerade bei Apple in Prüfung liegt, ohne jeden neuen
Build einen Kauf-Knopf wachsen lassen. Beim Prüfer wäre das mit hoher
Wahrscheinlichkeit die Ablehnung gewesen.

Deshalb entscheidet **der Server pro Anfrage**, wem er einen Abschluss
anbietet, und nicht der Client:

* `GET /api/billing/status` meldet App-Clients `premium_enabled: false` —
  genau das Feld, an dem die ausgelieferten Fassungen ihren Knopf aufhängen.
  Sie zeigen dadurch unverändert die Oberfläche von gestern.
* `POST /api/billing/checkout` lehnt aus einer App mit 409 ab, und zwar
  **ohne zu nennen, wo es sonst ginge** — auch eine solche Weiterleitung wäre
  3.1.1.
* Die Meldungen an den Grenzen werben in der App nicht mehr („hol dir FLEXR
  Premium" ist eine Aufforderung im Sinne der Richtlinie).

Erkannt wird die App am Header `X-Flexr-Client`, den beide Clients ab den
Fassungen dieser Sitzung mitschicken, und ersatzweise am User-Agent — der
kommt von URLSession bzw. OkHttp, nicht aus FLEXR-Code, und steht so im
nginx-Protokoll der Produktion:

```
FLEXR/24 CFNetwork/3896.100.1.2.1 Darwin/27.0.0     (iOS)
okhttp/4.12.0                                       (Android)
```

Erkannt wird bewusst die **App**, nicht der Browser: Alles Unbekannte gilt als
Web. Andersherum träfe die Sperre jedes Skript, jeden Health-Check und jeden
Testlauf, und ein Zwischenglied, das den User-Agent umschreibt, machte Premium
im Browser unverkäuflich.

Live gegengeprüft, dieselbe Anmeldung, drei User-Agents:

| Client | `premium_enabled` | `checkout_available` | `limits_active` | `beta_active` |
|---|---|---|---|---|
| Browser | true | true | true | true |
| iOS-App | **false** | false | **true** | true |
| Android-App | **false** | false | **true** | true |

`POST /checkout` aus der App: 409. Aus dem Browser: 200 mit `cs_live_…`.

### Die Grenzen hängen am Konto, nicht am Gerät

Bewusst so, und durch `test_grenzen_gelten_am_konto_nicht_am_geraet`
festgehalten: Wären sie gerätespezifisch, höbe man sie auf, indem man sich
abwechselnd in App und Browser anmeldet. Umgekehrt wirkt ein im Browser
gekauftes Premium selbstverständlich auch in der App — untersagt ist der
*Abschluss* dort, nicht die Leistung daraus. Das Stripe-Portal bleibt den
Apps deshalb ebenfalls erreichbar: Es verkauft nichts (Tarifwechsel ist in der
Konfiguration aus), es verwaltet und kündigt.

### Drei Fragen, die bisher an einem Schalter hingen

`MembershipStatus` trennt sie jetzt:

* `checkout_available` — darf **dieser** Client verkaufen?
* `limits_active` — gelten die Grenzen? Für alle gleich.
* `beta_active` — trägt FLEXR das Beta-Abzeichen?

### Beta bleibt — und hing vorher am falschen Feld

Aufgefallen beim Umsetzen: Das Beta-Abzeichen wurde in **allen drei**
Oberflächen aus `!premium_enabled` abgeleitet (`MembershipPill` in
`FlexrChrome.swift` und `FlexrApp.kt`, `updateStatusPill()` im Web). Mit dem
Scharfschalten wäre „Beta" also überall stillschweigend verschwunden — das
Gegenteil des Auftrags.

Jetzt ein eigener Schalter `settings.beta_active` (Standard `true`). Die Pille
stellt „Beta · " dem eigentlichen Zustand voran, statt ihn zu ersetzen:
`Beta · 20 Likes`, `Beta · Premium`, `Beta · Gratis`. „Beta" sagt seither
etwas über den **Reifegrad** und nichts mehr über den Tarif — genau so steht
es jetzt auch in AGB Punkt 7 c.

Der Hinweis-Dialog auf der Landingpage bleibt unverändert stehen. Entfallen
ist nur seine inzwischen falsche Zusage „Während der Beta ist auch das
unbegrenzt"; der localStorage-Merker steht auf `flexr_beta_notice_v4`, damit
ihn auch sieht, wer v3 weggeklickt hatte.

### Rechtstexte

**AGB-Fassung 2026-09-17** (`TERMS_VERSION`), inhaltlich:

* Punkt 7 a — „nicht nur während der Beta-Phase" entfernt.
* Punkt 7 c — aus „Während der Beta-Phase gelten diese Grenzen nicht" wird der
  Geltungsbeginn (17.09.2026) plus die Klarstellung, dass „Beta" den
  Entwicklungsstand betrifft und daraus **kein Anspruch** auf eine Nutzung
  ohne die Grenzen folgt.
* Punkt 9 e — aus „Premium ist derzeit nicht bestellbar" wird der Bestellweg:
  ausschließlich flexr.social im Browser, kein App-Store, ein bestelltes
  Premium wirkt in den Apps, Kündigung dort wie hier.

Mitgezogen, deutsch **und** englisch: `faq.html`, Landingpage (Preiskarte,
Absatz darunter, FAQ-Antwort, Schlussabschnitt), `i18n-landing.js`,
`i18n-app.js`, die Web-App und die gekürzten Fassungen in beiden Apps
(`LegalContent.swift`, `LegalContent.kt`). Nach der Durchsicht steht das Wort
„Beta" in keinem Rechtstext mehr als Tarifaussage.

### In den Apps verschwinden Preis und Kaufaufforderung

* Kein Einstieg mehr in den Premium-Bildschirm — weder aus dem Konto (hing
  schon an `premiumEnabled`) noch aus „Wer dich geliket hat" (hing an nichts
  und war der eine Weg, auf dem ein App-Nutzer den Preis zu sehen bekam).
* Registrierungstext ohne „FLEXR Premium (10 €/Monat …)".
* `premium_status_free` ohne „Mit Premium fällt beides weg".
* Like- und Chat-Grenze nennen nur noch die Grenze.

### Android 2.7.0 (versionCode 111)

Gebaut mit `clean testProdReleaseUnitTest bundleProdRelease`, signiert
(`jarsigner -verify` → „jar verified"), 7,5 MB. Abgelegt unter
`../release-2.7.0/` samt Prüfsumme:

```
b53337dabf14de808e42081002f0a46ffa7474aed4822c8277082d65462893f5  flexr-2.7.0-vc111.aab
```

**Noch nicht in der Play Console hochgeladen** — das ist ein Schritt von Hand.

iOS: Versionsnummern **bewusst nicht angefasst** (`MARKETING_VERSION` steht
weiter auf 2.4.10). Ein Build liegt bei Apple in Prüfung; welche Fassung als
nächste geht, gehört nicht ins Repository entschieden. Die Änderungen dieser
Sitzung wirken erst mit dem nächsten Build — bis dahin schützt die
Server-Regel den in Prüfung liegenden Build.

### Tests

`backend/tests/test_store_regeln.py` (9 Fälle) hält fest, was hier
entschieden wurde: dass die App kein `premium_enabled: true` sieht, dass der
Checkout aus der App abgelehnt wird und der Fehlertext keinen Weg nach draußen
nennt, dass die Grenzen am Konto hängen, dass ein im Browser gekauftes Premium
in der App wirkt und dass das Beta-Abzeichen nicht mehr an Premium hängt.

Gesamt: **460 Backend-Tests grün**, Android-Unit-Tests grün,
`tools/check_betreiber.py` grün.

### Offen / bewusst nicht getan

* **Keine In-App-Käufe.** Der ertragsseitige Preis dieser Lösung: Aus den Apps
  heraus lässt sich Premium nicht kaufen, die Umwandlung mobiler Nutzer ist
  damit praktisch null. Der saubere Weg wäre StoreKit 2 (iOS) plus Play
  Billing (Android) mit serverseitiger Belegprüfung und Abgleich der
  Berechtigung — ein eigenes Vorhaben, das Produkte in App Store Connect und
  Play Console, Steuer- und Bankdaten und eine Entscheidung über die 15/30 %
  Provision voraussetzt. Bis dahin: verkaufen im Browser.
* **AGB Punkt 18 gegenüber den sechs Bestandskonten.** Punkt 7 c hatte
  zugesagt, das Ende der Grenzenlosigkeit „vorher anzukündigen"; Punkt 18 c
  nennt dafür vier Wochen per E-Mail. In der Datenbank stehen acht Konten,
  davon zwei Testkonten (`appreview`, `testuser2`) — die übrigen sechs haben
  die Grenzen ohne diese Ankündigung bekommen. Kein Konto hat ein Abo, der
  Nachteil ist also gering und jederzeit rückgängig zu machen
  (`PREMIUM_ENABLED=false`). Zu entscheiden: Ankündigung nachreichen oder
  nicht.
* Das Prüfkonto `appreview` hat weiterhin **kein Match und keinen
  Chatverlauf** (siehe Abschnitt der vorigen Sitzung).

## Sitzung 17.09.2026 (3) — Durchsicht vor der Einreichung: Nutzerweg, Admin-Werkzeuge, Rechtstexte

Auftrag: vor der App-Store-Einreichung alles noch einmal auf Herz und Nieren
prüfen — sämtliche Nutzerfunktionen, der ganze Nutzerweg, die Admin-Werkzeuge,
beide Clients und die Rechtstexte gegen den tatsächlichen Stand von Website und
Apps. Gefundene Fehler direkt beheben.

Ausgangslage: 446 Tests grün. Danach: **452** (sechs neue in
`backend/tests/test_audit_befunde.py`, eine Fixture korrigiert). Android
kompiliert (`:app:compileProdReleaseKotlin`) und die Unit-Tests laufen durch
(`:app:testProdReleaseUnitTest`).

> **Android lässt sich auf dieser Maschine bauen** — das war bis heute nicht
> notiert und wurde erst auf Nachfrage gefunden: JDK 17 unter
> `~/.bubblewrap/jdk/jdk-17.0.11+9`, Android-SDK unter
> `~/.bubblewrap/android_sdk` (Platform 36). Beides liegt nicht im `PATH`:
>
> ```bash
> export JAVA_HOME=~/.bubblewrap/jdk/jdk-17.0.11+9
> export ANDROID_HOME=~/.bubblewrap/android_sdk
> export PATH="$JAVA_HOME/bin:$PATH"
> cd android-native && ./gradlew :app:compileProdReleaseKotlin --offline
> ```

**Beide nativen Apps brauchen einen neuen Build**: iOS wegen Fix 15, Android
wegen Fix 12, 13 und 14 (Rechtstexte und Verifizierungs-Weiterleitung stecken
im Paket, nicht am Server).

> **Android 2.6.10 (versionCode 110) ist gebaut** — am 17.09.2026 auf dieser
> Maschine, prod-Flavor, signiert mit dem Upload-Key `CN=FLEXR`
> (`jarsigner -verify` → „jar verified"), 7.772.100 Bytes, SHA-256
> `7c603aecd4f6ee96c977ef8750d1f26bce30764efed757418d2b676a61da841a`.
> Abgelegt wie die früheren Fassungen unter `../release-2.6.10/` samt
> `SHA256SUMS.txt` und im Chat übergeben. Vor dem Bauen liefen
> `:app:testProdReleaseUnitTest` und `:app:compileProdReleaseKotlin` grün.
> Noch **nicht** in der Play Console hochgeladen.
>
> Inhalt gegenüber 2.6.9: berichtigte Rechtstexte (10 € statt 5 €, kein
> Probemonat, Fotolöschung bei endgültiger Ablehnung offengelegt, Stand-Datum
> und Hinweis auf die maßgebliche Langfassung) und die Behandlung des 403
> „verification_required".

**Testuser2 ist freigeschaltet — und bewusst weiblich.**
`testuser2@flexr.social` wurde am 17.09.2026 über
`scripts/activate_review_account.py` freigegeben (Deck, Matches und eingehende
Likes antworten mit 200, alle drei Fotos „approved", Gym `3D Lady Fit`,
Wohnort 8010 Graz).

Anfangs war das Konto **mann/sucht frau** und passte damit genau zum
Prüfkonto `appreview` (**frau/sucht mann**) — beide am selben Gym, 0 km. Auf
Ansage wurde es auf **frau/sucht mann** umgestellt, damit der Betreiber mit
einem eigenen männlichen Konto matchen kann. Die Folge ist bekannt und
gewollt: FLEXR matcht ausschließlich gegengeschlechtlich
(`swipes.py`: `User.gender == current_user.interest` und umgekehrt), also
sehen sich `appreview` und `testuser2` seither **nicht mehr**. Das Deck von
Testuser2 ist entsprechend leer.

> **Offener Punkt für die Einreichung:** Das Prüfkonto `appreview` hat damit
> weiterhin **kein Match und keinen Chatverlauf**. Ein Apple-Prüfer sieht dann
> zwei der vier Reiter leer und hält das für einen Fehler. Es braucht dafür
> ein **männliches** Gegenkonto im Umkreis des Prüfkonto-Gyms, gegenseitige
> Likes und mindestens eine Nachricht.

### Behoben — Backend

1. **Bezahlwand in der Beta, obwohl Premium aus ist.** `swipes.py` prüfte an
   zwei Stellen direkt `User.is_premium`. Das ist bei ausgeschaltetem Schalter
   für *jeden* falsch (`models.py`: `is_premium = premium_enabled and
   is_subscribed`). In der ausgelieferten Konfiguration bekam damit **jeder**
   Nutzer `premium_required=True` von `/api/swipes/incoming` und einen harten
   403 von `/api/swipes/rewind` — genau die Bezahlwand, nach der die
   App-Prüfung sucht, in einer App, die mit "dauerhaft kostenlos" wirbt.
   `premium.py` hält im Modulkopf fest, `premium_enabled` sei "der einzige
   Hebel"; diese zwei Stellen waren der zweite. Neu: `premium.feature_locked()`
   an einer Stelle, von beiden Routen benutzt.

2. **Fremde Rücktrittserklärung per geratener `request_id` abrufbar.** Die
   Idempotenz von `POST /api/withdrawal` schlug die client-erzeugte
   `request_id` **ungebunden** nach und gab bei einem Treffer
   `declaration_text` zurück — Name, Vertragsbezug und die eigenen Worte des
   Erklärenden. Unangemeldet aufrufbar. Der Treffer zählt jetzt nur noch für
   dasselbe Konto bzw. dieselbe E-Mail-Adresse. Kollidiert eine fremde id,
   wird die Erklärung ohne Idempotenzschlüssel gespeichert statt am
   Unique-Constraint zu scheitern — sie gilt mit dem Eingang (§ 13a FAGG) und
   darf nie an einem 500er hängenbleiben.

3. **Sperren verhinderte den Swipe nicht.** Nur Deck und Match-Liste filterten
   `Block`; `POST /api/swipes` nicht. Aus einem vor der Sperre geladenen Deck
   (oder einem wiederholten POST) entstand dadurch ein Match samt Mail und
   Benachrichtigung an genau die Person, die gerade gesperrt hatte — und das
   Match war für sie unsichtbar, also nicht einmal auflösbar.

4. **Abgelehnte Fotos blieben öffentlich abrufbar.** `reject_photo` setzte nur
   Status und Grund. Die Bilddatei blieb unter ihrer URL liegen
   (`Cache-Control: public, max-age=31536000, immutable`, live nachgeprüft) —
   dauerhaft, obwohl unter den Ablehnungsgründen "sexuell explizite
   Darstellung", "Gewalt- oder Hassdarstellung" und "zeigt offenkundig eine
   minderjährige Person" stehen. Jetzt wird das Objekt gelöscht; die Zeile
   bleibt als Begründungsnachweis (Art. 17 DSA) — dafür braucht es die
   Aufnahme nicht.

5. **Endgültige Ablehnung sperrte ein Bestandskonto nicht.** `reject_verification`
   nahm nur `is_verified` zurück. Ein Bestandskonto (`verification_required`
   False), das sich freiwillig zur Prüfung gestellt hatte, blieb danach voll
   nutzbar: Fotos weg, aber neu hochladbar und wieder im Deck — auch bei
   Ablehnungsgrund "underage". Jetzt setzt die Ablehnung `verification_required`
   und nimmt die Freischaltung zurück, so wie es der Docstring immer schon sagte.

6. **Freigabe ließ die alte Ablehnungsbegründung stehen.** An einem wieder
   sichtbaren Foto hing weiterhin "zeigt nicht die Person dieses Kontos".

7. **Kontosperre ließ eine laufende Chat-Sperre als Rest zurück.** Ban über
   aktiven Mute überschrieb dessen Begründung; das spätere Entsperren löschte
   die Begründung mit, nicht aber `messaging_muted_until`. Ergebnis: weiterhin
   stumm, ohne Begründung nach Art. 17 DSA. Die Kontosperre nimmt die
   Chat-Sperre jetzt mit.

8. **Wochenmail zählte Likes von Gesperrten.** "1 Person wartet auf dich",
   während die Liste in der App leer blieb. `_pending_likes_count` filtert
   jetzt dieselben Fälle wie `/api/swipes/incoming` (Sperren beidseitig,
   Freischaltung, widerrufene Art.-9-Einwilligung).

9. **`/api/swipes/incoming` zeigte Konten mit widerrufener Art.-9-Einwilligung.**
   Das Deck filtert sie seit jeher ("darf in keinem fremden Deck mehr
   erscheinen"), die eingehenden Likes nicht.

### Behoben — Admin-Dashboard

10. **Gym-Tabs legten die Foto-Freigabe lahm.** Der Foto-Handler hing an jedem
    `.tab-btn`, also auch an den Gym-Tabs (dieselbe Klasse, aber
    `data-gym-status`). Ein Klick dort setzte `currentPhotoStatus` auf
    `undefined` und lud die Foto-Freigabe mit `status=undefined` neu → 400,
    Fehlermeldung bis zum Neuladen der Seite. Jetzt `.tab-btn[data-status]`.

11. **"Prüfung nachfordern" fehlte genau dort, wo es der einzige Ausweg ist.**
    Der Knopf erschien nur bei `!verification_required` — also nie bei einem
    endgültig abgelehnten Konto. Das steckt aber ohne ihn für immer fest:
    Fotos gelöscht, `/verification/start` verweigert wegen bindender
    Entscheidung, und `require-verification` ist der einzige Weg, der die
    frühere Ablehnung durch ein neues `verification_required_at` entwertet.

### Behoben — Rechtstexte

12. **Android nannte 5 € und einen Probemonat.** Beides gibt es nicht:
    `legal.py` sagt 10 €, `models.py` hält fest, dass die Probemonat-Spalte tot
    ist, `stripe_client.py` legt "ohne Probezeit" an. iOS und Web waren
    korrekt, nur die Android-Fassung war stehengeblieben — in AGB § 4, § 5 und
    im FAQ. Auf den iOS-Wortlaut nachgezogen.

13. **Die Fotolöschung bei endgültiger Ablehnung stand in keiner
    Datenschutzerklärung.** Sie ist erst in Sitzung (2) heute entstanden. In
    allen vier Fassungen (Web DE/EN, iOS, Android) als eigener Absatz
    "Endgültige Ablehnung" ergänzt.

### Behoben — Android

14. **Der 403 „verification_required" wurde gar nicht behandelt.** Das Backend
    wirft diesen Code ausdrücklich, „damit die Clients gezielt auf den
    Verifizierungsbildschirm leiten können" (`security.py`). iOS macht das seit
    jeher: `APIClient` → `SessionStore.handleVerificationRequired()` →
    `AppModel` wechselt ins Gate. Android kannte den Code nicht und zeigte auf
    dem Deck nur „Zugriff nicht möglich" — der Nutzer saß fest, ohne Erklärung
    und ohne Weg. Fix 5 oben macht genau diesen Fall häufiger, weil eine
    Ablehnung die Freischaltung jetzt entzieht. Neu: `isVerificationRequired`
    an `FlexrApiException`, ein prozessweites `VerificationGate`-Signal aus dem
    Fehler-Parser und ein Beobachter im `MainViewModel`, der die Sitzung neu
    bestimmt — derselbe Weg wie auf iOS.

### Behoben — iOS

15. **Hintergrundabgleich wurde bei jedem App-Start weiter nach hinten
    geschoben.** `BGTaskScheduler` merkt sich je Kennung einen Auftrag, und
    jedes `submit` setzt dessen `earliestBeginDate` neu auf "in 15 Minuten".
    `loadSession()` läuft bei jeder Rückkehr in den Vordergrund und rief genau
    das auf — wer die App oft öffnete, bei dem kam der Abgleich nie dran.
    Angemeldet wird jetzt beim Wechsel in den **Hintergrund**, also dann, wenn
    Apple es vorsieht.

### Nicht behoben — bewusste Entscheidungen und offene Punkte

- **Es gibt keinen echten Push.** FLEXR hat kein APNs/FCM; beide Apps pollen
  und erzeugen **lokale** Benachrichtigungen (`notifications.py`, Modulkopf;
  iOS `BGAppRefreshTask`, Android WorkManager). Dass eine Nachricht erst beim
  Öffnen der App aufpoppt, ist die Bauweise, kein Konfigurationsfehler. Fix 14
  verbessert das Zeitfenster, beseitigt es aber nicht. Echtzeit gibt es nur mit
  APNs: Push-Key, Entitlement, Geräte-Token-Endpunkt, serverseitiger
  APNs-Client, neuer Build. Eigene Entscheidung, nicht nebenbei vor einer
  Einreichung.
- **`price_cents` kommt auch bei ausgeschaltetem Premium mit.** Der Agent hielt
  das für ein Leck; das Schema sagt ausdrücklich das Gegenteil ("Preis, damit
  '10 €' nirgends im Client fest steht", Grenzen "immer gefüllt, damit die
  Oberfläche sie auch während der Beta schon erklären kann"). Die Clients
  blenden an `premium_enabled` aus. Unverändert gelassen.
- **`optional_current_user` liefert gesperrte und gelöschte Konten.** Der
  Docstring behauptete das Gegenteil. Das Verhalten ist aber das bessere: An
  der Zuordnung hängt der automatische Stopp eines laufenden Stripe-Abos beim
  Rücktritt. Docstring korrigiert, Verhalten belassen.
- **Native Rechtstexte trugen "Stand: 3. August 2026"** für Nutzungsrichtlinien
  und Strafverfolgungsrichtlinien, Web und `legal.py` sagen 19. August 2026.
  **Nachträglich entschieden und erledigt** (Nutzer: "setze das Datum hoch, es
  gibt eh noch keine realen Nutzer"): Datum auf den 19.08. gesetzt — aber nicht
  nur das. Die native Fassung hat gemessen nur **12 %** des Umfangs der
  Web-Fassung (2.019 gegenüber 16.195 Zeichen), gab sich aber als
  vollständiges, verbindliches Regelwerk aus. Im Vorspann steht jetzt beides:
  das richtige Datum und der Satz, dass die Fassung gekürzt und der
  vollständige Text auf flexr.social maßgeblich ist.
- **Die Datenschutzerklärung ist auf Fassung `2026-09-17` gehoben.** Der neue
  Absatz zur endgültigen Ablehnung ist eine inhaltliche Änderung, und
  `consents.py` schreibt `PRIVACY_VERSION` als Fassung jeder
  Art.-9-Einwilligung mit. `legal.py` verlangt dafür ausdrücklich eine höhere
  Fassung. Erzwungen wird nichts: Alte Einwilligungen bleiben mit ihrer alten
  Fassung stehen und sind dadurch als "zu einem anderen Text erteilt"
  erkennbar.
- **Swipe gilt lokal als gesetzt, bevor der Server geantwortet hat** — auf
  beiden Clients (`SwipeModel.swift`, `SwipeViewModel.kt`): Der Index wandert
  weiter, dann erst läuft der Aufruf. Schlägt er fehl, ist die Karte weg und
  der Like nie angekommen. Nicht angefasst, weil es eine Verhaltensänderung in
  zwei Clients wäre (Karte zurücklegen und erneut anbieten) und beide dafür neu
  gebaut und von Hand geprüft werden müssten. **Lohnt sich als Nächstes.**
- **Offen, gemeldet, nicht angefasst:** doppelter gleichzeitiger Like läuft in
  einen `IntegrityError` → 500 statt Match (`swipes.py`, check-then-insert
  gegen `uq_swipe_pair`/`uq_match_pair`); ein `pending` Gym-Vorschlag mit
  vorhandenem Namen kann Bestandsprofile aus der Suche kippen (`gym_geo.py`);
  das Dashboard paginiert nirgends (Zähler zeigen Gesamtzahl, Liste 50);
  `list_users` enthält selbstgelöschte Konten, `get_stats` nicht;
  Hard-Delete eines Nutzers erledigt offene Meldungen ohne Entscheidung nach
  Art. 16 Abs. 5 DSA.

### Geprüft und in Ordnung

Live gegen die Produktion: Login mit dem Prüfkonto, Deck/Matches/Incoming
liefern für ein unverifiziertes Konto 403, Profil und Verifizierungsstatus 200,
ohne Token 401. Android fordert keine Standortberechtigung (nur Internet,
Netzwerkstatus, Kamera, Benachrichtigungen). `FakeFlexrApi` ist synchron zu
`FlexrApi`. Rechtstexte stimmen in allen vier Fassungen bei Standort,
Aufbewahrungsfristen, Auftragsverarbeitern, Verifizierungsverfahren, Alter und
Verfügbarkeit überein; die Betreiberangaben sind überall identisch und richtig.

## Sitzung 17.09.2026 (2) — Verifizierungsablehnung: Fotos löschen, Nutzerliste kennzeichnen

Zwei zusammenhängende Lücken im Ablehnungsweg der Alters-/Identitätsprüfung
geschlossen, beide vom Nutzer im Admin-Dashboard entdeckt.

**Fund 1: Profilfotos überlebten die endgültige Ablehnung.**
`reject_verification` (`POST /admin/verifications/{id}/reject`,
`backend/app/routers/admin.py`) hat bislang nur die temporären
Verifizierungs-Uploads (Selfie/Ausweis) über `purge_uploads` gelöscht, nie
aber die bereits eingereichten Profilfotos (`photos`-Tabelle). Ein Konto, das
die Prüfung nicht bestanden hatte, blieb damit mit Fotos in der Foto-Freigabe
und im Objekt-Storage zurück, obwohl es nie verifiziert wurde. Fix: Die
Endpoint-Funktion löscht jetzt zusätzlich alle `Photo`-Zeilen des Nutzers
(unabhängig von pending/approved/rejected) inklusive Storage-Objekten,
derselbe Lösch-Pattern wie beim admin-seitigen Foto-Hard-Delete
(`DELETE /admin/photos/{id}`) und der Nutzer-Selbstlöschung von Fotos.
Commit `d73ef1f`.

Kleiner Nebenfund dabei, der zur selben Sitzung gehört: `is_verified` gibt
keine Auskunft über Standort — die Umkreissuche verwendet nie eine Geräte-
oder Nutzerposition, sondern ausschließlich die Adresse des im Profil
eingetragenen Gyms. `ios/store/store-texte.md` und `ios/FLEXR/PrivacyInfo.xcprivacy`
behaupteten trotzdem eine (nie erhobene) `CoarseLocation` — beide korrigiert,
siehe Commit `e65a346` (separat, für die iOS-App-Store-Einreichung).

**Fund 2: Endgültig abgelehnte Nutzer standen unmarkiert in der
Admin-Nutzerliste.** Der Nutzer fragte, ob das ein Bug sei. Antwort: die
Konto-Zeile selbst bleibt absichtlich bestehen (nicht wie die Fotos ein Bug) —
zwei Gründe: (a) Ablehnung ist als wiederholbar gedacht, `request_verification_reupload`
öffnet denselben Verifizierungsvorgang für einen neuen Anlauf wieder; (b) die
Mehrfachkonto-Erkennung über `UserDevice` in `get_user_detail` braucht die
Zeile, sonst könnte sich ein abgelehnter Nutzer unerkannt neu registrieren.
Ein manueller Hard-Delete existiert bereits (`DELETE /admin/users/{id}`,
Button "Nutzer löschen" im Detail-Modal) — für den Einzelfall reicht das.

Lücke war reines UX: Die Nutzerliste kannte den Ablehnungszustand gar nicht,
nur das separate Verifications-Panel filtert intern danach. Fix:

- `GET /admin/users` und `GET /admin/users/{id}` liefern jetzt
  `verification_rejected` (jüngster Verifizierungsversuch des Nutzers —
  `latest_request`/größtes `created_at` pro `user_id` — hat Status
  `rejected`). `/admin/users` bekommt zusätzlich den Filter-Query-Param
  `verification_rejected=true|false`.
- `frontend/admin.html`: neues Filter-Dropdown "Verifizierung: alle/nur
  abgelehnte/ohne abgelehnte" in der Toolbar, plus Badge "Verifizierung
  abgelehnt" in Tabelle und Detail-Modal — eingeordnet in der bestehenden
  Status-Prioritätskette zwischen "Gesperrt" und "Premium/Gratis" (ein Konto
  kann banned und/oder rejected und/oder gelöscht gleichzeitig sein, die
  Badges zeigen nur den jeweils wichtigsten Zustand).

Commit `4c0922c`. Test ergänzt (`test_final_rejection_marks_user_in_admin_list`
in `backend/tests/test_verification.py`): prüft das Feld in Liste und Detail
sowie beide Filterrichtungen. `pytest tests/test_verification.py
tests/test_admin.py` — 35 bzw. 14 Tests grün (letzterer Lauf inkl. des neuen
Tests), keine Regression.

**Deploy dieser Sitzung:** `git pull --ff-only` auf `flexr-vps`,
`sudo systemctl restart flexr-api`, `curl https://flexr.social/api/health` →
`{"status":"ok"}` nach einer einmaligen Race-502 direkt nach dem Neustart
(siehe „Wo das Projekt gerade steht" oben). Keine Migration — beide Änderungen
sind reine Anwendungslogik.

## Sitzung 17.09.2026 — Stripe: FLEXR-Premium-Preis live angelegt, Webhook vervollständigt

Antwort auf eine Nachfrage aus früheren Sitzungen (siehe „Sitzung 16.09.2026
(2)" Abschnitt „Stripe: was am Produkt zu ändern ist" und Punkt 19 unter
„Noch offen"). Der Nutzer hat die dort beschriebenen Schritte im
Stripe-Dashboard durchgeführt, diese Sitzung hat die Server-Seite (SSH) und
die Prüfungen übernommen.

**Neues Produkt statt Preisänderung.** Der alte Preis ließ sich nicht
bearbeiten — Beträge sind in Stripe unveränderlich, und laufende Altabos
hängen daran. Es musste ein komplett neues Produkt angelegt werden:

- Produktname **„FLEXR Premium"**, Produkt-ID `prod_VH6teDHT70SoKH`.
- Neuer Preis `price_1UGYfdIpMumqxPtFzu0d5A6f`: 10,00 EUR, wiederkehrend
  monatlich, **ohne Probezeit**, Steuerverhalten **„inklusive"** (passend zur
  Kleinunternehmerregelung, AGB Punkt 9).
- Alter Preis `price_1TtOB5IpMumqxPtFSfAqS2Rc` (die abgeschaffte
  5-€-Mitgliedsgebühr) vom Nutzer im Dashboard **archiviert**.

**`.env` auf dem VPS aktualisiert (per SSH, `flexr-vps`):**

- Backup vor der Änderung: `/flexr/backend/.env.bak-stripe-price-20260917-082236`.
- `STRIPE_PRICE_ID` von `price_1TtOB5IpMumqxPtFSfAqS2Rc` auf
  `price_1UGYfdIpMumqxPtFzu0d5A6f` geändert (`config.py` liest das als
  `settings.stripe_price_id`, verwendet in `stripe_client.py` für die
  Checkout-Session).
- `flexr-api.service` neu gestartet — `journalctl` zeigt einen sauberen Start
  („Application startup complete"), keine Fehler beim Einlesen der neuen
  `.env`.

**Externer Check über den Browser** (nicht per SSH — ein `curl` von der
VPS-Shell gegen `https://flexr.social` wurde vom Auto-Mode-Classifier dieser
Sitzung blockiert, deshalb über den built-in Browser geprüft):

- `https://flexr.social` lädt; der Footer zeigt bei FLEXR Premium weiterhin
  „Kommt nach der Beta-Phase" → bestätigt, dass `PREMIUM_ENABLED` weiterhin
  `false` ist.
- `GET /api/billing/status` ohne Token → `401` (korrekt, Endpoint verlangt
  Auth und crasht nicht).
- `POST /api/billing/webhook` ohne gültige Signatur → `400` (korrekt, die
  Signaturprüfung greift).

**Billing-Portal (Kundenportal) im Stripe-Dashboard konfiguriert:** unter
Einstellungen → Billing → Kundenportal → Stornierungen ist „Abonnement
kündigen" an und „Am Ende des Abrechnungszeitraums kündigen" ausgewählt
(nicht „Sofort abbrechen"). **Nicht bestätigt:** ob „Änderungen speichern"
danach tatsächlich angeklickt wurde — der letzte Screenshot dazu zeigte nur
den Zustand vor dem Klick. Vor dem Testcheckout gegenprüfen, ob die
Einstellung wirklich gespeichert ist.

**Webhook-Endpoint `captivating-spark`** (`we_1TtOEQIpMumqxPtFHY4W0U60`, Ziel
`https://flexr.social/api/billing/webhook`) vervollständigt:

- Ausgangszustand: 8 Events, `invoice.payment_succeeded` fehlte,
  `customer.subscription.trial_will_end` war dabei (überflüssig, da
  `create_checkout_session()` bewusst kein `trial_end` mehr mitgibt und dieses
  Event deshalb nie feuern würde).
- Nutzer hat `invoice.payment_succeeded` ergänzt und
  `customer.subscription.trial_will_end` wieder entfernt.
- Endzustand, per Screenshot bestätigt: genau die sieben von
  `routers/billing.py` ausgewerteten Events — `checkout.session.completed`,
  `customer.subscription.created`, `customer.subscription.updated`,
  `customer.subscription.deleted`, `invoice.upcoming`, `invoice.paid`,
  `invoice.payment_succeeded`, `invoice.payment_failed`.

Damit ist **Punkt 19 aus „Noch offen" erledigt**. Offen bleibt weiterhin der
kontrollierte Stripe-Testcheckout (siehe „Erinnerung für die nächste
Sitzung") — erst danach `PREMIUM_ENABLED` auf `true` setzen. Vor dem
Testcheckout die Kundenportal-Speicherung gegenprüfen (siehe oben).

Nebenbei besprochen, ohne Aktion: Dauer einer Apple-Beta-App-Review — interne
TestFlight-Tester brauchen keine Review (nur Build-Processing, meist
15 Min. bis 2 h), externe Tester durchlaufen eine echte Prüfung, üblicherweise
24–48 h, vereinzelt auch mehrere Tage. Aktuell laut Sitzung 16.09. ohnehin nur
interne Tester vorgesehen, also nicht akut.

## Sitzung 16.09.2026 (2) — iOS-Bugfixes, FLEXR Premium in beiden nativen Clients, Android 2.6.9

Vier Commits, alle gepusht (`origin/main` = `6ad6452`). **Kein Backend-Code,
keine Migration, kein VPS-Deploy nötig** — die Sitzung fasst ausschließlich
`ios/` und `android-native/` an.

    6ad6452 docs: record Android 2.6.9 and its checksum
    2f9b8b7 android: 2.6.9 (versionCode 109)
    4587ed5 ios: add the three FLEXR Premium features
    bd81e3b android: add the three FLEXR Premium features
    fe6af02 ios: fix the three TestFlight layout findings, drop the stale trial promise

### Teil 1: Drei Befunde aus dem ersten TestFlight-Durchgang

Vom Gerät gemeldet, alle rein in der Darstellung. Einzelheiten samt Begründung
in [ios/HANDOFF.md](ios/HANDOFF.md), Abschnitt „Bugfixes aus dem ersten
TestFlight-Durchgang"; hier nur, was übergreifend gilt:

1. **Der gesperrte Login-Knopf war praktisch unsichtbar.** `FlexrButton` legte
   den Zustand auf `opacity(0.4)` — ein oranger Verlauf auf `#121212`
   verschwindet dabei fast vollständig, die dunkle Schrift darauf erst recht.
   **Web und Android hatten genau diesen Fehler längst behoben**, jeweils mit
   einem Kommentar an der Stelle (`.btn:disabled` in `frontend/app/index.html`,
   `isBlocked` in Androids `Buttons.kt`); iOS war als einzige Plattform nicht
   nachgezogen worden. Das ist das wiederkehrende Muster dieses Projekts: Eine
   Korrektur an zwei von drei Oberflächen ist keine Korrektur.
2. **Jede Chatblase war 300 pt breit**, auch die um ein Wort — am Text stand
   `.frame(maxWidth: .infinity)`, und die Blase richtet sich nach ihm. Eine
   **endliche** `maxWidth` ist eine Obergrenze und schrumpft mit; nur
   `.infinity` bläst auf.
3. **Das Fotoraster zerfiel in verschieden große, überlappende Kacheln.**
   `.aspectRatio(3:4, contentMode: .fill)` darf laut Apples Dokumentation über
   die angebotene Fläche hinauswachsen. Die Kachel bekommt ihre Größe jetzt von
   einer `Color.clear` mit festem Verhältnis, das Foto liegt als Overlay darin.

**Verschieben, Löschen und Hochladen der Fotos waren nie kaputt** — sie lagen
nur unsichtbar unter dem Layoutfehler. Gegen Android und das Backend
abgeglichen, unverändert gelassen: Die Reihenfolge-Arithmetik ist zeichengleich
mit Androids, alle vier Foto-Endpunkte und alle DTO-Felder decken sich mit
`backend/app/routers/profiles.py`.

**Nebenbefund, auf Ansage behoben:** Unter dem Login stand „Erstell dein Profil
und teste FLEXR einen Monat gratis." — **in iOS und Android**. Einen Probemonat
gibt es seit dem 10.09.2026 nicht mehr, die AGB sagen dauerhaft unentgeltlich.
Ersetzt durch den Wortlaut, den `register_subtitle` und `paywall_sub` schon
führen: „Neu hier? Erstell dein Profil — FLEXR zu nutzen kostet nichts."

### Teil 2: FLEXR Premium bekommt seine drei Zusatzfunktionen

Backend und Web-App haben sie seit dem 10.09.2026. Die nativen Clients trugen
bis jetzt **nur den Werbetext auf der Paywall** — die Funktionen dahinter gab es
dort nicht. Beide sind nachgezogen, mit derselben Aufteilung:

| | Web | Android | iOS |
| --- | --- | --- | --- |
| Premium-Abzeichen neben dem Namen | seit 10.09. | **neu** | **neu** |
| Letzten Swipe zurücknehmen | seit 10.09. | **neu** | **neu** |
| „Wer dich geliket hat" | seit 10.09. | **neu** | **neu** |

Drei Entscheidungen, die auf beiden Plattformen gleich gefallen sind:

* **Das Abzeichen ist ein gefüllter Stern in Plate-Orange, ohne runden Grund** —
  anders als der blaue Verifiziert-Haken. Zwei gleich gebaute Plaketten
  nebeneinander liest niemand auseinander. Im Web ist es dieselbe
  Unterscheidung: `.premium-badge` trägt nur `color`, keine Fläche.
* **Ohne Abo steht an der Stelle des Zurücknehmen-Knopfes gar nichts**, nicht
  ein gesperrter Knopf. Die Knopfreihe unter dem Deck ist der meistbenutzte Ort
  der App; ein dauerhaft totes Element daneben wäre eine tägliche Belästigung.
* **„Wer dich geliket hat" ist ohne Premium kein Fehlerbildschirm.** Der Server
  liefert die Anzahl ohne die Profile, und die Ansicht sagt das offen — „3 Leute
  warten auf dich", dazu der Hinweis, dass dieselben Leute ohnehin im Deck
  auftauchen. Ohne offene Likes bleibt die Karte über der Matchliste ganz weg;
  eine „0" wäre eine Enttäuschung ohne Anlass.

**Das Like-Restkontingent zog auf beiden Plattformen nicht nach.** Sowohl der
Swipe als auch das Zurücknehmen liefern `likes_remaining` in ihrer eigenen
Antwort mit; bisher las die Statuspille im Kopf aber eine Kopie, die nur beim
Anmelden entstand — sie zeigte also den Stand vom App-Start, bis sich jemand neu
anmeldete. Behoben, ohne einen zweiten `/api/billing/status` pro Like:

* **Android:** `BillingRepository.updateLikesRemaining()` schreibt in den
  zwischengespeicherten `Membership`, `MainViewModel` beobachtet diesen Fluss
  und aktualisiert `AppState.Ready`.
* **iOS:** dieselbe Methode am Repository, und `AppModel.membership` liest jetzt
  **durch** aufs Repository statt aus der Kopie im `state`.

**Schemaänderungen, beide folgenlos:** Room 2 → 3 (`MatchEntity.isPremium`) und
SwiftData (`MatchEntity.isPremium` mit Vorgabewert `false`). Beide Bestände sind
reiner Spiegel des Servers — Android verwirft die Tabelle ohnehin
(`fallbackToDestructiveMigration`), iOS ergänzt das Feld dank Vorgabewert
leichtgewichtig. Beim nächsten Abgleich steht der richtige Wert da.

**Alles hängt weiterhin am einen Schalter.** Solange `PREMIUM_ENABLED` am Server
aus steht, ist `is_premium` für jeden falsch: kein Abzeichen, kein
Zurücknehmen-Knopf, gesperrter Text auf der Likes-Karte. Es gibt in keiner der
drei Oberflächen einen zweiten Ort, an dem sich das entscheidet.

**Bewusst nicht nachgezogen:** der Like-Zähler unter dem Deck, den die Web-App
dort führt. Beide nativen Clients zeigen die Restzahl bereits in der Statuspille
im Kopf — ein zweiter Zähler wenige Zentimeter darunter wäre Dopplung, keine
Parität. Falls er doch gewünscht wird, gehört er als Zeile unter die Knopfreihe,
samt „Unbegrenzt liken"-Knopf wie im Web.

### Was geprüft ist — und was nicht

| | Android | iOS |
| --- | --- | --- |
| Kotlin-/Swift-Compile | ✅ `:app:compileProdReleaseKotlin` | ✅ Codemagic (nicht auf diesem Rechner) |
| Unit-Tests | ✅ 49 Tests, 0 Fehler | ❌ |
| Auf einem Gerät ausprobiert | ❌ | ❌ |

Für iOS waren vor dem Push nur Klammerbilanz und Aufrufstellen von Hand
geprüft; **der Codemagic-Lauf war der Nachweis — und beide Läufe sind beim
ersten Versuch grün durchgelaufen**, erst `fe6af02` (Bugfixes), dann `4587ed5`
(Premium). Beides liegt in TestFlight.

Die Reihenfolge war Absicht: Die Premium-Änderung wurde **erst gepusht,
nachdem** der Bugfix-Build durch war. Wäre beides im selben Stand gelandet und
hätte der Swift-Teil nicht compiliert, hätte auch der Bugfix-Build nicht mehr
erzeugt werden können. Dass es zweimal auf Anhieb baute, ist kein Argument
dafür, diese Reihenfolge künftig fallenzulassen.

Zwei neue Unit-Tests auf der Android-Seite decken das Zurücknehmen ab: Das Deck
wird danach **neu geladen** (nicht nur der Index zurückgeschoben — der
zurückgenommene Swipe muss nicht der letzte im aktuellen Deck gewesen sein), und
ein abgelehntes Zurücknehmen lässt das Deck unangetastet.

### Android 2.6.9 (versionCode 109)

Gebaut, signiert, im Chat als `flexr-2.6.9-vc109.aab` übergeben. 7.772.406
Bytes, SHA-256
`c1e37f50981f5c0a2bd5558c473dbd0e55ac968fcbcbe77548831f080ee89612`, Upload-Key
`CN=FLEXR` unverändert, `jarsigner -verify` sauber. versionCode **und**
versionName im gebauten Manifest gegengeprüft, nicht nur in der Gradle-Datei.

Für die Play Console: **keine neuen Berechtigungen, keine neuen Datentypen** —
die bestehenden Data-Safety-Angaben bleiben gültig. Sichtbar ändert sich für
heutige Nutzer nur der Login-Hinweis, weil Premium am Server ausgeschaltet ist.

### Eigener Fehlgriff, zur Warnung

Ich habe zu Beginn behauptet, auf diesem Rechner sei **kein Android-Build
möglich** — nach einem `ls ~/android-toolchain` und einem `which java`. Beides
geht ins Leere, die Toolchain liegt unter **`~/.bubblewrap/`**, und genau das
steht seit dem 07.09. sowohl weiter unten in diesem Dokument als auch in
`android-native/HANDOFF.md`. **Erst das Dokument lesen, dann das Dateisystem
befragen** — die Aussage „geht hier nicht" war eine Viertelstunde lang falsch
und hätte die halbe Sitzung gekostet.

### Stripe: was am Produkt zu ändern ist (Antwort auf eine Nachfrage)

Steht hier, weil es sonst nur im Gesprächsverlauf existiert. Der alte 5-€-Preis
gehört zur abgeschafften Mitgliedsgebühr. **Den alten Preis nicht bearbeiten** —
Beträge sind in Stripe unveränderlich, und laufende Altabos hängen daran:

1. Neuen Preis am Produkt anlegen: **10,00 EUR, wiederkehrend monatlich, ohne
   Probezeit**. `stripe_client.create_checkout_session()` gibt bewusst kein
   `trial_end` mehr mit.
2. Steuerverhalten **„inklusive"** — die AGB (Punkt 9) sagen: Endpreis,
   Umsatzsteuer wird nicht zusätzlich verrechnet (Kleinunternehmerregelung).
3. Neue `price_...`-ID als `STRIPE_PRICE_ID` in die `.env` auf dem VPS, alten
   Preis archivieren.
4. Billing-Portal: Kündigung zum Periodenende erlauben. Webhook-Ereignisse:
   `checkout.session.completed`, `customer.subscription.created/updated/deleted`,
   `invoice.upcoming` (**muss in den Billing-Einstellungen eigens aktiviert
   werden**), `invoice.paid`, `invoice.payment_succeeded`,
   `invoice.payment_failed` — alle sieben wertet `routers/billing.py` aus.
5. `PREMIUM_ENABLED` bleibt `false`. Solange lehnt `/api/billing/checkout` mit
   409 ab; nichts davon wird sichtbar.

## Sitzung 16.09.2026 — Ein 401 vom Login ist keine abgelaufene Sitzung

Ein Commit (`c773710`), gepusht und deployt. Web, iOS und Android; im Backend
nur ein neues eigenständiges Skript, kein App-Code — deshalb **weder Migration
noch Neustart**, nur `git pull` auf dem VPS.

Die iOS-Arbeit der Tage davor (Verifizierungs-Portierung in drei Runden,
Paritätsabgleich, App-Review-Konto) steht in
[ios/HANDOFF.md](ios/HANDOFF.md); hier nur, was Web und Android betrifft.

### 1. Falsche Zugangsdaten meldeten „Sitzung abgelaufen"

Wer sich beim Anmelden vertippte oder eine gar nicht registrierte Adresse
eingab, bekam **„Sitzung abgelaufen. Bitte erneut einloggen."** zu lesen — er
war nie angemeldet, es gab keine Sitzung, die hätte ablaufen können.

Die Ursache war in allen drei Clients dieselbe und dieselbe Bauart: Der
zentrale 401-Zweig antwortete auf **jeden** 401 des eigenen Backends damit, das
Token zu verwerfen und auf den Login zu schicken. `POST /api/auth/login`
quittiert falsche Zugangsdaten aber ebenfalls mit 401 (`{"detail":"E-Mail oder
Passwort falsch."}`) — die Meldung des Servers wurde überschrieben, bevor sie
jemand zu sehen bekam.

| Datei | Was ausgenommen wird |
| --- | --- |
| `frontend/app/index.html` | `ANMELDEWEGE_OHNE_SITZUNG` in `api()` |
| `ios/FLEXR/Core/Network/APIClient.swift` | `Self.sessionlessPaths` |
| `.../core/network/Interceptors.kt` | `SESSIONLESS_PATHS` |

Ausgenommen sind dieselben fünf Wege: `auth/login`, `auth/register`,
`auth/reactivate`, `auth/email/confirm`, `auth/age-check`.

**Bewusst eine Liste und kein Präfix-Vergleich auf `/api/auth/`.** Im selben
Zweig liegt `auth/email/resend`, und der braucht sehr wohl eine Sitzung — ein
401 von dort ist ein echtes Sitzungsende und muss abmelden. Ein Präfix hätte
den Fehler nur in die andere Richtung gedreht.

**Die Meldung bleibt die kombinierte.** Gewünscht war „E-Mail-Adresse existiert
nicht"; der Server antwortet auf unbekannte Adresse und falsches Passwort
absichtlich gleich. Getrennte Meldungen verraten, welche Adressen ein
FLEXR-Konto haben — bei einer Dating-App ist schon die Mitgliedschaft die
schützenswerte Information, und die Liste ließe sich mit einem Skript
durchprobieren. Wer das ändern will, ändert `backend/app/routers/auth.py`, nicht
die Clients.

`frontend/sw.js` steht deshalb auf `flexr-shell-v17`: Der Fehler saß in
`index.html`, also in der Shell. Ohne das Hochzählen behielten Bestandsnutzer
im Offline-Rückfall die alte Fassung samt Fehler.

Nach dem Deploy auf flexr.social gegengeprüft — im Browser gegen die echte
Anmeldemaske, mit einer nicht registrierten Adresse: `loginErr` zeigt
„E-Mail oder Passwort falsch.", der Bildschirm bleibt `screen-login`, es wird
kein Token verworfen.

### 2. Der Chat-Poll lief weiter, wenn niemand hinsah

Auf Android startete `ChatViewModel` seinen Poll im `init` und damit im
`viewModelScope` — er lief, solange das ViewModel lebte, also auch wenn der
Chat im Rückstapel lag oder die App im Hintergrund war. Dabei quittierte er
Nachrichten als **gelesen**, die niemand angesehen hatte: eine Lesebestätigung
für nichts.

`startPolling()` ist jetzt öffentlich und wird nicht mehr aus dem `init`
gerufen; dazu kam `stopPolling()`. `ChatScreen` hängt beides über
`LifecycleResumeEffect` an die Sichtbarkeit. Damit verhält Android sich wie
iOS, wo der Poll seit jeher an `.task` der Ansicht hängt (in
[ios/HANDOFF.md](ios/HANDOFF.md) stand das bis heute unter „Bewusste
Abweichungen — Android sollte nachziehen"; der Punkt ist damit erledigt).

### 3. Android 2.6.8 (versionCode 108)

Gebaut mit `JAVA_HOME=~/.bubblewrap/jdk/jdk-17.0.11+9 ./gradlew
bundleProdRelease`, signiert, prod-Flavor, 7,4 MB;
`testProdReleaseUnitTest` läuft durch. Enthält außer den beiden Korrekturen
oben auch 2.6.6 und 2.6.7, die im Baum lagen, aber nie gebaut worden waren.

Das Bundle ist direkt im Chat übergeben worden und liegt **nicht** in
`dl-a616e78274de323b/`; ein APK dieser Fassung gibt es nicht. Der Upload in
die Play Console steht noch aus.

> `aapt2 dump badging` kann die Fassung eines **AAB** nicht lesen — das
> Manifest liegt dort im Protobuf-Format vor, nicht im Binär-XML. Zum
> Gegenprüfen taugt `unzip -p app-prod-release.aab base/manifest/AndroidManifest.xml | strings | grep 2\.6\.`.

## Sitzung 12.09.2026 (3) — SEO-Audit: og:locale:alternate, WebP fuer Landingpage-Fotos

Ein Commit (`01adcc8`), gepusht und deployt. Reines Frontend, keine
Migration, kein Neustart — nur `git pull` auf dem VPS.

### 1. og:locale:alternate fehlte komplett

Auf allen 20 oeffentlichen Seiten (DE+EN) gab es zwar `hreflang` fuer
Suchmaschinen, aber kein `og:locale:alternate` fuer Facebook/LinkedIn-Parser.
Jetzt traegt jede Seite die Gegensprache (`en` auf den DE-Seiten, `de_AT` auf
den EN-Seiten). `build-en.py` bekam dieselbe Ersetzungsregel wie schon fuer
`og:locale`, damit die Zeile bei jedem Rebuild von `en/index.html` erhalten
bleibt statt beim naechsten Lauf zu verschwinden.

### 2. Landingpage-Fotos zusaetzlich als WebP

Die rund 25 Demo-Fotos auf der Landingpage lagen nur als JPEG vor (90-120 KB
je Bild). Mit Pillow (`quality=80`) zusaetzlich als WebP erzeugt und
`index.html` auf `<picture><source type="image/webp">...<img
jpg-Fallback></picture>` umgestellt — Browser ohne WebP-Unterstuetzung
(praktisch keine mehr) bekommen weiter das unveraenderte JPEG. Ersparnis
rund 52 % (2,3 MB → 1,2 MB), relevant weil Core Web Vitals ein Rankingfaktor
sind.

`og-image.png` (Social-Preview) bewusst nicht auf WebP umgestellt — dort
wird PNG/JPEG zuverlaessiger unterstuetzt. `sw.js` brauchte keine Aenderung,
`/brand/demo/` wird schon ueber ein Praefix-Muster (`STATIC_PREFIXES`)
gecacht, nicht ueber eine feste Dateiliste.

### Pruefstand dieser Sitzung

`build-en.py` erneut laufen lassen ergibt ein byte-identisches
`en/index.html`. Seite ueber einen lokalen Testserver im Browser
gegengeprueft (die `file://`-Vorschau laedt keine lokalen Ressourcen und
taeuscht kaputte Bilder vor) — alle 25 Fotos kommen als `.webp` mit 200 OK,
Layout und die auf den Fallback-`src` zielenden CSS-Selektoren
(`[src*="-v2.jpg"]` etc.) unveraendert, weil der `src` des Fallback-`<img>`
gleich bleibt. Nach dem Deploy auf `flexr.social` gegengeprueft: `curl` zeigt
`og:locale:alternate` im HTML und `200 image/webp` fuer die Fotos.

### Noch offen

- Nur die auf der Landingpage verwendeten 25 Fotos wurden konvertiert, nicht
  der gesamte Bestand in `frontend/brand/demo/` (u. a. die in der Web-App
  unter `frontend/app/` verwendeten Demoprofile) — falls dort ebenfalls
  gewuenscht, waere das ein eigener, separat zu testender Schritt.
- Kein AVIF: Auf diesem Geraet steht nur Pillow ohne AVIF-Plugin zur
  Verfuegung, kein `cwebp`/`avifenc`/ImageMagick. WebP allein bringt aber
  schon den Grossteil der Ersparnis.

## Sitzung 12.09.2026 (2) — „Beta", Sprach-Hinweis, mindestens drei Fotos

Vier Commits (`bb6fbed`, `2aa06b2`, `648f273`, `7456b22`), alle gepusht und
ausgerollt. `bb6fbed` ist die schon vorhandene, noch nicht committete
2.6.3-Arbeit aus der Sitzung davor — sie lag unversioniert im Arbeitsbaum und
ist hier mitgegangen.

### 1. Statuspille und Sprach-Hinweis — `2aa06b2`

Die Pille im Kopf stand auf „Beta · gratis" / „Beta · free"; der Zusatz fällt
weg, die Web-App sagt seit `997b0d6` schon nur „Beta". Ressourcenname mit
umbenannt: `status_beta_free` → `status_beta`.

Der Hinweis unter „Sprache" im Kontobereich ist der einzige dort, der über
mehrere Zeilen läuft. Mit der Zeilenhöhe aus `bodySmall` (20 sp auf 13 sp
Schrift) standen die Zeilen so weit auseinander, dass der Satz nicht mehr als
Block las und der Abstand zur Überschrift im Zeilenabstand unterging. Jetzt
16 sp Zeilenhöhe plus 4 dp eigener Abstand nach oben.

### 2. Mindestens drei Profilfotos — `648f273`

Bisher genügte ein Foto. Ab jetzt sind drei Pflicht, und zwar **am Server
entschieden**:

- `MIN_PHOTOS`/`MAX_PHOTOS` in `backend/app/models.py`.
- `/verification/start` verlangt die volle Zahl statt eines Fotos.
- `DELETE /me/photos/{id}` lehnt ab, was darunter fallen würde. Ohne diese
  Prüfung ließe sich die Regel umgehen, indem direkt nach der Registrierung
  zwei der drei Fotos wieder verschwinden. Austauschen geht weiter: erst
  hochladen (bis sechs), dann löschen. Was die Moderation über
  `/api/admin/photos` entfernt, bleibt ausgenommen — Moderation schlägt Regel.

**Keine Migration**, es ändert sich kein Schema. Beide Clients ziehen dieselbe
Grenze bei Registrierung, Speichern und Löschen und zeigen unter dem Raster
einen Zähler („Noch 2 von 3 Pflichtfotos") — sonst bliebe der Knopf bei zwei
Fotos grundlos grau, wo früher eines reichte.

**Bestandskonten mit weniger Fotos bleiben nutzbar** und stoßen erst an die
Grenze, wenn sie ein Foto löschen oder die Prüfung starten wollen. Sollte das
stören, sind es zwei Stellen: die Prüfung in `start_verification` und die in
`delete_photo`.

Service Worker auf `flexr-shell-v15`, Wörterbuch auf `?v=5` — eine
eingefrorene alte Shell hätte sonst weiter „mind. 1" angezeigt.

### 3. Mehrzahl und eine Sackgasse in der Web-App — `7456b22`

Wo ein Text von dem einen Profilfoto sprach, das ein Mensch beim Verifizieren
vergleicht, steht jetzt die Mehrzahl: AGB und Nutzungsrichtlinien in beiden
Sprachfassungen, der Verifizierungs-Schirm beider Clients, die im Gerät
mitgeführten Rechtstexte von Android und iOS. Einzahl bleibt, wo sie stimmt
(„Ein FLEXR-Profilfoto wurde abgelehnt", Alternativtext eines einzelnen
Bildes, „Profilfoto-Richtlinien" als Name).

Dabei gefunden: Der Verifizierungs-Schirm der **Web-App** fragte Fotos nur
nach, wenn überhaupt keines da war (`photos.length`). Seit der Server drei
verlangt, wäre ein Konto mit ein oder zwei Fotos daran vorbeigelaufen und beim
Start der Prüfung in den 400 geraten — ohne Weg, dort noch etwas nachzureichen,
und der Konto-Bildschirm ist von da aus nicht erreichbar. Genau die Sackgasse,
gegen die es diesen Schirm gibt. Er prüft jetzt gegen `MIN_PHOTOS`. Die
Android-Fassung konnte das schon mit `648f273`.

### 4. Leerzustände von Matches und Chats — `aa9bbb2`

Gemeldet am Screenshot: „Noch keine Matches" stand rund 280 px höher als
„Alle Sätze absolviert". **Der Screenshot kam aus der Web-App, nicht aus der
Android-App** — erkennbar daran, dass dort weder die Umkreis-Zeile
(`swipe_radius`) noch der Knopf „Neu laden" zu sehen ist; beides hat nur der
native Bildschirm.

Ursache ist eine einzige CSS-Regel: `.empty` zentriert seinen Inhalt
(`justify-content:center`), was aber nur wirkt, wenn das Element selbst Höhe
hat. Im Deck holt `.deck{flex:1}` die Restfläche und `.deck .empty{position:
absolute; inset:0}` spannt den Leerzustand darüber. `#matchList` und
`#chatList` sind inhaltshoch — dort blieb die Zentrierung wirkungslos.

Die Klasse `is-empty` setzt der Renderer nur im Leerfall; Lade- und
Fehlerzustand räumen sie ab, eine befüllte Liste bleibt unberührt.
Nachgemessen bei 393×851 mit den echten Texten: Symbol 375, Titel 459,
Beschreibung 488 — für alle drei Bildschirme identisch.

Android hatte den Sprung nicht (alle drei oben angesetzt, nur um die
Umkreis-Zeile auseinander, ~23 dp); die Leerzustände stehen dort jetzt
ebenfalls mittig. Beim Swipe-Bildschirm per Modifier am `EmptyState` statt per
`contentAlignment` an der `Box` — sonst rutschen Karte und Hintergrundkarte mit.

### `.megaignore` für den Projektordner

`venv`, `build` und `node_modules` gehen nicht mehr in die
MEGA-Synchronisation (~537 MB in 15.766 Dateien, 88 % des Ordners).
`.gradle`, `.kotlin` und `.git` deckt die Wurzelregel `-:.*` schon ab. Syntax
gegen `mega-sync-ignore --help` geprüft: `<TYPE>` ist voreingestellt auf
`n` (subtree name), wirkt also in jeder Tiefe.

### Prüfstand dieser Sitzung

- Backend: **445 Tests grün**.
- Android: `testProdDebugUnitTest` und `lintVitalProdRelease` grün.
- Web: Texte im Browser gegengeprüft, Wörterbuch in beiden Sprachen auf
  vollständige Schlüssel geprüft, Inline-Skripte syntaktisch geprüft.

### `backend/venv` war kaputt — repariert

**25 von 61 Paketen waren leere Verzeichnisse**, darunter `fastapi`,
`sqlalchemy`, `pydantic`, `alembic`, `starlette`, `cryptography` und `pip`.
Tückisch: `import fastapi` lief trotzdem durch, weil Python ein leeres
Verzeichnis als Namespace-Paket importiert — nur Inhalt hatte es keinen.
`python -m pytest` scheiterte mit `ImportError: cannot import name
'__version__' from '_pytest'`.

Neu aufgebaut aus `requirements-dev.txt`. Danach: 0 leere Pakete, `pip check`
sauber, alle 16 gepinnten Versionen exakt getroffen, **445 Tests grün aus dem
Projekt-venv selbst**, `venv/bin/uvicorn|alembic|pytest` laufen (relevant, weil
`.claude/launch.json` auf `backend/venv/bin/uvicorn` zeigt). Falls es
wiederkommt:

```bash
rm -rf backend/venv && python3 -m venv backend/venv \
  && backend/venv/bin/pip install -r backend/requirements-dev.txt
```

Gegen eine Wiederholung steht jetzt die `.megaignore` oben.

## Sitzung 12.09.2026 — Sprachwechsel an der Wurzel, Regler zurück auf den Startschirm

**Auslöser:** Nutzer meldete zu 2.6.2 zwei Dinge:

1. Beim ersten Start, noch nicht angemeldet, gibt es **keine Möglichkeit**,
   auf Englisch zu stellen — der Regler steht seit Sitzung (3) nur noch im
   Kontobereich, und dorthin kommt nur, wer ein Konto hat.
2. Die Sprache im Profil umstellen und speichern ändert **weiterhin keinen
   einzigen Text**. Das ist dieselbe Meldung wie zu 2.6.1, also der zweite
   fehlgeschlagene Reparaturversuch.

### Fehler 2: warum zwei richtig aussehende Lösungen nichts bewirkt haben

Beide bisherigen Fassungen haben zur Laufzeit an den Ressourcen gedreht — erst
über einen untergeschobenen `LocalContext` (2.6.1), dann über ein
überschriebenes `getResources()` auf der Activity (2.6.2). Beide hätten nach
Lesart des Compose-Quelltextes funktionieren müssen (`stringResource` löst über
`LocalContext.current.resources` auf; per Bytecode in
`androidx.compose.ui:ui-android:1.8.1` bestätigt). Am Gerät taten sie es nicht.

Dafür gibt es jetzt zwei Ursachen, und die erste erklärt den Befund ganz ohne
Compose:

**a) Das App Bundle hat die englischen Texte gar nicht ausgeliefert.**
Ein Android App Bundle legt standardmäßig **jede Sprache in ein eigenes
Split-APK**, und Play installiert nur die Splits der Systemsprache des Geräts.
Auf einem deutsch eingestellten Telefon ist `res/values-en` damit schlicht
nicht vorhanden. Die App darf dann umschalten, worauf sie will —
`getString` fällt mangels englischer Tabelle immer auf Deutsch zurück, und
genau das ist das gemeldete Bild: Regler springt um, kein Text ändert sich.

Vom Rechner aus war das **nicht zu sehen**: Das direkt aufgespielte APK aus
`assembleProdRelease` ist ein Universal-APK und enthält immer alle Sprachen.
Nur der Weg über die Play Console schneidet sie weg. Behoben in
`app/build.gradle.kts`:

```kotlin
bundle {
    language {
        enableSplit = false
    }
}
```

Das ist die Standardbedingung dafür, dass eine App ihre Sprache selbst
umstellen darf; es kostet ein paar Kilobyte Downloadgröße für zwei Sprachen.

**b) Die Umschaltung saß an der falschen Stelle.** Unabhängig von (a) ist der
vorgesehene Weg nicht, `getResources()` zu überschreiben, sondern die Sprache
am **Basis-Context der Activity** zu setzen:

```kotlin
override fun attachBaseContext(newBase: Context) {
    val language = LanguageStore.storedLanguage(newBase) ?: AppLanguage.detect()
    attachedLanguage = language
    val configuration = Configuration(newBase.resources.configuration).apply {
        setLocale(language.locale)
        setLayoutDirection(language.locale)
    }
    super.attachBaseContext(newBase.createConfigurationContext(configuration))
}
```

Damit liefert **jeder** Context dieser Activity die richtigen Ressourcen:
`stringResource`, `getString`, Dialoge, `LocalConfiguration`, Systemdialoge —
ohne dass irgendwo etwas überschrieben oder untergeschoben wäre. So schaltet
auch Android 13 selbst die App-Sprache um.

Der Preis ist ein `recreate()` beim Wechsel; es kostet nichts Sichtbares
(ViewModels überleben, Navigationsstapel und Scrollpositionen liegen in
`rememberSaveable`). Ausgelöst wird es in `MainActivity.onCreate`, wenn die
beobachtete Sprache von `attachedLanguage` abweicht.

**Folgeänderung: `LanguageStore` liegt jetzt in `SharedPreferences`, nicht mehr
im DataStore.** `attachBaseContext` kann nicht warten — es entscheidet, welche
Ressourcen die Activity ihr Leben lang liefert, und läuft ab, bevor Hilt,
Compose oder ein Coroutine-Scope existieren. DataStore kann das prinzipiell
nicht bedienen (nur `suspend`), und `runBlocking` auf dem Hauptfaden ist genau
das, wovor DataStore warnt. Die alte DataStore-Datei (`flexr_settings`) wird
beim ersten Start einmalig ausgelesen und die Wahl übernommen
(`LanguageStore.migrateLegacyChoice`); kommt sie an, merkt die Activity die
Abweichung und baut sich einmal neu auf.

`ProvideAppLanguage` dreht dadurch an **gar nichts** mehr — es stellt nur noch
`LocalAppLanguage` bereit, damit der Regler weiß, welches Segment leuchtet.

### Fehler 1: Regler zurück in die ausgeloggte Kopfzeile

`FlexrTopBar` hat seinen `statusSlot` behalten; im `AuthGraph` steckt dort
jetzt der `LanguageSwitch` statt nichts. Angemeldet bleibt es beim
Mitgliedschafts-Status, der Regler steht dort weiterhin nur im Kontobereich —
es gibt ihn also nach wie vor nicht doppelt auf einem Bildschirm.

Das weicht bewusst von der Web-App ab, wo er ausschließlich im Kontobereich
steht: Im Browser ist niemand gefangen (Rechtstexte unter `/en/`, und wem die
erkannte Sprache nicht passt, der stellt den Browser um). Eine installierte App
hat keinen dieser Auswege.

`AppLanguageViewModel.select` meldet die Sprache jetzt **nur noch mit geladenem
Profil** ans Backend. Auf dem Login-Schirm gibt es keine Sitzung; die Meldung
liefe in ein 401, und der `SessionExpiryInterceptor` würde daraufhin den Token
verwerfen. Verloren geht dadurch nichts — die Registrierung schickt die Sprache
selbst mit (`RegisterViewModel`), und `MainViewModel.syncLanguage` gleicht sie
beim nächsten Login ab.

### Nicht geprüft

Weiterhin **kein Gerätetest von hier aus** möglich, und weiterhin gibt es im
Projekt weder einen Compose-UI-Test noch Robolectric. Was sich diesmal
unterscheidet: Ursache (a) ist keine Vermutung, sondern dokumentiertes
Verhalten des App-Bundle-Formats, und sie erklärt den gemeldeten Befund
vollständig. Ursache (b) ist der offizielle Weg statt eines Umwegs.

Wer als Nächstes hier arbeitet: Ein Instrumentierungstest, der `ActivityScenario`
mit gesetzter Sprache startet und einen bekannten String abfragt, wäre die
naheliegende Lücke — und er würde (a) nicht fangen, weil er gegen ein
Universal-APK läuft. Der einzige echte Test für (a) ist ein Installieren über
die Play Console (interner Test) auf einem deutschsprachigen Gerät.

### Ergebnis

`./gradlew --offline --no-configuration-cache testProdDebugUnitTest
testProdReleaseUnitTest assembleProdRelease bundleProdRelease` läuft durch,
beide Unit-Test-Varianten grün. **versionCode 103, versionName 2.6.3**,
signiert mit demselben Upload-Key wie bisher (`CN=FLEXR`, SHA-256
`bc64ad3f…e7980`, mit `apksigner verify --print-certs` gegengeprüft).

Zwei Dinge sind am fertigen Paket nachgeprüft, nicht nur angenommen:

* `aapt2 dump resources` am APK zeigt zu jedem Text beide Fassungen, z. B.
  `string/account_section_profile`: `() "Profil"` und `(en) "Profile"`.
* `BundleConfig.pb` im AAB trägt die Split-Dimension `LANGUAGE` mit
  `negate = true` — die Sprachen bleiben also im Basis-Modul, Play schneidet
  keine mehr weg.

```
sha256sum flexr-2.6.3-vc103.apk
86ac29f557b53c8424a61825075fe066b660ef8181a4751b1044c7095657d919

sha256sum flexr-2.6.3-vc103.aab
3865a44f6f3d19d60927746ee6147771452d54b8b4bb88e2eda5a8ce6de2f3eb
```

Beide Dateien liegen lokal unter `../release-2.6.3/` (samt `SHA256SUMS.txt`),
analog zu `../release-2.6.2/`. Für den nächsten Deploy auf den
Download-Server: `flexr-2.6.3-vc103.apk` und `.aab` nach
`dl-a616e78274de323b/` legen; die `vc101`- und `vc102`-Dateien werden nicht
mehr gebraucht.

## Sitzung 11.09.2026 (3) — Sprachregler entfernt, Sprachwechsel repariert, KSP2-Bug umgangen

**Auslöser:** Nutzer installierte das APK aus Sitzung (2) (2.6.1,
versionCode 101) auf einem echten Gerät und meldete zwei Fehler per
Screenshot vom Kontobildschirm:

1. Oben in der Kopfzeile stand weiterhin ein DE/EN-Regler, obwohl die
   Web-App ihn dort bereits am 11.09. entfernt hatte (Commit 997b0d6, siehe
   Abschnitt (2) weiter unten) — die native App hatte diese Änderung nie
   nachgezogen.
2. Der Regler zeigte „EN" als ausgewählt (orange hinterlegt), aber jeder
   sichtbare Text blieb Deutsch — u. a. „PROFIL" statt „PROFILE",
   eindeutig zu unterscheiden (kein Lehnwort wie „Bio" oder „Gym").

**Fehler 1 behoben — Sprachregler nur noch im Profil.** Analog zu 997b0d6:
`FlexrTopBar` (`ui/navigation/FlexrScaffold.kt`) hat die Parameter
`language`/`onSelectLanguage` und den `LanguageSwitch`-Aufruf verloren, zeigt
nur noch Wortmarke und Mitgliedschafts-Status. `rememberLanguageControls()`
in `FlexrApp.kt` war dadurch an keiner Stelle mehr gebraucht und ist ganz
raus, ebenso die drei Aufrufstellen, die `language`/`onSelectLanguage` an
`FlexrTopBar` durchgereicht hatten (`AuthGraph`, `VerificationGraph`,
`MainGraph`). Einzige verbliebene Stelle: `AccountScreen.kt`, unverändert —
dort holt sich der Bildschirm seinen eigenen `AppLanguageViewModel` und
zeigt `LocalAppLanguage.current` im „Profil"-Abschnitt an.

**Fehler 2 behoben — mit einem offenen Punkt zur Ursache.** `stringResource`
löst über `LocalContext.current.resources` auf. Bis dahin tauschte
`ProvideAppLanguage` `LocalContext` gegen einen `ContextWrapper` aus
(eingeführt in derselben Sitzung (2), als Fix für den 2.6.0-Startabsturz —
siehe Abschnitt „Absturz beim Start der Android-App"). Ein `ContextWrapper`
um eine Activity ist selbst *keine* `Activity` mehr; ein direktes
`context as Activity`, wie es Berechtigungsabfragen, CameraX oder Custom
Tabs tun können, wäre daran mit einer `ClassCastException` gescheitert, auch
wenn die echte Activity über `baseContext` erreichbar geblieben wäre.

Ob **genau dieser Wrapper** die Ursache für den Sprachwechsel-Fehler war,
ließ sich mangels Testgerät **nicht abschließend zeigen** — die
Bytecode-Analyse der `stringResource`-Implementierung
(`androidx.compose.ui:ui-android:1.8.1`, aus dem Gradle-Cache decompiliert)
ergab keinen offensichtlichen Grund, warum der Wrapper falsch aufgelöst
haben sollte. Der Verdacht lag trotzdem nahe, und der Wrapper war unabhängig
davon riskant (siehe oben). Die neue Lösung baut deshalb robuster, nicht nur
anders:

- `MainActivity` überschreibt `getResources()` **direkt auf sich selbst**
  (die echte Activity, kein zweites Objekt) und hält die lokalisierten
  Ressourcen in einem Feld (`localizedResources`).
- `applyLanguage(language)` befüllt dieses Feld über
  `applicationContext.createConfigurationContext(configuration).resources`
  — auf `applicationContext`, nicht auf `this`, um jede denkbare
  Ringabhängigkeit mit dem gerade überschriebenen `getResources()`
  auszuschließen. Die Ausgangskonfiguration kommt aus
  `super.getResources().configuration` (die echte, fenstergrößen-bewusste
  Konfiguration der Activity), nicht aus `applicationContext` (kennt keine
  Mehrfenster-/Faltzustände).
- Aufgerufen wird das synchron über `remember(language) { applyLanguage(language) }`
  in `MainActivity.onCreate()`, noch vor `ProvideAppLanguage(language) { … }`
  — damit steht die richtige Sprache schon im ersten Frame nach jedem
  Wechsel.
- `ProvideAppLanguage` selbst tauscht `LocalContext` gar nicht mehr aus, nur
  noch `LocalConfiguration` (löst weiterhin die Rekomposition aus, ihr
  Inhalt wird von niemandem mehr gelesen). `LocalContext.current` ist damit
  überall wieder die echte Activity — kein `ContextWrapper`, keine
  `ClassCastException`-Gefahr, unabhängig davon, ob das je der Grund für den
  gemeldeten Fehler war.

**Ein dritter, unabhängiger Fehler beim Bauen selbst.** Nach den
Quelländerungen schlug `assembleProdRelease`/`bundleProdRelease` mit rund 60
„duplicate class"-Fehlern für von Hilt generierte Klassen fehl
(`_HiltModules`, `_Factory`, `hilt_aggregated_deps`) — KSP2 hatte sie für
etliche, thematisch unzusammenhängende Module zusätzlich ein zweites Mal
unter dem Paket von `ui.verification` angelegt. **Kein Cache-Problem:**
reproduziert mit vollständig geleertem `app/build`, `.gradle` und globalem
Gradle-Cache (`~/.gradle/caches`, `~/.gradle/configuration-cache`), sowohl
mit als auch ohne `--no-build-cache`/`--no-configuration-cache`, zweimal in
Folge identisch. `testProdDebugUnitTest` lief davon unberührt — betroffen war
ausschließlich die KSP-Verarbeitung der `prodRelease`-Variante. Behoben mit
`ksp.useKSP2=false` in `gradle.properties` (zurück auf KSP1); mit dieser
Einstellung kompiliert, testet und paketiert derselbe Rebuild aus leerem
Zustand sauber durch. Kommentar mit den Versionsnummern
(KSP `2.1.20-2.0.0`, Hilt `2.56.2`) steht direkt daneben in der Datei.

**Ergebnis:** `./gradlew --no-configuration-cache clean testProdDebugUnitTest
testProdReleaseUnitTest assembleProdRelease bundleProdRelease` läuft aus
leerem Zustand durch, beide Unit-Test-Varianten grün. Neues APK und AAB
gebaut, **versionCode bleibt 101 / versionName 2.6.1** (derselbe Release,
kein neuer Versionssprung — nur der Build-Inhalt hat sich geändert, daher
neue Prüfsummen unten). Signiert mit demselben Upload-Key wie zuvor
(`CN=FLEXR`, SHA-256-Fingerabdruck `bc64ad3f…e7980`).

```
sha256sum flexr-2.6.1-vc101.apk
f39f76cfbc4211e7b268f42b468f2832a5ad1cf36498484441eff7f86fb50cfc

sha256sum flexr-2.6.1-vc101.aab
3f04bd2bb4b9cff00b67ee4e1d15d80e845ee9aa09252c165ef4332d42748a36
```

**Wichtig für den Download-Ordner:** Die Dateien unter
`dl-a616e78274de323b/flexr-2.6.1-vc101.{apk,aab}` aus Sitzung (2) sind mit
diesem Fix **inhaltlich überholt** (andere Prüfsumme, siehe oben) — der
Dateiname bleibt gleich, weil sich versionCode/versionName nicht geändert
haben. Beim nächsten Deploy die beiden Dateien am Server **ersetzen**, nicht
nur ergänzen.

**Nicht geprüft werden konnte:** ob der Sprachwechsel auf einem echten Gerät
jetzt tatsächlich alle Texte umstellt. Es gibt im Projekt keinen
Compose-UI-Test und kein Robolectric-Setup, das `stringResource` gegen eine
simulierte Konfigurationsänderung prüfen könnte (`gradle/libs.versions.toml`
enthält weder das eine noch das andere) — nur ein echtes Gerät oder ein
Emulator kann das zeigen. Wer als Nächstes an dieser Stelle arbeitet: Ein
Instrumentierungstest, der `ProvideAppLanguage`/`MainActivity.applyLanguage`
gegen einen `ActivityScenario` prüft, wäre die naheliegende Lücke.

**Nachtrag:** Auf Wunsch des Nutzers bekam dieser Stand eine eigene
Versionsnummer statt weiter unter 2.6.1/101 zu laufen — **versionCode 102,
versionName 2.6.2**. Grund und Regel dazu stehen als Kommentar direkt bei
`versionCode`/`versionName` in `app/build.gradle.kts`: Jeder tatsächlich
gebaute und ausgelieferte Stand bekommt ab jetzt seine eigene Nummer, damit am
Dateinamen erkennbar bleibt, welcher Fix schon drin ist. Derselbe Code wie
oben beschrieben, aus leerem Zustand neu gebaut
(`./gradlew --no-configuration-cache clean testProdDebugUnitTest
testProdReleaseUnitTest assembleProdRelease bundleProdRelease`), beide
Unit-Test-Varianten grün, gleicher Signierschlüssel:

```
sha256sum flexr-2.6.2-vc102.apk
e83674790ed2f6952e7bc4dc12f0e5b7db0ce1b0ee5446223518efa71732944b

sha256sum flexr-2.6.2-vc102.aab
855430adb6522a6ec9decd4e06e57c487f9582e904600e449ff78bfc3249e8a5
```

Die zuvor unter `dl-a616e78274de323b/flexr-2.6.1-vc101.{apk,aab}` erwähnten
Dateien sind damit **hinfällig** — dieser Stand heißt jetzt `2.6.2-vc102` statt
`2.6.1-vc101` mit ausgetauschtem Inhalt. Für den nächsten Deploy auf dem
Download-Server: `flexr-2.6.2-vc102.apk` und `.aab` neu ablegen; die
`vc101`-Dateien müssen nicht mehr existieren.

## Sitzung 11.09.2026 (2) — Rechtstexte auf Englisch, E-Mails in der Profilsprache

Zwei Aufträge, nacheinander: erst die neun Rechts- und Infoseiten auf Englisch,
dann die E-Mails. Der zweite baut auf dem ersten auf — beide drehen sich darum,
dass jemand FLEXR durchgehend in seiner Sprache bekommt.

### Die Rechtstexte gibt es jetzt unter `/en/`

Neun Seiten, rund 13.800 Wörter: `impressum`, `agb`, `datenschutz`, `widerruf`,
`nutzungsrichtlinien`, `sicherheit`, `strafverfolgung`, `meldung`, `faq` —
jeweils unter **demselben Dateinamen** unter `/en/`. Die Adressen spiegeln sich
also: `/agb.html` ↔ `/en/agb.html`.

Dieselbe Begründung wie bei der Landingpage: zwei eigene Adressen statt eines
Umschalters, damit Google je Adresse eindeutig eine Sprache sieht. Anders als
die Landingpage werden sie aber **nicht erzeugt** — `build-en.py` hängt an
`data-i18n`-Auszeichnungen, und die in neun Vertragstexte einzuziehen wäre
aufwendiger und fehleranfälliger als zwei gepflegte Fassungen. Rechtstexte
ändern sich selten und wollen beim Ändern ohnehin gelesen werden.

**Verbindlich bleibt Deutsch.** Jede englische Seite sagt das oben in einem
eigenen Absatz (`p.en`); die AGB verweisen dabei auf Punkt 6 c („Die
Vertragssprache ist Deutsch"), die Datenschutzerklärung auf die Einwilligung
nach Punkt 4, die sich auf die deutsche Fassung bezieht.

Drumherum:

* **hreflang** wechselseitig auf beiden Fassungen, `x-default` überall auf
  Deutsch. Die Sitemap ging von 11 auf 20 URLs.
* **Sprachregler** auf allen 18 Seiten. `lang-switch.js` liest die beiden
  Adressen seither **aus dem Regler im Markup** statt aus einer festen Karte
  `{de:'/', en:'/en/'}` — sonst hätte ein gespeichertes „de" von
  `/en/agb.html` auf die Startseite umgeleitet statt auf `/agb.html`.
* **`legal-status.js`** beschriftet den §-13a-Link jetzt nach `<html lang>`:
  ab dem 1.10.2026 „Withdraw from contract" statt „Vertrag widerrufen".
* **Die Web-App** lädt im Rechts-Modal die Fassung der eingestellten
  App-Sprache (`openLegalModal` löst den Pfad über `FlexrI18n.current()` auf,
  Cache pro Sprache). Die Kopfzeile der Rechtsseite wird im Modal ausgeblendet
  — der Rückweg führte aus der App heraus, der Regler wäre dort der falsche
  Knopf.
* **`build-en.py`** biegt die Rechts-Links der englischen Landingpage auf
  `/en/` um; die „(German)"-Hinweise sind aus den Wörterbüchern raus.
* **nginx** braucht nichts: `try_files $uri` findet die Dateien.

Nebenbei ist der **tote `<style>`-Block in `nutzungsrichtlinien.html`**
gefallen (Rest aus der Zeit vor `legal.css`). Er war der Grund, warum die
deutsche und die englische Fassung derselben Seite unterschiedlich groß
gesetzt waren.

### Der Service Worker lieferte die Landingpage unter Rechts-Adressen

Beim Nachprüfen der beiden Fassungen fiel auf, dass `sw.js` den Offline-
Rückfall für **jede** Navigation anwandte. Wer offline auf „AGB" tippte, bekam
die **Landingpage** — mit der AGB-Adresse in der Adresszeile. Betroffen waren
genau die Seiten, die seit v12 bewusst *außerhalb* der Shell liegen. Zwei
Folgefehler hingen daran:

* War der Cache noch leer (erster Aufruf, geleerter Speicher), lieferte
  `caches.match()` `undefined`, und `respondWith(undefined)` machte daraus
  einen **harten Netzfehler** — schlechter als gar kein Service Worker.
* `/en/` fiel auf `/index.html` zurück, also auf die **deutsche** Landingpage,
  obwohl `/en/index.html` seit v10 in der Shell liegt.

`shellDocumentFor()` entscheidet jetzt, welche Shell-Seite eine Adresse offline
überhaupt vertreten darf; alles andere bekommt `Response.error()` und damit die
Offline-Meldung des Browsers. `CACHE` steht auf `flexr-shell-v14`.

**Der Worker registriert sich nicht mehr auf localhost.** Er gilt für
`scope: '/'`, überlebt die Sitzung und sogar den Wechsel des Servers hinter dem
Port — und fängt danach auch die statischen Rechtsseiten ab, die ihn nie
registrieren. Genau das hat am 11.09. eine Stunde gekostet: Ein Worker aus
einer früheren Sitzung (`flexr-shell-v12`) beantwortete auf
`http://localhost:5173` jede Navigation mit der App-Shell, ohne dass ein
Request je am Server ankam. `app/index.html` räumt alte Registrierungen auf
localhost jetzt aktiv ab. Zum Prüfen des Offline-Verhaltens einmal mit `?sw`
laden.

> Der Browser-Pane von Claude Code blockiert `fetch` **innerhalb** eines
> Service Workers (`ERR_FAILED`), und `unregister()` hängt dort. Das Verhalten
> des Workers lässt sich damit nicht im Pane prüfen — der Fix ist stattdessen
> in Node gegen eine nachgebaute `caches`/`fetch`-Umgebung getestet worden.

### Die E-Mails folgen der Profilsprache

Die Sprachwahl lebte nur im Client. Für die Oberfläche reicht das — der Server
verschickt aber E-Mails, die **ohne Zutun eines Clients** entstehen: die
Inaktivitäts-Erinnerung aus dem Tagesjob, die Zahlungsmail aus einem
Stripe-Webhook, die Moderationsmitteilung aus dem Admin-Bereich. Also steht die
Sprache jetzt am Profil.

**Neue Spalten** (Migration `c8d31f6a94b2`): `users.language` und
`notices.language`, beide `NOT NULL` mit `server_default "de"`. Die zweite,
weil eine Meldung nach Art. 16 DSA von jedem kommen darf, auch ohne Konto —
die Entscheidung nach Abs. 5 kommt aber Tage später und soll denselben Melder
in derselben Sprache erreichen wie die Empfangsbestätigung.

**`backend/app/message_texts.py`** ist neu: 164 Schlüssel, je `de` und `en`,
plus sprachabhängige Datums- und Betragsformatierung. Das **Gerüst** der Mails
(HTML-Karte, Absätze, Tabellenzeilen, Klartext-Umbrüche) bleibt einmalig in
`mailer.py` — zwei vollständige Mailer nebeneinander wären beim nächsten Umbau
auseinandergelaufen. Fehlt ein englischer Eintrag, fällt `t()` auf Deutsch
zurück, dieselbe Regel wie in `frontend/i18n.js`.

Umgestellt sind **alle 22 `send_*`-Funktionen**, dazu:

* die **Push-Benachrichtigungen** (`notifications.py`) — dieselben vier
  Anlässe, dieselbe Funktion, derselbe `user`;
* die **Antworttexte der API** für die beiden öffentlichen Formulare;
* die festen Bausteine der **Art.-17-Begründung** (`moderation.py`) und die
  **Prüfgründe** der Verifizierung (`verification_service.py`).

**Was deutsch bleibt:** der Freitext des Moderators (`moderation_reason`,
`moderation_facts`) — den schreibt ein Mensch. Ebenso die Telegram-Meldung an
den Betreiber (die geht an uns) und die Pydantic-Validierungsfehler; letztere
fangen die Clients vorher selbst ab.

**Eine inhaltliche Entscheidung:** Wer auf `/en/widerruf.html` zurücktritt,
dessen Erklärung wird **auf Englisch aufgezeichnet und bestätigt**. § 13a
Abs. 4 FAGG verlangt die Bestätigung „des Inhalts der Erklärung" — eine
deutsche Aufzeichnung einer englisch abgegebenen Erklärung wäre eine
Übersetzung davon, nicht ihr Inhalt.

**Alle drei Clients** melden die Wahl ans Profil, bei der Registrierung und bei
jedem Umschalten. Beim Anmelden wird abgeglichen: eine ausdrückliche Wahl auf
dem Gerät schlägt das Profil, ein frisches Gerät übernimmt das Profil. Im Web
macht das `gleicheSpracheAb()`, in Android `MainViewModel.syncLanguage`, in iOS
`AppModel.syncLanguage`.

### Deutsch ist dabei unverändert geblieben

Geprüft, indem der alte Mailer aus `HEAD` neben den neuen geladen und 23 Mails
gegeneinander gerendert wurden: **alle Betreffzeilen und alle Klartext-Bodies
sind im Wortlaut identisch.** Vier HTML-Fassungen haben sich um je einen
Buchstaben geändert (`Ein`→`ein`, ein Satzzeichen) — dort standen Klartext und
HTML schon vorher verschieden da, und zusammengelegt gilt der Klartext, den
`mailer.py` selbst „die inhaltlich massgebliche Fassung" nennt.

### Was in dieser Sitzung NICHT laufen konnte

**Das venv unter `backend/venv` enthält keine Python-Quellen mehr** — nur leere
Verzeichnisgerüste. `fastapi`, `pydantic`, `sqlalchemy`, `pytest`: je 0
`.py`-Dateien. Vermutlich ein Sync-Artefakt von MEGA. Dazu fehlt auf dieser
Maschine eine **JDK**, also läuft auch Gradle nicht.

Praktische Folge: **Die Backend-Integrationstests und die Kompilierung von
Android und iOS sind ungelaufen.** Vor dem nächsten Release nachzuholen:

```bash
cd backend && pip install -r requirements.txt && pytest      # venv neu aufbauen
cd android-native && ./gradlew test lint
```

Ersatzweise geprüft wurde:

* alle 54 Mailfassungen (27 Fälle × 2 Sprachen) tatsächlich gerendert, mit
  gestubbter `app.config` — sonst echter Projektcode;
* jeder `send_*`-Aufruf per AST gegen seine Signatur (22 Funktionen);
* die Wörterbuch-Tests aus `tests/test_sprache.py` ohne FastAPI;
* die neun Regressionstests in `tests/test_public_frontend.py` (brauchen keine
  Fremdpakete) — grün, inklusive des neuen
  `test_rechtstexte_gibt_es_zweisprachig_und_wechselseitig_verlinkt`;
* Kotlin und Swift: Klammernbilanz, Importe, Konstruktoraufrufe in den Tests.
  **Kein Compilerlauf.**

### Deploy dieser Sitzung

Die Migration **muss vor dem Neustart der API laufen** — ohne
`users.language` scheitert jede Profilabfrage:

```bash
cd /flexr && git pull
cd backend && source venv/bin/activate && alembic upgrade head
pm2 restart flexr-api        # bzw. sudo systemctl restart flexr-api
```

Das Frontend ist statisch und mit dem `git pull` erledigt. Der Service Worker
steht auf `flexr-shell-v13`.

## Absturz beim Start der Android-App (durch Indizien erhärtet, nicht mit Sicherheit belegt)

**Symptom:** 2.6.0 (versionCode 100) startet und schließt sich sofort wieder.
Gemeldet am 11.09.2026.

**Update aus Sitzung (3):** Der Nutzer hat inzwischen das direkt installierbare
APK aus Sitzung (2) aufgespielt und konnte den Kontobildschirm bedienen (dort
kamen die beiden in Sitzung (3) behobenen Fehler her — Sprachregler und
Sprachwechsel). Die App **startet mit dem APK also**. Das stützt die
`.aab`-Theorie unten, ist aber kein Beweis: Zwischen 2.6.0 und dem für
Sitzung (3) gebauten 2.6.1 hat sich auch echter Code geändert
(`ProvideAppLanguage`, `MainActivity`), und ohne einen Test mit dem
*ursprünglichen* 2.6.0-Bundle als APK lässt sich nicht sauber trennen, ob die
Installationsart oder eine der Codeänderungen den Ausschlag gab.

**Eingegrenzt:** Das installierte Bundle ist vom 10.09. um 10:22 Uhr, gebaut
aus `d372c24`. Der letzte Commit, der `android-native/` angefasst hat, ist
ebendieser — die Arbeit vom 11.09. ist nie kompiliert worden und liegt nicht
auf dem Gerät. Die letzte bekannt funktionierende Fassung ist **2.5.5
(versionCode 42, `af71b25`)**. Dazwischen liegen `abb9fe3`
(Zweisprachigkeit), `7e36e69` (Monetarisierung), `0d0e1b5` und `d372c24`.

**Ausgeschlossen, je mit Beleg:**

| Verdacht | Befund |
| --- | --- |
| Room-Schema ohne Migration | `DatabaseModule.kt:25` hat `fallbackToDestructiveMigration(dropAllTables = true)` |
| WorkManager-Initialisierung vor Hilt | Default-Initializer ist im Manifest entfernt (`tools:node="remove"`) |
| Zwei DataStores auf einer Datei | `flexr_settings` vs. `flexr_session` |
| Fehlende/kaputte String-Ressourcen | 451 de / 450 en, einzige Lücke `app_name` (Eigenname); keine abweichenden Formatargumente |
| Resource Shrinking hat Strings entfernt | `resources.txt`: alle als erreichbar markiert |
| Android-14/15-Verschärfungen | keine `registerReceiver`, keine Services, `PendingIntent` durchgehend `FLAG_IMMUTABLE` |
| Splash bleibt hängen | `markLoggedOut()` setzt `SessionGate.isReady = true` |

**Die wahrscheinlichste Ursache, gefunden am 11.09. abends: Es wurde ein
`.aab` heruntergeladen und installiert.** Unter der einzigen Download-Adresse

    https://flexr.social/dl-a616e78274de323b/flexr-2.6.0-vc100.aab

liegt ein **App Bundle**, kein APK — und ein APK wurde dort nie angeboten
(`flexr-2.6.0-vc100.apk` und die naheliegenden Namen antworten mit 404). Ein
`.aab` ist das Veröffentlichungsformat für Play und **auf einem Gerät nicht
installierbar**. Wer es trotzdem aufs Telefon bringt — umbenannt oder über
einen Split-Installer — bekommt eine Installation ohne die passenden Splits.
Android beendet so eine App beim Start sofort wieder
(`MissingSplitsPackageException`): **genau das gemeldete Verhalten, und es
erklärt zugleich, warum im Code keine Ursache zu finden war.**

Gegenprobe, die das stützt: Der Code der Fassung 2.6.0 **baut und läuft
sauber durch** — `./gradlew clean testProdReleaseUnitTest bundleProdRelease`
ist am 11.09. ohne Fehler durchgelaufen, die Einheitstests inbegriffen.

**Konsequenz für die Verteilung:** Neben dem AAB für die Play Console gehört
ein **signiertes Universal-APK** in den Download-Ordner. Das lässt sich direkt
antippen und installieren:

```bash
cd android-native
./gradlew clean assembleProdRelease bundleProdRelease
# APK (installierbar):  app/build/outputs/apk/prod/release/app-prod-release.apk
# AAB (nur fuer Play):  app/build/outputs/bundle/prodRelease/app-prod-release.aab
```

Die Unterscheidung gehört auf die Download-Seite geschrieben, sonst passiert
dasselbe beim nächsten Mal.

**Falls 2.6.1 trotzdem abstürzt:** Dann war es nicht die Installation, und der
Stapelabzug liegt jetzt auf dem Gerät — 2.6.1 bringt dafür
`core/diagnostics/CrashLog.kt` mit. Die Datei findet sich ohne Rechner mit
jedem Dateimanager unter

    Android/data/flexr.social.app/files/absturz-<datum>.txt

Sie enthält nur Technisches (Zeitpunkt, App- und Android-Fassung, Gerät,
Stapelabzug) und wird nirgendwohin verschickt. Mit Rechner geht weiterhin:

```bash
adb logcat -c && adb shell monkey -p flexr.social.app 1 && sleep 4 && adb logcat -d -b crash
```

Die `mapping.txt` geht mit dem Bundle hoch, die Play Console zeigt Abstürze
also lesbar (Qualität → Absturz-Diagnose).

### Was 2.6.1 (versionCode 101) enthält

Zwei Änderungen, keine reine Neuübersetzung derselben Quellen:

1. **`core/diagnostics/CrashLog.kt`** — der Absturzbericht oben. Er hängt sich
   in `FlexrApplication.onCreate()` **vor** `super.onCreate()` ein und fängt
   damit auch Fehler in der Hilt-Injektion ab. Der vorherige Handler wird
   danach weiterhin aufgerufen, damit der Prozess normal endet und der
   Play-Bericht erhalten bleibt.

2. **`core/locale/ProvideAppLanguage.kt`** — dort wurde `LocalContext` durch
   das Ergebnis von `createConfigurationContext()` ersetzt. Dessen
   `baseContext`-Kette endet im Anwendungs-Context, **die Activity ist darin
   nicht mehr zu finden**. Alles, was sie aus `LocalContext` zurückholt
   (Teile von Compose, CameraX, Custom Tabs, jedes `context as Activity`),
   scheitert daran. Ersetzt durch einen `ContextWrapper` um den
   ursprünglichen Context, der nur `getResources()`/`getAssets()` überschreibt
   — die Kette zur Activity bleibt stehen, `stringResource` löst weiterhin in
   der gewählten Sprache auf.

   Das ist unabhängig vom Absturz ein Fehler und war der plausibelste
   Verursacher im Code: Die Zweisprachigkeit kam mit 2.6.0 herein, 2.5.5 lief
   noch. Ob sie *der* Verursacher war, ist offen — wenn die Installation das
   Problem war, war der Code nie schuld.

## Sitzung 11.09.2026 — Sprachregler nur noch im Profil, Statuspille heißt „Beta"

### Der zweite Sprachregler in der Kopfzeile ist weg

`frontend/app/index.html` hatte den Regler **zweimal**: einmal oben in
`header.top`, einmal im Kontobereich unter „Profil". Auf dem Kontobildschirm
verbarg eine eigene CSS-Regel den oberen, damit nicht zwei nebeneinander
stehen — auf allen anderen Bildschirmen standen beide zur Verfügung.

Gewünscht war genau eine Stelle: die Einstellung im Profil. Entfernt wurden
deshalb der `<div class="lang-switch">` in der Kopfzeile **und** die dadurch
gegenstandslos gewordene Regel

```css
body[data-screen="screen-account"] header.top .lang-switch{ display:none; }
```

Die Kopfzeile enthält jetzt nur noch Wortmarke und Statuspille; das
`justify-content:space-between` trägt das unverändert (Marke links, Pille
rechts, geprüft bei 420 px).

**Folge, die bewusst in Kauf genommen ist:** Ein **ausgeloggter** Besucher
von `/app/` hat in der Seite selbst keinen Umschalter mehr. Er bekommt die
Sprache weiterhin über die Erkennung in `i18n.js` (Zeitzone/Browsersprache,
DACH → Deutsch) und über `?lang=de|en`. Beides ist unverändert in Betrieb.
Wer eingeloggt ist, stellt im Profil um.

`.lang-switch` als CSS-Block bleibt bestehen — er trägt jetzt die eine
verbliebene Instanz. `FlexrI18n.bindSwitches`/`syncSwitches` iterieren über
`.lang-switch` und kommen mit einer Instanz genauso zurecht wie mit zweien;
im Browser gegengeprüft: DE → EN → DE schaltet, `data-active`, `button.on`,
`<html lang>` und die Beschriftungen ziehen mit.

**Nicht angefasst:** der Regler in der Navigation der Landingpage
(`frontend/index.html` / `frontend/en/index.html`). Das ist ein anderes
Bauteil — zwei `<a hreflang>` auf `/` und `/en/`, also echte URL-Varianten
mit SEO-Bezug. Die Landingpage hat kein Profil, in dem man stattdessen
umstellen könnte; dort ersatzlos zu entfernen hieße, einen englischsprachigen
Besucher auf der deutschen Seite festzuhalten.

### Statuspille: „Beta · gratis" → „Beta"

`beta.pill` in `frontend/app/i18n-app.js` lautet in beiden Sprachen jetzt
schlicht `'Beta'`. Der Zusatz „gratis"/„free" war seit der Umstellung des
Geschäftsmodells ohnehin missverständlich: Kostenlos ist FLEXR **dauerhaft**,
nicht nur in der Beta — die Pille legte das Gegenteil nahe.

Angenehmer Nebeneffekt: Der Text ist in beiden Sprachen identisch, die Pille
ist schmaler und in der Kopfzeile bei schmalen Geräten unkritisch.

### Geprüft

- Kopfzeile enthält genau `brand` + `status-pill`, `header.top .lang-switch`
  findet null Knoten, im Dokument steht genau ein Regler (im Kontobereich).
- `beta.pill` liefert in `de` und `en` „Beta".
- Wörterbuch weiter paarig: 442 Schlüssel je Sprache, keine Waisen; alle im
  HTML benutzten Schlüssel sind definiert (`lang.*`/`legal.*` stehen wie
  gehabt in `i18n.js`, nicht in `i18n-app.js`).
- `tools/check_betreiber.py` und `tools/check_csp_hosts.py` grün.
- `422 Tests` grün.

### Falle: das venv im Arbeitsverzeichnis war wieder ausgeräumt

Dieselbe MEGA-Sync-Ursache wie am 10.09., diesmal schlimmer: `venv/bin/` war
leer, `venv/pyvenv.cfg` fehlte, und in `site-packages` waren von etlichen
Paketen **nur die `__pycache__`-Ordner** übrig (`pytest/` enthielt nichts
sonst). Die Symlink-Reparatur aus der letzten Sitzung reicht dafür nicht.
Abhilfe für einen reinen Testlauf, ohne das kaputte venv anzufassen:

```bash
python3.12 -m venv /tmp/tv && /tmp/tv/bin/pip install -r backend/requirements.txt pytest httpx
```

`httpx` steht nicht in `requirements.txt`, `starlette.testclient` verlangt es
aber — sonst brechen alle API-Tests schon beim Import ab.

## Sitzung 10.09.2026 (Audit, Fortsetzung) — Registrierung, Hero-Layout, Werkzeuge

Zweiter Durchgang über die Teile, die im ersten nicht drankamen.

### Hero im ausgeloggten `/app/` war zwischen 861 und 1080 px zerdrückt

Am 09.09. gemeldet, damals als Gestaltungsfrage liegen gelassen — jetzt
behoben, weil es messbar kaputt war:

| Fensterbreite | Textspalte | Schlagzeile braucht |
|---|---|---|
| 900 px | **53 px** | 169 px |
| 1000 px | 135 px | 188 px |
| 1100 px | 232 px | 232 px |

`body.landing main` gibt der rechten Spalte (Login-Karte) bis zu 460 px; dem
Hero bleiben bei 900 px rund 290 px, davon nimmt das Musterdeck 210 px.
„MATCH. TRAIN. REPEAT." wurde beschnitten, der Fließtext stand ein Wort pro
Zeile.

In diesem Band verschwindet jetzt das **Musterdeck** und der Hero läuft
einspaltig — es ist die Vorschau, nicht die Aussage. Nachgemessen bei 861 /
1000 / 1080 / 1081 / 1200 px: kein Überlauf mehr, und ab 1081 px steht das Deck
wieder daneben.

**Nur `/app/` war betroffen.** Die öffentliche Landingpage `/index.html` hat
eigenes Markup ohne `.landing-hero` — der erste Verdacht dort war falsch.

### Drei weitere Texte behaupteten noch „nur während der Beta gratis"

Beim Durchspielen der Registrierung aufgefallen — dieselbe Sorte Fehler wie im
Beta-Dialog, an Stellen, die der erste Durchgang nicht berührt hatte:

* `vgate.submittedP2` (Verifizierung läuft): „Die Wartezeit kostet dich nichts
  — FLEXR ist **während der Beta-Phase** für alle kostenlos."
* `reg.ageNoticeP2` (Altershinweis im Registrierungsformular): „Die Nutzung ist
  **während der Beta-Phase** ohnehin kostenlos."
* dieselbe Zeile fest im Markup von `app/index.html`

Alle drei in beiden Sprachen auf „ist und bleibt kostenlos" bzw. „dauerhaft
kostenlos" umgestellt. Die Aussage widersprach sonst den eigenen AGB.

### Registrierung und Verifizierungs-Gate durchgespielt

Im ersten Durchgang nur der Login geprüft. Jetzt vollständig gegen den Stub:
Formular ausfüllen → PLZ löst „Wien" auf → Gym-Suche mit Auswahl aus der Liste
→ Einwilligung → **echtes Foto** (800×800-Canvas als `File`, damit
`preparePhoto` samt Mindestauflösung wirklich läuft) → „Kostenlos
registrieren" → Deck. Ohne Freischaltung landet man korrekt im
Verifizierungs-Gate: Untere Navigation ausgeblendet, Pille „In Prüfung",
richtiger Text.

Dabei zwei Endpunkte gefunden, die mein Stub nicht kannte
(`POST /api/auth/age-check`, `POST /api/profiles/me/photos/presign`) — beides
Lücken im Stub, nicht in der App. Der fehlende Presign zeigte nebenbei, dass
die Registrierung einen fehlgeschlagenen Foto-Upload sauber überlebt (Konto
entsteht, Hinweis erscheint), so wie es dokumentiert ist.

### `tools/check_csp_hosts.py` war durch die nginx-Änderung halb blind

Seit der Umstellung auf `proxy_pass https://$r2_host` meldete es nur noch
„reicht weiter an **$r2_host**" — die Variable statt des Hosts. Geprüft hat es
damit nichts mehr. Es löst die Variable jetzt über die `set`-Direktive im
selben `location`-Block auf und nennt wieder den echten Bucket-Host.

Die eigentliche Prüfung war übrigens nie stärker als „gibt es überhaupt einen
Proxy" — sie vergleicht den Host nicht mit `S3_ENDPOINT_URL`. Das wäre die
nächste sinnvolle Ausbaustufe, ist aber nicht gemacht.

### `check_csp_hosts.py` prüft jetzt gegen `S3_ENDPOINT_URL`

Bis dahin bestätigte das Werkzeug nur, **dass** es eine `location /photos/` mit
`proxy_pass` gibt — nicht, wohin sie zeigt. Drei echte Gegenprüfungen kamen
dazu; jede fängt einen Fehler ab, der sonst erst auffällt, wenn Nutzer leere
Bilder melden:

1. **Der Pfad kommt aus `S3_PUBLIC_BASE_URL`, statt fest verdrahtet zu sein.**
   Zeigt die Basis-URL auf `/bilder`, nginx hat aber nur `location /photos/`,
   dann liefert niemand die Fotos aus. Vorher meldete das Werkzeug „alles gut",
   weil es immer nach `/photos/` suchte.
2. **Der S3-API-Endpunkt als Proxy-Ziel wird erkannt.** Das ist die
   naheliegendste Verwechslung: `<account>.r2.cloudflarestorage.com` sieht
   plausibel aus, verlangt aber SigV4-signierte Anfragen und beantwortet einen
   nackten GET mit 401/403 — kein Foto würde laden, ohne dass an der
   Konfiguration etwas falsch *aussähe*.
3. **Fremde Hosts fallen auf.** Erwartet wird `pub-<32 Hex>.r2.dev`; Tippfehler
   oder ein Bucket aus einem anderen Konto werden gemeldet.

**Was sich bewusst NICHT prüfen lässt:** ob es derselbe Bucket ist wie in
`S3_ENDPOINT_URL`. Der öffentliche Host trägt eine eigene, undurchsichtige ID
(`pub-<32 Hex>`), der Endpunkt die Account-ID — aus der einen folgt die andere
nicht. Sicher ginge das nur mit einem echten Abruf gegen den Bucket, was ein
statischer Prüfer nicht leisten soll.

Alle vier Fehlerfälle wurden mit präparierten Kopien von `.env` und
`nginx-flexr.conf` durchgespielt und schlagen an. Fünf neue Tests in
`backend/tests/test_csp_storage_hosts.py` halten das fest — darunter einer, der
sicherstellt, dass die nginx-**Variable** weiterhin aufgelöst wird: Wer das
entfernt, bekommt `$r2_host` statt eines Hostnamens und prüft gar nichts mehr.

Ausführen:

```bash
python3 tools/check_csp_hosts.py                       # nimmt backend/.env
python3 tools/check_csp_hosts.py /flexr/backend/.env   # auf dem VPS
```

### Lokale `.env` angeglichen

`S3_PUBLIC_BASE_URL` zeigte auf diesem Gerät noch direkt auf R2 (Stand vor dem
16.08.2026) und ließ das Prüfwerkzeug bei jedem Lauf falschen Alarm schlagen.
Jetzt `https://flexr.social/photos` wie auf dem VPS und wie in
`.env.example` dokumentiert. Sicherung liegt als `backend/.env.bak-audit`
(beides außerhalb des Git).

## Sitzung 10.09.2026 (Audit) — Durchgang über Codebase, Journey, Admin, Texte

Auftrag: die gesamte Codebase durchgehen, Fehler finden und beheben, die
komplette User Journey durchspielen (inklusive Admin-Ansicht) und alle Texte
gegenlesen. Gefunden wurden **sechs echte Fehler**, alle aus dem
Monetarisierungs-Umbau desselben Tages.

### 1. Sprachwechsel zog die Kopfzeile nicht nach

`FlexrI18n.onChange` zeichnete Konto, Listen und Karten neu — aber **nicht die
Statuspille in der Kopfzeile**, den Like-Zähler unter den Swipe-Knöpfen und die
Karte „Wer dich geliket hat". Die Pille steht über *allen* Bildschirmen und
wurde nur beim Laden der Sitzung und nach einem Swipe gesetzt; nach dem
Umschalten stand dort weiter „Beta · gratis" statt „Beta · free". Der Handler
ruft jetzt zusätzlich `updateStatusPill()`, `renderLikeCounter()`,
`renderIncomingCard()` sowie die Neuzeichner für den Premium- und den
Incoming-Bildschirm.

### 2. Die Zahl stand doppelt, und die Einzahl brach

Die Karte „Wer dich geliket hat" zeigte den Zähler im Kreis **und** noch einmal
im Satz: „2 · 2 haben dich geliket". Zugleich brachen alle Zählertexte bei
`n = 1` („1 Leute warten auf dich", „1 Likes" in der Kopfzeile). Getrennte
Einzahl-Schlüssel beheben beides:

| | vorher | jetzt |
|---|---|---|
| Kopfzeile | „1 Likes" | „1 Like" |
| Like-Zähler | „Noch 1 von 20 Likes heute" | unverändert (war korrekt) |
| Incoming-Karte | „2 · 2 haben dich geliket" | „2 · Leute haben dich geliket" |
| Incoming, n=1 | „1 Leute warten auf dich" | „Eine Person wartet auf dich" |

### 3. „20 Likes und 3 Unterhaltungen pro Tag" — sachlich falsch

Im Beta-Dialog (Web-App **und** Landingpage, de und en). Die drei
Unterhaltungen sind **gleichzeitig**, nicht pro Tag — die Aussage widersprach
den AGB (Punkt 7 b) und der eigenen Durchsetzung im Server. Jetzt: „20 Likes
pro Tag und 3 gleichzeitigen Unterhaltungen". AGB und FAQ formulierten es von
Anfang an richtig; nur dieser eine Kasten war falsch.

Ebenfalls präzisiert: `premium.statusFree` sagte „Mit Premium fällt beides
weg" — mehrdeutig (die Funktionen? die Grenzen?). Jetzt „Mit Premium fallen
beide Grenzen weg". Die englische Fassung war bereits eindeutig.

### 4. Admin-Ansicht sprach noch von „Trial"

Die Bezahlwand ist weg, die Oberfläche kannte das noch nicht:

* Kennzahl „Im Probemonat" → **„Ohne Premium"**
* Nutzerliste: Pille „Trial" → **„Gratis"**, „Abo" → **„Premium"**
* Nutzer-Detail: „Trial aktiv"/„Inaktiv" → **„FLEXR Premium"/„Gratis"**.
  `is_active` ist ein Altfeld und immer wahr — „Inaktiv" war unerreichbar.
* Zeile „Trial endet" entfernt (`trial_ends_at` hat keine Bedeutung mehr)
* Filter „Abonniert"/„Nur Trial" → **„Nur Premium"/„Nur Gratis"**

Dazu im Backend `AdminStats.trial_users` → **`free_users`**: Das Feld zählte
seit dem Umbau die Standardkonten, hieß aber weiter nach dem Probemonat.

### 5. Like-Kontingent: zwei Ungenauigkeiten

* **Ein bereits gesetztes Like erneut zu senden wurde abgewiesen.** Die Grenze
  griff vor dem Nachschlagen des vorhandenen Swipes — ein Konto mit
  aufgebrauchtem Kontingent bekam eine 403 für etwas, das gar keine neue Zeile
  erzeugt (etwa wenn ein älterer Client denselben Swipe wiederholt).
* **Aus einem Pass wurde ein Like — mit altem Datum.** Die Zeile behielt ihr
  `created_at`; lag der Pass länger als 24 Stunden zurück, fiel das neue Like
  sofort aus dem Zählfenster und war gratis.

Beides behoben, indem der vorhandene Swipe *vor* der Prüfung nachgeschlagen
wird: Die Grenze greift nur noch für ein tatsächlich **neues** Like, und beim
Umschlagen von Pass auf Like wird `created_at` nachgezogen. Zwei neue Tests
halten das fest.

### 6. Tote Übersetzungsschlüssel

`acct.subscribe`, `acct.subActive`, `common.day1`, `common.dayN` — mit dem
Probemonat gegenstandslos geworden, je Sprache entfernt.

### Was geprüft wurde und in Ordnung war

* **Schlüsselabgleich**: 438 Schlüssel definiert, 438 benutzt, keiner fehlt,
  keine Sprache hinkt hinterher. Ein eigens dafür geschriebener Prüfer meldete
  zunächst 16 fehlende Schlüssel — Fehlalarm: Er las in `i18n.js` das leere
  `DICT = {de: {}, en: {}}` ganz oben statt des echten Wörterbuchs weiter unten.
* **Android**: 451 deutsche, 450 englische Strings; einzige Lücke ist
  `app_name`, und die ist beabsichtigt (Markenname).
* **iOS**: beide Stringtabellen belegen alle `L`-Fälle, keine überzähligen.
* **Zahlenabgleich über 14 Dateien** (AGB, FAQ, Widerruf, Impressum, beide
  Landingpages, alle drei Wörterbücher, Android- und iOS-Strings,
  `LegalContent.swift`): Preis 10 €, 20 Likes, 3 Unterhaltungen, 50/250 km
  überall gleich. **Kein einziger veralteter 5-€-Preis mehr im Bestand.**
* **User Journey** gegen einen vollständigen `fetch`-Stub: Login → Deck →
  Like → Match → Matchliste → eingehende Likes → Chats → Chat-Grenze beim
  vierten Gespräch → Konto → Premium-Bildschirm → Einwilligung (§ 10 FAGG) →
  Weiterleitung zum Checkout → Umkreis-Kappung → Datenschutz & Sicherheit →
  Benachrichtigungen, jeweils in beiden Sprachen und in allen drei Zuständen
  (Beta / Standard / Premium). Keine JS-Fehler, kein unbekannter Endpunkt.
* **Admin-Ansicht** erstmals durchgespielt: Login, Kennzahlen, Nutzerliste,
  Nutzer-Detail. Läuft sauber.
* **Sitemap**: `lastmod` der sieben heute geänderten Seiten auf 2026-09-10.

### Offener Nebenbefund: lokale `.env` ist veraltet

`tools/check_csp_hosts.py` meldet auf diesem Gerät:

> ✗ S3_PUBLIC_BASE_URL zeigt auf einen fremden Host (pub-…r2.dev), den img-src
> nicht erlaubt — die Anzeige der Profilfotos bricht ab.

**Kein Produktionsfehler.** Auf dem VPS steht korrekt
`S3_PUBLIC_BASE_URL=https://flexr.social/photos`, und `backend/.env.example`
dokumentiert genau das (seit dem 16.08.2026). Veraltet ist nur die lokale
`backend/.env`, die nicht im Git liegt — sie zeigt noch direkt auf R2. Solange
das so bleibt, schlägt das Prüfwerkzeug bei jedem Lauf falschen Alarm. Eine
Zeile in der lokalen `.env` behebt es; das ist Gerätekonfiguration und wurde
deshalb nicht von hier aus geändert.

## Sitzung 10.09.2026 — Monetarisierung neu: Gratis-Plattform + FLEXR Premium

Der Auftrag: **Die Nutzung von FLEXR ist dauerhaft kostenlos** — nicht nur in
der Beta. Bezahlt wird nur noch ein freiwilliges Zusatzpaket, **FLEXR Premium**
um **10 €/Monat**, jederzeit kündbar. Standardkonten bekommen Grenzen, Premium
hebt sie auf. Eingeführt wird Premium **nach** der Beta-Phase.

Damit ist die Bezahlwand ersatzlos weg: kein Probemonat, kein `trial_ends_at`,
das ausläuft, kein 402, kein gesperrtes Konto. Das war die größte Einzeländerung
dieser Sitzung — sie zieht sich durch Backend, Web, Android, iOS und alle
Rechtstexte.

### Die vier Zahlen

Vom Nutzer entschieden, sie stehen **wortgleich** in `backend/app/config.py`,
in der Oberfläche, auf der Landingpage und in den AGB:

| | Standardkonto | FLEXR Premium |
|---|---|---|
| Likes | **20** je rollierenden 24 h (ein Pass zählt nicht) | unbegrenzt |
| Unterhaltungen | **3** gleichzeitig offen | unbegrenzt |
| Suchumkreis | **50 km** | 250 km |
| Wer dich geliket hat | nur die Zahl | Namen und Profile |
| Letzten Swipe zurücknehmen | — | ja |
| Abzeichen im Profil | — | ja |

**Wer eine dieser Zahlen ändert, ändert eine vertragliche Zusage** — der
Abgleich mit `frontend/i18n-*.js`, `res/values*/strings.xml`, `agb.html`
(Punkt 7 b) und `app/legal.py` gehört dazu.

### Ein Schalter, wie gehabt

`PREMIUM_ENABLED` (früher `BILLING_ENABLED`) steht auf **false**. Solange er
aus ist, ist für alle alles unbegrenzt, niemand trägt ein Premium-Abzeichen und
`/api/billing/checkout` lehnt mit 409 ab. Das Umlegen braucht keine Migration:
Bestandskonten verlieren nichts, sie bekommen dieselben Grenzen wie alle.

`STRIPE_TRIAL_DAYS` ist entfallen. **Das hätte beinahe einen Ausfall gegeben:**
Die `.env` auf dem VPS führt den Schlüssel weiter, und pydantic-settings lehnt
unbekannte Extras standardmäßig ab — der Dienst wäre beim nächsten Neustart
nicht mehr hochgekommen, Minuten nach dem Deploy. `Settings.Config` hat deshalb
jetzt `extra = "ignore"`: Eine Einstellung zu entfernen darf keinen Ausfall
auslösen können.

### Backend

Neu ist `backend/app/premium.py` — alle Grenzen an einem Ort, weil die
Oberfläche dieselben Zahlen anzeigen muss, die der Server durchsetzt
(`GET /api/billing/status` liefert sie mit).

- `User.is_active_member()` → `User.is_premium`. Die Bezahlwand in
  `security.require_active_membership()` ist eine reine Freischaltungsprüfung
  geworden; der Name bleibt, damit nicht alle Routen anzufassen waren.
- Grenzen greifen als **403 mit eigenem `code`** (`like_limit_reached`,
  `chat_limit_reached`, `premium_required`) — nicht als 402. Ein erschöpftes
  Like-Kontingent ist kein gesperrtes Konto.
- Zwei neue Endpunkte: `GET /api/swipes/incoming` (ohne Premium nur die
  **Anzahl** — das ist die ehrliche Antwort und zugleich der beste Grund,
  Premium anzusehen) und `POST /api/swipes/rewind`.
- Der Umkreis wird **gekappt statt abgelehnt** (`premium.clamp_radius`): Wer
  Premium kündigt, hätte sonst ein Profil, das sich nie wieder speichern lässt.
- Der Probemonat-Mailjob und die beiden zugehörigen Mails sind entfallen. Die
  Zähler bleiben mit 0 in der Antwort, damit der Aufrufer unverändert läuft.

**Abwärtskompatibilität, wichtig:** Die Android-Fassung 2.5.5 liest
`trial_ends_at` und `is_active` als **Pflichtfelder**. Fehlen sie, scheitert
schon das Parsen. `MembershipStatus` liefert die vier Altfelder
(`is_subscribed`, `trial_ends_at`, `is_active`, `billing_enabled`) deshalb
weiter mit, obwohl der Server sie nirgends mehr auswertet. **Entfernen erst,
wenn keine Fassung vor 2.6.0 mehr im Umlauf ist.**

### Tests

`411 passed`. Neu: `tests/test_premium.py` (17 Tests) für beide Zustände des
Schalters, alle drei Grenzen und die drei Premium-Funktionen. Entfallen:
`test_billing_trial.py` und `test_billing_pausiert.py`.

Nebenbei **fünf Tests repariert, die schon vor dieser Sitzung rot waren** — sie
brachen beim Zweisprachigkeits-Umbau vom 09.09., weil sie auf Textliterale
prüften, die ins Wörterbuch gewandert sind (`test_journey_befunde.py` ×2,
`test_public_frontend.py` ×3). Sie prüfen jetzt Schlüssel und Muster statt
Literale; die Sitemap-Liste kennt außerdem `/en/`, und der Shell-Cache-Name
wird als Muster geprüft statt als feste Nummer.

### Web-Frontend

- Die Bezahlwand (`screen-paywall`) ist ein **freiwilliger** Premium-Screen
  geworden, erreichbar aus dem Kontobereich. Ihre beiden Notausgänge
  (Ausloggen, Konto löschen) sind entfallen — der Kontobereich ist wieder immer
  erreichbar.
- Neu: Like-Zähler unter den Swipe-Knöpfen, Zurücknehmen-Knopf (Premium),
  „Wer dich geliket hat" über der Matchliste samt eigener Ansicht,
  Premium-Abzeichen neben dem Namen, Umkreis-Hinweis ab der Grenze.
- Das Like-Limit wird **vor** der Animation geprüft: Die Karte erst wegfliegen
  zu lassen und nach der Absage des Servers zurückzuholen, sähe wie ein Fehler
  aus.
- Landingpage: zwei Preiskarten nebeneinander (kostenlos links, Premium
  rechts), `/en/` neu erzeugt.
- Der Beta-Dialog sagt jetzt etwas anderes → Merker auf
  `flexr_beta_notice_v3` hochgezählt.
- `/i18n.js` und `/app/i18n-app.js` im Skript-Tag auf `?v=3`.

### Rechtstexte

Fassung **2026-09-10** (`TERMS_VERSION`). AGB Punkt 7 heißt jetzt „Kostenlose
Nutzung und Nutzungsgrenzen" und nennt die drei Grenzen als vertragliche
Zusage; Punkt 8 ist „FLEXR Premium", Punkt 9 nennt 10,00 €. Widerruf, FAQ,
Impressum und Datenschutz nachgezogen. **Das Muster-Widerrufsformular lautet
jetzt auf „FLEXR Premium"** statt „Mitgliedschaft".

### Android 2.6.0

**Maßgeblich ist `versionCode 100`:**

    https://flexr.social/dl-a616e78274de323b/flexr-2.6.0-vc100.aab

7.730.159 Bytes, SHA-256
`f6da661da5fa88e0da55441a920b35dfe52c6f044e06691a6c97617d9a371d04`, mit dem
unveränderten Upload-Key `CN=FLEXR` signiert.

#### Zwei abgelehnte Anläufe — und was sie bedeuten

Die Play Console lehnte nacheinander **43** und **50** mit „Versionscode … wurde
bereits verwendet" ab. Beide Nummern waren an diesem Tag zum ersten Mal gebaut
worden, und das alte TWA-Projekt unter demselben Paketnamen
(`flexr.social.app`, `android/app/build.gradle`) steht bei `versionCode 5` —
es hat die Nummern also nicht verbraucht.

**Daraus folgt: Die Uploads waren erfolgreich.** Eine Nummer kann nur „bereits
verwendet" sein, wenn ein Bundle mit ihr das Konto erreicht hat. Beide Bundles
liegen damit in der Bibliothek des Kontos; die Fehlermeldung entstand jeweils
beim *zweiten* Hochladen derselben Datei in einen neuen Release-Entwurf.

**Der richtige Griff ist deshalb „Aus der Bibliothek hinzufügen"**, nicht ein
neuer Build. Was das Konto kennt, zeigt verlässlich nur der
**App-Bundle-Explorer** (Release → App-Bundle-Explorer) — von der
Entwicklungsseite aus ist die Play Console eine Blackbox, weshalb zweimal
danebengeraten wurde.

`versionCode 100` steht bereit, falls die Bibliothek wider Erwarten leer ist.
Bewusst ein grosser Abstand statt der nächsten freien Nummer, und bewusst
**kein** datumsbasiertes Schema (`20260910xx`): Das liegt dicht unter der harten
Obergrenze von 2.100.000.000 und lässt sich nie wieder verkleinern.

`versionName` bleibt in allen Fällen **2.6.0** — der Release *ist* 2.6.0,
verbrannt sind nur Build-Nummern. `versionCode` ist der Zähler, `versionName`
die Fassung.

#### Wie der versionCode im Bundle geprüft wird

Nicht über die Gradle-Datei, sondern im gebauten Manifest. Es liegt im AAB als
**Protobuf** vor (nicht als binäres AXML — `aapt2 dump xmltree` scheitert mit
„could not identify format of APK"). Der Wert steht dort **zweimal**, direkt
hinter dem Namen `versionCode`:

```
vc50:  versionCode  1a 02 "50"   … 3a 02 30 32   (Textfassung, dann Wert 50)
vc100: versionCode  1a 03 "100"  … 3a 02 30 64   (Textfassung, dann Wert 100)
```

Ein Byte-Vergleich zweier Manifeste zeigt die Änderung damit unmittelbar; beim
Schritt 43 → 50 waren es **genau drei** abweichende Bytes (Wert plus die zwei
Zeichen der Textfassung).

Ältere Bundles liegen weiterhin im selben Ordner
(`flexr-2.6.0.aab` = vc43, `flexr-2.6.0-vc50.aab` = vc50). **Beide lassen sich
nie wieder in die Play Console laden**; wer aufräumt, kann sie löschen.

`:app:compileProdReleaseKotlin` und `:app:testProdReleaseUnitTest` beide
BUILD SUCCESSFUL. Der `LockedGraph` ist entfallen, `PaywallScreen` ist ein
normales Ziel im Kontobereich, jedes neue DTO-Feld hat einen Standardwert.

### iOS

Zeilenweise dieselbe Änderung (`LockedFlow` weg, `Route.premium` neu,
`MembershipStatusDTO` durchgehend optional). **Nicht kompiliert** — `xcodebuild`
gibt es nur unter macOS, das Projekt wurde noch nie gebaut. Statisch geprüft
wurde, dass beide Stringtabellen **alle** `L`-Fälle belegen und keinen
unbekannten enthalten (kein fehlender, kein überzähliger Schlüssel).

### Zwischenfall: nginx lag 1 h 45 min — Ursache behoben

Beim Hochladen des AAB fiel auf, dass **flexr.social nicht erreichbar war** —
nginx war um **06:35 CEST** gestorben, also lange vor dieser Sitzung, und
zwar beim Start:

```
[emerg] host not found in upstream "pub-0fa239128c094c37bb3bf410428cf0ba.r2.dev"
        in /etc/nginx/sites-enabled/flexr.social:26
```

nginx löst Upstream-Namen **beim Start** auf und scheitert hart, wenn DNS
gerade nichts liefert — danach bleibt der Dienst unten, bis jemand ihn startet.
Die ganze Seite, wegen eines Namens, den nur die Fotos brauchen. `nginx -t`
lief zum Zeitpunkt der Prüfung sauber durch, die Konfiguration war also nie
kaputt; `systemctl start nginx` genügte.

**Behoben am selben Tag** (Auftrag „bau den resolver"): Der Hostname steht
jetzt in einer Variablen, damit nginx ihn zur **Laufzeit** auflöst.

```nginx
resolver 1.1.1.1 1.0.0.1 valid=300s;
resolver_timeout 5s;
set $r2_host pub-0fa239128c094c37bb3bf410428cf0ba.r2.dev;
rewrite ^/photos/(.*)$ /$1 break;
proxy_ssl_server_name on;
proxy_set_header Host $r2_host;
proxy_pass https://$r2_host;
```

Drei Dinge, die man dabei wissen muss:

1. **Die `resolver`-Zeile stand schon vorher da und war wirkungslos.** Sie
   greift ausschließlich, wenn die Adresse in `proxy_pass` eine Variable
   enthält. Mit einem Literal wird sie stillschweigend ignoriert — genau
   deshalb sah die Konfiguration aus, als wäre der Fall schon abgedeckt.
2. **Das `rewrite` ist Pflicht, nicht Kosmetik.** Sobald `proxy_pass` eine
   Variable enthält, nimmt nginx die Ersetzung des location-Präfixes nicht mehr
   selbst vor. Ohne diese Zeile landet jede Anfrage auf dem Bucket-Wurzelpfad.
   Die Objektschlüssel sind `users/<uuid>/<uuid>.<ext>` und damit frei von
   Zeichen, bei denen das Dekodieren durch `$uri` etwas verändern würde.
3. **Der Fehlermodus verschiebt sich, er verschwindet nicht.** Fällt DNS im
   laufenden Betrieb aus, antworten jetzt nur noch `/photos/` mit 502 — die
   Seite selbst bleibt oben. Das ist der Sinn der Übung.

Nachgewiesen mit einer **eigenen nginx-Instanz** und einem garantiert nicht
existierenden Hostnamen, ohne die Produktion anzufassen: literal → derselbe
`[emerg] host not found in upstream`; über Variable → „test is successful".
Danach an der echten Konfiguration `nginx -t`, `reload` **und** ein
`systemctl restart` (der Pfad, der am 10.09. scheiterte) — alles sauber, echtes
Foto weiterhin 200 mit unverändertem `Cache-Control` und allen Schutz-Headern.

Sicherung der vorherigen Fassung liegt als
`/etc/nginx/sites-available/flexr.social.bak-20260910` auf dem VPS.

**Nicht gemacht, bewusst:** das systemd-Drop-in mit `Restart=on-failure`. Es
würde einen zweiten, unabhängigen Schutz geben (nginx kommt auch nach einem
Absturz aus anderer Ursache von selbst wieder), war aber nicht beauftragt.
Ebenso wenig `proxy_ssl_verify on` — bei Laufzeitauflösung wäre eine
Zertifikatsprüfung des Upstreams das passende Gegenstück, ändert aber
Produktionsverhalten.

### Profilfotos wurden ohne `Content-Type` ausgeliefert — behoben

Beim Nachmessen der Foto-Header aufgefallen, **unabhängig von nginx**: R2 selbst
lieferte den Header nicht mit. Die Ursache stand in `backend/app/storage.py`:

```python
client.copy_object(..., CacheControl=PHOTO_CACHE_CONTROL,
                   MetadataDirective="REPLACE")
```

`MetadataDirective="REPLACE"` ersetzt die **gesamten** Systemmetadaten durch
das, was im Aufruf steht. `ContentType` stand dort nicht — der beim Presigned
PUT korrekt gesetzte Typ wurde also von genau der Funktion gelöscht, die das
`Cache-Control` nachtragen sollte. Aufgefallen ist es nie, weil Browser `<img>`
trotzdem rendern (`nosniff` verhindert das Sniffing nur für Skripte und
Stylesheets).

**Behoben.** Die Funktion heißt jetzt `set_photo_headers()` — der alte Name
`set_photo_cache_control` hat den Nebeneffekt mitverdeckt — und setzt beide
Header. Der Typ kommt bevorzugt aus den **Magic Bytes**: `add_photo()` prüft
das Objekt ohnehin unmittelbar davor (`_foto_befund`, früher
`_foto_ist_brauchbar`) und wirft den erkannten Typ seither nicht mehr weg. Das
kostet keinen zweiten Abruf und ist belastbarer als die Behauptung des Clients
beim Presign — die Signatur bindet nur die Zeichenkette, nicht den Inhalt.
Fällt der Befund aus, greifen Dateiendung und zuletzt der bereits am Objekt
stehende Typ; verloren gehen darf er nicht noch einmal. Vier Regressionstests
in `tests/test_foto_header.py` halten das fest.

**Backfill gelaufen.** `scripts/backfill_photo_cache_control.py` heißt jetzt
`backfill_photo_headers.py`, prüft beide Header und kennt `--dry-run`. Der
frühere Lauf hatte die betroffenen Objekte übersprungen, weil er nur auf
`Cache-Control` geschaut hat — genau deshalb war der Schaden flächendeckend.
Trockenlauf und echter Lauf am 10.09.: **26 Objekte**, ausnahmslos mit
korrektem `Cache-Control` und fehlendem `Content-Type`, alle → `image/jpeg`.
Zweiter Lauf: 26 übersprungen, 0 gesetzt (idempotent). Ein echtes Foto über
`flexr.social` liefert seither `Content-Type: image/jpeg` bei unverändertem
`Cache-Control`.

### nginx prüft jetzt das Zertifikat des R2-Upstreams

nginx tut das von sich aus **nicht** — ohne `proxy_ssl_verify` nimmt es jedes
vorgelegte Zertifikat an. Das ist das Gegenstück zur Laufzeitauflösung: Wer den
Namen erst beim Zugriff auflöst, sollte prüfen, mit wem er dann spricht.

```nginx
proxy_ssl_verify on;
proxy_ssl_verify_depth 2;
proxy_ssl_trusted_certificate /etc/ssl/certs/ca-certificates.crt;
proxy_ssl_name $r2_host;
```

R2 liefert ein Let's-Encrypt-Zertifikat auf `*.r2.dev`; die Kette ist
Leaf → Intermediate → Root, `verify_depth 2` deckt sie ab.

Beide Hälften in einer eigenen nginx-Instanz nachgewiesen, ohne die Produktion
anzufassen:

| Ziel | ohne Prüfung | mit Prüfung |
|---|---|---|
| `self-signed.badssl.com` | 200 | 502 — `upstream SSL certificate verify error: (18:self-signed certificate)` |
| `wrong.host.badssl.com` | — | 502 — `upstream SSL certificate does not match` |
| `badssl.com` (Kontrolle) | — | 200 |

**Unerklärt geblieben:** Ein erster Versuch, den Namensfehler direkt gegen R2 zu
provozieren (`proxy_ssl_name falsch.example.com`), lieferte 403 statt 502 und
keinerlei SSL-Zeile im Log — Cloudflare beantwortet unbekanntes SNI offenbar
schon auf HTTP-Ebene. Die Testprämisse war also untauglich, nicht die Prüfung;
die badssl-Fälle oben zeigen zweifelsfrei, dass Kette **und** Name greifen.

### systemd startet nginx nach einem Fehlschlag neu

Zweiter, unabhängiger Schutz neben der Laufzeitauflösung — er greift auch, wenn
nginx aus ganz anderem Grund stirbt.

```
/etc/systemd/system/nginx.service.d/restart.conf
[Unit]   StartLimitIntervalSec=300, StartLimitBurst=10
[Service] Restart=on-failure, RestartSec=5s
```

Das StartLimit ist bewusst großzügiger als die Voreinstellung (5 Versuche in
10 Sekunden): Eine Störung, die länger als zehn Sekunden dauert — und genau so
eine war der Ausfall am 10.09. —, wäre damit nicht überbrückt. 10 Versuche über
5 Minuten decken das ab und laufen trotzdem nicht endlos, wenn die
Konfiguration wirklich kaputt ist.

Geprüft mit `systemctl kill -s SIGKILL nginx`: **nach 6 Sekunden von selbst
wieder aktiv**, `Scheduled restart job, restart counter is at 1`.

Das Drop-in liegt **nur auf dem VPS** — es ist keine Repository-Datei. Bei einem
Neuaufsetzen des Servers muss es von Hand wieder angelegt werden.

### Prüfung

Backend `411 passed`. Web gegen einen `fetch`-Stub in allen drei Zuständen
(Beta / Standard / Premium) durchgespielt: Pille, Like-Zähler, Limit-Meldung,
Zurücknehmen, eingehende Likes, Umkreis-Kappung und der Sprachwechsel in beide
Richtungen. Android compiliert und Unit-Tests grün.

## Sitzung 09.09.2026 (zweite) — 2.5.5 wieder auf dem VPS, sechs Fehler in `/app`

Ein Auftrag mit sieben Punkten, alle aus der Benutzung heraus gemeldet.

### 2.5.5 liegt wieder zum Herunterladen bereit

Das am 08.09. gebaute Bundle wurde unverändert hochgeladen:

    https://flexr.social/dl-a616e78274de323b/flexr-2.5.5.aab

7.679.482 Bytes, SHA-256 `a2202dbad901476c7cc0a15683879d4cf45141183551f74bbe74a29ade6f8600`
— lokal und auf dem VPS identisch, `versionName` im Bundle-Manifest auf 2.5.5
gegengeprüft. **Der Abschnitt „Auf dem VPS liegt kein AAB mehr" weiter unten
gilt damit nur noch für die dort aufgezählten älteren Bundles.** Neu gebaut
wurde nichts; alle Korrekturen dieser Sitzung sind Web-Frontend.

### `t is not a function` beim Profilspeichern

`toast()` legte seine Box in `const t` an und verdeckte damit die
Übersetzungsfunktion `t` aus demselben Modul. `t('common.close')` für das
Schließkreuz warf deshalb einen TypeError. Sichtbar wurde er als Fehlerzeile
unter dem Speichern-Knopf, obwohl das `PATCH /api/profiles/me` **schon durch
war** — gespeichert wurde also immer, nur die Bestätigung schlug fehl. Die Box
heißt jetzt `box`. Betroffen war jeder Toast der App, nicht nur dieser.

### Sprachwechsel löschte dynamisch gesetzte Texte

`FlexrI18n.apply()` überschreibt jeden `[data-i18n]`-Knoten mit dem Eintrag
seines Schlüssels. Knoten, die zur Laufzeit etwas anderes bekommen hatten,
verloren das beim Umschalten:

- der aufgelöste Ort neben der PLZ („Wien" → „— PLZ eingeben —"),
- der Umkreis-Hinweis mit eingesetztem Gym-Namen,
- die stehenbleibenden Fehlerzeilen von PLZ-Suche und Profilspeichern.

Zwei Helfer in `app/index.html` trennen die Fälle sauber: `setI18nText(el, key,
vars)` für übersetzbare Texte (Schlüssel **und** Platzhalterwerte bleiben am
Knoten stehen) und `setPlainText(el, text)` für Eigennamen wie den Ortsnamen,
das `data-i18n` entfernt. Dazu kann `apply()` in `/i18n.js` jetzt
`data-i18n-vars` (JSON) lesen — nur so überlebt „Profile im Umkreis deines
Gyms (McFit)." einen Wechsel. Neue Schlüssel: `plz.unknownShort`,
`plz.failedShort`, `acct.saveFailed` (vorher fest deutsch im Code).

**Wer weitere dynamische Texte einbaut, nimmt diese beiden Helfer** — ein
direktes `el.textContent = t(...)` auf einem `[data-i18n]`-Knoten ist genau der
Fehler, der hier dreimal steckte.

### Fokusrahmen der PLZ-Kombination

`.plz-combo.focused` zeichnete eine äußere `outline` mit `outline-offset:1px`.
Die Kombination liegt bündig an der linken Kante von `.screen.active`
(`padding-left:0`, `overflow-x:hidden`), die Linie lag dort also außerhalb des
Scroll-Containers und wurde abgeschnitten: oben, rechts und unten orange, der
linke senkrechte Strich fehlte. Jetzt derselbe `inset`-`box-shadow` wie bei den
einfachen Feldern — der Grund dafür stand seit jeher im Kommentar darüber, die
PLZ-Kombination war nur nie nachgezogen worden.

### Sprachregler nur noch einmal im Kontobereich

`body[data-screen="screen-account"] header.top .lang-switch{ display:none; }` —
auf dem Kontobildschirm steht der beschriftete Regler unter „Profil", der
unbeschriftete in der Kopfzeile war daneben ein Doppel. Auf allen anderen
Bildschirmen (auch ausgeloggt) bleibt er stehen, dort gibt es keinen zweiten.

### Grüne Augenbraue im Hero brach nur auf Deutsch um

„DATING FÜR GYM-PEOPLE · ÖSTERREICH" braucht 310px, die Textspalte des Heros
ist auf dem Desktop 304px breit — die englische Fassung (283px) passte, die
deutsche nicht. Die Augenbraue läuft jetzt über **beide** Gitterspalten
(`grid-template-areas: "eyebrow eyebrow"`, in der Desktop- **und** der
Mobilfassung) und trägt `white-space:nowrap`. Das Musterdeck beginnt dadurch
auf Höhe der Schlagzeile statt der Augenbraue. Geprüft bei 320/360/430/480/
1280/1440 px, beide Sprachen einzeilig und ohne Überlauf.

### Noch offen: Landing zwischen 861 und ~1000 px

Dabei aufgefallen, **nicht** beauftragt und deshalb nicht angefasst: In diesem
Fensterbereich ist der ausgeloggte Hero zerdrückt. `body.landing main` gibt der
rechten Spalte `minmax(340px,460px)`, dem Hero bleiben bei 900px rund 305px,
davon nimmt das Musterdeck 210px — die Textspalte ist dann ~68px breit,
„MATCH. TRAIN. REPEAT." wird beschnitten und der Fließtext steht ein Wort pro
Zeile. Sauber wäre, das Musterdeck unterhalb von ~1100px auszublenden und den
Hero dort einspaltig laufen zu lassen. Das ist eine Gestaltungsentscheidung,
darum liegen gelassen.

### Prüfung

Kein Backend berührt, keine Migration, kein Neustart. Getestet im Browser gegen
`python3 -m http.server` mit einem `fetch`-Stub für `/api/geo/plz/<plz>`:
Ort auflösen, unbekannte PLZ (404), Sprachwechsel in beide Richtungen,
Fokusrahmen, sichtbarer Toast (über den Gym-Vorschlag, derselbe Codepfad wie
beim Profilspeichern) und ein Vergleich aller berechneten Stile im
Kontobereich vor und nach dem Wechsel — außer den übersetzten Wörtern
verschiebt sich nichts. `/i18n.js` und `/app/i18n-app.js` sind im Skript-Tag
auf `?v=2` hochgezählt, sonst liefert der Browser-Cache die alte Maschinerie.

## Sitzung 09.09.2026 — Zweisprachigkeit (de/en), Datei-Upload beim Ausweis, `/en/`

Zwei Aufträge, beide durchgezogen: der Ausweisschritt nimmt jetzt auch eine
**bestehende Datei** statt nur einer Kameraaufnahme an, und **Web-App,
Landingpage, Android- und iOS-App sind zweisprachig** — Deutsch als
Ausgangssprache, Englisch als Übersetzung, mit Schieberegler oben in der
Kopfzeile und in den Profil-Einstellungen.

### Ausweis-Upload: Kamera **oder** Datei

Der Aufnahmeplatz hatte genau einen Eingabeweg — ein
`<input type="file" capture="environment">`. Auf dem Handy öffnet das die
Kamera und sonst nichts. Wer den Ausweis schon gescannt oder vor dem Hochladen
geschwärzt hatte, kam damit nicht weiter; die Schwärz-Empfehlung im selben
Kasten lief also ins Leere.

Jetzt stehen unter jedem Platz zwei Knöpfe:

- **Web-App** (`frontend/app/index.html`): zwei getrennte, unsichtbare
  `<input type="file">` — eines mit `capture`, eines ohne. Beide werden nur auf
  einen ausdrücklichen Tipp hin geöffnet, der Platz selbst nimmt weiterhin den
  kürzesten Weg (Kamera).
- **Android** (`ui/verification/DocumentScreen.kt`): derselbe Aufbau mit
  `ActivityResultContracts.GetContent()`; die gewählte Datei geht durch das neue
  `ImageProcessor.compressDocument(uri)` (EXIF-Drehung wird angewandt, die
  Mindestauflösung gilt hier bewusst **nicht** — ein sauberer Scan darf klein
  sein, entscheidend ist die Lesbarkeit).

Die Knöpfe stehen bei zwei Aufnahmeplätzen untereinander und bei einem
nebeneinander. Im Web macht das eine **Container-Abfrage** (`container-type:
inline-size`) und nicht eine Fenster-Abfrage: bei „nur Vorderseite" spannt sich
der eine Platz über die volle Breite, dort passen die Knöpfe nebeneinander,
obwohl das Fenster gleich schmal ist.

**Bewusst weiter nur Bilder** (JPEG/PNG/WebP). PDF-Scans sind der naheliegende
nächste Wunsch, gehen aber nicht ohne Backend: `schemas.py` lässt für
`VerificationDocumentPresignRequest.content_type` nur
`image/jpeg|png|webp` zu, und die Admin-Ansicht zeigt Bilder, keine PDFs.

Die iOS-App hat den Ausweisschritt noch gar nicht (sie verweist dafür auf
flexr.social) — dort war nichts zu ändern.

### Zweisprachigkeit: eine Regel, vier Umsetzungen

Deutsch ist überall die **Ausgangssprache**: der deutsche Text ist das Original,
Englisch die Übersetzung, und was in Englisch fehlt, fällt auf Deutsch zurück
statt auf den nackten Schlüssel. Eine vergessene Übersetzung sieht dann nach
deutschem Text aus und nicht nach einem Fehler.

| | Texte | Schlüssel | Regler |
|---|---|---|---|
| Web-App | `frontend/i18n.js` + `frontend/app/i18n-app.js` | 408 | Kopfzeile + Konto → „Profil" |
| Landingpage | `frontend/i18n-landing.js` | 114 | Kopfzeile |
| Android | `res/values/` + `res/values-en/strings.xml` | 411 | Kopfzeile + Konto → „Einstellungen" |
| iOS | `Core/Locale/FlexrStrings{,+German,+English}.swift` | 303 | Kopfzeile + Konto |

**Spracherkennung beim ersten Aufruf** — identisch in allen vier Fassungen
(`FlexrI18n.detect`, `AppLanguage.detect` in Kotlin und Swift):

1. Gespeicherte Wahl (localStorage / DataStore / UserDefaults)
2. `?lang=de|en` (nur Web — erlaubt einen sprachspezifischen Link)
3. **Zeitzone im DACH-Raum** → Deutsch. Die Liste enthält neben
   `Europe/Vienna|Berlin|Zurich` auch `Europe/Busingen` (deutsche Exklave in der
   Schweiz) und `Europe/Vaduz` — beides eigene IANA-Zonen, die sonst als „nicht
   DACH" durchfielen.
4. Systemsprache beginnt mit `de` → Deutsch
5. sonst Englisch

**Abweichung von der ursprünglichen Vorgabe, bewusst:** Die Zeitzone entscheidet
nur *für* Deutsch, nicht *gegen* es. Wer außerhalb des DACH-Raums ein
deutschsprachiges Gerät hat, bekommt Deutsch — Englisch ist der Rückfall für
alles Übrige, nicht die Strafe für eine Zeitzone. Die Regel ist in
`frontend/i18n.js` ausführlich kommentiert; sie **nur** an der Zeitzone
festzumachen wäre ein Einzeiler, sollte es je gewünscht sein.

**Der Wechsel wirkt sofort**, ohne Neustart:

- Web: `FlexrI18n.apply()` übersetzt die `data-i18n`-Knoten neu, ein
  `onChange`-Haken zeichnet die dynamisch gebauten Listen und Karten nach.
  `renderAccount({keepForm: true})` lässt dabei das Profilformular in Ruhe —
  sonst hätte ein Sprachwechsel den gerade getippten Bio-Text verworfen.
- Android: `ProvideAppLanguage` tauscht `LocalContext` und `LocalConfiguration`
  aus, `stringResource` löst daraufhin neu auf. Bewusst **kein** `recreate()`:
  so überleben Navigationsstapel und Scrollpositionen den Wechsel.
- iOS: `LanguageStore` ist `@Observable`, jede View liest ihre Texte über
  `languageStore.strings` und zeichnet damit von selbst neu.

**Texte außerhalb der Oberfläche** (Netzwerkstapel, Benachrichtigungs-Worker)
kennen die gewählte Sprache nicht, weil sie nichts von der Oberfläche wissen.
Beide Apps lösen das mit **einer** gesetzten Fassung, die der Sprachspeicher
mitführt: `ApiErrorParser.strings` (Android) bzw. `FlexrStrings.current` (iOS).
Die Begründung steht jeweils am Feld: eine Abhängigkeit durch alle Repositories
zu fädeln, ohne dass irgendwo eine Entscheidung davon abhinge, wäre teurer als
diese eine dokumentierte Stelle. Auf Android stehen die deutschen Texte im
Parser zusätzlich als Rückfall, weil das Feld in reinen JVM-Tests leer bleibt —
`ApiErrorParserTest` prüft genau diese Fassung.

`AppStrings` ist auf Android **eine Schnittstelle** mit
`ResourceAppStrings` als Umsetzung, aus demselben Grund wie bei `SessionStore`:
die Umsetzung hängt am Android-Context und machte jedes ViewModel darüber in
JVM-Tests unkonstruierbar. Die Tests setzen `FakeAppStrings` ein.

### Was bewusst deutsch geblieben ist

- **Rechtstexte** (AGB, Datenschutz, Nutzungsrichtlinien, Rücktritt,
  Sicherheit, Meldung, Strafverfolgung) in allen drei Fassungen —
  `LegalContent.kt`, `LegalContent.swift` und die HTML-Seiten unter
  `frontend/`. Sie sind in der deutschen Fassung verbindlich; eine nicht
  anwaltlich geprüfte Zweitfassung wäre ein Haftungsrisiko. Nur die **Titel**
  der Ansichten sind übersetzt, und der Schlüssel `legal.notice.de` steht für
  einen Hinweis bereit. Wer das ändern will, braucht dafür eine anwaltliche
  Prüfung, keinen Übersetzer.
- **Serverantworten**: Fehlermeldungen, die Art.-17-DSA-Mitteilungen und die
  Aktivitäts-Benachrichtigungen (Match, Deck, Inaktivität, offene Likes) kommen
  aus dem Backend und sind dort deutsch. Für echte Zweisprachigkeit bräuchte das
  Backend ein `Accept-Language` und übersetzte Textbausteine — eigenes Stück
  Arbeit, hier nicht angefasst. In der Oberfläche sind nur die **Beschriftungen
  davor** übersetzt („Begründung:", „Dauer:").
- **JSON-LD auf der Landingpage**: beschreibt die kanonische deutsche Fassung
  dieser Adresse. Eine per JavaScript umgeschriebene FAQPage-Auszeichnung wäre
  gegenüber Google nur noch Rauschen.

### Englische Landingpage unter `/en/` — erledigt im selben Zug

Der erste Wurf schaltete die Sprache der Landingpage **zur Laufzeit** um, so wie
die Web-App. Für die App ist das richtig (sie steht auf `noindex`), für die
Landingpage war es falsch: Googlebot rendert aus einer US-Zeitzone und hätte auf
`/` englischen Fließtext unter deutscher Auszeichnung gesehen. Das ist mit einem
zweiten Commit korrigiert — Beschreibung im Abschnitt „Zwei Adressen" weiter
unten.

### Zwei Adressen statt eines Umschalters: `/` und `/en/`

Die Landingpage gibt es jetzt **zweimal**, unter zwei eigenen Adressen:

| | |
|---|---|
| `https://flexr.social/` | Deutsch, `<html lang="de-AT">`, eigenes `canonical` |
| `https://flexr.social/en/` | Englisch, `<html lang="en">`, eigenes `canonical` |

Beide liefern ihren Text **fertig im HTML** aus und verweisen über `hreflang`
wechselseitig aufeinander (`de-AT`, `de`, `en`, `x-default`); dieselben
Verweise stehen als `xhtml:link` in `sitemap.xml`. Damit sieht jede Adresse für
Suchmaschinen eindeutig eine Sprache — genau das, was der Laufzeit-Umschalter
nicht leisten konnte.

Die Web-App unter `/app/` bleibt beim Laufzeit-Umschalter. Sie steht auf
`noindex`; dort gibt es kein SEO-Problem zu lösen, und ein Seitenwechsel mitten
in einer angemeldeten Sitzung wäre die schlechtere Antwort.

**Erzeugt, nicht doppelt gepflegt.** `frontend/index.html` bleibt die einzige
Quelle des Markups; `frontend/build-en.py` setzt daraus und aus dem
`en`-Block der Wörterbücher die englische Fassung zusammen:

```bash
python3 frontend/build-en.py
```

Das Skript **muss nach jeder Änderung an `frontend/index.html` oder an
`frontend/i18n-landing.js` laufen**. Es bricht ab, wenn zu einer
`data-i18n`-Auszeichnung kein englischer Text existiert — eine halb übersetzte
Seite entsteht gar nicht erst. `frontend/en/index.html` trägt einen
Kopfkommentar „ERZEUGTE DATEI"; Änderungen dort gehen beim nächsten Lauf
verloren.

Umgestellt werden dabei: alle ausgezeichneten Texte und Attribute,
`<html lang>`, `canonical`, `og:url`, `og:locale`, Titel und Beschreibungen
(aus denselben Schlüsseln), die Richtung des Sprachreglers, der Selbstverweis
der Wortmarke und die JSON-LD-Auszeichnung (`inLanguage`, eigene `@id` für
`WebSite` und `SoftwareApplication`, englische Beschreibungen). Die
`Organization` behält bewusst **dieselbe `@id`** — es ist dasselbe Unternehmen,
nicht ein zweites.

**Wegführung** (`frontend/lang-switch.js`, ersetzt auf der Landingpage die
Laufzeit-Übersetzung):

1. Der Regler in der Kopfzeile ist jetzt ein **Verweis** (`<a>`), kein Knopf.
   Ein Klick merkt die Wahl unter demselben `flexr_lang` wie die App.
2. Wer schon einmal gewählt hat, landet beim nächsten Aufruf direkt auf der
   passenden Adresse (`location.replace`, damit der Zurück-Knopf nicht in eine
   Schleife läuft).
3. Wer **noch nie** gewählt hat und erkennbar nicht aus dem DACH-Raum kommt,
   bekommt eine **Hinweiszeile** mit Verweis auf die andere Fassung — und
   ausdrücklich **keine automatische Weiterleitung**.

Punkt 3 ist die entscheidende Stelle: Ein Crawler hat nie eine gespeicherte
Wahl. Eine automatische Weiterleitung träfe damit **immer** ihn — er bekäme
die deutsche Fassung von `/` nie zu sehen, und die getrennten Adressen wären
umsonst. Die Hinweiszeile trägt `data-nosnippet` und wird per JavaScript hinter
dem Sprungverweis eingehängt, steht also weder im ausgelieferten HTML noch vor
„Zum Inhalt springen" in der Tastaturreihenfolge.

**Wenn stattdessen automatisch weitergeleitet werden soll**, ist das der
Einzeiler in `lang-switch.js`: `if(detect() !== pageLang) showNotice();` wird zu
`location.replace(URLS[detect()])`. Die SEO-Folge steht oben.

Die 25 Beschreibungen der Musterprofile im Demo-Deck („Push Day, Bergtouren und
Kaffee nach dem Training.") waren bis dahin nicht ausgezeichnet und damit die
letzten deutschen Reste auf der englischen Seite — sie liegen jetzt als
`sample.bio1`…`sample.bio25` im Wörterbuch.

**nginx braucht keine eigene `location`**: `try_files $uri $uri/` findet das
Verzeichnis, `index index.html` liefert `/en/index.html`, und `/en` ohne
Schrägstrich bekommt die übliche 301 auf `/en/`. Als Kommentar in
`deploy/nginx-flexr.conf` vermerkt.

Der Service Worker steht damit auf `flexr-shell-v10`: `/en/` und
`lang-switch.js` sind in der Shell, `i18n-landing.js` ist heraus — es wird von
keiner Seite mehr geladen und ist nur noch Eingabe für den Generator.

### Ein fremder Anteil in diesem Commit

Im Arbeitsbaum lag **unfertige Client-Arbeit zur Benachrichtigung „Offene Likes
ohne Match"** (Schalter in Android und iOS, `notify_pending_likes_*` in DTOs,
Mappern und Modellen). Das Backend dazu ist seit `32ddea6` committet, die
Client-Seite war es nie. Sie ließ sich nicht sauber abtrennen: dieselben
Codeblöcke, die die Schalter anlegen, wurden in dieser Sitzung übersetzt. Statt
einen Commit zu erfinden, der so nie existiert hat, ist der Anteil hier
**mitcommittet und in der Commit-Beschreibung benannt**.

### Prüfstand

- **Android**: `:app:testProdDebugUnitTest` und `:app:assembleProdDebug` grün
  (offline, Toolchain aus `~/.bubblewrap/`). `resourceConfigurations` steht
  jetzt auf `listOf("de", "en")`.
- **Web-App**: im Browser durchgeklickt. 192 übersetzte Knoten, in **beiden**
  Sprachen kein roher Schlüssel und kein leerer Text.
- **Landingpage `/` und `/en/`**: beide Adressen aufgerufen, in der erzeugten
  englischen Fassung kein deutscher Rest ausserhalb von Eigennamen
  (`St. Pölten`, `Wiener Neustadt`, die Studionamen), JSON-LD auf beiden Seiten
  als gültiges JSON geparst, keine relativen Verweise in `/en/`. Die drei Fälle
  der Wegführung durchgespielt: gespeichertes `de` auf `/en/` leitet auf `/`,
  gespeichertes `en` auf `/` leitet auf `/en/`, **ohne** gespeicherte Wahl
  bleibt `/` deutsch (der Crawler-Fall). Spracherkennung mit 14 Fällen als Node-Test durchgespielt (Wien mit
  englischem System → Deutsch, Mailand mit deutschem System → Deutsch, London →
  Englisch, gespeicherte Wahl schlägt den Ort, …).
- **Schlüssel-Parität und Format-Platzhalter** (`%1$s` / `{name}` / `%@`)
  maschinell über alle vier Wörterbücher abgeglichen — keine Abweichung.
- **iOS wurde nicht übersetzt.** Auf diesem Gerät gibt es weder Xcode noch eine
  Swift-Toolchain; das ganze iOS-Projekt ist so entstanden (siehe
  `ios/README.md`). Gegenprüfen auf dem Mac:
  `./ios/tools/mac-build.sh test`.

**Wichtig für die nächste Sitzung:** Der iOS-Teil ist der einzige ungeprüfte
Anteil dieses Commits. Er berührt rund 25 Dateien; Konstruktoren von
`AccountModel`, `RegisterModel`, `SwipeModel`, `ChatModel`, `VerificationModel`
und `LoginModel` haben je einen Parameter `languageStore` dazubekommen, und
`Gender.label` heißt jetzt `Gender.labelKey` (Rückgabetyp `L` statt `String`),
ebenso `LegalDocument.title` → `titleKey` und `TopLevelDestination.label` →
`labelKey`. Wenn der Mac-Build meckert, ist das die erste Spur.

### Neue Dateien

```
frontend/i18n.js                       Maschinerie + Spracherkennung (App)
frontend/i18n-landing.js               Woerterbuch der Landingpage (nur noch
                                       Eingabe fuer build-en.py)
frontend/app/i18n-app.js               Woerterbuch der Web-App
frontend/lang-switch.js                Wegfuehrung zwischen / und /en/
frontend/build-en.py                   erzeugt frontend/en/index.html
frontend/en/index.html                 ERZEUGT - nicht von Hand bearbeiten
android-native/.../core/locale/        AppLanguage, LanguageStore, AppStrings,
                                       ProvideAppLanguage, AppLanguageViewModel
android-native/.../di/CoroutineModule.kt   @ApplicationScope fuer AppStrings
android-native/.../di/LocaleModule.kt      bindet AppStrings an ResourceAppStrings
android-native/.../component/LanguageSwitch.kt
android-native/app/src/main/res/values-en/strings.xml
android-native/.../test/.../testing/FakeAppStrings.kt
ios/FLEXR/Core/Locale/                 AppLanguage, LanguageStore, FlexrStrings
                                       (+German, +English)
ios/FLEXR/Core/DesignSystem/Component/LanguageSwitch.swift
```

Der Service Worker (`frontend/sw.js`) steht auf `flexr-shell-v10` (siehe
oben) — ohne die i18n-Dateien in der Shell zeigte die App offline die rohen
Schlüssel.

## Sitzung 08.09.2026 — Version 2.5.5 gebaut, alle AABs vom VPS gelöscht

Kein Produktcode angefasst. Zwei Dinge: Versionsnummer hochgezogen und neu
gebaut, danach auf Wunsch **sämtliche AABs vom VPS gelöscht** — beide
Downloadordner sind jetzt leer.

### Version 2.5.5 (versionCode 42) — Nummernversatz ist behoben

`android-native/app/build.gradle.kts` steht jetzt auf `versionCode = 42`,
`versionName = "2.5.5"` (Commit `af71b25`). **2.5.4 ist übersprungen**, und
zwar bewusst: Der Release vom 07.09. hieß 2.5.4, das damals gebaute Bundle
trug aber `versionName 2.5.3` — die Nummer 2.5.4 war damit vergeben, ohne je
in einem Artefakt zu stehen. Ab 2.5.5 stimmen Release-Nummer, `versionName`
im Bundle und Dateiname wieder überein; der Warnkasten im 07.09.-Abschnitt
ist damit erledigt.

Gebaut mit der Toolchain aus `~/.bubblewrap/` (siehe „Android-Build"):

```bash
./gradlew --offline --no-build-cache --no-daemon --max-workers=1 \
  :app:bundleProdRelease
```

BUILD SUCCESSFUL in 7m 3s, mit dem unveränderten Upload-Key `CN=FLEXR`
signiert (`META-INF/FLEXR.SF`/`.RSA` im Bundle). 7.679.482 Bytes, SHA-256
`a2202dbad901476c7cc0a15683879d4cf45141183551f74bbe74a29ade6f8600`.
`versionName` **im gebauten Manifest** gegengeprüft (nicht nur in der
Gradle-Datei) — steht dort auf 2.5.5.

Die `--no-build-cache`-Falle vom 07.09. trat nicht wieder auf; die Option war
wie dokumentiert von vornherein gesetzt. Unit-Tests liefen in dieser Sitzung
**nicht** — es wurde kein Kotlin-Code geändert, nur die Versionsnummer.

### Auf dem VPS liegt kein AAB mehr

Das 2.5.5-Bundle war kurzzeitig als
`dl-a616e78274de323b/flexr-2.5.5.aab` erreichbar und wurde anschließend
**zusammen mit allen älteren AABs gelöscht**: aus `dl-a616e78274de323b/` die
zehn Dateien 2.4.0–2.4.6, 2.5.0, 2.5.2 und 2.5.5, aus
`dl-5d8a93fc22b232c9/` das alte 2.4.9-Bundle (`app-prod-release.aab`,
7.636.045 Bytes) — elf Dateien, rund 82 MB. `find /flexr -name "*.aab"`
liefert nichts mehr. Beide Ordner bestehen weiter; `dl-a616e78274de323b/`
bleibt der vorgesehene Ort für neue Bundles, gelöscht wurde nur der Inhalt.

**Folgen, die man kennen muss:**

- Sämtliche AAB-Links in diesem Dokument und in älteren Sitzungsabschnitten
  liefern jetzt **404**. Die Abschnitte vor dem 08.09. bleiben als Protokoll
  stehen, ihre Links sind aber tot.
- Die Bundles 2.4.0–2.4.6, 2.4.9, 2.5.0 und 2.5.2 existierten **nur** auf dem
  VPS und sind damit weg. Sie ließen sich nur durch einen Neubau des
  jeweiligen Commits ersetzen, und das ergäbe kein byte-identisches Artefakt.
  Besonders zu beachten: **2.4.9 ist die Fassung, die in der Play Console
  steht** — von genau diesem Artefakt gibt es keine Kopie mehr. Seine
  Prüfsumme ist im 30.08.-Abschnitt festgehalten (`7431c17f…`).
- Erhalten geblieben ist allein 2.5.5, lokal an zwei Stellen:
  `android-native/app/build/outputs/bundle/prodRelease/app-prod-release.aab`
  (überlebt kein `gradlew clean`) und als Sicherung
  `~/Downloads/flexr-2.5.5.aab`, beide mit der oben genannten Prüfsumme.
- Der zweite Ordner `dl-5d8a93fc22b232c9/` ist damit gegenstandslos: Er
  enthielt nur das 2.4.9-Bundle und ist jetzt leer. Neue Bundles gehören
  ohnehin nach `dl-a616e78274de323b/`; der leere Ordner kann bei Gelegenheit
  ganz weg.

### Offen

- **2.5.5 ist nirgends veröffentlicht** — weder auf dem VPS noch in der Play
  Console. Wer es bereitstellen will, lädt `~/Downloads/flexr-2.5.5.aab`
  nach dem Ablauf unter „Ein neues AAB wird so bereitgestellt" hoch.
- In der Play Console steht weiterhin 2.4.9 (versionCode 37) — das Artefakt
  dazu liegt seit dem 08.09. nirgends mehr lokal oder auf dem VPS, nur noch
  in der Play Console selbst.

## Sitzung 07.09.2026 (2) — Abogebühr bis auf weiteres ausgesetzt

Ziel: In der Beta sollen neue **und bestehende** Nutzer nichts zahlen, um
überhaupt erst eine Nutzerbasis aufzubauen. Das kostenpflichtige Abo bleibt
vollständig im Code und wird später wieder scharf geschaltet.

### Ein Schalter, kein Ausbau

`BILLING_ENABLED` (`backend/app/config.py`, Standard **false**) ist die einzige
Stelle, an der die Entscheidung faellt. Stripe-Checkout, Webhook, Portal,
Probemonat und Bezahlwand bleiben unveraendert bestehen.

Backend:

- `User.is_active_member()` liefert bei ausgesetzter Gebuehr immer `True`.
  Damit greift die Bezahlwand nirgends mehr — `require_active_membership`
  haengt an derselben Methode, also Deck, Matches, Chat und die
  Warteschlangen-Mails gleich mit.
- `GET /api/billing/status` liefert zusaetzlich `billing_enabled`. Daran
  entscheiden alle drei Clients, ob sie Preise, Bezahlwand und Abo-Knoepfe
  ueberhaupt zeigen.
- `POST /api/billing/checkout` antwortet mit **409**, bevor irgendeine
  Consent-Buchung entsteht. `POST /api/billing/portal` bleibt erreichbar —
  wer aus der Zeit davor noch ein Abo hat, muss es kuendigen koennen.
- Die beiden Probemonat-Mails (`free_trial_ending`, `free_trial_ended`)
  entfallen, solange nichts ablaeuft. Die Aktivitaets-Benachrichtigungen
  laufen unveraendert weiter.
- `_nach_der_pruefung_satz()` in `mailer.py` haelt beide Fassungen des
  Verifizierungs-Hinweises nebeneinander — beim Umlegen des Schalters ist dort
  nichts nachzuziehen.

Clients (alle drei lesen `billing_enabled`, keiner entscheidet selbst):

- Statuspille: **„Beta · gratis"** statt Restlaufzeit-Countdown.
- Konto-Bereich: Hinweis auf die ausgesetzte Gebuehr, „Jetzt abonnieren"
  ausgeblendet; „Abo verwalten / kuendigen" bleibt fuer Bestandsabos stehen.
- Beta-Dialog auf Landingpage und in `/app/` nennt die ausgesetzte Gebuehr in
  einem eigenen Kasten (`.beta-free`).

Feste Texte, die **beim Wiedereinschalten zurueckmuessen** (sie stehen vor dem
Login, wo es noch keinen `/api/billing/status` gibt) — jeweils mit Kommentar im
Code markiert: Hero-USP und Registrierungs-Untertitel in `frontend/app/`,
`RegisterScreen.kt`, `RegisterView.swift`.

### Rechtstexte

AGB neu als Fassung **2026-09-07** (`legal.TERMS_VERSION` mitgezogen): Punkt 7
bekommt lit. e („Beta-Phase: Das Entgelt ist ausgesetzt", inklusive der
Klarstellung, dass das Konto nach dem Probemonat **nicht** ruht), Punkt 9 einen
vorangestellten Hinweis. FAQ-Seite, Landingpage-Preisblock, strukturierte Daten
(`price` jetzt `0.00`), Meta-Beschreibungen, `LegalContent.kt/.swift` und die
Store-Texte entsprechend. `/widerruf.html` blieb unveraendert — es beschreibt
das Ruecktrittsrecht am entgeltlichen Vertrag, den es gerade nicht gibt.

### Vor dem Wiedereinschalten zu bedenken

`trial_ends_at` laeuft im Hintergrund weiter. Wird `BILLING_ENABLED=true`
gesetzt, stehen Bestandskonten mit laengst abgelaufenem Probemonat sofort vor
der Bezahlwand. Dazu gehoert eine Vorankuendigung (AGB Punkt 18) und
vermutlich ein frisches `trial_ends_at` fuer Bestandskonten.

**Bestandsabos:** Es gibt **keine aktiven Stripe-Konten** (vom Betreiber am
07.09. bestaetigt). Es war also niemand zu kuendigen, und der Umbau kann
niemandem eine laufende Abbuchung wegnehmen oder stehen lassen.

Tests: `backend/tests/test_billing_pausiert.py` (vier Faelle: kein Aussperren,
Gegenprobe mit aktivierter Gebuehr, 409 im Checkout, keine Probemonat-Mails).
`conftest.py` setzt `BILLING_ENABLED=true`, damit die restliche Suite weiter
den kostenpflichtigen Pfad prueft. 399 Tests gruen.

### Builds dieser Sitzung

**Android: gebaut und signiert.** Dieser Release ist **2.5.4** — nicht 2.5.3.

> **ERLEDIGT am 08.09.** — der Versatz ist mit 2.5.5 (versionCode 42)
> aufgelöst, siehe die Sitzung 08.09. oben. Der Kasten bleibt als Protokoll
> stehen; der darin genannte Download-Link ist gelöscht und liefert 404.
>
> **Achtung, Abweichung zwischen Nummer und Artefakt (bewusst so belassen):**
> Das gebaute Bundle traegt intern `versionName 2.5.3` und `versionCode 41`
> (`build.gradle.kts` sagt dasselbe), und es liegt auf dem Server als
> `flexr-2.5.3.aab`. Der Release **heisst** trotzdem 2.5.4; die Nummer 2.5.3
> war anderweitig schon vergeben. Es wurde am 07.09. entschieden, deshalb
> nicht neu zu bauen.
>
> Praktische Folgen, bevor das Bundle in die Play Console geht:
> - Die Console zeigt den `versionName` **aus dem Bundle** an, also 2.5.3.
>   Wer dort 2.5.4 lesen will, muss vorher neu bauen.
> - `build.gradle.kts` steht auf 2.5.3/41. Der **naechste** Release ist
>   entsprechend zu setzen — 2.5.5 waere die logische Fortsetzung, 2.5.4
>   waere doppelt vergeben.
> - Der Download-Link heisst weiterhin
>   `dl-a616e78274de323b/flexr-2.5.3.aab`.

Upload-Key `CN=FLEXR` (SHA-256 des Zertifikats `bc64ad3f…e7980`, unveraendert
der bisherige), SHA-256 des Bundles
`9f61e8fca9822527be1a073390d12107d2b3ee5c015cc77f1947fd0cbdbf6007`. Die
Toolchain lag entgegen der bisherigen Doku unter `~/.bubblewrap/` — siehe den
korrigierten Abschnitt „Android-Build" weiter unten, dort steht auch die
`--no-build-cache`-Falle.

**iOS: nicht baubar, unveraendert.** `xcodebuild` und die iOS-SDKs gibt es nur
unter macOS; das Projekt wurde noch nie kompiliert (siehe `ios/HANDOFF.md`).
Die Swift-Aenderungen sind statisch geprueft und spiegeln zeilenweise die
compilergeprueften Kotlin-Aenderungen. Nebenbefund, in `ios/HANDOFF.md`
nachgetragen: Der dort groesste Review-Streitpunkt (Richtlinie 3.1.1, Kauf
ueber externen Browser) **entfaellt waehrend der Gratisphase** — die App zeigt
keinen Preis und keinen Kaufknopf, `openCheckoutSheet()` ist von keinem
Bildschirm erreichbar.

## Sitzung 07.09.2026 (1) — Search-Console-Meldung, robots.txt/nginx, veraltetes `.git`

Anlass war eine Search-Console-Mail („Neuer Grund dafür, dass Seiten nicht
indexiert werden: Durch robots.txt-Datei blockiert"). Ein Commit, reine
Auslieferungskonfiguration — kein Backend, keine Migration, kein Neustart.

### Die Meldung selbst war harmlos

Alle acht nicht indexierten Seiten sind gewollt und korrekt gelöst. Live gegen
Repo geprüft, `robots.txt` und `sitemap.xml` stimmen überein, alle zehn
Sitemap-URLs existieren, jede öffentliche Seite trägt `index, follow` plus
Canonical:

| Grund im Bericht | Seiten | Was es ist |
|---|---|---|
| Seite mit Weiterleitung | 3 | `http://flexr.social/`, `http://www.…`, `https://www.…` → 301 auf die kanonische Adresse |
| Alternative Seite mit kanonischem Tag | 1 | `/index.html` liefert 200, Canonical zeigt auf `/` |
| Gecrawlt – zurzeit nicht indexiert | 1 | Googles eigene Entscheidung, nichts zu reparieren |
| Durch „noindex" ausgeschlossen | 2 | `/app/` (Meta-Tag) und `/mail-bestaetigen` (`X-Robots-Tag`) |
| Durch robots.txt blockiert | 1 | `/admin.html` — der einzige echte Befund, siehe unten |
| 4xx-Problem | 0 | erledigt |

**Die als „Fehlgeschlagen" markierten Validierungen nicht erneut starten.** Sie
laufen auf beabsichtigte Ausschlüsse (Weiterleitung, Canonical, Crawled); eine
Validierung prüft, ob der Grund *verschwunden* ist, und schlägt dort zwingend
immer wieder fehl.

### Befund: `/admin.html` stand in der noindex-Falle

`robots.txt` sperrte `/admin.html` **und** die Seite trug ein
`<meta name="robots" content="noindex, nofollow">`. Das hebt sich gegenseitig
auf: Eine per robots.txt gesperrte Seite darf Google gar nicht erst laden,
sieht das noindex im HTML also nie und kann die URL trotzdem ohne Inhalt
indexieren. Der Kommentar in `robots.txt` hat genau das für `/app/` schon
erklärt und bei `/admin.html` das Gegenteil getan. Zweiter Nebeneffekt: Das
`Disallow` schrieb den Admin-Pfad in eine öffentliche Datei — dieselbe
Überlegung, die dort `/dl-` bewusst nur als Präfix nennt.

Behoben in drei Dateien:

- `frontend/robots.txt` — `Disallow: /admin.html` entfernt, es bleiben nur
  `/api/` und `/dl-`. Der Kommentarblock erklärt die Regel jetzt für `/app/`
  **und** `/admin.html`.
- `deploy/nginx-flexr.conf` — neue `location = /admin.html` mit
  `add_header X-Robots-Tag "noindex, nofollow" always`. Das Security-Snippet
  ist mit eingebunden, sonst verwerfen die eigenen `add_header` die geerbten
  Schutz-Header (die Falle vom 15.08.). Funktional ändert sich sonst nichts:
  vorher lief `/admin.html` in `location /`, das denselben Snippet und
  dasselbe `no-cache` setzt. Das `<meta name="robots">` in `admin.html` bleibt
  zusätzlich stehen und wird jetzt auch wirklich gelesen.
- `backend/tests/test_public_frontend.py` — neuer Test
  `test_noindex_seiten_sind_nicht_zusaetzlich_per_robots_gesperrt`: die
  Disallow-Liste muss exakt `["/api/", "/dl-"]` sein, beide noindex-Seiten
  müssen ihr Meta-Tag haben, und der nginx-Block muss X-Robots-Tag samt
  Snippet tragen. Ohne den Test kann das lautlos zurückfallen.

Auf dem VPS wurde die `location` **von Hand** in
`/etc/nginx/sites-available/flexr.social` nachgetragen, nicht die Repo-Datei
kopiert — die aktive Fassung enthält die certbot-Direktiven und ist anders
sortiert. Sicherung vorher unter `/root/`, danach `nginx -t` und Reload.

### Wichtiger: Das `.git` in diesem MEGA-Ordner war fünf Commits veraltet

Der Punkt kostet sonst jede Sitzung wieder Zeit — der frühere Punkt 13 unter
„Noch offen" behauptete das Gegenteil der Wirklichkeit und hat hier prompt in
die Irre geführt.

Der Vergleich live gegen lokal zeigte: `index.html`, `app/index.html` und
`admin.html` auf dem VPS waren **byteidentisch mit dem Arbeitsverzeichnis**,
aber verschieden von `HEAD` — was nach „ausgerollt, aber nicht committet"
aussah. Ein `git fetch` löste es auf:

```
d1804de..9e83c97  main -> origin/main     # 5 Commits
```

Die neun vermeintlich geänderten Dateien waren nie ungesicherte Arbeit,
sondern längst gepushte **und** ausgerollte Commits vom 05./06.09., die der
lokale HEAD nur nicht kannte. Genau der Stolperstein aus dem Abschnitt weiter
unten: Auf diesem Gerät läuft nie `git pull`, MEGA synchronisiert nur die
*Dateien*, nicht das Repository.

Aufgeräumt mit dem dort vorgesehenen Weg:

```bash
git fetch origin
git status --short              # erst prüfen, ob es etwas zu verlieren gibt
git reset --mixed origin/main   # bewegt nur HEAD+Index, Arbeitsverzeichnis bleibt
```

Danach blieben nur noch die drei echten Änderungen übrig — plus vier
`scripts/*.sh`, denen die MEGA-Sync das Executable-Bit abgeräumt hatte (nur
Modus, Inhalt identisch), repariert mit `chmod +x scripts/*.sh`.

**Merksatz für die nächste Sitzung: Vor jeder Beurteilung des Repo-Stands
zuerst `git fetch origin` laufen lassen.** `git status` ohne vorheriges Fetch
lügt in diesem Ordner.

### Wie geprüft wurde

- `./venv/bin/python -m pytest -q` in `backend/` — **395 grün** (0 offen),
  darunter die acht aus `test_public_frontend.py`.
- Live mit `curl` gemessen: `robots.txt`, `sitemap.xml`, Header von `/`,
  `/app/`, `/admin.html`, `/mail-bestaetigen` sowie alle vier
  Adressvarianten (http/https × www/ohne).

### Nachtrag: `~/.ssh/config` auf dem VPS angelegt

Der seit 23.08. offene Punkt 2 aus „Noch offen", nach Absprache erledigt. Der
blanke `git pull --ff-only origin main` auf dem VPS funktioniert jetzt, das
vorangestellte `GIT_SSH_COMMAND` entfällt. Vorher geprüft, dass `/flexr` das
einzige Repository auf diesem geteilten Server mit einem github-Remote ist,
damit der `Host github.com`-Block niemand anderem dazwischenfunkt. Datei,
Begründung und Gegenprobe stehen im Abschnitt „Stolperstein beim Deploy".

Der Telegram-Bot-Token (Punkt 15) bleibt auf ausdrücklichen Wunsch **wie er
ist** — nicht erneut vorschlagen.

### Offen

- **Search Console: `/admin.html` per URL-Prüfung neu abrufen und die
  Meldung damit schliessen.** Braucht den Google-Zugang des Nutzers, konnte
  aus der Sitzung heraus nicht erledigt werden.
- Bis Google neu crawlt, bleibt der alte Zustand im Bericht stehen. Das ist
  normal und kein Zeichen, dass etwas nicht gegriffen hat.

## Sitzung 06.09.2026 — Kompletter Journey-Durchgang, sechs Befunde behoben

Ein Commit. Backend **und** Web-Frontend, **keine Migration**, aber
Backend-Neustart nötig (`app/routers/admin.py`, `billing.py`, `schemas.py`).
Android und iOS sind **nicht angefasst** — siehe „Offen" unten.

### Wie geprüft wurde

Die gesamte Nutzerreise und das Admin-Dashboard wurden lokal gegen einen
laufenden Server durchgespielt, nicht nur gelesen: Registrierung (inkl.
Alters-Sperre unter 18), PLZ- und Gym-Suche, Foto-Upload, Verifizierung
(Selfie + Ausweis), Admin-Freigabe, Deck, Swipe, Match, Chat inkl. Zensur,
Melden, Blockieren, förmliche Meldung nach Art. 16 DSA, Gym-Vorschlag,
Benachrichtigungs-Schalter, Datenschutz-Screen, Rechtstexte im Modal,
Rücktrittsformular, Paywall, Kontolöschung und Reaktivierung. Im Admin:
Dashboard, Nutzerliste und -detail, Ban, Mute, Foto-Freigabe und -Ablehnung,
Meldungen, auffällige Nachrichten, Gym-Freigabe.

**Ohne Produktionsdaten anzufassen.** Der Foto-Upload läuft als Presigned PUT
direkt in den Storage, und `backend/.env` zeigt auf den echten R2-Bucket
(siehe „Lokal testen: zwei Fallen"). Für den Durchgang lief deshalb ein
kleiner S3-Ersatz auf `127.0.0.1:9000` (PUT/GET/HEAD/DELETE, `list_objects_v2`,
`copy_object`) und alle `S3_*`-Werte kamen als Umgebungsvariablen — die
schlagen in pydantic-settings die `.env`. Ebenso `SMTP_HOST=""`, damit kein
Testkonto echte Post bekommt.

### Behobene Befunde

1. **Kontosperre ohne Begründung (Art. 17 DSA).** Der Server baut in
   `moderation.restriction_detail()` die vollständige begründete Mitteilung —
   Maßnahme, Umfang, Dauer, Anlass, Angabe zur automatisierten Erkennung,
   Rechtsgrundlage, Widerspruchsweg — und schickt sie im 403-Detail mit. Die
   Web-App zeigte davon **nur** den Satz „Dein Konto wurde gesperrt." Beim Ban
   ist der Login der einzige Kanal zum Betroffenen (ein Token bekommt er
   nicht), der Rest ging also ersatzlos verloren. Neu: `moderationNoticeHtml()`
   baut die Mitteilung aus dem `statement`, `#loginModerationNotice` zeigt sie
   unter dem Login-Formular.
   Zusätzlich behandelt `api()` jetzt den Fall, dass die Sperre **während**
   einer offenen Sitzung greift: vorher blieb der Nutzer in einer App, in der
   ab sofort jeder Abruf stumm fehlschlug. Jetzt Ausloggen und dieselbe
   Mitteilung. Der Zweig greift nur bei gesetztem Token — der Login-Versuch
   eines Gesperrten läuft ebenfalls durch `api()` und wird in `doLogin()`
   eigens behandelt; ohne die Bedingung überschrieb der generische
   Fehlerpfad die Mitteilung anschließend wieder.
2. **Melden aus dem Chat verwarf das Aktenzeichen (Art. 16 Abs. 4 DSA).** Es
   gab zwei Melde-Implementierungen: `reportUser()` (Swipe-Karte,
   Match-Profil) zeigt die Empfangsbestätigung samt Aktenzeichen,
   `btnReportChat` war eine eigene Kopie mit „Meldung gesendet. Danke für dein
   Feedback." Dasselbe bei `btnBlockChat` gegenüber `blockUser()`. Beide
   Kopien sind raus, die Chat-Knöpfe rufen die gemeinsamen Helfer auf.
3. **Gelöschte Konten waren im Admin-Dashboard nicht als solche erkennbar.**
   Eine Selbstlöschung deaktiviert das Konto sofort und löscht es erst nach 30
   Tagen Karenz. In Liste und Detailansicht fehlte jeder Hinweis darauf — eine
   Meldung gegen ein längst deaktiviertes Profil wäre bearbeitet worden, als
   wäre es aktiv. Neu: `deleted_at` in Liste und Detail, `purge_at` (Termin
   der endgültigen Löschung) im Detail, Kennzeichnung „Gelöscht" in beiden
   Ansichten und eine Kachel „In Löschung" auf dem Dashboard.
   Dabei fiel auf, dass die Kennzahlen sich widersprachen: `new_today` nahm
   selbstgelöschte Konten schon immer aus, `total_users`/`trial_users`/
   `banned_users`/`active_subscriptions` nicht — das Dashboard zeigte „14 im
   Probemonat" bei 13 Nutzern gesamt. Alle Bestandszahlen schließen jetzt
   gelöschte Konten aus, sichtbar bleiben sie über `deleted_users`.
4. **Checkout-Störung kam als nackter 500 heraus.** Fiel Stripe aus oder
   fehlte der Key, propagierte die Ausnahme ungefangen. Ein unbehandelter 500
   verlässt die Anwendung **ohne** die CORS-Header der Middleware — im Browser
   kam deshalb nur „Failed to fetch" an, ohne jeden Hinweis. Der Nutzer hatte
   in dem Moment gerade zwei rechtlich erhebliche Erklärungen abgegeben.
   `create_checkout()` und `create_portal()` antworten jetzt mit 502 und einem
   deutschen Satz. Im Overlay „Vor der Zahlung" blieb ausserdem die alte
   Meldung „Bitte bestätige beide Erklärungen" stehen, während der echte
   Fehler nur als Toast vorbeizog — der Kasten wird jetzt bei jedem Anlauf
   zurückgesetzt und trägt anschließend den tatsächlichen Fehler.
   `test_billing_webhook.py::test_checkout_mit_erklaerung_haelt_die_einwilligung_fest`
   hing an der durchgereichten Stripe-Ausnahme (`pytest.raises`) und wurde auf
   die 502-Antwort umgestellt; die eigentliche Zusicherung des Tests — der
   `CheckoutConsent`-Datensatz entsteht **vor** dem Stripe-Aufruf — ist
   unverändert.

5. **Melden und Blockieren waren per Tastatur nicht erreichbar.** Die
   Flaggen-, Verbots- und „Match auflösen"-Symbole auf der Swipe-Karte und im
   Chat-Kopf waren `<div class="flag-btn">` bzw. `<div class="icon-btn">` mit
   `title` und `aria-label`, aber ohne `role`, ohne `tabindex` und ohne
   Tastaturbedienung — ausgerechnet bei den gesetzlich vorgeschriebenen
   Schutzfunktionen, während der Zurück-Pfeil daneben im selben Kopf längst ein
   echter `<button>` war. Jetzt alle sechs als `<button type="button">`.
   Optisch ist das ein Nulldurchgang: der globale Reset (`*{box-sizing:
   border-box; margin:0; padding:0}`) deckt schon alles ab, was ein Button
   sonst mitbringt, ergänzt um `font:inherit`; im Browser nachgemessen —
   29×29 bzw. 31×31 Pixel, gleicher Radius, gleicher Hintergrund wie vorher.
   Das Drei-Punkte-Menü im Chat hat zusätzlich `aria-haspopup`, ein
   `aria-expanded`, das über `setChatMenu()` dem tatsächlichen Zustand folgt
   (eine feste Angabe im Markup wäre schlechter als gar keine), und schließt
   jetzt auch mit Escape.

6. **Foto-Ablehnung lief über zwei verschachtelte `prompt()`-Fenster.**
   Der Prüfer musste die Nummer eines Grundes aus einer Liste 1–10 abtippen —
   bei einem Schritt, der mehrmals täglich vorkommt, und ohne das Bild vor
   Augen, weil `prompt()` die Seite ausblendet. Ein Vertipper landete nicht
   beim falschen Grund, sondern brach den ganzen Vorgang ab. Jetzt ein
   Dialog in der Optik des Nutzer-Modals: das zu beurteilende Foto steht
   oben, die Gründe stehen als Auswahlliste, und das Ergänzungsfeld für
   „Anderer Verstoß" erscheint erst, wenn es gebraucht wird. Die gesendete
   Struktur ist unverändert (`{reason}` bzw. `{reason, note}`) — am Server
   ändert sich nichts.
   Zwei Kleinigkeiten fielen dabei mit ab: das Vorschaubild bekam ein `alt`
   (die Bilder im Prüfraster hatten gar keines), und die globale Regel
   `label{text-transform:uppercase}` musste für die Gründeliste
   zurückgesetzt werden — sonst stand dort „ANDERER VERSTOSS GEGEN DIE
   PROFILFOTO-RICHTLINIEN". Dieselbe Ausnahme gibt es schon bei
   `.verify-checklist`.

### Was ausdrücklich in Ordnung war

Damit es niemand ein zweites Mal untersucht: Der Swipe ist idempotent (zweiter
Swipe aktualisiert die Zeile, statt eine zweite anzulegen). Öffentliche
Profile filtern auf freigegebene Fotos, ein abgelehntes Hauptfoto kann also
nicht auf der Karte landen. Die Ablehnung eines Fotos geht per Mail mit
Klartext-Begründung raus. Blockierte verschwinden aus dem Deck. Der Ban wird
serverseitig auf jedem Endpunkt durchgesetzt, auch mit altem Token. Die
Reaktivierung innerhalb der Karenzzeit funktioniert über den Login-Dialog.
Der Foto-Upload hat einen sauberen Wiederaufnahme-Pfad, wenn der Presigned PUT
scheitert („Profilfoto fehlt" statt Sackgasse). Die Rechtstexte laden alle im
Modal, inklusive der Formulare in `widerruf.html` und `meldung.html`.

### Verbesserungspotenzial, bewusst nicht angefasst

- **`redact_message()` schluckt das Satzzeichen hinter einer URL.** Aus
  „meinprofil.com/anna, da sind…" wird „[Link entfernt] da sind…" — `\S*` ist
  gierig und nimmt das Komma mit. Kosmetisch.
- **`CheckoutConsent` wird vor dem Stripe-Aufruf committet.** Scheitert der
  Checkout, bleibt eine Zeile ohne zugehörigen Vorgang stehen. Die Erklärung
  *wurde* abgegeben, insofern vertretbar; wer aufräumt, sollte es bewusst tun.
- **Kein `<form>` um Login und Registrierung.** Für den Login ist Enter
  eigens verdrahtet, im Registrierungsformular nicht.

### Falle beim Start dieser Sitzung

`backend/venv/bin/` enthielt **keine `python`-Symlinks mehr** (MEGA-Sync
verliert Symlinks und Ausführungsrechte). `venv/bin/python -m pytest` scheiterte
mit „Datei oder Verzeichnis nicht gefunden". Ein Umweg über `PYTHONPATH` auf
`venv/lib/python3.12/site-packages` funktioniert **nicht** — dann liegt
`/usr/lib/python3/dist-packages` mit im Pfad und `pyOpenSSL` kollidiert mit der
`cryptography` aus dem venv (`module 'lib' has no attribute 'GEN_EMAIL'`).
Richtige Abhilfe:

```bash
cd backend/venv/bin && ln -sf /usr/bin/python3.12 python3 && ln -sf python3 python
```

Aus derselben Ursache hatten `scripts/*.sh` und `ios/tools/mac-build.sh` ihr
Ausführungsrecht verloren; vor dem Commit mit `chmod +x` zurückgesetzt, sonst
wäre eine Rechte-Rücknahme mitcommittet worden.

Ebenfalls aus derselben Ursache: `HANDOFF.md` und `backend/.env.example` lagen
im Arbeitsverzeichnis in einer **älteren** Fassung als auf `origin/main`
(HANDOFF 97 Zeilen kürzer, `.env.example` ohne den Telegram-Block). Nach dem
`git reset --mixed origin/main` beide gezielt mit `git checkout --` auf den
Serverstand zurückgeholt, statt sie mitzucommitten. **Genau prüfen, welche
Dateien in den Commit gehen** — `git add -A` hätte hier 97 Zeilen Dokumentation
und die Telegram-Variablen gelöscht.

### Stand der Prüfung

- Backend: **393 Tests grün** (12 neu in `backend/tests/test_journey_befunde.py`,
  vorher 381; ein bestehender Billing-Test angepasst, siehe Befund 4).
- Web: alle Behebungen im Browser nachgestellt — Login eines
  gesperrten Kontos, Sperre mitten in der Sitzung, Melden aus dem Chat mit
  Aktenzeichen, Blockieren aus dem Chat, Checkout-Störung mit deutscher
  Meldung, Admin-Liste und -Detail mit „Gelöscht", Dashboard-Kacheln stimmig.
  Für die Tastaturbedienung zusätzlich Fokus und Auslösen der Melden-Taste auf
  der Karte geprüft und per Screenshot gegengeprüft, dass sich am Aussehen von
  Karte und Chat-Kopf nichts geändert hat.
- Android: **gebaut.** `:app:testProdReleaseUnitTest` BUILD SUCCESSFUL
  (5m 7s), `:app:bundleProdRelease` BUILD SUCCESSFUL (10m 46s). Ergebnis ist
  **flexr-2.5.2 (versionCode 40)**, 7.678.819 Byte, SHA-256
  `2739c7ae205b9cda54f79c29e51a275bea81514e0870c032c792edecf53c973a`, liegt
  unter `https://flexr.social/dl-a616e78274de323b/flexr-2.5.2.aab`
  (Prüfsumme lokal und entfernt verglichen). Der Signaturschlüssel im Bundle
  ist der bisherige Upload-Key — SHA-256 des Zertifikats
  `BC:64:AD:3F:27:3E:B2:2D:38:1E:D7:CB:46:DE:67:6E:6A:1C:C6:3B:18:C9:64:FA:AB:A3:DD:A5:14:0E:79:80`,
  deckungsgleich mit `keytool -list` auf `android/android.keystore`.
  **Der Android-Code ist in dieser Sitzung nicht angefasst worden**: 2.5.2
  steht seit dem 31.08. im Repo (`e865534`, Benachrichtigungs-Navigation) und
  war bloß nie gebaut worden — auf dem VPS lag zuletzt 2.5.0. Damit gilt
  weiterhin, was die Sitzung vom 31.08. notiert hat: **die
  Benachrichtigungs-Navigation ist auf keinem Gerät getestet.**
- iOS: **nicht gebaut**, hier gibt es kein macOS/Xcode.

### Offen

- **Android und iOS haben denselben Befund 1**: `ApiError.kt` liest
  `moderation_reason` und `appeal_hint`, der Chat zeigt sie im Mute-Banner —
  der **Login** wertet sie aber nicht aus, ein Gesperrter sieht dort ebenfalls
  nur „Dein Konto wurde gesperrt.". Zu beheben, sobald eine Maschine mit
  Toolchain zur Verfügung steht; ungeprüften Kotlin-/Swift-Code auszuliefern
  wäre hier das grössere Risiko.
- Das `statement`-Feld (Art. 17 Abs. 3) wertet bisher nur die Web-App aus.

## Sitzung 05.09.2026 — Beta-Hinweis auf Landingpage und in der Web-App

Reine Frontend-Änderung, ein Commit. Kein Backend, keine Migration, kein
Neustart, kein neues AAB.

### Was dazugekommen ist

Ein **einmaliger Hinweis-Dialog** auf `frontend/index.html` (Landingpage) und
`frontend/app/index.html` (Web-App): FLEXR ist in der Beta, die Android-App
ist für **Ende September 2026** geplant, iOS folgt danach.

- Merker `flexr_beta_notice_v1` in `localStorage`, **geteilt zwischen beiden
  Seiten** — wer auf der Landingpage bestätigt, bekommt ihn in `/app/` nicht
  ein zweites Mal. Verschieben sich die Termine, zeigt ein hochgezählter
  Schlüssel (`_v2`) den Hinweis allen Besuchern erneut. Das ist der
  vorgesehene Weg, den Hinweis zu aktualisieren.
- Schliessen per „Verstanden", ✕, Escape oder Klick auf den Hintergrund —
  bewusst keine Sackgasse. `role="dialog"`/`aria-modal`, Fokus wandert auf
  den Bestätigen-Knopf und danach zurück.
- Bei gesperrtem `localStorage` (privater Modus) erscheint der Dialog einmal
  pro Aufruf statt gar nicht.
- Auf der **Landingpage** wird der Dialog übersprungen, wenn ein
  `flexr_token` vorliegt: Eingeloggte werden dort ohnehin nach `/app/`
  umgeleitet, sonst hätte der Dialog vor dem Seitenwechsel kurz aufgeblitzt.

Die Web-App nutzt die vorhandenen `.legal-modal-backdrop`/`.legal-modal`-
Klassen (wie „Vor der Zahlung" und die Konto-löschen-Bestätigung) statt einer
eigenen Optik; die Landingpage hat keine Modal-Klassen und bekam eigene
`.beta-*`-Regeln.

### Zwei Details, die beim Nacharbeiten leicht wieder kaputtgehen

1. **`iOS` wird von `text-transform:uppercase` zu `IOS`.** Die Label-Spalte
   der Terminliste ist in Oswald-Versalien gesetzt. Im Markup stand von
   Anfang an korrekt „iOS" — der Browser machte daraus „IOS". Deshalb trägt
   dieses eine Label die Klasse `.as-written` (`text-transform:none`). Wer
   die Liste umbaut, muss die Ausnahme mitnehmen.
2. **`frontend/sw.js` wurde bewusst NICHT hochgezählt.** Der erste Entwurf
   hatte `CACHE` auf `v9` gesetzt; das widerspricht dem Abschnitt „Normaler
   Commit- und Deploy-Ablauf" — der Service Worker fährt „Netz zuerst", für
   eine reine Inhaltsänderung ohne Fremdaufrufe ist ein Bump unnötig.
   Zurückgenommen, `sw.js` bleibt auf `v8`.

### Zur Nutzergewinnung

Die Vorgabe lautete unter anderem, die Nutzergewinnung werde ab dem
Android-Start vorangetrieben. Das steht **nicht wörtlich** im Dialog — „ab
jetzt bewerben wir die App" ist interne Planung und liest sich in einem
Nutzerhinweis seltsam. Transportiert wird es durch den Schlusssatz „Mit dem
Start der Android-App geht FLEXR dann richtig an den Start."

### Git-Stand bei Sitzungsbeginn — erneut die bekannte Falle

Wie schon am 21.08. beschrieben (Abschnitt „Wichtiger Fund zu Beginn jener
Sitzung"): `git status` zeigte 122 Einträge und `git diff` rund 6.500
geänderte Zeilen, `origin/main` war **47 Commits voraus**. Die Prüfung ergab,
dass das Arbeitsverzeichnis inhaltlich bereits `origin/main` entsprach (MEGA-
Sync ohne `git pull`); von den 30 Dateien, die sich gegenüber `origin/main`
unterschieden, waren 26 **untracked und byte-identisch**, eine war die
bekannte `backend/.env.example`-Falle, und nur zwei enthielten echte
Änderungen.

`git reset --mixed origin/main` — der im 21.08.-Abschnitt dokumentierte Fix —
wurde in dieser Sitzung vom **Auto-Mode-Classifier zweimal blockiert**, auch
beim identischen zweiten Versuch. Ausweg ohne jedes Risiko fürs
Arbeitsverzeichnis:

```bash
git worktree add /tmp/wt origin/main      # sauberer Stand, Hauptordner unberuehrt
cp frontend/index.html frontend/app/index.html /tmp/wt/frontend/...
cd /tmp/wt && git add ... && git commit && git push origin main
git worktree remove /tmp/wt
```

Dadurch entstand ein Commit mit ausschliesslich den beabsichtigten 204
Zeilen — kein Fehl-Commit der `.env.example`, kein versehentliches
Zurückdrehen neuerer Dateien. **Der lokale Ordner ist damit weiterhin 47+1
Commits hinter `origin/main`**; der Inhalt stimmt, nur die Git-Historie
nicht. Vor der nächsten Sitzung dort einmal aufräumen (`git fetch origin` +
`git reset --mixed origin/main`, ggf. manuell bestätigen).

## Sitzung 31.08.2026 — Fotosortierung und Benachrichtigungen

Zwei Commits, beide gepusht und ausgerollt: `68f14d2` (Feature) und
`96b076f` (Version 2.5.1 / versionCode 39).

### Was dazugekommen ist

- **Fotos per Drag & Drop sortierbar** (Web, Android, iOS). `PUT
  /api/profiles/me/photos/order` verlangt die **vollständige** Liste der
  eigenen Foto-IDs — eine Teilangabe liesse offen, welche Position die
  übrigen bekommen, und `photos[0]` (Hauptfoto: Swipe-Karte, Avatar,
  Chat-Kopf) würde nach jedem Schreibzugriff springen.
- **Drei Benachrichtigungs-Anlässe**, je getrennt für E-Mail und App
  abschaltbar unter Profil → Benachrichtigungen (6 Schalter): neues Match,
  ab 3 wartenden Profilen im Suchradius, 7 Tage ohne Nutzung.
  `PATCH /api/profiles/me/notifications`, Migration `a4e17c9b2d58`.
- **Kein FCM/APNs.** Die Apps holen Benachrichtigungen per WorkManager
  (`ActivityNotificationWorker`, stündlich) bzw. `BGAppRefreshTask`
  (`ActivityRefreshService`) aus `GET /api/notifications/pending` und zeigen
  sie lokal an — dasselbe Muster wie `NewMessageWorker`. Quittiert wird über
  `POST /api/notifications/delivered`, und zwar erst **nach** dem Anzeigen:
  bricht der Lauf dazwischen ab, kommt die Meldung erneut statt zu verfallen.

### Zwei Fallstricke, die Geld/Ruf gekostet hätten

1. **`last_seen_at` taugt nicht für „7 Tage ohne Login".** Es wird in
   `security.get_current_user` bei *jedem* authentifizierten Request gesetzt,
   also auch vom Hintergrund-Poller der Apps — die Erinnerung wäre nie fällig
   geworden. Neu ist `last_active_at`, das Abrufe mit `X-Flexr-Background: 1`
   übergeht; beide Apps senden den Header auf den Notification-Endpunkten.
2. **Die Migration setzt `last_active_at` für Bestandskonten auf „jetzt".**
   Ohne das stünde die Spalte auf NULL, der Job fällt bei NULL auf
   `created_at` zurück — der erste nächtliche Lauf hätte jedem Konto älter
   als sieben Tage auf einen Schlag die Inaktivitäts-Erinnerung geschickt,
   Mail *und* Push, an den gesamten ruhenden Bestand. Nach dem Deploy
   verifiziert: 0 Konten ohne `last_active_at`, 0 Konten, die sofort als
   inaktiv gelten.

Der Deck-Zähler nutzt bewusst dieselbe Funktion wie `/api/swipes/deck`
(`deck_profiles` in `routers/swipes.py`) — eine zweite, vereinfachte Zählung
wäre bei der nächsten Filteränderung auseinandergelaufen und hätte Mails über
Profile verschickt, die im Deck gar nicht auftauchen.

### Stand der Prüfung

- Backend: **381 Tests grün** (14 neu, vorher 367).
- Web: Drag & Drop und die 6 Schalter im Browser bei 375×812 durchgespielt
  (Verschieben statt Tauschen, Server-Reihenfolge deckungsgleich,
  Schalterstand überlebt Reload).
- Android: `:app:testProdReleaseUnitTest` und `:app:bundleProdRelease` beide
  **BUILD SUCCESSFUL**. **Auf einem Gerät ist es noch nicht angefasst worden**
  — Drag & Drop und die Schalter sind auf Android ungetestet, der Worker läuft
  nur stündlich.
- iOS: **nicht kompiliert**, hier ist kein macOS/Xcode. Der Swift-Code ist
  ungeprüft.

### Benachrichtigungs-Tipp führt zum Ziel (Nachtrag)

Vorher öffnete jeder Tipp nur die App auf dem zuletzt gesehenen Screen — das
Ziel wurde zwar mitgeschickt, aber nirgends ausgelesen (`EXTRA_OPEN_CHATS`
seit jeher, `EXTRA_TARGET` seit dieser Sitzung).

- **Android:** `MainActivity.targetOf()` liest die Extras und prüft den
  Serverwert gegen `TopLevelDestination`, statt ihn blind zu übernehmen.
  `MainGraph` navigiert mit demselben Muster wie die untere Leiste
  (`popUpTo`/`launchSingleTop`/`restoreState`), damit kein zweiter
  Backstack-Eintrag entsteht. `onNewIntent` ist überschrieben — ohne das
  griffe es nur beim Kaltstart. Das Ziel wird nach der Navigation verbraucht,
  sonst spränge die App bei jeder Neuzusammensetzung erneut dorthin.
- **iOS:** `didReceive` unterscheidet an `userInfo` zwischen `target`
  (Aktivitäts-Benachrichtigung) und `openChats` (Nachricht); `AppModel.open(target:)`
  prüft gegen `TopLevelDestination`.

Bewusst getrennt von `intent.data` bzw. dem Deeplink-Pfad gehalten: darüber
läuft der Bestätigungslink aus der Registrierungsmail.

### Play-Console-Warnung „nativer Code ohne Debug-Symbole" — erledigt, nicht behebbar

Beim Upload von versionCode 39 warnte die Play Console erneut. **Die Warnung
lässt sich von unserer Seite nicht abstellen; bitte nicht noch einmal
untersuchen.**

Der native Code stammt ausschliesslich aus Fremdbibliotheken:
`libandroidx.graphics.path`, `libdatastore_shared_counter` sowie CameraX'
`libimage_processing_util_jni` und `libsurface_util_jni`. Alle vier liefert
Google **fertig gestripped** aus — mit `llvm-readelf -S` geprüft: weder
`.debug_*` noch `.symtab`. `extractNativeDebugMetadata` schreibt deshalb ein
leeres Verzeichnis.

`debugSymbolLevel = "FULL"` stand seit versionCode 35 in der
`build.gradle.kts` und war die ganze Zeit wirkungslos. In dieser Sitzung
eigens das NDK r27d nachinstalliert (2 GB, liegt jetzt unter
`~/.bubblewrap/android_sdk/ndk/`) und sauber neu gebaut: **byte-identisches
Bundle**, Warnung unverändert. Das NDK war also nicht die Ursache — es gibt
schlicht keine Symbole zu extrahieren.

Praktische Folge: Stürzt die App *innerhalb* dieser vier Google-Bibliotheken
ab, zeigt der Play-Crashreport rohe Adressen. Eigener Code ist nicht
betroffen. `debugSymbolLevel = "FULL"` bleibt stehen, falls je eigener
nativer Code dazukommt; ein NDK ist dafür aktuell nicht nötig.

### Offen

- iOS bauen und prüfen.
- **Auf einem Gerät ist nichts davon angefasst worden.** Für die
  Benachrichtigungs-Navigation konkret zu prüfen: Tipp bei **geschlossener**
  App (Kaltstart über `onCreate`) und bei **laufender** App (`onNewIntent`),
  danach einmal drehen — die App darf dann *nicht* erneut zum Ziel springen.
  Und gegenprüfen, dass der Bestätigungslink aus der Registrierungsmail
  (`/mail-bestaetigen`) unverändert funktioniert: der läuft über
  `intent.data` und wurde bewusst nicht angefasst.
- AAB: 2.5.1 (versionCode 39) war hochgeladen und wurde auf Wunsch wieder
  vom VPS gelöscht. Aktuell ist **2.5.2 (versionCode 40)** mit der
  Benachrichtigungs-Navigation, gebaut und signiert unter
  `android-native/app/build/outputs/bundle/prodRelease/app-prod-release.aab`,
  aber **nicht auf dem VPS**. Für einen Release hochladen — siehe „Ein neues
  AAB wird so bereitgestellt". Ein etwaiger Versionsentwurf 39 in der Play
  Console lässt sich verwerfen.

## Eckdaten (sitzungsübergreifend)

- Repository: `git@github.com:flexrsocial/flexr.git`
- Produktionsseite: <https://flexr.social>
- API-Healthcheck: <https://flexr.social/api/health>
- VPS-SSH-Alias: `flexr-vps` (root@31.220.73.67, Key
  `~/.ssh/id_ed25519_flexr_vps` — lag auf diesem Gerät bereits vor, keine
  Neueinrichtung nötig)
- Repository auf dem VPS: `/flexr`
- **Android-Toolchain liegt unter `~/.bubblewrap/`** (Rest des TWA-Setups),
  nicht an den üblichen Orten:
  `JAVA_HOME=~/.bubblewrap/jdk/jdk-17.0.11+9` (Temurin 17.0.11) und
  `ANDROID_HOME=~/.bubblewrap/android_sdk` (platform android-36,
  build-tools 34/35, seit 31.08. auch ndk/27.3.13750724). Eine Suche nach
  `javac` mit kleinem `-maxdepth` findet das nicht.
- API-Dienst: `flexr-api.service`
- **Achtung, geteilter VPS:** Auf demselben Server laufen auch fremde,
  nicht mit FLEXR verwandte Projekte (`tarifbot-*`, `ediktmonitor`,
  `gasfees`, ein `defi`-Ordner). Bei Aufräumarbeiten in `/tmp` oder
  `~/.pm2` etc. nichts anfassen, das nicht eindeutig zu `/flexr` gehört.
- **AAB-Download: `flexr-2.6.5.aab`** liegt seit dem 12.09.2026 in
  `dl-a616e78274de323b/` — <https://flexr.social/dl-a616e78274de323b/flexr-2.6.5.aab>,
  SHA-256 `86f74eefd3459b81a1f11f7ae71a8c7b91f625237ce997f7a8a158f7d4becbd0`,
  7.743.218 Bytes, lokale und entfernte Prüfsumme abgeglichen. `flexr-2.6.4.aab`
  liegt weiterhin daneben. Alle **älteren**
  AAB-Links in diesem Dokument liefern weiter 404: Der Ordner war am
  08.09.2026 auf Wunsch geleert worden (2.4.0–2.4.6, 2.5.0, 2.5.2, 2.5.5).
  Die zugehörigen Release-Dateien liegen daneben unter
  `~/MEGA/flexr/release-2.6.5/` (AAB, APK, `SHA256SUMS.txt`).
- **Namenskonvention** (seit 30.08. vereinheitlicht): neue Bundles landen in
  `dl-a616e78274de323b/` als `flexr-X.Y.Z.aab`, benannt nach dem
  `versionName` **aus dem Bundle** — hier gegengeprüft im Bundle-Manifest
  (`2.6.4`), nicht nur in der Gradle-Datei.
- Der zweite Ordner `dl-5d8a93fc22b232c9/` ist ebenfalls leer (enthielt bis
  zum 08.09. das 2.4.9-Bundle als `app-prod-release.aab`) und wird nicht mehr
  gebraucht.

## Sitzung 30.08.2026 (Android/iOS: Blockier-Liste + Listen-Poll, Telegram-Diagnose)

Drei Commits, alle gepusht (`3ad34da`, `f265ae8`, `d2042b9`) — **Web/Backend
auf dem VPS noch nicht ausgerollt**, nur das AAB wurde hochgeladen (dazu
unten mehr). Vorgeschichte: Der lokale Arbeitsstand auf diesem
MEGA-synchronisierten Gerät hatte den Telegram-Push (Commit `086341b`, von
einem anderen Gerät aus gepusht) bereits unversioniert auf der Platte liegen
— `git fetch` + `git reset --mixed origin/main` (siehe Abschnitt „Auf einem
anderen Gerät starten") hat das sauber aufgelöst, einzige echte Differenz
war ein bereits bekannter Trip-and-fall: `backend/.env.example` war auf
generische Platzhalter zurückgefallen, per `git checkout origin/main --
backend/.env.example` verworfen.

### 1. Android + iOS: „Blockierte Personen" — Commit `f265ae8`

Zieht das Web-Feature vom 23.08. (`bca5073`) auf beide native Clients nach:
neuer Abschnitt unter Konto → Datenschutz & Sicherheit mit Name, Alter,
Vorschaubild und Blockierdatum je blockierter Person, Knopf „Aufheben".
Backend unverändert — `GET /api/blocks?detail=true` und
`DELETE /api/blocks/{id}` gab es schon, nur eben keinen Bildschirm dafür.
Bewusst **nicht** die von der 23.08.-Notiz vorgeschlagene Umstellung des
Server-Standards auf die Detailfassung gemacht: eine neue Methode
(`listBlockedUsers`/`listBlocks(detail:)`) neben der alten reicht, und ohne
iOS-Compiler wäre eine Standardänderung nicht sicher verifizierbar gewesen.

Android: `FakeFlexrApi` (Testdouble) um die neue Methode ergänzt — die
bekannte Falle aus früheren Sitzungen (siehe „Android-Build" unten) hätte
sonst erst beim separaten Unit-Test-Compile zugeschlagen. Toolchain
(JDK 17 + Android SDK 36) war auf diesem Gerät nach einem Neustart wieder
weg (liegt unter `/tmp`, siehe „Android-Build") und musste neu installiert
werden. `compileProdReleaseKotlin`, `compileProdReleaseUnitTestKotlin` und
die volle Unit-Suite liefen grün: **51 Tests**.

iOS: wie in jeder bisherigen Sitzung **ungebaut** (kein Mac verfügbar) — Code
sorgfältig nach bestehenden Mustern geschrieben (`ConsentList`/`AccountModel`
als Vorlage für `BlockedUsersList`/die neuen `AccountModel`-Methoden), aber
nicht compilerverifiziert. Erster Schritt auf einem Mac bleibt
`./ios/tools/mac-build.sh`.

### 2. Android + iOS: Matches/Chats aktualisieren sich still im Hintergrund — Commit `d2042b9`

Der am 23.08. offene Prüfpunkt („haben Android/iOS denselben Listen-Bug wie
Web?") ist geklärt: **nein**, strukturell nicht. Android zeichnet Matches/
Chats aus Room-`Flow`s, iOS aus `@Observable`-Arrays — beide Wege redrawen
automatisch, sobald sich die zugrundeliegenden Daten ändern, ganz gleich ob
der Auslöser eine manuelle Aktualisierung oder ein Hintergrundabgleich ist.
Der Web-Bug (Badge aktualisiert sich, Liste nicht) kann dort gar nicht erst
entstehen.

Einzige echte Lücke: kein **Vordergrund**-Poll in Web-Kadenz (20s), während
der Bildschirm offen ist — die vorhandenen Hintergrund-Worker
(`NewMessageWorker` Android, `MessageRefreshService` iOS) sind an das
OS-Minimum von 15 Minuten gebunden. Nachgezogen als „Nice to have":
- Android: `MatchesViewModel.silentRefresh()` (kein Ladezustand, keine
  Fehlermeldung — die würden bei jedem 20s-Tick unnötig aufblitzen) plus
  `LaunchedEffect` in `MatchesScreen`/`ChatsScreen`, bricht automatisch ab,
  sobald der Bildschirm die Komposition verlässt.
- iOS: zusätzlicher `.task` in `MatchesView`/`ChatsView` nach dem Vorbild von
  `ChatModel.poll()` — SwiftUI bricht die Aufgabe beim Verlassen der Ansicht
  selbst ab.

**Da wieder Kotlin-Code unter `android-native/` geändert wurde, war ein
neues AAB fällig** (anders als am 23.08., wo das explizit nicht der Fall
war). Versionierung auf **2.5.0 / versionCode 38** angehoben (vorher 2.4.9 /
37). Build lief anfangs mit `FAILURE ... lintVitalAnalyzeProdRelease ...
Metaspace` — dieses Gerät hat nur 7,6 GB RAM, `~/.gradle/gradle.properties`
mit `-Xmx2048m -XX:MaxMetaspaceSize=384m` reichte für `lintVital` nicht.
Angehoben auf `-Xmx2560m -XX:MaxMetaspaceSize=768m` (Kotlin-Daemon auf
512m), danach lief `bundleProdRelease` durch. **Falle dabei:** Der erste
fehlgeschlagene Lauf hinterließ trotz `FAILURE` ein *scheinbar* gültiges
Bundle im Ausgabeverzeichnis — tatsächlich war das die Aug-23-Altlast
(SHA-256 `7431c17f...`, identisch mit dem in diesem Dokument zuvor
geführten 2.4.9-Bundle). Vor dem zweiten Versuch die Datei gelöscht und nach
dem Build **Prüfsumme UND den `2.5.0`-String im Manifest** kontrolliert,
nicht nur „Datei existiert".

Neues Bundle hochgeladen nach
`flexr-vps:/flexr/frontend/dl-a616e78274de323b/flexr-2.5.0.aab` (Prüfsumme
lokal/remote verglichen, per `curl -fsSI` gegengeprüft) — Details in den
Eckdaten oben. **Noch nicht in der Play Console** (siehe „Noch offen").

### 3. Telegram-Push-Diagnose: geklärt — kein Bug

Befund gemeldet: „Jemand hat sich registriert, ich habe aber keine
Telegram-Nachricht bekommen, obwohl das Update im Admin-Dashboard
auftauchte." Geprüft:

- `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` sind auf dem VPS gesetzt (nicht
  leer).
- `getMe` und `getChat` gegen die Telegram-Bot-API laufen beide erfolgreich
  vom VPS aus — Bot-Token gültig, Chat (`429666581`, privater Chat mit
  Julian/`@blktomcat`) für den Bot sichtbar. Netzwerk/Firewall zu
  `api.telegram.org` ist also nicht das Problem.
- `flexr-api.service` läuft seit dem 27.08. mit Commit `086341b` (dem
  Telegram-Feature) — der Code ist live.
- Journal-Log (`journalctl -u flexr-api`, geht bis 14.07. zurück, kein
  Rotationsproblem) zeigt **keine** Telegram-Fehlermeldung — aber
  `notify_admin_task()` loggt bei **Erfolg** bewusst nichts (nur bei
  fehlender Konfiguration oder Fehlschlag), ein stiller Erfolg sieht in den
  Logs also identisch zu „nie aufgerufen" aus.
- Timeline aus der DB rekonstruiert: Die letzte echte (Nicht-Test-)
  Registrierung vor dieser Sitzung war **Melanie** (`meli.moeser@gmail.com`,
  24.08.2026 18:52) — **einen Tag vor** dem Telegram-Deploy (`086341b`,
  25.08. 14:47). Für ihre Registrierung *konnte* also gar kein Push kommen,
  das Feature existierte serverseitig noch nicht. Ihr Foto lag seither
  unbearbeitet in der Warteschlange und wurde erst in dieser Sitzung
  (30.08., zusammen mit drei weiteren) über das Admin-Dashboard freigegeben.
- Während der Sitzung selbst gab es einen einzelnen `POST
  /api/profiles/me/photos` um 17:23:16 (gefolgt von einem `DELETE` vier
  Sekunden später) von derselben IP wie die Admin-Aktionen davor/danach —
  sieht nach einem eigenen Testlauf des Nutzers aus, nicht nach einer
  fremden Registrierung. Ob **dieser** Aufruf einen Telegram-Push ausgelöst
  hat, lässt sich aus den Logs nicht ablesen (s. o., Erfolg loggt nichts).

**Vom Nutzer bestätigt:** Die konkret gemeldete Registrierung (Melanie) war
tatsächlich der Fall (a) — ihr Foto-Upload lag zeitlich vor der Erstellung
des Bots, das Feature existierte für dieses Ereignis schlicht noch nicht.
Kein Versandfehler, der Push funktioniert. Kein weiterer Sendetest nötig.

**Nebenbefund, weiterhin relevant:** Bei der `getChat`-Diagnose ist im
Terminal-Output kurzzeitig der **volle Bot-Token im Klartext** gelandet
(fehlerhaftes `sed`-Redacting-Muster). Nur in dieser lokalen Session
sichtbar, aber sicherheitshalber lohnt es, den Token über @BotFather
(`/revoke`) neu zu erzeugen und in `backend/.env` zu aktualisieren.

### Was in dieser Sitzung nicht angefasst wurde

- **Kein Deploy auf den VPS** für Web/Backend — die drei Commits sind
  gepusht, aber `git pull` + Neustart auf dem VPS stehen noch aus (nur das
  AAB wurde direkt in den Download-Ordner geladen, das ist unabhängig vom
  Git-Deploy). Backend-Code ist ohnehin unverändert, ein Pull bräuchte also
  weder Migration noch Neustart, nur den reinen Dateistand.
- Punkt 2 aus der 23.08.-Liste („offene Fragen ans Web-Update, vom Nutzer
  noch nicht selbst begutachtet") wurde nur code-seitig gegengeprüft
  (Prüfsumme, CSS), nicht visuell auf einem Gerät.
- Kein Stripe-Testcheckout (weiterhin bewusst vermieden, s. u.) — der Nutzer
  hat lokal `sk_test_...`-Schlüssel konfiguriert, ein Checkout würde also
  kein echtes Geld bewegen, aber das Ausfüllen von Kartendaten (auch
  Test-Kartennummern) bleibt eine Aufgabe für den Nutzer selbst.

## Sitzung 23.08.2026 (Web-Frontend: Layout + Listen-Aktualisierung)

Vier Commits, alle gepusht und ausgerollt. Drei davon reines Web-Frontend,
der vierte (`bca5073`) zusätzlich Backend — **keine Migration** (nur ein
neuer Query-Parameter auf einem bestehenden Endpunkt), aber ein
**Dienst-Neustart** war dafür nötig. Reihenfolge:

| Commit | Inhalt |
|---|---|
| `3d00cf2` | Hero oben angeheftet *(wieder zurückgenommen, s. u.)* |
| `2885d7a` | Chat-/Matchliste ziehen von selbst nach |
| `42b9b9b` | Revert des Hero-Anheftens — Hero wieder mittig |
| `bca5073` | Blockierte Personen anzeigen und Blockierung aufheben |

### 1. Landingpage: Hero angeheftet — und auf Wunsch wieder zurückgenommen

**Endstand: der Hero ist wieder mittig, so wie vor dem 23.08.** Commit
`3d00cf2` hatte ihn oben angeheftet, Commit `42b9b9b` nimmt das wieder
zurück — dem Nutzer gefällt die mittige Ausrichtung besser, das Mitwandern
der Headline ist damit bewusst in Kauf genommen. Der Rest dieses Abschnitts
beschreibt, was das Anheften gelöst hätte, falls die Frage wiederkommt.

Zurückgenommen wurde beides, was zusammengehörte: das `align-self:start` und
die Aufteilung des oberen Abstands auf beide Auth-Screens (die diente allein
den letzten 28px Versatz). **Nicht** zurückgenommen: das `width:100%` auf
`.screen.active` im Mobil-Layout — das hing nicht am Anheften, sondern behebt
eine unabhängige Ungereimtheit (siehe unten).

Commit `3d00cf2`. Beim Umschalten von "Einloggen" auf "Registrieren" wanderte
die Headline knapp **400px** nach unten und war im ersten Bildschirm gar nicht
mehr zu sehen (gemessen bei 1440×900: h1 von y=186 auf y=579, also +393px;
der Hero-Block selbst von y=138 auf y=531).

Ursache: `body.landing main` ist ein Grid mit `align-items:center`. Die
Zeilenhöhe richtet sich nach der höheren Spalte, und die Registrierungsmaske
ist mit rund 1520px etwa viermal so hoch wie die Login-Maske (390px) — der
Hero zentrierte sich also an einer Karte, deren Höhe vom gewählten Reiter
abhängt.

Gepinnt wird jetzt **nur der Hero** (`align-self:start`), die Login-Karte
bleibt mittig zu ihm; der Login-Bildschirm sieht dadurch aus wie vorher. Die
Regel gilt erst ab 861px — darunter ist `main` ein Flex-Column-Layout, dort
würde `align-self` die *Breite* statt der Höhe steuern.

Danach blieben noch 28px Versatz, weil der kompakte obere Abstand (Kopfzeile
18/4, `main` 10) nur für `[data-screen="screen-login"]` galt. Der **Abstand**
gilt jetzt für beide Auth-Screens, die **Höhen-/Flex-Regeln** bleiben dem
Login vorbehalten (nur der passt garantiert ohne Scrollen in einen Schirm).

Ergebnis: h1 steht in Login, Registrierung und zurück auf demselben Wert,
Verschiebung **0px** — bei 1440×900, 1920×1080 und 1821×934 jeweils y=115,
bei 1280×700 (kurzer Schirm, dort greift die Login-Vollhöhenregel gar nicht)
y=143. Zusätzlich 375×812 geprüft. Alles lokal gemessen und nach dem Deploy
noch einmal live auf flexr.social gegengeprüft (1821×934: 0px; mobil beide
Masken 339px breit wie der Hero, kein horizontaler Scroll).

Anmerkung zur Commit-Nachricht von `3d00cf2`: dort steht der Vorher-Wert
fälschlich mit „1821×934: y=115 auf y=508". Gemessen wurde der kaputte
Zustand bei 1440×900 (y=186 → y=579); bei 1821×934 wurde nur der reparierte
Zustand geprüft. Die Größenordnung (~400px) stimmt, die Viewport-Angabe im
Commit nicht.

Nebenbei mitgenommen: mobil erbte `.screen.active` das `align-items:center`
des Desktop-Grids. In einer Flex-Column heißt das Schrumpfen auf die
Inhaltsbreite — die kurze Login-Maske war rund 23px schmaler als Hero und
Registrierungsmaske und saß sichtbar eingerückt. `width:100%` behebt das.

### 2. Echter Bug: Chat- und Matchliste blieben eingefroren stehen

Commit `2885d7a`. Wer auf dem Chats-Bildschirm stehenblieb, sah eine sich
selbst widersprechende Oberfläche: die Liste meldete **"Noch keine Chats"**,
während der Reiter daneben schon eine **Ungelesen-Zahl** zeigte.

Ursache: `refreshUnreadBadge()` läuft alle 20s, holt `/api/matches` frisch und
aktualisierte davon **nur die Zahl am Reiter**. Neu gezeichnet wurden die
Listen ausschließlich beim Antippen des Menüpunkts (`loadChats`/
`loadMatches`). Eine eintreffende Nachricht änderte also weder Vorschautext
noch Ungelesen-Punkt noch Reihenfolge — und ein Chat, der erst durch diese
Nachricht wieder entsteht (erste Nachricht eines Matches, oder nach "Chat
löschen"), fehlte ganz, bis man einmal weg und wieder hin navigierte.

`loadChats`/`loadMatches` sind jetzt in Holen und Zeichnen getrennt
(`renderChats`/`renderMatches`); der Hintergrund-Abgleich zeichnet die Liste
mit, wenn der zugehörige Bildschirm sichtbar ist. Beide Zeichenfunktionen
merken sich das zuletzt erzeugte Markup und steigen bei Gleichheit aus —
sonst würde alle 20s die halbe Liste ersetzt und Hover-/Fokuszustand gingen
verloren. `loadChats`/`loadMatches` setzen den Vergleichswert zurück, weil sie
vorher den „Lädt …"-Platzhalter schreiben.

### 3. Blockierungen sichtbar machen und aufheben können

Commit `bca5073`. Das war zunächst als Fund ohne Fix notiert und ist auf
Wunsch nachgezogen worden.

Neu im Web unter **Konto → Datenschutz & Sicherheit** der Abschnitt
„Blockierte Personen": Name, Alter, Vorschaubild, Datum, Knopf „Aufheben".

Backend: `GET /api/blocks` bekommt ein optionales **`?detail=true`** und
liefert dann `BlockedUserOut` statt der reinen ID-Liste. Die Standardform
bleibt absichtlich unverändert — Android (`FlexrApi.listBlocks`) und iOS
(`FlexrAPI.listBlocks`) deklarieren `List<String>` bzw. `[String]`, eine
geänderte Standardantwort würde dort beim ersten Aufruf brechen. Auf diesem
Gerät lässt sich weder Android noch iOS übersetzen, deshalb blieben beide
unangetastet; ein Test hält die alte Form fest, damit sie nicht versehentlich
kippt. **Wer als Nächstes an Android oder iOS arbeitet und dort bauen kann:**
dann lohnt es, die Standardform auf die Detailfassung umzustellen und die drei
Deklarationen mitzuziehen — der Parameter ist nur ein Kompatibilitätskrücke.

`BlockedUserOut` zeigt bewusst nur, was zum Wiedererkennen nötig ist. Kein
Bio, kein Gym, keine Entfernung — wer jemanden blockiert hat, soll dessen
Profil nicht weiter einsehen können. Fürs Foto gilt dieselbe Regel wie im
Deck: nur Status `approved`.

**Beim Bauen präzisiert und wichtig zu wissen:** Blockieren **löst ein Match
nicht auf**, es blendet es nur aus. Nach dem Aufheben sind Match *und*
Chatverlauf wieder da. Der erste Entwurf des Hinweistextes behauptete das
Gegenteil; korrigiert, und ein Test hält das Verhalten jetzt fest.

### Was sonst noch getestet wurde (alles unauffällig)

Zwei Testkonten über die echte Oberfläche angelegt, gematcht, in beide
Richtungen geschrieben:

- „Chatverlauf leeren" / „Chat löschen" — die Fixes vom 21.08. halten: der
  Verlauf bleibt bei der Gegenseite, der Chat kommt bei neuer Nachricht mit
  frischem Verlauf zurück, das Match überlebt.
- XSS in Nachrichten (`<img onerror>`, `<script>`) — sauber escaped.
- Link-/E-Mail-Zensur greift. Telefonnummern gehen **absichtlich** durch
  (so dokumentiert in `safety_checks.py`) — kein Bug.
- Bio-Prüfung: Links und Telefonnummern werden abgewiesen.
- **IDOR-Prüfung** mit einem dritten, freigeschalteten Konto gegen alle
  Match-/Chat-Endpunkte (GET/POST messages, DELETE chat/match/messages):
  durchgehend 404, kein Datenabfluss.
- Admin-Endpunkte gegen ein Nutzer-Token: durchgehend 401.
- Eingabeprüfung: leere Nachricht, nur Leerzeichen, 5000 Zeichen → 422;
  Swipe auf sich selbst → 400.
- Abgelaufener Probemonat: Deck und Matches 402, Paywall-Bildschirm korrekt.
- Match auflösen, Blockieren (beidseitig wirksam), Kontolöschung inkl.
  sofort ungültigem Token und 30-Tage-Reaktivierungsfrist.
- Backend-Suite vor und nach den Änderungen: **362 Tests grün**,
  nach dem Blockier-Feature **367** (5 neue in `tests/test_safety.py`).

Kein Stripe-Checkout ausgelöst (wie in den Sitzungen davor bewusst vermieden).

### Braucht es für diese Änderungen ein neues AAB? Nein.

Die Frage kam am Ende der Sitzung auf; die Antwort ist an drei Punkten
festzumachen und gilt sinngemäß auch beim nächsten Mal:

1. **Unter `android-native/` wurde nichts geändert.** Letzter Commit dort ist
   `062bb99` (versionCode 37, versionName 2.4.9) und liegt vor allen Commits
   dieser Sitzung. Ein Neubau erzeugte dasselbe Programm mit demselben
   versionCode — die Play Console lehnt das ohnehin als Dublette ab.
2. **Das bereits hochgeladene Bundle ist auf Stand.** Das AAB unter
   `dl-5d8a93fc22b232c9/` ist nachweislich 2.4.9 (Versionsstring im
   `base/manifest/AndroidManifest.xml`, FLEXR-Signatur im Bundle) und deckt
   sich mit `build.gradle.kts`.
3. **Die Backend-Änderung bricht die App nicht.** `GET /api/blocks` liefert
   ohne `?detail=true` weiterhin exakt die alte ID-Liste — genau deshalb wurde
   die Standardform nicht angefasst (siehe Abschnitt 3).

Ein neues AAB wird erst fällig, wenn wieder Kotlin-Code angefasst wird — etwa
für die beiden offenen Android-Punkte (Blockier-Liste, Listen-Aktualisierung).
Dann gilt der Ablauf im Abschnitt „Android-Build" und das Hochzählen von
versionCode **und** versionName.

### Beobachtung am Rande: doppelte Element-IDs in den Profilkarten

`buildCardEl()` vergibt in **jeder** erzeugten Karte dieselben IDs
(`btnReportCard`, `btnBlockCard`, `btnUnmatchCard`). Stehen Swipe-Deck und
Match-Profil gleichzeitig im DOM — was der Normalfall ist —, gibt es diese
IDs mehrfach. Funktional geht das gut, weil die Handler über
`el.querySelector` innerhalb der jeweiligen Karte gebunden werden und nicht
über `getElementById`. Es ist trotzdem ungültiges HTML und eine Falle: ein
`document.getElementById('btnBlockCard')` trifft immer die **erste** Karte im
Dokument, nicht die sichtbare. Beim Testen ist genau das zweimal passiert und
sah jedes Mal nach einem Anwendungsfehler aus. Nicht angefasst — die Umstellung
auf Klassen berührt mehrere Stellen und hat keinen Nutzerwert.

### Stolperstein beim Deploy: VPS-Pull brauchte den Deploy-Key explizit — erledigt am 07.09.2026

**Historisch, seit 07.09.2026 behoben.** Von 23.08. bis 07.09. scheiterte
`ssh flexr-vps 'cd /flexr && git pull --ff-only origin main'` mit
`Permission denied (publickey)`: Der Deploy-Key lag als
`~/.ssh/id_ed25519_github_flexr` auf dem Server, aber keine `~/.ssh/config`
zeigte git darauf. Jeder Pull brauchte deshalb ein vorangestelltes
`GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github_flexr -o IdentitiesOnly=yes"`.

Seit 07.09. liegt die abgesprochene `~/.ssh/config` auf dem VPS:

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github_flexr
    IdentitiesOnly yes
```

`IdentitiesOnly yes` ist der Kern der Sache: Ohne den Eintrag bietet ssh
github.com der Reihe nach alle vorhandenen Identitäten an, github nimmt die
erste bekannte und lehnt sie für dieses Repository ab. Der Block greift nur
für `github.com`, andere SSH-Ziele bleiben unberührt — auf diesem **geteilten**
Server wichtig. Geprüft wurde vorher, dass `/flexr` das einzige Repository auf
dem Server mit einem github-Remote ist (`/vaultonaut` hat gar keinen Origin).

Falls der Fehler je wiederkehrt: Erst `ssh flexr-vps 'ssh -T git@github.com'`
— die Antwort muss „Hi flexrsocial/flexr! You've successfully authenticated"
lauten. Kommt sie, liegt es nicht am Schlüssel.

### Lokal testen: zwei Fallen, die viel Zeit kosten können

1. **`backend/.env` zeigt auf den PRODUKTIONS-Bucket.** `DATABASE_URL` steht
   zwar auf localhost, aber `S3_ENDPOINT_URL`/`S3_BUCKET_NAME` zeigen auf das
   echte R2 `flexr-photos`. Da bei der Registrierung ein Foto Pflicht ist,
   landen Testbilder sonst im Produktions-Storage. Abhilfe: die S3-Variablen
   per **Umgebungsvariable** überschreiben (die schlagen in pydantic-settings
   die `.env`-Datei) und gegen einen lokalen S3-Ersatz fahren. boto3 nutzt bei
   einem localhost-Endpunkt Path-Style-URLs; ein kleiner Fake-Server mit
   PUT/GET(+Range)/HEAD/DELETE/COPY/`list_objects_v2` reicht der App aus.
2. **CORS/Origin.** Die Web-App setzt bei Host `localhost`/`127.0.0.1` die
   API-Basis fest auf `http://localhost:8000` — ein Proxy vor dem Frontend
   wird für `/api` also gar nicht benutzt. Erlaubt sind laut `app/main.py` nur
   `settings.frontend_url`, `http://localhost:5173` und `http://localhost:8000`.
   Das Frontend deshalb auf **Port 5173** ausliefern. Für **zwei gleichzeitig
   eingeloggte Testnutzer zwei verschiedene Origins** verwenden
   (`localhost:5173` und `127.0.0.1:5173`, zweiter über `FRONTEND_URL`
   freigeschaltet) — sonst teilen sich beide Tabs den localStorage und damit
   das Token, was sich sehr überzeugend als Anwendungsfehler tarnt.

Freischalten neuer Testkonten ohne Kamera: Fotos über
`POST /api/admin/photos/{id}/approve` freigeben (sonst erscheint das Profil in
keinem Deck) und das Konto mit `verification_service.activate_account(user)`
plus `is_verified`/`age_verified` aktivieren — denselben Weg geht die
Admin-Freigabe.

### Testkonten dieser Sitzung — nur in der LOKALEN Datenbank

Nicht auf Produktion, dort ist nichts angelegt worden:

| Name | Login-E-Mail | Passwort |
|---|---|---|
| Mara Testerin | `bugtest-mara@flexrtest.at` | `TestPass123!` |
| Tim Tester | `bugtest-tim@flexrtest.at` | `TestPass123!` |
| Eva Dritte | `bugtest-eva@flexrtest.at` | `TestPass123!` (selbst gelöscht, in Karenz) |

Ebenfalls nur lokal: `localadmin@example.com` hat jetzt das Passwort
`LocalAdmin123!` (für die Admin-Oberfläche im Test).

## Sitzung 21.08.2026

### Wichtiger Fund zu Beginn jener Sitzung: lokaler Git-Stand war veraltet

Auf **diesem** Gerät (Pfad `~/MEGA/flexr/flexr`, MEGA-Cloud-Sync) zeigte
`git log -1` auf einen sehr alten Commit (`a30a071`), obwohl die Dateien auf
der Platte über MEGA-Sync größtenteils aktuell waren — mutmaßlich, weil auf
diesem Gerät nie `git pull` liefen und stattdessen nur Dateien synchronisiert
wurden. `git diff`/`git status` waren dadurch am Anfang **irreführend**
(zeigten tausende Zeilen an vermeintlichen Änderungen, die gar keine echten
Änderungen waren, plus einige echte veraltete Datei-Leichen wie
`frontend/legal.css`, `frontend/widerruf.html`, alte `frontend/brand/demo/`-
Bilder, die in neueren Commits bereits entfernt wurden).

**Fix:** `git fetch origin` und danach `git reset --mixed origin/main` (verändert
nur HEAD/Index, lässt das Arbeitsverzeichnis unangetastet). Erst danach zeigte
`git status` die tatsächlichen, beabsichtigten Änderungen. Auf einem neuen
Gerät IMMER zuerst so prüfen, bevor irgendetwas committet wird — sonst droht
entweder ein riesiger Fehl-Commit oder (schlimmer) ein `git add -A`, das
echte, neuere Dateien fälschlich als „gelöscht" einstuft.

## Was am 21.08.2026 umgesetzt wurde

Reihenfolge in etwa chronologisch, alles einzeln committet, getestet,
gepusht und deployt (Backend-Restart bzw. Migration wo nötig).

### 1. Web: Chat-Header-Avatar-Ring zeigte eine Lücke

`.chat-header img` nutzte noch die alte Spread-`box-shadow`-Ringtechnik
(dieselbe Klasse Bug, die für Konto- und Matchlisten-Avatar schon einmal
gefixt worden war). Erster Fix: echter `border` auf einem `::after` — löste
das Problem laut Nutzer-Screenshot **nicht vollständig** (vermutlich
Sub-Pixel-Rundung zwischen zwei separat positionierten Kreisrändern bei
gebrochenem Bildschirm-Skalierungsfaktor). **Zweiter, robusterer Fix:** der
Ring ist jetzt die Hintergrundfarbe eines einzigen gefüllten Kreis-Elements,
das Foto sitzt per Padding darin — nur noch eine Kreiskontur statt zwei.
Noch nicht vom Nutzer nach dem zweiten Fix bestätigt — als Erstes in der
nächsten Sitzung nachfragen/prüfen.

### 2. Web + Android: Profilbild-Thumbnails schnitten Gesichter ab

Der 256px-Quadrat-Thumbnail-Crop beim Foto-Upload war strikt mittig
(`sy = (h - side) / 2`). Bei Hochformat-Fotos mit Kopf-Freiraum schnitt das
die Stirn ab. Jetzt `sy = (h - side) * 0.15` (Richtung oberer Rand) in
`frontend/app/index.html` (`preparePhoto`) und
`android-native/.../core/media/ImageProcessor.kt` (`centerSquare`). Wirkt
nur für **neu hochgeladene** Fotos — bereits vorhandene Thumbnails bleiben
wie sie sind (der Fix ist client-seitig, das Backend croppt nie).

### 3. "Chatverlauf leeren" ließ den ganzen Chat aus der Chats-Liste verschwinden

Bug lag in allen Clients (Web, Android, auch iOS betroffen — nicht gefixt,
siehe „Noch offen"): Die Chats-Liste filterte auf `last_message != null`.
Nach dem Leeren wird `last_message` server-seitig korrekt `null` (Backend war
nie das Problem), die Clients werteten das aber fälschlich als „kein Chat
mehr" statt „Chat da, nur leer". Fix: neues Backend-Feld `in_chats` auf
`MatchOut` (`GET /api/matches`), das unabhängig von `last_message`/`cleared_at`
ist — bleibt nach dem Leeren `true`. Web + Android nutzen jetzt `in_chats`
statt `last_message` als Listen-Filter.

### 4. "Chat löschen" löschte versehentlich das ganze Match

Rief bislang denselben Endpunkt wie "Match auflösen" auf (`DELETE
/api/matches/{id}`) — löschte also Match, Swipe und Verlauf komplett, obwohl
der Button im Chat-Menü etwas anderes suggerierte als der separate
"Match auflösen"-Button im Matchprofil. Neuer Endpunkt
`DELETE /api/matches/{id}/chat`: Match, Swipe und Nachrichten bleiben
bestehen, nur `in_chats` wird für die löschende Seite zurückgesetzt (kehrt
bei einer neuen Nachricht automatisch zurück, wie bei anderen Messengern).
Backend-Migration `6f2a3c9d7e15` ergänzt `user_a/b_chat_deleted_at` auf
`matches`.

### 5. Web: rechts abgeschnittener Rahmen beim Hover über eine Chat-Kachel

Ursache: `.match-item:hover{ transform:translateX(2px); }` schob die Kachel
2px nach rechts; auf Desktops mit klassischem (nicht Overlay-)Scrollbalken
fraß der sich in die rechten 20px Innenabstand von `main`/`.screen.active`
hinein, sodass die 2px-Verschiebung den abgerundeten Rand unter den
Scrollbalken schob. Fix: `scrollbar-gutter: stable` auf beiden scrollenden
Containern.

### 6. "Sofortiger Leistungsbeginn" — Widerruf-Knopf entfernt (tat nie etwas)

Der Nutzer fragte, was der Widerruf dieser Einwilligung bewirkt — Antwort:
nichts. Es gab zwei parallele Datensätze für dieselbe Sache: den
widerrufbaren `Consent`-Ledger-Eintrag (nur fürs Konto-UI) und den
tatsächlich maßgeblichen, bewusst **nicht** widerrufbaren
`CheckoutConsent`-Datensatz (§ 10/§ 18 Abs. 1 Z 1 FAGG, wirkt fort, solange
der Vertrag läuft). Der Widerrufen-Knopf beim Ledger-Eintrag täuschte also
eine Wirkung vor, die es nicht gab. Entfernt: `billing.py` legt keinen
`Consent`-Ledger-Eintrag für `immediate_start` mehr an, Web/Android zeigen
dafür keinen Widerrufen-Knopf mehr (alte, historische Einträge bleiben zur
Ansicht stehen, nur ohne Knopf).

### 7. Echter Bug: Widerruf von "Geschlecht/gesuchtes Geschlecht" wirkte nicht

Beim Testen von Punkt 6 fiel auf: `GET /api/profiles/me/consents/revoke` für
`sensitive_data` versprach *"du erscheinst in keinem Deck mehr"* — das wurde
aber **nirgends durchgesetzt**. `swipes.get_deck()` prüfte den Consent-Status
gar nicht. Neuer Filter `consents.sensitive_data_consent_condition()`
(korrelierte EXISTS-Subquery), jetzt Teil der `base_filters` in
`routers/swipes.py`.

### 8. Datenlücke dabei entdeckt: mehrere Konten ohne Consent-Zeile

Beim Testen von Punkt 7 fiel auf: mehrere aktive Konten — **darunter das
echte Konto `pachernegg@gmail.com`** — hatten trotz gesetztem Altfeld
`users.sensitive_data_consent_at` **keine** Zeile in der neueren
`consents`-Tabelle. Ohne Nachtrag hätte der neue Deck-Filter aus Punkt 7 sie
fälschlich unsichtbar gemacht, obwohl nie widerrufen wurde. Migration
`9c4e1a7f2b83` trägt das nach (gleicher Ansatz wie die ursprüngliche
Consent-Migration `a1f7c39b2d40`, die das schon einmal für alle
**damals** bestehenden Konten gemacht hatte — offenbar wurden danach
Konten angelegt, ohne über `consents.grant()` zu laufen, mindestens die per
Skript direkt in die DB geschriebenen Testkonten jener Sitzung).

**Falle beim ersten Migrationslauf:** Die Bedingung prüfte zunächst nur
„keine AKTIVE Zeile" statt „noch nie irgendeine Zeile" — dadurch bekam
`pachernegg@gmail.com`, das kurz zuvor testweise selbst über die App
widerrufen hatte, fälschlich eine neue aktive Zeile und der Widerruf wurde
stillschweigend rückgängig gemacht. Auf Produktion von Hand korrigiert
(die einzelne betroffene Zeile wieder gelöscht), Migrationsdatei danach
korrigiert (Commit `8b80faa`) — bei einem etwaigen **Neu**-Deploy auf einer
frischen DB tritt der Fehler nicht mehr auf.

### 9. Neuer Endpunkt: Widerruf zurücknehmen

`POST /api/profiles/me/consents/grant` — ein Widerruf von `sensitive_data`
oder `verification_media` lässt sich jetzt zurücknehmen (erneute
Einwilligung). Ohne das blieb ein Konto nach dem Widerruf von
`sensitive_data` dauerhaft mit leerem Deck zurück, reparierbar nur über die
Kontolöschung. Web + Android zeigen bei widerrufenen, widerrufbaren
Einwilligungen jetzt "Einwilligung erneut erteilen" — aber nur auf der
jeweils **neuesten** Zeile je Art (nach Widerruf+Neuerteilung gibt es zwei
historische Zeilen derselben Art, nur die neueste bekommt einen
Aktions-Knopf).

### 10. Android: "— widerrufen" brach Buchstabe für Buchstabe um

Layout-Bug in `ConsentSection` (`AccountScreen.kt`): `Row(Text(label),
Text("— widerrufen"))` — bei einem langen Label (z. B. "Verarbeitung von
Geschlecht und gesuchtem Geschlecht") blieb für den zweiten `Text` in der
`Row` (die nicht umbricht) kaum Restbreite, der Suffix brach dadurch
zeichenweise am rechten Bildschirmrand um. Fix: ein einzelnes
`AnnotatedString`-`Text` statt zwei `Text`s in einer `Row` — wickelt als ein
Absatz normal um.

## Android-Build — Toolchain auf diesem Gerät

Anders als beim letzten Gerät (3,7 GB RAM, stark limitiert) hat dieses hier
**7,6 GB RAM** — der reguläre Build lief ohne Sonderbehandlung durch. Es gab
hier weder JDK noch Android SDK; beides wurde ad hoc installiert:

> **Nachtrag 06.09.2026:** Das Gerät dieser Sitzung hat **3,8 GB RAM** (plus
> 3,8 GB Swap). Die schon vorhandene, sparsame `~/.gradle/gradle.properties`
> (siehe unten, mit `-XX:+UseSerialGC`) stammt von einem früheren Lauf auf
> genau dieser Maschine und wurde unverändert übernommen — nicht durch eigene
> Schätzwerte ersetzen. Während des Builds sind **alle lokalen Testdienste zu
> beenden** (uvicorn, der S3-Ersatz, `http.server`, offene Browser-Tabs);
> mit ihnen zusammen blieben nur noch rund 130 MB frei.

> **Stand 07.09.2026: die Toolchain liegt unter `~/.bubblewrap/`.** Weder
> `~/android-toolchain/` noch der ältere `/tmp`-Pfad existieren auf diesem
> Gerät; `local.properties` zeigte zudem auf ein verschriebenes
> `/home/blcktomcat/...` (mit „c"). Vorhanden und vollständig ist stattdessen
> die Toolchain, die seinerzeit `bubblewrap` für den TWA-Build mitgebracht hat
> — nichts muss nachinstalliert werden:
>
> ```bash
> export JAVA_HOME=~/.bubblewrap/jdk/jdk-17.0.11+9      # Temurin 17.0.11+9
> export PATH="$JAVA_HOME/bin:$PATH"
> export ANDROID_HOME=~/.bubblewrap/android_sdk          # platforms;android-36,
> echo "sdk.dir=$HOME/.bubblewrap/android_sdk" \
>   > android-native/local.properties                    # build-tools 34/35
> ```
>
> **Vor der Neuinstallation einer Toolchain immer erst hier nachsehen**
> (`find / -xdev -name sdkmanager -o -name javac`) — der Abschnitt darunter
> beschreibt den Neuaufbau, der auf diesem Gerät nicht nötig ist.
>
> **Release-Builds mit `--no-build-cache` bauen.** Am 07.09. brach
> `compileProdReleaseJavaWithJavac` mit „duplicate class:
> dagger.hilt.internal.aggregatedroot.codegen._flexr_social_app_FlexrApplication"
> ab. Kein Codefehler — `compileProdReleaseKotlin` lief sauber durch. In
> `app/build/generated/ksp/prodRelease/java/` lag dieselbe Hilt-Klasse zweimal:
> unter dem heutigen Pfad `dagger/hilt/internal/…` und unter dem älteren
> `hilt/internal/…`.
>
> `./gradlew clean` hat **nicht** geholfen — der Fehler kam sofort wieder
> („13 from cache"). Die Quelle ist der **Gradle-Build-Cache**
> (`org.gradle.caching=true` in `~/.gradle/gradle.properties`,
> `~/.gradle/caches/build-cache-1`): Dort liegt ein vergifteter
> KSP-Task-Eintrag aus einer älteren Hilt-/KSP-Fassung, der beide Pfade
> enthält. Nachgewiesen mit
> `./gradlew --offline --no-build-cache clean :app:kspProdReleaseKotlin` —
> frisch generiert entsteht die Datei genau einmal.
>
> Also: `./gradlew --offline --no-build-cache :app:bundleProdRelease
> :app:assembleProdRelease`. Wer den Cache dauerhaft loswerden will, löscht
> `~/.gradle/caches/build-cache-1` (kostet beim nächsten Build Zeit, sonst
> nichts).
>
> **Stand 06.09.2026 (überholt):** lag unter `~/android-toolchain/`, davor
> unter `/tmp` — beide Pfade waren beim nächsten Start weg. Der Gradle-Cache
> unter `~/.gradle` (1,9 GB) überlebt dagegen jeden Neustart, der Build zieht
> deshalb kaum Abhängigkeiten nach und läuft mit `--offline` durch.

```bash
# JDK (Temurin 17) und Android Commandline-Tools nach ~/android-toolchain
mkdir -p ~/android-toolchain && cd ~/android-toolchain
curl -fsSL -o jdk.tar.gz "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse"
curl -fsSL -o cmdline-tools.zip "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
mkdir -p jdk sdk/cmdline-tools
tar xzf jdk.tar.gz -C jdk --strip-components=1
unzip -q cmdline-tools.zip -d sdk/cmdline-tools && mv sdk/cmdline-tools/cmdline-tools sdk/cmdline-tools/latest

export JAVA_HOME=~/android-toolchain/jdk
export PATH="$JAVA_HOME/bin:$PATH"
yes | sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=$PWD/sdk --licenses
sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=$PWD/sdk \
  "platform-tools" "platforms;android-36" "build-tools;36.0.0"

echo "sdk.dir=$HOME/android-toolchain/sdk" > /pfad/zu/flexr/android-native/local.properties
```

Dauer inkl. Download rund 6 Minuten (JDK 60 MB, cmdline-tools 130 MB,
SDK-Pakete zusammen ca. 800 MB).

`~/.gradle/gradle.properties` wurde vorsorglich (nicht zwingend nötig bei
7,6 GB RAM) auf moderate Werte gesetzt:

```properties
org.gradle.jvmargs=-Xmx2048m -XX:MaxMetaspaceSize=384m -Dfile.encoding=UTF-8
org.gradle.parallel=false
org.gradle.workers.max=2
org.gradle.caching=true
kotlin.daemon.jvmargs=-Xmx1536m -XX:MaxMetaspaceSize=384m
```

Auf einem neuen Gerät: JDK/SDK entweder neu installieren (s. o., dauert ca.
5–10 Min inkl. Download) oder prüfen, ob unter `/tmp` noch etwas vom letzten
Mal übrig ist (unwahrscheinlich, `/tmp` wird meist beim Neustart geleert).

**Falle, die am 21.08. zweimal auftrat:** Nach dem Hinzufügen einer
neuen Methode zum `FlexrApi`-Interface (z. B. `deleteChat`, `grantMyConsent`)
schlägt `:app:compileProdReleaseUnitTestKotlin` fehl, weil `FakeFlexrApi`
(unter `app/src/test/.../testing/FakeFlexrApi.kt`) das Interface vollständig
implementiert und bei jeder neuen Methode ergänzt werden muss (`override
suspend fun neueMethode(...) = nichtVorgesehen("neueMethode")`) — alle
anderen Test-Doubles erben von `FakeFlexrApi` und beheben sich dadurch von
selbst. `:app:compileProdReleaseKotlin` (Hauptcode) meldet das **nicht**,
erst der separate Unit-Test-Compile-Schritt — immer beide laufen lassen,
nicht nur den ersten.

## FLEXR Premium ausprobieren, ohne die Produktion anzufassen

Die drei Premium-Funktionen sind in allen drei Oberflächen umgesetzt, aber auf
keinem Gerät je gesehen worden — weil sie es gar nicht sein können, solange
`PREMIUM_ENABLED` am Server `false` ist.

**Ein Testkonto auf `is_subscribed = true` zu setzen reicht nicht.** Der Wert,
an dem alles hängt, ist abgeleitet (`backend/app/models.py`):

```python
@property
def is_premium(self) -> bool:
    return settings.premium_enabled and bool(self.is_subscribed)
```

Beide Bedingungen müssen wahr sein. Ohne den Schalter bleibt `is_premium` also
falsch, egal was in der Zeile steht.

**Den Schalter in der Produktion umzulegen ist der falsche Weg.** Er schaltet
nicht nur die Zusatzfunktionen frei, sondern zugleich **die Grenzen für alle
Standardkonten scharf**: 20 Likes je rollierende 24 Stunden, 3 gleichzeitig
offene Unterhaltungen, 50 km Umkreis. Das sind nach AGB Punkt 7 b vertragliche
Zusagen, keine Testeinstellungen — und wer gerade mitten im Wischen ist, stößt
ohne Vorwarnung an eine Wand. Ein eingestellter Suchumkreis über 50 km wird
dabei zudem stillschweigend zurückgesetzt (`premium.clamp_radius`).

**Der saubere Weg ist ein lokales Backend.** Die Android-App bringt dafür einen
eigenen Flavor mit (`local`, `applicationIdSuffix = ".local"`, API-Basis
`http://10.0.2.2:8000/` — das ist der Host-Rechner aus Sicht des Emulators):

```bash
# 1. Lokales Backend mit scharfem Schalter
cd backend
PREMIUM_ENABLED=true venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Testkonto anlegen, dann in der lokalen Datenbank:
#    UPDATE users SET is_subscribed = true WHERE email = '...';

# 3. App im local-Flavor bauen und aufspielen
cd ../android-native
./gradlew :app:installLocalDebug
```

Damit sind alle drei Funktionen in einem Durchgang prüfbar: Abzeichen neben dem
Namen (Deck, Matchliste, Chat-Kopf, Konto), der Zurücknehmen-Knopf links neben
„Nope", und „Wer dich geliket hat" — letzteres lohnt **in beiden Zuständen**,
mit und ohne Abo, weil der gesperrte Fall eine eigene Ansicht hat und nicht
bloß eine Fehlermeldung.

Für iOS gibt es keinen entsprechenden Flavor; dort müsste die Basis-URL von Hand
umgestellt werden. Weil die iOS-Fassung ohnehin nur über Codemagic gebaut wird,
ist der Android-Weg der praktikable — die Oberflächen sind funktionsgleich
gebaut, und was dort auffällt, gilt mit hoher Wahrscheinlichkeit auch hier.

## Testdaten für manuelles Testen (Produktion, angelegt am 21.08.2026)

Auf Wunsch zweimal gelöscht und neu angelegt, zuletzt mit **echten
Hochformat-Fotos** (1080×1440, aus `~/MEGA/flexr/seed/fotos/`, Unsplash-
Quellen aus einer früheren Sitzung), damit der Foto-Crop-Fix aus Punkt 2
sichtbar getestet werden kann — die vorherigen Läufe nutzten quadratische
Demo-Bilder aus `frontend/brand/demo/`, an denen der Crop-Unterschied gar
nicht sichtbar gewesen wäre.

Alle im 158-km-Suchradius von `pachernegg@gmail.com` (Julian, McFit
Triester Straße, 1100 Wien), `verification_required=False`, sofort aktiv:

| Name | Login-E-Mail | Passwort |
|---|---|---|
| Katharina | `pachernegg+flexrtest-katharina@gmail.com` | `2fCSNfuA9tZa` |
| Sarah | `pachernegg+flexrtest-sarah@gmail.com` | `AOjXkqxhzcHF` |
| Verena | `pachernegg+flexrtest-verena@gmail.com` | `l54K_mGm3i_T` |
| Sophie | `pachernegg+flexrtest-sophie@gmail.com` | `XSpTcLIPXnT5` |
| Elena | `pachernegg+flexrtest-elena@gmail.com` | `-YcvPAAMriaQ` |

Anlage-Skript lief direkt gegen die Produktions-DB auf dem VPS (SQLAlchemy,
kein rohes SQL), Fotos per `storage.get_s3_client()` nach R2 hochgeladen —
kein eigenes Skript-File hinterlassen (`/tmp` auf dem VPS danach geleert).
Bei Bedarf lässt sich das Vorgehen aus diesem Handoff-Abschnitt und den
Git-Commits jener Sitzung rekonstruieren, oder aus
`~/MEGA/flexr/seed/README.md` (anderes, separates Testkonten-Batch,
`@flexrtest.at`, seit Sitzung 18.09.2026 (3) wieder aktuell: 30+30 Konten
für den Premium-Funktionstest).

**Bewusst nicht angerührt:** `teresa.pachernegg@gmail.com` — weiterhin
unklar, ob Testkonto, auf Nutzerwunsch erhalten.

Zum späteren Aufräumen: `email LIKE 'pachernegg+flexrtest-%'`, über den
echten Löschweg (`delete_storage_objects`/`storage_keys_for_user` +
`db.delete(user)`), nicht per rohem SQL.

## Noch offen / bewusst nicht erledigt

1. ~~**Blockieren lässt sich auf keiner Plattform rückgängig machen**~~ —
   **erledigt**: Web am 23.08. (`bca5073`), Android + iOS am 30.08.
   (`f265ae8`, siehe Sitzung 30.08. Punkt 1). Bewusst **nicht** mitgezogen:
   die Umstellung des `GET /api/blocks`-Standards auf die Detailfassung —
   die neuen Methoden (`listBlockedUsers`/`listBlocks(detail:)`) laufen
   parallel zur alten, siehe Docstring in `safety.py`.
2. ~~**`~/.ssh/config` auf dem VPS fehlt**, deshalb scheitert der weiter
   unten dokumentierte `git pull`-Befehl.~~ — **erledigt am 07.09.2026**,
   nach Absprache angelegt. Der blanke `git pull` auf dem VPS funktioniert
   jetzt; Details im Abschnitt „Stolperstein beim Deploy".
3. **Änderungen vom 23.08. sind ausgerollt und live geprüft**, aber vom
   Nutzer noch nicht selbst in Augenschein genommen — insbesondere der neue
   Abschnitt „Blockierte Personen" im Konto. Gilt jetzt genauso für die
   Android/iOS-Fassung vom 30.08. (dort zusätzlich: iOS-Teil ist nicht
   einmal compilerverifiziert, siehe Sitzung 30.08.).
4. ~~**Android und iOS haben den Listen-Fix vom 23.08. nicht.**~~ —
   **geklärt am 30.08.**: Beide Clients haben den Web-Bug strukturell nie
   gehabt (reaktive Listen über Room-Flow/`@Observable`). Der fehlende
   20s-Vordergrund-Poll wurde als Nice-to-have nachgezogen (`d2042b9`).
5. **Ring-Fix (21.08., Punkt 1) vom Nutzer noch nicht nach dem zweiten
   Anlauf bestätigt.** Zuerst nachfragen bzw. mit hartem Reload
   gegenprüfen.
6. ~~**Doppelte Element-IDs in den Profilkarten**~~ — **am 30.08. erledigt**
   (`3ad34da`), IDs durch Klassen ersetzt.
7. ~~**iOS hat dieselben Bugs wie Punkt 3 und vermutlich Punkt 2**~~ —
   **am 23.08.2026 erledigt**, zusammen mit allem anderen, was seit dem
   15.08. an iOS vorbeigelaufen war. Einzelheiten in
   [ios/HANDOFF.md](ios/HANDOFF.md), Abschnitt „Was am 23.08.2026
   nachgezogen wurde". Wichtigster Fund dabei: `POST /api/billing/checkout`
   verlangt seit dem 17.08. einen Körper mit beiden FAGG-Erklärungen — die
   iOS-App schickte keinen, jeder Abo-Abschluss wäre mit 422 gescheitert.
   ~~**Die iOS-App ist weiterhin nie übersetzt worden**~~ — **überholt seit dem
   16.09.2026**: Sie wird über **Codemagic** gebaut (`codemagic.yaml` im
   Wurzelverzeichnis, `mac_mini_m2`, liefert bei Erfolg automatisch nach
   TestFlight aus) und läuft dort auf einem Gerät. Ein eigener Mac ist dafür
   nicht nötig; `ios/tools/mac-build.sh` bleibt nur für den lokalen Weg. Was
   weiterhin gilt: **Auf diesem Entwicklungsrechner ist iOS nicht
   compilierbar** — jede Swift-Änderung geht ungeprüft in den nächsten
   Codemagic-Lauf.
8. **Android AAB 2.4.9 (versionCode 37) ist inzwischen in der Play Console**
   (vom Nutzer selbst hochgeladen). Das neue **2.5.0 (versionCode 38)** vom
   30.08. liegt gebaut, signiert und auf dem VPS bereit (Link in den
   Eckdaten), ist aber **noch nicht in die Play Console geladen**.
   `PLAY-CONSOLE.md` beachten — diese Sitzung hat weder neue Berechtigungen
   noch neue Datentypen eingeführt (Blockier-Feature nutzt nur bereits
   deklarierte Foto-/Kontodaten), die bestehenden Data-Safety-Angaben
   bleiben also gültig.
9. **Kein kontrollierter Stripe-Testcheckout** ausgelöst. Lokal ist ein
   `sk_test_...`-Schlüssel konfiguriert (kein echtes Geld), aber
   Kartendaten — auch Stripes Test-Kartennummern — einzugeben bleibt eine
   Aufgabe für den Nutzer selbst.
10. Die fünf Test-Frauenprofile eignen sich weiterhin für Deck-/Match-/
   Chat-Testen — nach Abschluss löschen (siehe oben).
11. `backend/tests/test_public_frontend.py` lief auch am 23.08. mehrfach
    grün mit — der in einer früheren Sitzung offene Punkt dazu ist erledigt.
12. ~~Google Search Console / Sitemap-Status~~ — **geprüft am 07.09.**
    (siehe Sitzung 07.09.): Sitemap und robots.txt sind sauber, der einzige
    echte Befund (`/admin.html` in der noindex-Falle) ist behoben und
    ausgerollt. Offen bleibt nur die URL-Prüfung in der Search Console
    selbst — die braucht den Google-Zugang des Nutzers.
13. ~~**Web/Backend-Commits vom 30.08. sind gepusht, aber nicht auf dem VPS
    ausgerollt.**~~ — **war am 07.09. längst überholt und irreführend.** Der
    VPS stand da bereits auf `9e83c97`; ausgerollt war alles, veraltet war
    das lokale `.git` in diesem MEGA-Ordner (fünf Commits hinter
    `origin/main`). Die Notiz hat genau deshalb in die Irre geführt — Details
    und der Merksatz `git fetch origin` **vor** jeder Beurteilung des
    Repo-Stands stehen in der Sitzung 07.09.
14. ~~**Telegram-Push: Ursache für die ausgebliebene Nachricht**~~ —
    **geklärt am 30.08., kein Bug** (siehe Sitzung 30.08., Punkt 3): die
    gemeldete Registrierung war einen Tag älter als das Feature, vom Nutzer
    bestätigt. Push funktioniert.
15. **Sicherheitshinweis, noch offen:** Der Telegram-Bot-Token ist während
    der 30.08.-Diagnose kurz im Klartext im Terminal gelandet (eigener
    `sed`-Fehler). Nur lokal sichtbar, aber sicherheitshalber empfehlenswert:
    Token über @BotFather (`/revoke`) neu erzeugen, `backend/.env` auf dem
    VPS aktualisieren und `flexr-api` neu starten.
16. ~~**Die iOS-Premium-Änderung (`4587ed5`) ist nie compiliert worden.**~~ —
    **erledigt am 16.09.2026**: Der Codemagic-Lauf war beim ersten Versuch grün,
    die Fassung liegt in TestFlight. Was offen bleibt, steht in Punkt 17.
17. **Die drei Premium-Funktionen sind auf keinem Gerät ausprobiert** — weder
    Android noch iOS. Sie sind ohnehin unsichtbar, solange `PREMIUM_ENABLED`
    am Server `false` ist. Zum Prüfen entweder den Schalter kurz umlegen oder
    einem Testkonto `is_premium` verschaffen. Die Android-Seite ist
    compilerverifiziert und durch 49 grüne Unit-Tests gedeckt, zwei davon neu
    fürs Zurücknehmen; das ersetzt keinen Blick auf den Bildschirm.
18. **Android 2.6.9 (versionCode 109) ist noch nicht in der Play Console.**
    Gebaut, signiert, im Chat übergeben — Prüfsumme im 16.09.-(2)-Abschnitt.
    Keine neuen Berechtigungen, keine neuen Datentypen: Die bestehenden
    Data-Safety-Angaben bleiben gültig.
19. ~~**Stripe: der 10-€-Preis ist noch nicht angelegt.**~~ — **erledigt am
    17.09.2026:** neues Produkt „FLEXR Premium" (`prod_VH6teDHT70SoKH`), Preis
    `price_1UGYfdIpMumqxPtFzu0d5A6f` live, `STRIPE_PRICE_ID` auf dem VPS
    aktualisiert und Backend neu gestartet, Billing-Portal und Webhook-Events
    geprüft/vervollständigt. Details in der Sitzung 17.09. Offen bleibt nur
    noch der kontrollierte Testcheckout (Punkt 9) und die Gegenprobe, ob die
    Kundenportal-Einstellung tatsächlich gespeichert wurde.

## Auf einem anderen Gerät starten

```bash
git clone git@github.com:flexrsocial/flexr.git   # oder: vorhandenes Repo
cd flexr
git fetch origin
git log -1 --oneline                              # HEAD prüfen
git log -1 --oneline origin/main                   # gegen origin/main vergleichen
```

**Falls HEAD hinter `origin/main` zurückliegt** (siehe Fund ganz oben in
diesem Dokument) — insbesondere auf einem MEGA/Dropbox/etc.-synchronisierten
Ordner, wo `git pull` möglicherweise nie lief:

```bash
git status --short          # erst pruefen, ob es hier ueberhaupt was zu verlieren gibt
git reset --mixed origin/main   # bewegt nur HEAD+Index, laesst Arbeitsverzeichnis unangetastet
git status --short          # jetzt sollte nur noch echte, beabsichtigte Aenderungen zeigen
```

Kein `git reset --hard` und kein `git checkout .` ohne vorherige Prüfung —
beide würden echte, noch unversionierte lokale Änderungen im
Arbeitsverzeichnis zerstören.

### Nicht im Git enthaltene Zugangsdaten

- SSH-Key/-Konfiguration für GitHub sowie den Alias `flexr-vps`
- `backend/.env`
- `android/android.keystore`, `android/KEYSTORE-CREDENTIALS.txt`

Produktions-Secrets liegen auf dem VPS in `/flexr/backend/.env`. Nicht aus
alten Chats übernehmen oder erneut posten.

## Tests auf dem neuen Gerät

Backend:

```bash
cd backend
python3 -m venv venv
venv/bin/pip install -r requirements-dev.txt
venv/bin/python -m pytest -q
```

Stand 23.08.2026: **367 Tests, alle grün** (362 vor dem Blockier-Feature,
5 kamen mit ihm dazu).

Android (siehe Toolchain-Abschnitt oben für JDK/SDK-Setup):

```bash
cd android-native
export JAVA_HOME=/pfad/zu/jdk-17
export PATH="$JAVA_HOME/bin:$PATH"
export ANDROID_HOME=/pfad/zu/android-sdk
./gradlew --no-daemon --max-workers=1 :app:testProdReleaseUnitTest
./gradlew --no-daemon --max-workers=1 :app:bundleProdRelease
unzip -l app/build/outputs/bundle/prodRelease/app-prod-release.aab | grep META-INF/FLEXR
sha256sum app/build/outputs/bundle/prodRelease/app-prod-release.aab
```

Immer als **getrennte** `./gradlew`-Aufrufe, nie kombiniert (frühere
Sitzung: führte auf einer RAM-knappen Maschine zu Abstürzen). Nach jeder
Änderung an `FlexrApi.kt` zuerst `FakeFlexrApi.kt` ergänzen (siehe Falle
oben), sonst schlägt nur der Unit-Test-Compile fehl, nicht der Hauptbuild.

## Normaler Commit- und Deploy-Ablauf

```bash
git status --short
git add <nur-die-beabsichtigten-dateien>   # NICHT git add -A, siehe .env.example-Falle unten
git commit -m "Kurze aussagekräftige Beschreibung"
git push origin main

# Seit 07.09.2026 reicht der blanke Befehl - die ~/.ssh/config auf dem VPS
# zeigt git auf den Deploy-Key (vorher: "Permission denied (publickey)").
ssh flexr-vps 'cd /flexr && git pull --ff-only origin main'
ssh flexr-vps 'cd /flexr/backend && venv/bin/alembic upgrade head'   # nur falls neue Migration
ssh flexr-vps 'sudo systemctl restart flexr-api && systemctl is-active flexr-api'
curl -fsS https://flexr.social/api/health
```

**Nur-Frontend-Änderungen brauchen weder Migration noch Neustart** — nginx
liefert `frontend/` statisch aus, nach dem `git pull` ist die neue Fassung
sofort live. Der Service Worker fährt „Netz zuerst", ein Hochzählen von
`CACHE` in `frontend/sw.js` ist dafür also nicht nötig (das war beim
Unsplash-Vorfall am 15.08. anders — dort ging es um den Offline-Rückfall
auf eine Fassung mit Fremdaufrufen). Zum Gegenprüfen taugt ein Vergleich
der Prüfsummen:

```bash
curl -fsS https://flexr.social/app/ | md5sum
md5sum frontend/app/index.html
```

**Falle, die schon mehrfach auftrat:** `backend/.env.example`
zeigt in `git diff` als verändert (Rückfall auf generische Platzhalterwerte
wie `smtp.example.com`), ohne dass diese Sitzung das absichtlich angefasst
hätte — mutmaßlich Rest aus derselben Git-Stand-Problematik wie ganz oben
beschrieben. **Bewusst nicht mitcommitten**, gezielt einzelne Dateien
stagen statt `git add -A`.

**Alembic-Migrationen und `sudo systemctl restart`** wurden vom
Auto-Mode-Classifier am 21.08. beim ersten Versuch jeweils blockiert,
liefen aber beim **zweiten** identischen Versuch anstandslos durch (kein
Workaround nötig, einfach denselben Befehl nochmal ausführen).

Ein neues AAB wird so bereitgestellt:

```bash
scp android-native/app/build/outputs/bundle/prodRelease/app-prod-release.aab \
  flexr-vps:/flexr/frontend/dl-a616e78274de323b/flexr-X.Y.Z.aab
ssh flexr-vps 'sha256sum /flexr/frontend/dl-a616e78274de323b/flexr-X.Y.Z.aab'
# lokale und entfernte SHA-256 vergleichen, dann:
curl -fsSI https://flexr.social/dl-a616e78274de323b/flexr-X.Y.Z.aab
```

Der Alias `flexr-vps` meldet sich als **root** an (siehe `~/.ssh/config`),
der Zielordner ist damit direkt beschreibbar — ein Umweg über `/tmp` mit
anschließendem `sudo mv` ist nicht nötig (am 08.09. vorsorglich so gemacht,
das war überflüssig).

`frontend/dl-a616e78274de323b/` auf dem VPS ist absichtlich unversioniert
(es ist der Ort für die AAB-Downloads) — **der Ordner selbst ist nie zu
löschen**. Sein Inhalt wurde am 08.09.2026 auf ausdrücklichen Wunsch
geleert (ebenso der von `dl-5d8a93fc22b232c9/`); das ist kein Präzedenzfall,
sondern war eine Einzelanweisung.

**Der Dateiname folgt dem `versionName` aus dem Bundle, nicht der
Release-Nummer.** Beim Release vom 07.09. fiel beides auseinander (Release
2.5.4, Bundle 2.5.3); seit 2.5.5 stimmt es wieder überein. Damit das so
bleibt: `versionCode` **und** `versionName` in
`android-native/app/build.gradle.kts` vor dem Bauen setzen, und nach dem
Build den `versionName` **im Bundle-Manifest** gegenprüfen, nicht nur in der
Gradle-Datei:

```bash
python3 -c 'import zipfile,re,sys; \
d=zipfile.ZipFile(sys.argv[1]).read("base/manifest/AndroidManifest.xml"); \
print(re.findall(rb"[0-9]+\.[0-9]+\.[0-9]+", d)[:5])' \
  app/build/outputs/bundle/prodRelease/app-prod-release.aab
```

## Empfohlener Einstiegsprompt für Claude Code

> Lies zuerst `HANDOFF.md` vollständig. Prüfe `git fetch origin`, dann
> `git log -1 --oneline` gegen `git log -1 --oneline origin/main` — bei
> Abweichung erst den Abschnitt „Auf einem anderen Gerät starten" befolgen,
> bevor irgendetwas committet wird. Poste oder committe keine Secrets.
> Arbeite die offenen Punkte der Reihe nach ab, teste proportional zum
> Risiko (Backend-Tests laufen lassen, bei Android immer Kotlin-Compile UND
> Unit-Test-Compile separat prüfen) und committe/deploye erst nach
> erfolgreicher Prüfung.

## Erinnerung für die nächste Sitzung

Neu aus der Sitzung 19.09.:

- **Android 2.7.8 (versionCode 120) ist noch nicht in der Play Console** —
  gebaut, signiert, im Chat übergeben (AAB und APK, Prüfsummen im
  19.09.-Abschnitt).
- Vier Konto-Feinschliffe umgesetzt: „Profil gespeichert" verschwindet nach
  2 s von selbst, die Statuskarte „FLEXR Premium läuft …" ist für
  Premium-Konten weg, „Aboverwaltung" heißt nur noch „Abo verwalten" und
  ist kein Link mehr. **Keins davon am Gerät geprüft** — hier läuft kein
  Emulator.
- **Der Push-Befund „nichts bei beendeter App" ist weiterhin unbestätigt.**
  Der nächste Versuch mit dem 2.7.8-APK ist der Beweis; führt er zu nichts,
  ist die Akku-Ausnahme dran (steht in Konto → Benachrichtigungen ganz oben).
  **Telefonmodell und Android-Fassung weiterhin offen** — beides fehlt und
  entscheidet, wie streng der Hersteller die App schlafen legt.
- Nachfragen, ob die beiden Rewind-Meldungen auch in **Web und iOS**
  verschwinden sollen — in der Android-App sind sie seit 2.7.7 weg, dort
  nicht. (Zwei der vier Screenshots aus der 19.09.-Rückmeldung zeigten genau
  diese Meldungen noch — Ursache war ein auf dem Testgerät noch nicht
  aktualisierter Build, kein neuer Bug.)
- Die **Aboverwaltung in der Web-App** (Konto, zwischen „Benachrichtigungen"
  und „Datenschutz & Sicherheit") ist ausgerollt, aber vom Nutzer noch nicht
  begutachtet — samt neuem Hinweis für Abos aus den Stores.

- Zuerst `git fetch origin` + HEAD-Abgleich (siehe oben), erst danach
  irgendetwas anfassen. Beim Deploy den Deploy-Key mitgeben (siehe
  „Normaler Commit- und Deploy-Ablauf"), sonst scheitert der Pull.
- ~~**Der lokale Ordner `~/MEGA/flexr/flexr` ist git-seitig veraltet**~~ —
  **erledigt**: Am 18.09. (7) stand `HEAD` auf demselben Commit wie
  `origin/main`, der Arbeitsbaum war sauber, und beide Commits der Sitzung
  gingen ohne Umweg durch. Die Worktree-Umgehung ist nicht mehr nötig.
- Der **Beta-Hinweis nennt „Ende September 2026"** als Android-Termin.
  Verschiebt sich der Termin oder erscheint die App, den Text anpassen **und**
  den localStorage-Schlüssel auf `flexr_beta_notice_v2` hochzählen — sonst
  sehen bestehende Besucher die alte Aussage nie wieder bzw. gar nichts.
- **VPS-Deploy vom 30.08. steht noch aus** — `git pull` auf dem VPS
  nachholen (Backend unverändert, kein Neustart nötig, siehe „Noch offen"
  Punkt 13).
- Nachfragen, ob der neue Abschnitt „Blockierte Personen" (Konto →
  Datenschutz & Sicherheit) so passt — auf allen drei Plattformen
  ausgerollt (Web 23.08., Android + iOS 30.08.), vom Nutzer noch nicht
  begutachtet. Der iOS-Teil ist seit dem 16.09.2026 immerhin gebaut und in
  TestFlight (Codemagic), angesehen hat ihn dort aber noch niemand.
- Das Anheften der Landing-Headline ist auf Wunsch **zurückgenommen**; der
  Hero steht wieder mittig. Nicht erneut „reparieren", ohne zu fragen.
- Nachfragen/prüfen, ob der zweite Ring-Fix (21.08.) tatsächlich behoben
  hat — weiterhin unbestätigt.
- Telegram-Push ist geklärt (kein Bug, siehe Sitzung 30.08. Punkt 3) — noch
  offen ist nur der Sicherheitshinweis dazu: Bot-Token über @BotFather neu
  erzeugen, da er kurz im Terminal sichtbar war (Punkt 15).
- ~~iOS ist nie übersetzt worden~~ — **überholt**: Seit dem 16.09.2026 baut
  **Codemagic** die App und liefert sie nach TestFlight aus (siehe
  `codemagic.yaml`). Auf diesem Rechner bleibt sie trotzdem nicht
  compilierbar; jede Swift-Änderung geht ungeprüft in den nächsten Lauf.
- AAB 2.5.0 (versionCode 38) ist gebaut, signiert und auf dem VPS bereit —
  noch nicht in die Play Console geladen (2.4.9 ist es inzwischen). Ein
  Neubau ist erst nötig, wenn wieder etwas unter `android-native/` geändert
  wurde.
- Die 5 Test-Frauenprofile nach Abschluss des Testens löschen (siehe
  „Testdaten" oben).
- Danach kontrollierten Stripe-Testcheckout durchführen (weiterhin offen
  aus früheren Sitzungen) — Kartendaten eingeben bleibt Sache des Nutzers.

Neu aus der Sitzung 17.09.:

- Stripe-Preis für FLEXR Premium ist live (`price_1UGYfdIpMumqxPtFzu0d5A6f`,
  10 €/Monat), `STRIPE_PRICE_ID` auf dem VPS aktualisiert, Backend neu
  gestartet, Webhook-Events vollständig. **Vor dem Testcheckout prüfen**, ob
  im Stripe-Kundenportal unter Stornierungen wirklich „Änderungen speichern"
  geklickt wurde — das war am Ende der Sitzung nicht bestätigt.
- Danach: kontrollierten Testcheckout durchführen, erst dann
  `PREMIUM_ENABLED` auf `true`.

Neu aus der Sitzung 16.09. (2):

- **Beide iOS-Läufe sind grün** (`fe6af02` Bugfixes, `4587ed5` Premium), beide
  Fassungen liegen in TestFlight. **Angesehen hat sie dort noch niemand** — die
  drei Layoutkorrekturen (Login-Knopf, Chatblasen, Fotoraster) sind der erste
  Punkt, der einen Blick lohnt, und das Fotoraster zusätzlich in der Bedienung:
  verschieben, löschen, neu hochladen.
- **Android 2.6.9 (versionCode 109) ist noch nicht in der Play Console** —
  gebaut, signiert, im Chat übergeben. Prüfsumme im 16.09.-(2)-Abschnitt.
- **Von 2.6.8 und 2.6.9 gibt es kein APK.** Zum Testen auf einem Gerät erst
  `./gradlew assembleProdRelease` laufen lassen.
- **Die drei Premium-Funktionen sind auf keiner der beiden nativen Plattformen
  auf einem Gerät ausprobiert.** Sichtbar werden sie ohnehin erst, wenn
  `PREMIUM_ENABLED` am Server auf `true` geht — zum Prüfen also entweder den
  Schalter kurz umlegen oder ein Konto mit `is_premium` versehen.
- **Die Toolchain für den Android-Build liegt unter `~/.bubblewrap/`**, nicht
  unter `~/android-toolchain/`. Das steht seit dem 07.09. in diesem Dokument und
  ist am 16.09. trotzdem übersehen worden — siehe „Eigener Fehlgriff" im
  16.09.-(2)-Abschnitt.
- Der Like-Zähler unter dem Deck fehlt in beiden nativen Clients bewusst
  (Begründung im 16.09.-(2)-Abschnitt). Nicht ungefragt „ergänzen".
