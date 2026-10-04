# Play Console — was beim nächsten Upload anzupassen ist

Stand: Version `2.7.22`, versionCode **134** (04.10.2026). Davor zuletzt
gepflegt zu `2.4.1`/versionCode 29 (20.08.2026) — Abschnitt 0 sammelt, was
seither für die Angaben in der Console dazukam.

**Was in der Console tatsächlich schon eingetragen ist, ist von hier aus nicht
einsehbar.** Im Play Store lag zuletzt die alte TWA (versionCode 5); einzelne
Bundles der nativen App liegen in der Bibliothek des Kontos (die Console hat am
10.09.2026 die versionCodes 43 und 50 als „bereits verwendet“ abgelehnt). Vor
der Veröffentlichung jede Angabe unten gegen die Console prüfen.

Die Punkte hier sind keine Empfehlung, sondern die Angaben, die zum tatsächlichen
Verhalten der App passen. Weicht die Deklaration davon ab, ist das ein
Richtlinienverstoß — unabhängig davon, wie datensparsam die App gebaut ist.

---

## 0. Seit 2.4.1 deklarationsrelevant dazugekommen

| Seit | Änderung | Was in der Console betroffen ist |
|---|---|---|
| 2.7.x (17./18.09.2026) | **Push über Firebase Cloud Messaging.** Der Server schickt, Google stellt zu; Titel und Text der Mitteilung laufen über Google. Das Gerät meldet dafür ein FCM-Token an den Server. | Datensicherheit: **Geräte- oder andere IDs** (FCM-Token) erhoben, Zweck *App-Funktionalität*. Google ist hier Dienstleister, das ist kein „Teilen“ im Sinne der Console. |
| 2.7.x | **Käufe über Google Play** (Play Billing 8, Abo „FLEXR Premium“). Der Server prüft den Kauf bei Google und bestätigt ihn; der Kauf trägt seit 2.7.21 die Konto-Kennung (`setObfuscatedAccountId`). | **Monetarisierung:** In-App-Käufe = *Ja*. Das Abo-Produkt muss in der Console angelegt sein, mit derselben Produkt-ID wie im Backend (`store_product_id` in `/api/billing/status`). Datensicherheit: **Finanzdaten → Kaufverlauf** (Kauf-Token, Abostatus) erhoben, Zweck *App-Funktionalität*. |
| schon länger | **Geräte-ID** (`X-Device-Id`, zufällig erzeugt, Mehrfachkonto-Erkennung; serverseitig gespeichert, siehe Datenschutzerklärung „Geräte-ID und User-Agent“) | Datensicherheit: **Geräte- oder andere IDs**, Zweck *Betrugsprävention, Sicherheit und Compliance*. In der Liste „bereits vorhanden“ (Abschnitt 1) fehlte sie. |
| 2.7.x | Profilfotos über den **System-Bildauswahldialog** (Photo Picker), der Ausweis wahlweise als Datei (`GetContent`) | Keine Berechtigung nötig, keine neue Angabe. Die frühere Aussage „kein Galerie-Zugriff“ (Abschnitt 4) ist damit überholt. |
| 2.7.17 | Online-Rücktrittsfunktion nativ (POST `/api/withdrawal`) | nein |
| 2.7.22 | Datenschutz-Kurzfassung in der App an die Fassung 2026-10-02 angeglichen | nein |

### App-Zugriff für die Prüfung (Pflicht)

FLEXR verlangt eine Anmeldung **und** vor der Nutzung die Alters- und
Identitätsprüfung mit Ausweis. Googles Prüfer kommen da nicht durch. Unter
*App-Inhalte → App-Zugriff* deshalb ein **bereits freigeschaltetes
Testkonto** hinterlegen (E-Mail, Passwort, Hinweis „Konto ist bereits
verifiziert“). Am einfachsten ein eigenes Konto unter `@flexrtest.at` mit dem
bestehenden Seed-Werkzeug (`~/MEGA/flexr/seed/`, außerhalb des Repos) — die
Zugangsdaten gehören nur in die Console, nicht ins Repo.

### Kontolöschung (Pflichtangabe in der Datensicherheit)

