# FLEXR — App-Store-Texte

Gegenstück zu `android/store/store-texte.md`. Die Beschreibung ist inhaltlich
dieselbe; die Feldnamen und Längenbegrenzungen sind die von App Store Connect.

---

## Für TestFlight (das braucht der Testrelease zuerst)

### Beta-App-Beschreibung

> FLEXR ist Dating für Gym-People in Österreich. In dieser Testfassung geht es
> um die Kernwege: Profil anlegen samt Foto, Umkreis und Gym einstellen, die
> Alters- und Identitätsprüfung durchlaufen (Pflicht, ohne sie bleibt das Deck
> gesperrt), durch Profile wischen, bei einem Match schreiben.
>
> Bitte gebt Rückmeldung zu: Ladezeiten der Fotos, Verhalten der Wischgeste,
> Zustellung der Chatnachrichten und allem, was sich auf eurem Gerät falsch
> anfühlt.

### Feedback-E-Mail

`flexr.social@proton.me`

### Beta-App-Review-Angaben (nur für externe Tester nötig)

**Anmeldedaten:** Ein Testkonto anlegen und hier eintragen — Apple prüft die App
sonst nicht, weil hinter der Registrierung alles verschlossen ist. Das Konto
muss die Alters- und Identitätsprüfung bereits bestanden haben (sonst bleiben
Deck, Matches und Chat gesperrt, siehe `require_activated_account` im Backend)
und sollte mindestens ein freigegebenes Foto und ein Match mit Chatverlauf
haben. Ein Abo ist nicht nötig — FLEXR ist derzeit für alle kostenlos.

| Feld | Wert |
|---|---|
| E-Mail | `appreview@flexr.social` |
| Passwort | *steht im Passwortspeicher und in App Store Connect — bewusst nicht hier* |

Das Passwort gehört nicht in dieses Repository. Es lebt an genau zwei Stellen:
im Passwortspeicher und im Feld *Sign-In Information* in App Store Connect.

So entsteht das Konto — beides auf dem **Produktivserver**, nicht lokal; die
App aus TestFlight spricht mit `https://flexr.social/`:

1. Über die Web-App mit genau diesen Daten registrieren: österreichische
   Postleitzahl, Studio aus der Liste, mindestens drei Fotos. Das geht nur
   über Web oder Android — die iOS-App kann die Prüfung noch nicht abschließen.
2. Auf dem Server freischalten:

   ```
   cd /flexr/backend && venv/bin/python scripts/activate_review_account.py \
       --email appreview@flexr.social --dry-run
   cd /flexr/backend && venv/bin/python scripts/activate_review_account.py \
       --email appreview@flexr.social
   ```

Das Skript setzt Freischaltung, Altersprüfung, blauen Haken und bestätigte
E-Mail und schließt einen etwaigen offenen Prüfvorgang. Es umgeht die
Prüfung bewusst und gilt nur diesem einen Konto — für alle anderen bleibt der
Freigabe-Knopf im Admin-Dashboard zuständig.

Danach ein zweites Konto anlegen, beide gegenseitig liken und eine Nachricht
schreiben: Ein Prüfer mit leerer Match- und Chatliste sieht zwei der vier
Reiter leer und hält das für einen Fehler.

**Anmerkungen für die Prüfung:**

> FLEXR ist ausschließlich in Österreich nutzbar; die Registrierung verlangt
> eine österreichische Postleitzahl (z. B. 1010 für Wien).
>
> Standortfreigabe wird nicht benötigt und nicht abgefragt — die
> Umkreissuche erfolgt rund um das im Profil eingetragene Gym, dessen
> Adresse (Postleitzahl) den Mittelpunkt liefert.
>
> Die Alters- und Identitätsprüfung verlangt ein Live-Selfie über die Frontkamera
> und einen amtlichen Lichtbildausweis. Sie ist **Pflicht**: Ohne bestandene
> Prüfung bleiben Deck, Matches und Chat gesperrt (nur Profil, Fotos,
> Verifizierung und Kontolöschung sind vorher erreichbar). Ein Mensch
> entscheidet, keine automatisierte Gesichtserkennung.
>
> FLEXR ist dauerhaft kostenlos nutzbar, auch über die Beta hinaus. Optional
> gibt es FLEXR Premium für 10 €/Monat, aktuell aber deaktiviert
> (`PREMIUM_ENABLED=false` im Backend) — die App bietet derzeit keinen Kauf und
> keinen Abo-Abschluss an. Wird Premium später aktiviert, läuft der Kauf wie
> vorgesehen über Stripe im externen Browser — **vor der Einreichung zur
> öffentlichen Veröffentlichung klären**, siehe ios/HANDOFF.md, Abschnitt „Der
> wahrscheinlichste Streitpunkt im Review".

