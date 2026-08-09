# Play Console — was beim Upload von 2.2.0 anzupassen ist

Stand: Version `2.2.0`, versionCode **17**. Neu in dieser Fassung ist die
verpflichtende Alters- und Identitätsprüfung: Verifizierungs-Selfies **und** eine
Aufnahme eines amtlichen Lichtbildausweises. Das berührt mehrere Angaben in der
Play Console, die bisher nicht nötig waren.

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

`CAMERA` ist bereits deklariert und wurde bisher nur für die Selfies gebraucht.
Ab 2.2.0 kommt die Rückkamera für den Ausweis dazu — dieselbe Berechtigung,
keine neue Deklaration nötig. In der Store-Beschreibung sollte stehen, wofür die
Kamera verlangt wird.

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

## 5. Vor dem Upload

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
sind grün, aber der Kameraweg — Rückkamera, Bildlage, Schärfe auf einem flach
liegenden Ausweis — lässt sich nur am Telefon beurteilen. Dafür eignet sich der
interne Test-Track oder die Debug-Variante (`./gradlew :app:installProdDebug`),
die als eigene App neben der Produktionsfassung installiert wird.