Die Console verlangt eine **Web-Adresse**, unter der man die Löschung auch ohne
die App beantragen kann. Die Web-App bietet dieselbe Löschung (flexr.social/app →
Konto → Konto löschen); als Adresse eignet sich
`https://flexr.social/faq.html` mit dem Eintrag „Wie lösche ich mein Konto?“.
Dieser Eintrag nennt bisher nur den „Konto-Bereich“, nicht ausdrücklich den Weg
über den Browser — wer es Google leichter machen will, ergänzt dort einen Satz
(Text in `frontend/faq.html` und der englischen Fassung).

### Weitere Angaben, die zur App passen müssen

* **Zielgruppe:** ausschließlich ab 18.
* **Werbung:** keine; die App enthält kein Werbe- oder Analyse-SDK.
* **Nutzergenerierte Inhalte:** Melden und Blockieren sind in der App vorhanden
  (Profil, Chat, Konto → Datenschutz & Sicherheit → Blockierte Personen).
* **Sexuelle Orientierung:** Die Datenschutzerklärung behandelt sie als besondere
  Kategorie (eigene Einwilligung bei der Registrierung). In der Datensicherheit
  unter *Personenbezogene Daten → Sexuelle Orientierung* angeben.

---

## 1. Datensicherheit (Data safety)

### Seit 2.2.0 zu deklarieren

| Feld | Angabe |
|---|---|
| Datentyp | **Fotos und Videos → Fotos** |
| Erhoben? | **Ja** (die Aufnahmen gehen an das eigene Backend) |
| Geteilt? | **Nein** (kein Empfänger außer dem eigenen Auftragsverarbeiter) |
| Verarbeitung | **Nicht** als „nur flüchtig“ einstufen — siehe unten |
| Pflichtangabe? | **Ja**, ohne die Prüfung wird kein Konto freigeschaltet |
| Zwecke | **Kontoverwaltung**, **Betrugsprävention, Sicherheit und Compliance** |

**Warum nicht „flüchtig verarbeitet“:** Diese Einstufung gilt nur, wenn Daten
ausschließlich im Arbeitsspeicher und nicht länger als für die Anfrage nötig
gehalten werden. Die Aufnahmen liegen bis zur manuellen Entscheidung im
Objekt-Storage (Cloudflare R2, privater Bereich). Das ist eine Speicherung.

**Löschung:** Die App erfüllt die Anforderung „Nutzer können die Löschung ihrer
Daten beantragen“ über die Kontolöschung im Konto-Bereich (Web-Adresse siehe
Abschnitt 0). Zusätzlich werden Selfies und Ausweisaufnahmen nach der
Entscheidung automatisch gelöscht, bei Kontolöschung sofort.

### Bereits vorhanden

Profilfotos, E-Mail, Name, Geburtsdatum, Nachrichten, Abo-Status. Dazu jetzt
(Abschnitt 0): Geräte- oder andere IDs (Geräte-ID, FCM-Token), Kaufverlauf,
sexuelle Orientierung. Der Abschnitt **Standort** ist seit 2.0.7 ersatzlos
entfallen — die Umkreissuche geht von der Adresse des eingetragenen Gyms aus.
Die Postleitzahl aus der Registrierung ist eine Nutzerangabe (Adressbestandteil),
keine Geräteposition.

---

## 2. Berechtigungen

Das eigene Manifest verlangt vier:

| Berechtigung | Wofür |
|---|---|
| `INTERNET`, `ACCESS_NETWORK_STATE` | normal, keine Nutzerabfrage |
| `CAMERA` | Verifizierungs-Selfie (Frontkamera), Ausweis (Rückkamera) |
| `POST_NOTIFICATIONS` | Mitteilungen bei neuen Nachrichten und Matches (Push über FCM) |

`CAMERA` lief in der TWA über Chrome und wurde nie von der App selbst
angefordert — gegenüber dem Play-Store-Stand ist das also **neu**. In der
Store-Beschreibung sollte stehen, wofür die Kamera verlangt wird.