---

## App-Name (max. 30 Zeichen)

```
FLEXR
```

## Untertitel (max. 30 Zeichen)

```
Dating für Gym-People
```

*(21 Zeichen. Alternative: „Match nach Gym & Umkreis" — 24 Zeichen.)*

## Werbetext / Promotional Text (max. 170 Zeichen, jederzeit änderbar)

```
Dating für Leute, die auch montags Beintag machen. Match nach Gym und Umkreis –
in ganz Österreich. Kostenlos nutzbar.
```

## Keywords (max. 100 Zeichen, kommagetrennt, ohne Leerzeichen)

```
gym,fitness,dating,österreich,training,partner,krafttraining,studio,match,sport,flirten,single
```

*(93 Zeichen. „FLEXR" nicht aufnehmen — der App-Name wird ohnehin indexiert.)*

## Beschreibung (max. 4000 Zeichen)

```
FLEXR ist Dating für Leute, die auch montags Beintag machen.

Schluss mit endlosem Wischen an Menschen, die „ins Fitnessstudio gehen" nur ins Profil schreiben. Auf FLEXR triffst du echte Gym-People aus deinem Umkreis – in ganz Österreich, von Wien über Graz und Linz bis Innsbruck.

WARUM FLEXR?

• Match nach Gym & Umkreis
Finde Leute, die im selben Studio oder in deiner Nähe trainieren. Du gibst dein Gym und deinen Radius an – FLEXR zeigt dir passende Profile in der Umgebung.

• Nur verifizierte Profile mit Foto
Jedes Konto durchläuft eine Alters- und Identitätsprüfung, bevor es matchen und schreiben kann. Kein Foto, kein Profil – das hält Fakes draußen und sorgt dafür, dass dein Match auch wirklich die Person ist, die du siehst.

• Gemeinsame Basis von Anfang an
Ob Powerlifting, Crossfit, Bodybuilding oder einfach der tägliche Gang aufs Laufband: Ihr habt sofort ein Thema. Und im Zweifel den nächsten Trainingspartner gleich mit dazu.

• Chatten, wenn's matcht
Sobald es auf beiden Seiten funkt, könnt ihr schreiben. Verabrede dich zum gemeinsamen Workout oder auf einen Kaffee (oder Protein-Shake) danach.

• Made in Austria
FLEXR ist für Österreich gebaut – mit echten Standorten und Studios im ganzen Land.

SO FUNKTIONIERT'S

1. Profil anlegen und Foto hochladen
2. Gym und Umkreis festlegen
3. Durch Profile in deiner Nähe wischen
4. Bei einem Match: loslegen und schreiben

SICHERHEIT

Jedes Foto wird von einem Menschen geprüft, bevor es jemand zu sehen bekommt. Links und Kontaktdaten werden in Nachrichten automatisch entfernt, Melden und Blockieren gibt es in jedem Profil und in jedem Chat. Mindestalter 18, serverseitig geprüft.

PREIS

FLEXR ist kostenlos nutzbar. Optional gibt es FLEXR Premium für 10 €/Monat, jederzeit kündbar.

FLEXR ist für alle ab 18 Jahren.

Match. Train. Repeat.

Lade FLEXR und finde jemanden, der deine PRs feiert statt sie zu googeln.
```

## Neue Funktionen (bei jedem Update)

```
Erste Fassung für iPhone und iPad.
```

---

## Angaben in App Store Connect

| Feld | Wert |
|---|---|
| Bundle-ID | `social.flexr.app` |
| SKU | `flexr-ios` |
| Primäre Kategorie | Soziale Netzwerke |
| Sekundäre Kategorie | Lifestyle |
| Altersfreigabe | 18+ (Dating; „Häufige/starke Hinweise auf sexuelles Verhalten oder Nacktheit" verneinen, aber „Nutzergenerierte Inhalte" und „Uneingeschränkter Internetzugang" wahrheitsgemäß angeben) |
| Verfügbarkeit | nur Österreich |
| Preis | Gratis (Abo läuft außerhalb des App Stores, siehe HANDOFF) |
| Copyright | `2026 Julian Pachernegg` |
| Support-URL | `https://flexr.social/faq.html` |
| Marketing-URL | `https://flexr.social/` |
| Datenschutz-URL | `https://flexr.social/datenschutz.html` |
| Exportbestimmungen | keine nicht ausgenommene Verschlüsselung (steht bereits als `ITSAppUsesNonExemptEncryption` in der Info.plist) |
| Lizenzvertrag | Apples Standard-EULA — **nichts eintragen**. Ein eigener Vertrag müsste im Volltext hinterlegt und von Apple mitgeprüft werden; die AGB auf flexr.social gelten davon unberührt weiter. |

### Kontaktangaben für den Review

Anschrift und E-Mail wie im Impressum: Julian Pachernegg, Einzelunternehmer,
Johann-Schrey-Weg 260, 8232 Grafendorf, Österreich, flexr.social@proton.me.

---

## App-Datenschutz („App Privacy")

Muss deckungsgleich sein mit `ios/FLEXR/PrivacyInfo.xcprivacy` und der
Datenschutzerklärung. **Tracking: nein** — die App setzt keine Analyse- oder
Werbe-SDKs ein und greift nicht auf die Werbekennung zu.

Alle folgenden Punkte: mit dem Nutzer **verknüpft**, Zweck **App-Funktionalität**,
**nicht** für Tracking verwendet.

| Kategorie | Datentyp | Was konkret |
|---|---|---|
| Kontaktdaten | Name | Vorname im Profil |
| Kontaktdaten | E-Mail-Adresse | Anmeldung |
| Sensible Daten | Sensible Daten | Geschlecht und gesuchtes Geschlecht (daraus ableitbar: sexuelle Orientierung), mit ausdrücklicher Einwilligung |
| Benutzerinhalte | Fotos oder Videos | Profilfotos, Verifizierungs-Selfies (letztere werden nach der Prüfung gelöscht) |
| Benutzerinhalte | E-Mails oder Textnachrichten | Chatnachrichten |
| Benutzerinhalte | Andere Benutzerinhalte | Bio, Gym, Ort |
| Kennungen | Benutzer-ID | Konto-ID |
| Kennungen | Geräte-ID | zufällige, app-eigene Kennung zur Mehrfachkonto-Erkennung; keine Hardware-Kennung, wird beim Löschen der App entfernt |
| Käufe | Kaufhistorie | Abo-Status (Kartendaten liegen ausschließlich bei Stripe) |
| Andere Daten | Andere Daten | Geburtsdatum (Altersgrenze 18), Postleitzahl |

**Nicht erhoben:** Standort (weder genau noch ungenau — die Umkreissuche
verwendet ausschließlich die Adresse des eingetragenen Gyms, nie eine
Geräte- oder Nutzerposition), Kontakte, Gesundheits- und Fitnessdaten,
Browser- und Suchverlauf, Nutzungsdaten, Diagnosedaten, Zahlungsdaten.

---

## Screenshots

Erzeugt `ios/store/gen.py` in den von App Store Connect verlangten Größen:

```bash
python3 ios/store/gen.py
```

| Datei | Größe | Wofür |
|---|---|---|
| `iphone-69-*.png` | 1320 × 2868 | iPhone 6,9″ — Pflicht |
| `iphone-65-*.png` | 1242 × 2688 | iPhone 6,5″ — Pflicht, wenn 6,9″ nicht alles abdeckt |
| `ipad-13-*.png` | 2064 × 2752 | iPad 13″ — Pflicht, weil die App auf dem iPad läuft |

Für **TestFlight** sind Screenshots nicht nötig — die braucht erst die
Einreichung zur Veröffentlichung.

**Vor der Einreichung ersetzen.** Die erzeugten Bilder sind gezeichnete
Nachbauten der Oberfläche, kein Bildschirmfoto der laufenden App — auf der
Karte steht ein Platzhalterbuchstabe statt eines Fotos. Richtlinie 2.3.3
verlangt Aufnahmen, die die App im Gebrauch zeigen. Der Marken-Rahmen darf
bleiben; hinein gehört eine echte Aufnahme aus Simulator oder Gerät, mit dem
Prüfkonto und seinen Fotos.

**Die iPad-Bilder entfallen, wenn die App nur fürs iPhone ausgeliefert wird.**
`TARGETED_DEVICE_FAMILY` steht auf `"1,2"`, deshalb verlangt Apple sie — und
prüft die App auch auf dem iPad. Auf `"1"` gesetzt, fällt beides weg; iPhone-
Apps laufen auf dem iPad weiterhin im Kompatibilitätsmodus. Gegen das
Beibehalten spricht nichts außer Aufwand: Die Oberfläche ist auf Hochformat
ausgelegt, das iPad zeigt sie entsprechend gestreckt.
