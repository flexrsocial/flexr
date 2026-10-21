# Play Console — Datensicherheit ausfüllen (Stand 21.10.2026, App 2.7.35/2.7.36)

**Anlass:** Der öffentliche Store-Eintrag zeigte am 21.10.2026 „Keine Daten
erhoben“ und „Keine Daten werden geteilt“. Das Zweite stimmt, das Erste nicht.
Die Antworten unten folgen der Datenschutzerklärung (Fassung 2026-10-14,
Abschnitt 2 und 6) und dem Code (Manifest, Abhängigkeiten, `models.py`).

Ort in der Console: **Überprüfen und optimieren → Richtlinien und Programme →
App-Inhalte → Datensicherheit → Verwalten** (im neuen Menü steckt „App-Inhalte“
dort; schneller über die Adresszeile: hinter `/app/<Zahl>/` den Rest durch
`app-content/overview` ersetzen). Nach dem Speichern prüfen, ob unter **Veröffentlichungsübersicht**
„Änderungen zur Überprüfung senden“ ansteht (bei verwalteter Veröffentlichung
gehen die Angaben sonst nicht raus).

Die Bezeichnungen unten entsprechen der deutschen Console sinngemäß; wo sie
leicht anders heißen, gilt die gemeinte Kategorie.

---

## Schritt 1: Datenerhebung und Sicherheit

| Frage | Antwort |
|---|---|
| Erhebt oder teilt deine App erforderliche Nutzerdatentypen? | **Ja** |
| Werden alle erhobenen Nutzerdaten bei der Übertragung verschlüsselt? | **Ja** (nur HTTPS) |
| Welche Methoden zur Kontoerstellung unterstützt deine App? | **Nutzername und Passwort** (E-Mail + Passwort) |
| Link zum Löschen des Kontos | `https://flexr.social/faq.html` (Eintrag „Wie lösche ich mein Konto?“, nennt App, Browser und Mail-Weg) |
| Können Nutzer das Löschen einzelner Daten beantragen, ohne das Konto zu löschen? | **Nein** (freiwillige Angabe; Fotos und Chatverläufe lassen sich zwar in der App selbst löschen, eine eigene Antragsseite gibt es nicht) |

## Schritt 2: Datentypen ankreuzen

**Ankreuzen** (alles andere bleibt leer):

- **Personenbezogene Daten:** Name · E-Mail-Adresse · Nutzer-IDs · Adresse ·
  Sexuelle Orientierung · Sonstige Informationen
- **Finanzdaten:** Kaufverlauf
- **Nachrichten:** Sonstige In-App-Nachrichten
- **Fotos und Videos:** Fotos
- **App-Aktivitäten:** App-Interaktionen · Sonstige nutzergenerierte Inhalte ·
  Sonstige Aktionen
- **Geräte- oder andere IDs**

**Nicht ankreuzen:** Standort (keine Geräteposition, Umkreis rechnet mit der
Adresse des Gyms) · Telefonnummer (Spalte existiert, wird nirgends befüllt) ·
Zahlungsinformationen (Karten- und Kontodaten nur bei Google/Stripe) ·
Gesundheit und Fitness · E-Mails · SMS · Videos · Audio · Dateien und Dokumente
(Ausweis nur als JPEG/PNG/WebP, also Foto) · Kalender · Kontakte ·
Suchverlauf · Installierte Apps · Web-Browsing · Absturzprotokolle und
Diagnosedaten (kein Crashlytics, kein Analyse-SDK).

## Schritt 3: Je Datentyp

Für **alle** Typen gilt: **Erhoben: Ja · Geteilt: Nein · Flüchtig verarbeitet:
Nein**.

Warum „Geteilt: Nein“ stimmt: Contabo, Cloudflare R2, Brevo und Firebase Cloud
Messaging verarbeiten als Dienstleister in unserem Auftrag; der Kauf läuft über
Google Play selbst; was andere Nutzer sehen (Profil, Nachrichten), schickt der
Nutzer bewusst an sie. Nichts davon zählt in der Console als „Teilen“.

| Datentyp | Was konkret | Erforderlich / optional | Zwecke |
|---|---|---|---|
| Name | Vorname im Profil | erforderlich | App-Funktionalität, Kontoverwaltung |
| E-Mail-Adresse | Anmeldung, Bestätigungs- und Aktivitäts-Mails | erforderlich | App-Funktionalität, Kontoverwaltung, Mitteilungen des Entwicklers |
| Nutzer-IDs | Konto-Kennung (auch als `obfuscatedAccountId` am Play-Kauf) | erforderlich | App-Funktionalität, Kontoverwaltung |
| Adresse | Postleitzahl und daraus abgeleiteter Ort | erforderlich | App-Funktionalität |
| Sexuelle Orientierung | aus Geschlecht und gesuchtem Geschlecht ableitbar (Art. 9) | erforderlich | App-Funktionalität |
| Sonstige Informationen | Geburtsdatum, Geschlecht, Gym, Suchradius, Dokumenttyp des Ausweises | erforderlich | App-Funktionalität, Betrugsprävention, Sicherheit und Compliance |
| Kaufverlauf | Kauf-Token, Abostatus, Ablaufzeit von FLEXR Premium | optional | App-Funktionalität |
| Sonstige In-App-Nachrichten | Chatnachrichten samt Zeitstempel, Scam-Filter-Markierungen | optional | App-Funktionalität, Betrugsprävention, Sicherheit und Compliance |
| Fotos | Profilfotos; Verifizierungs-Selfie und Ausweisaufnahme bis zur Prüfung | erforderlich | App-Funktionalität, Kontoverwaltung, Betrugsprävention, Sicherheit und Compliance |
| App-Interaktionen | letzte Aktivität (Online-Anzeige), ein Zugriffseintrag je Tag | erforderlich | App-Funktionalität, Analysen |
| Sonstige nutzergenerierte Inhalte | Bio, Meldungen samt Begründung | optional | App-Funktionalität, Betrugsprävention, Sicherheit und Compliance |
| Sonstige Aktionen | Likes und Passes, Matches, Blockierungen | erforderlich | App-Funktionalität, Betrugsprävention, Sicherheit und Compliance |
| Geräte- oder andere IDs | zufällige Geräte-ID (Mehrfachkonten), Firebase-Token für Push | erforderlich | App-Funktionalität, Betrugsprävention, Sicherheit und Compliance |

Anmerkungen:

- **Fotos nicht „flüchtig“:** Selfie und Ausweis liegen bis zur manuellen
  Entscheidung in R2. Das ist Speicherung (siehe `PLAY-CONSOLE.md` Abschnitt 1).
- **Adresse statt ungefährer Standort:** Die PLZ tippt der Nutzer selbst ein,
  die App fragt keine Position ab. Wer es strenger auslegen will, kreuzt
  zusätzlich „Ungefährer Standort“ an — falsch wäre das nicht, nur im Store
  missverständlich.
- **Analysen** nur bei App-Interaktionen: Die Tagesstatistik (tagesaktive
  Nutzer) ist die einzige statistische Auswertung.

## Danach

Store-Eintrag öffnen (`play.google.com/store/apps/datasafety?id=flexr.social.app`)
und prüfen, ob dort nicht mehr „Keine Daten erhoben“ steht. Die Übernahme kann
nach der Überprüfung einige Stunden dauern.