`POST_NOTIFICATIONS` ist seit Android 13 eine Laufzeitberechtigung und
gegenüber der TWA ebenfalls neu. **Überholt** ist die frühere Aussage, die
Mitteilungen entstünden nur lokal ohne Push-Dienst: Seit 2.7.x stellt Firebase
Cloud Messaging sie zu (Abschnitt 0).

Über Bibliotheken kommen im fertigen Manifest dazu (geprüft an 2.7.22 mit
`aapt2 dump permissions`): `com.android.vending.BILLING` (Play Billing),
`com.google.android.c2dm.permission.RECEIVE` (FCM), `WAKE_LOCK`,
`RECEIVE_BOOT_COMPLETED` und `FOREGROUND_SERVICE` (WorkManager/Firebase). Keine
davon verlangt eine eigene Angabe in der Console — es gibt insbesondere keine
`FOREGROUND_SERVICE_<TYP>`-Berechtigung, für die das Formular zu
Vordergrunddiensten nötig wäre.

Nicht vorhanden: Standort (seit 2.0.7 entfallen), Speicher-/Medienzugriff
(Fotos über den System-Bildauswahldialog, ohne Berechtigung), Werbe-ID
(`com.google.android.gms.permission.AD_ID` fehlt im fertigen Manifest — in der
Console „Werbe-ID: Nein“).

---

## 3. Inhaltsfreigabe (Content rating) und Store-Eintrag

* Die Altersfreigabe bleibt unverändert; FLEXR war schon vorher ab 18.
* Der Store-Eintrag sollte den Ablauf der Prüfung erwähnen, damit Nutzer nicht
  von der Ausweisanfrage überrascht werden. Vorschlag für einen Satz:
  *„Vor der Freischaltung prüfen wir einmalig Alter und Identität anhand eines
  Verifizierungs-Selfies und eines amtlichen Lichtbildausweises — manuell durch
  einen Menschen, ohne automatische Gesichtserkennung. Die Aufnahmen werden nach
  der Prüfung gelöscht.“*
* Datenschutzerklärung: https://flexr.social/datenschutz.html (Fassung
  2026-10-02). Die App enthält eine Kurzfassung, die auf diese Seite verweist.

---

## 4. Was im Code dafür getan ist

* **Kein Cloud-Backup, kein Gerätetransfer** — `allowBackup="false"` und
  `res/xml/data_extraction_rules.xml` schließen alle Domains aus.
* **Screenshots sind zugelassen.** Bis 2.2.4 lief die Verifizierung mit
  `FLAG_SECURE`; das ist auf Wunsch des Betreibers entfernt, weil sich die
  Bildschirme sonst nicht dokumentieren lassen. Preis dafür: Android legt beim
  Wechsel in den Hintergrund wieder ein Abbild im Recents-Cache ab, bei der
  Ausweisaufnahme also ein Bild des Ausweises auf der Geräteplatte. Das liegt
  außerhalb unserer Löschzusage und betrifft nur das Gerät des Nutzers selbst.
* **Bildauswahl ohne Berechtigung:** Selfies entstehen live über CameraX.
  Profilfotos kommen über den System-Bildauswahldialog, der Ausweis wahlweise
  über die Kamera oder als Datei — beides ohne Speicherberechtigung.
* **Direkter Upload in den privaten Bereich** des Objekt-Storage über Presigned
  PUT. Die Prüfaufnahmen bekommen nie eine öffentliche Adresse; Prüfer sehen sie
  nur über kurzlebige signierte Links.
* **Kein Zwischenspeichern auf dem Gerät:** Die Prüfaufnahmen liegen als
  `ByteArray` im ViewModel und werden nach dem Einreichen verworfen.
* **Play-Anforderungen** (geprüft 04.10.2026): Ziel-SDK 36, Play Billing 8,
  alle nativen Bibliotheken im Bundle mit 16-KB-Seitenausrichtung (CameraX,
  Datastore, Compose — die App kompiliert selbst keinen nativen Code),
  Edge-to-Edge und vorausschauende Zurück-Geste aktiv.

---

## 5. Versionsverlauf seit 2.2.0 (Deklarationsrelevanz)

