# Play Console — was beim nächsten Upload anzupassen ist

Stand: Version `2.4.1`, versionCode **29** (Stand 20.08.2026).

**Der Sprung ist größer als eine Versionsnummer.** Im Play Store liegt weiterhin
die alte TWA mit versionCode **5** — die native App wurde nie hochgeladen. Der
nächste Upload springt also von 5 auf 29 und muss *alle* Änderungen an den
Deklarationen mitbringen, die seitdem aufgelaufen sind. Dieses Dokument sammelt
sie; nichts davon ist bereits in der Console eingetragen.

Der Kern ist die verpflichtende Alters- und Identitätsprüfung aus 2.2.0:
Verifizierungs-Selfies **und** eine Aufnahme eines amtlichen Lichtbildausweises.
Was seit 2.2.0 dazukam, steht in Abschnitt 6.

Die Punkte hier sind keine Empfehlung, sondern die Angaben, die zum tatsächlichen
Verhalten der App passen. Weicht die Deklaration davon ab, ist das ein
Richtlinienverstoß — unabhängig davon, wie datensparsam die App gebaut ist.

---

## 1. Datensicherheit (Data safety)

### Neu zu deklarieren

| Feld | Angabe |
|---|---|
| Datentyp | **Fotos und Videos → Fotos** |
| Erhoben? | **Ja** (die Aufnahmen gehen an das eigene Backend) |
| Geteilt? | **Nein** (kein Empfänger außer dem eigenen Auftragsverarbeiter) |
| Verarbeitung | **Nicht** als „nur flüchtig" einstufen — siehe unten |
| Pflichtangabe? | **Ja**, ohne die Prüfung wird kein Konto freigeschaltet |
| Zwecke | **Kontoverwaltung**, **Betrugsprävention, Sicherheit und Compliance** |

**Warum nicht „flüchtig verarbeitet":** Diese Einstufung gilt nur, wenn Daten
ausschließlich im Arbeitsspeicher und nicht länger als für die Anfrage nötig
gehalten werden. Die Aufnahmen liegen bis zur manuellen Entscheidung im
Objekt-Storage (Cloudflare R2, privater Bereich). Das ist eine Speicherung.

**Löschung:** Die App erfüllt die Anforderung „Nutzer können die Löschung ihrer
Daten beantragen" bereits über die Kontolöschung im Konto-Bereich. Zusätzlich
werden Selfies und Ausweisaufnahmen nach der Entscheidung automatisch gelöscht,
bei Kontolöschung sofort.

### Bereits vorhanden, unverändert

Profilfotos, E-Mail, Name, Geburtsdatum, Nachrichten, Abo-Status. Der Abschnitt
**Standort** ist seit 2.0.7 ersatzlos entfallen — die Umkreissuche geht von der
Adresse des eingetragenen Gyms aus.

---

## 2. Berechtigungen

Das Manifest verlangt genau vier:

| Berechtigung | Wofür |
|---|---|
| `INTERNET`, `ACCESS_NETWORK_STATE` | normal, keine Nutzerabfrage |
| `CAMERA` | Profilfotos, Verifizierungs-Selfie (Frontkamera), Ausweis (Rückkamera) |
| `POST_NOTIFICATIONS` | Hinweis auf neue Nachrichten (`NewMessageWorker`) |

`CAMERA` lief in der TWA über Chrome und wurde nie von der App selbst
angefordert — gegenüber dem Play-Store-Stand ist das also **neu**. Ab 2.2.0
kommt die Rückkamera für den Ausweis dazu; dieselbe Berechtigung, keine
zusätzliche Deklaration. In der Store-Beschreibung sollte stehen, wofür die
Kamera verlangt wird.

`POST_NOTIFICATIONS` ist seit Android 13 eine Laufzeitberechtigung und
gegenüber der TWA ebenfalls neu. Die Benachrichtigungen entstehen lokal auf dem
Gerät aus abgerufenen Nachrichten — es gibt keinen Push-Dienst und damit auch
keinen Empfänger, der zu deklarieren wäre.

Nicht mehr vorhanden: `ACCESS_COARSE_LOCATION` und `ACCESS_FINE_LOCATION`, seit
2.0.7 ersatzlos entfallen.

---

## 3. Inhaltsfreigabe (Content rating) und Store-Eintrag

* Die Altersfreigabe bleibt unverändert; FLEXR war schon vorher ab 18.
* Der Store-Eintrag sollte den neuen Ablauf erwähnen, damit Nutzer nicht von der
  Ausweisanfrage überrascht werden. Vorschlag für einen Satz:
  *„Vor der Freischaltung prüfen wir einmalig Alter und Identität anhand eines
  Verifizierungs-Selfies und eines amtlichen Lichtbildausweises — manuell durch
  einen Menschen, ohne automatische Gesichtserkennung. Die Aufnahmen werden nach
  der Prüfung gelöscht."*
* Die Datenschutzerklärung unter https://flexr.social/datenschutz.html beschreibt
  den Ablauf in Abschnitt 3a und ist bereits aktualisiert.

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
* **Kein Galerie-Zugriff:** Die Aufnahmen entstehen live über CameraX, es gibt
  keinen Bildauswahl-Dialog und keine Speicherberechtigung.
* **Direkter Upload in den privaten Bereich** des Objekt-Storage über Presigned
  PUT. Die Aufnahmen bekommen nie eine öffentliche Adresse; Prüfer sehen sie nur
  über kurzlebige signierte Links.
