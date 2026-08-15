# Übergabe — Stand 14.08.2026

Dieses Dokument beschreibt den Zustand des Arbeitsverzeichnisses zum Zeitpunkt
des Gerätewechsels. Es liegt bewusst **im Repo**, damit es beim Kopieren des
Ordners mitkommt.

Letzter Commit: `53fc55c` (gepusht **und auf dem VPS deployt**). Das
Arbeitsverzeichnis ist sauber — es steht nichts mehr offen.

Der VPS lief zuvor auf `06462b2` vom 09.08. und war elf Commits zurück; mit
diesem Deploy sind 2.2.8, 2.2.9 und die E-Mail-Bestätigung dort angekommen.
Die Datenbank wurde vor der Migration gesichert nach
`/root/flexr-backups/flexr-20260814-194613.sql.gz`.

---

## 0. Nachtrag vom 15.08.2026 — wie der Umzug ausgegangen ist

Der Rest dieses Dokuments beschreibt den **alten** Rechner und bleibt
unverändert stehen. Was auf dem neuen tatsächlich ankam, steht hier.

### Der Transportweg hat mehr gekostet als gedacht

Der Ordner ging über MEGA. `/home/cooltek/MEGA/.megaignore` enthält die Regel
`-:.*` — **MEGA synchronisiert keine Datei mit führendem Punkt.** Im
angekommenen Baum standen exakt null Dotfiles. Verloren gingen damit `.git`
(die Warnung „muss mit" aus Abschnitt 1 lief also ins Leere), `.gitignore`,
`backend/.env`, `.claude/launch.json`, `frontend/.well-known/assetlinks.json`
und sogar das Exec-Bit von `android-native/gradlew`. Mitgekommen ist dafür
genau das, was bleiben sollte: 880 MB Baureste.

**Wiederhergestellt** durch einen frischen Klon von
`github.com/flexrsocial/flexr` — der Arbeitsbaum war danach deckungsgleich mit
`a30a071`, es ist nichts verloren gegangen. Die Lehre gehört in die Regel, nicht
in den Kopf: Code wandert über `git clone`, nicht über den Cloud-Ordner. Für
Bauartefakte stehen jetzt zusätzlich `-d:build`, `-d:venv`, `-d:node_modules`
und `-d:__pycache__` in der `.megaignore`.

### Was auf dem neuen Rechner fehlt

| | |
|---|---|
| Android-Toolchain | **komplett** — kein `java`, kein JDK, kein SDK, kein `adb`. Bundles sind hier nicht baubar. |
| Postgres | nicht installiert. Die App importiert sauber, der Dev-Server kommt bis zum Verbindungsaufbau. |
| `backend/.env` | neu angelegt, siehe unten |

### Die lokale `.env` zeigt nicht mehr auf Produktion

Abschnitt 5 warnt, dass ein einfach gestarteter Dev-Server gegen echtes R2 und
echtes Stripe läuft. Das ist auf diesem Rechner nicht mehr so: Die neue
`backend/.env` enthält bewusst **keine echten Zugangsdaten**. S3 steht auf
nicht auflösbaren `.invalid`-Namen, Stripe ist leer. Alle Tests sind damit
grün, ohne dass ein Testlauf die Produktion berührt.

Das heißt auch: Die „213 grün" aus diesem Dokument wurden seinerzeit **gegen
Produktions-Storage** erzeugt. Zwei Kniffe stehen als Kommentar in der `.env`,
weil sie sonst niemand findet:

```bash
cd backend && AWS_MAX_ATTEMPTS=1 venv/bin/python -m pytest -q -p no:warnings
```

Ohne `AWS_MAX_ATTEMPTS=1` dauert der Lauf 12 Minuten statt 2 — botocore
wiederholt jeden ins Leere laufenden Aufruf fünfmal mit Wartezeit. Und
`.invalid` darf nicht durch `127.0.0.1:9` ersetzt werden: „connection refused"
nimmt einen anderen Fehlerpfad, dann fällt
`test_documents_never_get_a_public_url` um.

### Seither entstanden

- **`a790371` — Abo-Kündigung entzog den Zugang nicht.** Der TODO in
  `billing.py` war keiner: `is_subscribed` wurde nur je auf True gesetzt. Wer
  über das Billing-Portal kündigte, behielt Swipe, Chat und Deck dauerhaft.
  Backend jetzt **223 grün**.
- **`f933a57` — `PLAY-CONSOLE.md` auf 2.3.0.** Stand vorher auf 2.2.0 /
  versionCode 17; `POST_NOTIFICATIONS` fehlte in der Berechtigungsliste.

### Was der Nachtrag am Rest dieses Dokuments korrigiert

- Abschnitt 2 sagt, es liege **kein** Bundle zum Download bereit. Das stimmte
  nicht — in `/flexr/frontend/dl-9a7043db0cab292e/` lag noch
  `flexr-2.2.9.aab`. Am 15.08. gelöscht, jetzt liegt wirklich keines mehr.
- Abschnitt 6 nennt `PLAY-CONSOLE.md` als offen — erledigt, siehe oben.
- Der in Abschnitt 1 genannte Pfad zu den Projekt-Erinnerungen gilt für den
  alten Rechner. Auf dem neuen liegen sie unter
  `~/.claude/projects/-home-cooltek-MEGA-flexr/memory/` und sind dort neu
  aufgebaut.

---

## 1. Wichtig vor dem Kopieren aufs Cloud-Laufwerk

### Der Ordner enthält Geheimnisse

| Datei | Inhalt |
|---|---|
| `backend/.env` | echter Cloudflare-R2-Schlüssel, echter Stripe-Secret-Key, JWT-Secret |
| `android/android.keystore` | Upload-Key für den Play Store |
| `android/KEYSTORE-CREDENTIALS.txt` | Passwort zum Keystore |

Alle drei sind per `.gitignore` von Git ausgenommen — sie liegen also **nur**
als Dateien im Ordner. Wer den Ordner auf ein Cloud-Laufwerk legt, legt damit
auch diese drei Dateien dorthin. Der Keystore ist nicht ersetzbar: Geht er
verloren, lässt sich die App im Play Store nicht mehr aktualisieren; wird er
zusammen mit dem Passwort kopiert, kann jeder, der beides hat, Updates
signieren. Das ist eine bewusste Entscheidung, keine Empfehlung — nur soll sie
nicht versehentlich fallen.

### Was nicht mitkopiert werden muss

Der Ordner ist **991 MB** groß, davon sind rund 910 MB reine Baureste:

| Verzeichnis | Größe | |
|---|---|---|
| `android-native/app/build` | 702 MB | wird neu gebaut |
| `backend/venv` | 179 MB | **funktioniert auf einem anderen Gerät ohnehin nicht** (absolute Pfade in den Skripten) |
| `android-native/.gradle` | 29 MB | Cache |
| `.git` | 20 MB | **muss mit** |

Ohne diese drei bleiben rund 80 MB. Auf dem neuen Gerät:

```bash
python3 -m venv backend/venv && backend/venv/bin/pip install -r backend/requirements.txt -r backend/requirements-dev.txt
```

Hinweis: Das venv war auf diesem Rechner kaputt (alle `.py`-Dateien fehlten,
nur `__pycache__` war übrig) und wurde neu aufgebaut. Ohne funktionierendes
venv läuft auch `.claude/launch.json` nicht — der Eintrag zeigt auf
`backend/venv/bin/uvicorn`.

### Was nicht mitkommt

Die Projekt-Erinnerungen liegen **außerhalb** des Ordners unter
`~/.claude/projects/-home-blktomcat-flexr-flexr/memory/`. Sie werden von einem
Ordner-Kopiervorgang **nicht** erfasst. Entweder separat mitnehmen oder darauf
verzichten — der Inhalt ist in diesem Dokument ohnehin zusammengefasst.

---

## 2. Was heute fertig wurde (committet und gepusht)

### 2.2.8 — `124aba9` / Merge `2b293f7`

**Einloggen-Knopf sporadisch unsichtbar.** Derselbe Fehler wie zuvor beim
Registrierungsknopf, nur an zweiter Stelle: `LoginScreen` übergab
`enabled = state.canSubmit`, und ein gesperrter `FlexrButton` lag auf
`alpha 0.4`. Der orange Verlauf über `#121212` wird dabei zu dunklem Braun,
die Schrift `#191008` verschwindet mit — Kontrast rund 1,7:1. Behoben an der
Wurzel: Der gesperrte Zustand verblasst nicht mehr, sondern wechselt die Farbe
(Stahlfläche, Stahlrahmen, `chalkDim`-Schrift). Der Ladezustand behält das
Orange. Der Login-Knopf ist zusätzlich immer tippbar.

**„Status aktualisieren" erkannte die Freischaltung nicht.** `refresh()` lud das
Profil neu und verließ sich darauf, dass die App dem Sitzungszustand folgt —
`MainViewModel` beobachtet aber nur `isLoggedIn`, nie das Profil. Wer während
der Wartezeit freigeschaltet wurde, bekam nach dem Knopfdruck gar nichts.
Die Freischaltung steht ohnehin in der Statusantwort (`account_activated`);
sie landet jetzt als `isActivated` im UI-Zustand und stößt `loadSession()` an.

### 2.2.9 — `887a0cc` / Merge `32cb5e8`

Ergebnis eines vollständigen Durchlaufs als neuer Nutzer.

**Sackgasse: Registrierung ohne Profilfoto.** Scheitert der Foto-Upload während
der Registrierung, existiert das Konto ohne Foto. `/verification/start` lehnt
dann korrekt ab — nur führte von dort kein Weg weiter, weil die Fotoverwaltung
im Konto-Bereich liegt, den ein nicht freigeschaltetes Konto nie erreicht.
Blieb: Konto löschen. Der Verifizierungs-Schirm bietet den Upload jetzt selbst
an (Web und App), der Hinweistext verweist dorthin statt ins Konto.

**Leerzeichen kamen an `min_length=1` vorbei.** Eine Chatnachricht aus lauter
Leerzeichen wurde angenommen und zählte beim Gegenüber als ungelesen; ein Name
aus lauter Leerzeichen ließ das Profil namenlos erscheinen. Name, Bio und
Nachrichtentext werden jetzt serverseitig getrimmt, bevor die Längengrenzen
greifen.

**Gesperrte Knöpfe im Web** hatten dieselbe Unsichtbarkeit wie in der App
(`opacity:0.4`) — betroffen waren die Altersgrenze im Formular und der Auslöser
bei fehlender Kamera. Gleiche Behandlung wie in der App.

**Nebenbei:** `PhotoPreparer`-Interface plus `MediaModule`, weil
`ImageProcessor` am Android-Context hängt und ViewModels darüber in reinen
JVM-Tests unkonstruierbar machte — dieselbe Trennung und derselbe Grund wie bei
`SessionStore`/`SessionModule`.

**Bundles auf dem VPS:** 2.2.8 und 2.2.9 wurden gebaut, signiert geprüft und in
`dl-`-Ordner unter `/flexr/frontend/` geladen. Alle Download-Ordner wurden
danach auf Wunsch gelöscht — es liegt derzeit **kein** Bundle zum Download
bereit.

---

## 3. E-Mail-Bestätigung per Aktivierungslink — deployt, aber schlafend

Committet als `3aca19b`, gemergt als `53fc55c`, auf dem VPS deployt und
migriert. Backend **213 Tests grün**, Android **45 Tests grün**, Version
**2.3.0 / versionCode 27**.

**Die Funktion ist derzeit wirkungslos** — und zwar mit Absicht: Auf dem VPS
sind keine SMTP-Zugangsdaten gesetzt, deshalb verlangt der Server die
Bestätigung nicht (siehe Weiche unter „Offene Punkte", Nr. 1). Für Nutzer
ändert sich nichts, bis SMTP eingetragen ist. Nach dem Deploy geprüft:
`email_configured() = False`, `email_confirmation_enforced() = False`, und alle
22 Bestandskonten sind durch die Migration als bestätigt markiert.

### Getroffene Entscheidungen

| Frage | Entscheidung |
|---|---|
| Strenge | **Blockierend vor der Ausweisprüfung** — `/verification/start` lehnt ohne bestätigte Adresse ab |
| Versand | **Erstmal Gmail**, Umzug später (reine `.env`-Änderung, keine Codeänderung) |
| App-Link | **Ja**, als Android App Link mit `assetlinks.json` |

### Warum blockierend

Es gibt kein „Passwort vergessen", und die E-Mail-Adresse ist nachträglich nicht
änderbar. Ein Tippfehler bei der Registrierung bedeutet heute ein unrettbares
Konto. Zudem soll kein Mensch eine Ausweisaufnahme begutachten, solange nicht
feststeht, dass die Adresse dem Nutzer gehört.

### Was gebaut wurde

**Backend**
- `app/models.py` — `User.email_verified_at` + `email_verified`-Property, neue
  Tabelle `EmailVerification` (Token nur als SHA-256-Hash, Ablaufzeit,
  Adresse mitgeführt)
- `alembic/versions/c1d84f30ab97_email_bestaetigung.py` — Spalte + Tabelle;
  **Bestandskonten werden auf „bestätigt" gesetzt**, sonst wären sie ausgesperrt
- `app/email_verification.py` — `issue()`, `confirm()`, `build_link()`,
  Token-Gültigkeit 24 h
- `app/routers/email_verify.py` — `POST /api/auth/email/confirm` (**ohne**
  Anmeldung, der Link wird oft auf einem anderen Gerät geöffnet) und
  `POST /api/auth/email/resend` (angemeldet, 3/Stunde)
- `app/mailer.py` — `send_verification_email()`; die alte Willkommensmail ist
  **entfallen**. Ihr Text war ohnehin veraltet („Drei Live-Selfies mit
  vorgegebenen Posen" — seit 2.2.x ist es ein Selfie, frontal, ohne Pose)
- `app/routers/verification.py` — Gate in `start`, `email_verified` in der
  Statusantwort (bewusst eigenes Feld statt neuem `next_step`-Wert, damit
  ausgelieferte App-Versionen es ignorieren statt es als „none" zu lesen)
- `app/schemas.py` — `email_verified` in `MyProfileOut`, neue Request/Response

**Web** — Seite `/mail-bestaetigen` in `frontend/index.html`,
`frontend/.well-known/assetlinks.json` angelegt

**Android** — `AndroidManifest.xml` (App-Link-Intent-Filter), `FlexrApi.kt`,
`Dtos.kt`, `Mappers.kt`, `VerificationRepository.kt`, `Models.kt`,
`FlexrApp.kt`, `MainViewModel.kt`, Gate-Screen und -ViewModel, Tests

### Offene Punkte

1. **SMTP auf dem VPS eintragen — bis dahin ist die Funktion schlafend.**
   In `/flexr/backend/.env` sind `SMTP_HOST` und `SMTP_FROM` leer. Ohne sie
   schreibt der Mailer nur ins Log. Deshalb wurde eine Weiche eingebaut
   (`verification.email_confirmation_enforced()`): Ohne Mailversand wird die
   Bestätigung **nicht verlangt**, sonst säße jedes neu registrierte Konto in
   einer Sackgasse — kein Link, kein Weiterkommen. Sobald die Zugangsdaten
   gesetzt und der Dienst neu gestartet ist, greift die Pflicht von selbst;
   Konten aus der Zwischenzeit kommen über „Neu senden" an ihren Link.
2. **Mit echtem Gmail-Konto testen.** App-Passwort, setzt 2FA voraus. Achtung:
   Gmail kann derzeit **nicht** als `noreply@flexr.social` senden — siehe
   Abschnitt 5.
3. **Ende-zu-Ende durchspielen**: Registrierung → Mail → Link → Bestätigung →
   Ausweisprüfung, einmal im Web und einmal auf einem echten Android-Gerät.
4. **`assetlinks.json`**: liegt bereits im Repo und stammt aus der TWA-Zeit; sie
   führt laut Manifest-Kommentar beide nötigen Fingerprints (Play-App-Signing
   und Upload-Key). Der zweite Intent-Filter mit `autoVerify="false"` ist der
   bestehende `flexr://checkout`-Deeplink für die Stripe-Rückkehr — kein
   Widerspruch. Schlägt die Verifizierung fehl, öffnet der Link den Browser und
   die Bestätigung läuft dort; der Weg geht also nie verloren.

### ⚠ Zwei Sitzungen haben gleichzeitig daran gearbeitet

In diesem Verzeichnis liefen parallel weitere Claude-Sitzungen. Eine davon hat
dieselbe Funktion gebaut. Konkret:

- `app/email_verification.py`, `app/routers/email_verify.py` und die Migration
  existierten bereits als unversionierte Dateien und wurden von mir mit `Write`
  **überschrieben**. Da sie nicht in Git waren, gibt es davon keine Sicherung.
  Dass jetzt alle Tests grün sind, spricht für ein stimmiges Ergebnis —
  verlorene Arbeit ist aber nicht auszuschließen.
- Während meiner Bearbeitung wurde `issue_and_send()` aus meiner Datei entfernt
  und `email_verified` in `VerificationStatusOut` ergänzt. Die Meldungen
  „Datei wurde verändert" kamen also von der anderen Sitzung, nicht von einem
  Linter.
- Auch `android-native/HANDOFF.md` wurde heute früh von außen geändert (Stand
  2.2.8 nachgetragen) — der Inhalt stimmte, ich habe ihn als `d3d9972`
  committet.

**Empfehlung für den Neustart:** nur **eine** Sitzung pro Arbeitsverzeichnis.
Falls doch mehrere nötig sind, getrennte Git-Worktrees verwenden.

---

## 4. Arbeitsweise in diesem Projekt

- Deutsch, auch in Commits und Kommentaren
- Jeder Fix: eigener `claude/…`-Zweig, deutscher Commit mit Fließtext-Begründung
  (**Ursache**, Beleg, Nebenwirkungen), dann `--no-ff`-Merge nach `main`
- Umlaute meidet die Commit-Historie (`ue`, `ae`), im Quellcode werden sie normal
  verwendet
- Jede App-Änderung bekommt neue `versionName`/`versionCode`
- Nicht ungefragt pushen, nichts ungefragt auf dem Server anfassen
- Wiederkehrendes Thema: **Sackgassen**. Bildschirme, aus denen ein Nutzer nicht
  mehr herauskommt, gelten als ernste Fehler — bei jeder Änderung an einem
  gesperrten Zustand prüfen, ob ein Ausweg bleibt

---

## 5. Betrieb und Umgebung

### Lokal testen, ohne Produktion zu treffen

`backend/.env` zeigt auf **echtes R2 und echtes Stripe** (nur `DATABASE_URL` ist
lokal). Wer den Dev-Server einfach startet, testet gegen Produktions-Storage.

Umgebungsvariablen haben bei pydantic-settings Vorrang vor `.env`. Für einen
gekapselten Durchlauf setzen: `DATABASE_URL` auf SQLite, `S3_ENDPOINT_URL` auf
einen lokalen Ersatz, `STRIPE_SECRET_KEY=""`.

Fallstrick: Die Variablen müssen in **derselben** Shell exportiert werden, aus
der uvicorn startet. Ein `set -a; . env.sh` vor einem `&`-Hintergrundblock
vererbt sie nicht an spätere Befehle derselben Zeile — genau daran lief der
Server einmal versehentlich gegen die lokale Postgres.

Ein S3-Ersatz muss mehr können als PUT: `head_object` braucht ein echtes
`Content-Length`, `inspect_uploaded_image` holt die ersten Bytes per
`Range`-Header, und der Browser lädt direkt dorthin hoch (CORS nötig).

Alembic läuft nicht gegen SQLite (Postgres-Enums); `Base.metadata.create_all()`
plus Gym-Seed aus `app/data/gyms_seed.json` erzeugt dasselbe Schema.

### Zwei Warteschlangen bis ein Konto sichtbar ist

1. **Verifizierung** — `POST /api/admin/verifications/{id}/approve`, verlangt
   eine vollständig bestätigte Checkliste im Body, sonst 422
2. **Fotomoderation** — `POST /api/admin/photos/{id}/approve`, davon unabhängig

Schritt 1 rührt den Fotostatus nicht an. Wer nur die Verifizierung freischaltet
und sich über ein leeres Deck wundert, sucht am falschen Ende. Ein Admin muss
direkt in die DB geschrieben werden; `AdminUser.name` ist NOT NULL.

Endpunkte heißen `/api/verification/document/…` (Einzahl), Nachrichten gehen an
`/api/matches/{id}/messages` mit dem Feld `content` (nicht `body`).

### Bundle bauen und bereitstellen

```bash
JAVA_HOME=~/.bubblewrap/jdk/jdk-17.0.11+9 ./gradlew :app:bundleProdRelease
unzip -l app/build/outputs/bundle/prodRelease/app-prod-release.aab | grep META-INF   # FLEXR.RSA muss da sein
```

Ohne `android/KEYSTORE-CREDENTIALS.txt` entfällt die Signatur **stillschweigend**.
Danach per `scp` nach `flexr-vps` in einen frisch zufälligen Ordner
`/flexr/frontend/dl-$(openssl rand -hex 8)/`, Datei als `flexr-<version>.aab`.
`robots.txt` sperrt das Präfix `/dl-` bereits.

Beim Prüfen aufpassen: Die nginx-Regel `try_files $uri $uri/ /index.html`
liefert für fehlende Dateien **HTTP 200 mit der Startseite**, nicht 404. Der
Statuscode allein beweist nichts — auf `Content-Type` und Größe schauen.

### DNS-Stand von flexr.social

| Eintrag | Stand |
|---|---|
| MX | **keiner** — die Domain empfängt keine Mail |
| SPF | **keiner** (nur `google-site-verification`) |
| DMARC | **keiner** |

Folge: Gmail kann nicht als `noreply@flexr.social` senden. Für eine
Fremdadresse verlangt Gmail „Senden als" und schickt einen Bestätigungscode
**an diese Adresse** — ohne MX kommt der nie an. Absender wäre also vorerst eine
`@gmail.com`-Adresse. Für den Betrieb ist ein Transaktionsversender mit eigener
Domain sinnvoller (Brevo 300/Tag gratis, Mailjet 6.000/Monat gratis, oder
Proton Business — Proton wird für den Support ohnehin genutzt). Am Code ändert
das nichts, `mailer.py` spricht Standard-SMTP.

---

## 6. Sonstiges Offenes

- **`android-native/PLAY-CONSOLE.md` steht noch auf 2.2.0 / versionCode 17.**
  Vor dem nächsten Store-Upload nachziehen.
- **Vorschlag, noch nicht entschieden:** Profilfotos bei der
  Verifizierungs-Freigabe automatisch mitfreigeben. Der Prüfer sieht das Foto
  dort ohnehin, und ein frisch freigeschaltetes Konto bleibt sonst unsichtbar,
  bis die zweite Warteschlange abgearbeitet ist.
- **Angeboten, nicht beauftragt:** `location ^~ /dl- { try_files $uri =404; }`
  in der nginx-Konfiguration, damit gelöschte Downloads 404 statt 200 liefern.
- **Die Android-Oberfläche wurde nie auf einem Gerät gesehen.** Auf diesem
  Rechner gibt es keinen Emulator; die Änderungen aus 2.2.8, 2.2.9 und 2.3.0
  sind kompiliert und unit-getestet, aber nicht visuell geprüft. Im Browser
  waren zusätzlich keine Screenshots möglich und synthetische Mausklicks kamen
  nicht an — geprüft wurde über DOM-Zustände.
- **Der Selfie-Schritt im Web ist ungetestet** (keine Kamera vorhanden). Der
  Fehlerpfad bei fehlender Kamera ist im Code behandelt und hat einen Rückweg.