| Version | Änderung | Deklaration betroffen? |
|---|---|---|
| 2.2.4 | `FLAG_SECURE` aus der Verifizierung entfernt | nein, siehe Abschnitt 4 |
| 2.2.8 | Gesperrte Knöpfe wechseln die Farbe statt zu verblassen; Freischaltung wird auf dem Wartebildschirm erkannt | nein |
| 2.2.9 | Foto-Upload direkt im Verifizierungs-Schirm; Namen, Bio und Nachrichten werden serverseitig getrimmt | nein |
| 2.3.0 | E-Mail-Bestätigung per Aktivierungslink, als Android App Link | **nur Deep Links**, siehe unten |
| 2.4.0 | Rechtstexte an den tatsächlichen Vertrags-, Zahlungs- und Datenschutzablauf angeglichen | Textangaben prüfen, keine neuen Datentypen |
| 2.4.1 | Konto-, Chat- und Deck-Oberfläche vereinfacht; Telefon-/SMS-Prüfung aus den nativen Rechtstexten entfernt, Brevo ergänzt | Brevo muss als E-Mail-Dienstleister angegeben sein |
| 2.5.0 (30.08.2026) | „Blockierte Personen“ verwalten/aufheben; stiller 20s-Vordergrund-Poll für Matches/Chats | nein |
| 2.7.x (09/2026) | Push über FCM, Käufe über Google Play, Photo Picker, Online-Rücktritt | **ja**, siehe Abschnitt 0 |
| 2.7.22 (04.10.2026) | Datenschutz-Kurzfassung (Sicherungskopien, Google Play als Empfänger) | nein |

Die Einzelheiten zu jeder Fassung stehen als Kommentar am `versionCode` in
`app/build.gradle.kts`.

**Deep Links prüfen.** Das Manifest führt seit 2.3.0 einen Intent-Filter mit
`autoVerify="true"` auf `https://flexr.social/mail-bestaetigen`. Android prüft
dafür beim Installieren `https://flexr.social/.well-known/assetlinks.json`. Die
Datei liegt im Repo unter `frontend/.well-known/` und führt beide nötigen
Fingerprints — den Play-App-Signing-Schlüssel (`3B:2B:6E…01:4A`) und den
Upload-Key (`BC:64:AD…79:80`); live geprüft am 04.10.2026. Nach dem Upload lohnt
ein Blick in der Console unter *Grow → Deep links*, ob die Verifizierung
durchgelaufen ist. Schlägt sie fehl, öffnet der Link den Browser und die
Bestätigung läuft dort weiter — der Weg geht also nicht verloren.

Der zweite Intent-Filter (`flexr://checkout`, `autoVerify="false"`) war der
Rückweg aus einem Stripe-Checkout im Browser. Die App bietet seit 2.7.0 keinen
Stripe-Abschluss mehr an (Server: `checkout_available=false` für App-Clients);
der Filter ist ohne Wirkung und für die Console ohne Belang.

---

## 6. Vor dem Upload

```bash
cd android-native
./gradlew :app:testProdDebugUnitTest :app:lintProdRelease   # muss grün sein
./gradlew :app:bundleProdRelease :app:assembleProdRelease

# Signatur gegenprüfen — ohne android/KEYSTORE-CREDENTIALS.txt entfällt sie
# stillschweigend und das Bundle ist nicht hochladbar:
unzip -l app/build/outputs/bundle/prodRelease/app-prod-release.aab | grep META-INF
# erwartet: META-INF/FLEXR.RSA und META-INF/FLEXR.SF
```

In die Console gehört das **.aab**. Die universelle **.apk** ist nur zum
direkten Aufspielen auf ein Testgerät gedacht — ein .aab lässt sich nicht
direkt installieren (siehe Kommentar zu versionCode 115).

**Auf echter Hardware gelaufen** ist die App seit September 2026 auf dem Gerät
des Betreibers (u. a. der Absturzbericht vom 18.09.2026, siehe versionCode 117). Der interne
Test-Track ist trotzdem der sichere Weg vor der Freigabe: Er installiert genau
das, was Nutzer später bekommen, inklusive Play Billing und App-Link-Prüfung.