* **Kein Zwischenspeichern auf dem Gerät:** Die Bilder liegen als `ByteArray` im
  ViewModel und werden nach dem Einreichen verworfen. Keine Datei, kein Cache.

---

## 5. Was seit 2.2.0 dazukam

Kurzfassung für die Frage, die beim Upload zählt: **Ändert sich dadurch eine
Angabe in der Console?**

| Version | Änderung | Deklaration betroffen? |
|---|---|---|
| 2.2.4 | `FLAG_SECURE` aus der Verifizierung entfernt | nein, siehe Abschnitt 4 |
| 2.2.8 | Gesperrte Knöpfe wechseln die Farbe statt zu verblassen; Freischaltung wird auf dem Wartebildschirm erkannt | nein |
| 2.2.9 | Foto-Upload direkt im Verifizierungs-Schirm; Namen, Bio und Nachrichten werden serverseitig getrimmt | nein |
| 2.3.0 | E-Mail-Bestätigung per Aktivierungslink, als Android App Link | **nur Deep Links**, siehe unten |
| 2.4.0 | Rechtstexte an den tatsächlichen Vertrags-, Zahlungs- und Datenschutzablauf angeglichen | Textangaben prüfen, keine neuen Datentypen |
| 2.4.1 | Konto-, Chat- und Deck-Oberfläche vereinfacht; Telefon-/SMS-Prüfung aus den nativen Rechtstexten entfernt, Brevo ergänzt | Brevo muss als E-Mail-Dienstleister angegeben sein |
| 2.5.0 (30.08.2026) | „Blockierte Personen" verwalten/aufheben unter Konto → Datenschutz & Sicherheit (nutzt bereits deklarierte Foto-/Kontodaten); stiller 20s-Vordergrund-Poll für Matches/Chats | nein — keine neue Berechtigung, kein neuer Datentyp |

**Hinweis:** Dieses Dokument selbst ist zwischen 2.4.1 (versionCode 29, Stand
oben im Dokumentkopf) und 2.5.0 nicht mitgepflegt worden — die
Zwischenversionen 2.4.2–2.4.9 haben ihre Deklarationsrelevanz nicht hier
festgehalten. Vor dem nächsten Play-Console-Upload lohnt ein Blick in die
`HANDOFF.md`-Sitzungen 21.08./23.08., ob dort deklarationsrelevante
Änderungen (neue Berechtigungen, Datentypen, Deep Links) übersehen wurden.

**Zur E-Mail-Bestätigung:** Die Adresse wurde schon vorher erhoben und ist als
Datentyp bereits deklariert. Neu ist allein der Weg — ein Link in einer Mail
öffnet die App. Für die Datensicherheit ändert das nichts.

**Deep Links prüfen.** Das Manifest führt seit 2.3.0 einen Intent-Filter mit
`autoVerify="true"` auf `https://flexr.social/mail-bestaetigen`. Android prüft
dafür beim Installieren `https://flexr.social/.well-known/assetlinks.json`. Die
Datei liegt im Repo unter `frontend/.well-known/` und stammt aus der TWA-Zeit;
sie führt bereits beide nötigen Fingerprints — den Play-App-Signing-Schlüssel
und den Upload-Key. Nach dem Upload lohnt ein Blick in der Console unter
*Grow → Deep links*, ob die Verifizierung durchgelaufen ist. Schlägt sie fehl,
öffnet der Link den Browser und die Bestätigung läuft dort weiter — der Weg
geht also nicht verloren, die App-Integration fehlt dann nur.

Der zweite Intent-Filter (`flexr://checkout`, `autoVerify="false"`) ist der
bestehende Rückweg aus dem Stripe-Checkout und kein Widerspruch dazu.

---

## 6. Vor dem Upload

```bash
cd android-native
./gradlew :app:testProdDebugUnitTest      # muss grün sein
./gradlew :app:bundleProdRelease

# Signatur gegenprüfen — ohne android/KEYSTORE-CREDENTIALS.txt entfällt sie
# stillschweigend und das Bundle ist nicht hochladbar:
unzip -l app/build/outputs/bundle/prodRelease/app-prod-release.aab | grep META-INF
# erwartet: META-INF/FLEXR.RSA und META-INF/FLEXR.SF
```

**Vorher auf einem echten Gerät testen.** Die App ist gebaut und die Unit-Tests
sind grün (45 Tests zum Stand 2.3.0), aber der Kameraweg — Rückkamera,
Bildlage, Schärfe auf einem flach liegenden Ausweis — lässt sich nur am Telefon
beurteilen. Dafür eignet sich der interne Test-Track oder die Debug-Variante
(`./gradlew :app:installProdDebug`), die als eigene App neben der
Produktionsfassung installiert wird.

**Die Oberfläche wurde bis heute auf keinem physischen Gerät gesehen.** Auf dem
Build-Rechner gab es weder Emulator noch angeschlossenes Telefon. Version 2.4.1
wurde mit JDK 17, Android SDK 36 und Build Tools 36 kompiliert; alle 45
Release-Unit-Tests sowie `bundleProdRelease` liefen am 20.08.2026 erfolgreich.
Kamera, Bildlage und Schärfe der Ausweisaufnahme bleiben deshalb im internen
Test-Track auf echter Hardware zu prüfen.
