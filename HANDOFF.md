# FLEXR — Handoff für ein anderes Gerät / Claude Code

Stand: **21.08.2026**

Produktstand vor diesem Dokumentationscommit: **`16f7947` auf `main`**. Das
vorliegende Handoff folgt als reiner Dokumentationscommit. Der jeweils
verbindliche Stand ist immer `git log -1 --oneline` auf `origin/main`.

## Kurzfassung

FLEXR ist auf GitHub und dem Produktions-VPS deployt. In dieser Sitzung wurde
eine Lücke geschlossen, die ChatGPT Codex auf einem anderen Rechner offen
gelassen hatte (Token-Limit erreicht): Der Widerruf der Matching-Einwilligung
war nur über die Web-App möglich. Dabei fiel zusätzlich ein Bug auf, der die
native Abo-Zahlung komplett blockierte, sowie eine optisch von der Marke
abweichende Web-Komponente. Alles behoben, committet, gepusht und deployt,
inklusive neu signiertem Android App Bundle Version **2.4.4**
(`versionCode 32`). Der Funktionsstand ist seit 2.4.2 unverändert — 2.4.3 und
2.4.4 waren reine Versions-Label-Anpassungen auf Nutzerwunsch, kein neuer Code.

- Repository: `git@github.com:flexrsocial/flexr.git`
- Produktionsseite: <https://flexr.social>
- API-Healthcheck: <https://flexr.social/api/health>
- VPS-SSH-Alias auf dem bisherigen Rechner: `flexr-vps`
- Repository auf dem VPS: `/flexr`
- API-Dienst: `flexr-api.service`
- E-Mail-Jobtimer: `flexr-email-jobs.timer`
- AAB-Download: <https://flexr.social/dl-a616e78274de323b/flexr-2.4.4.aab>
- AAB SHA-256: `340f516533a38e9688d73b4d731b3d7c294d6dc84fed3a780fd0753a8aa8a873`
- Vorgänger `flexr-2.4.2.aab` und `flexr-2.4.3.aab` liegen aus
  Kompatibilitätsgründen noch auf dem VPS (identischer Funktionsstand, nur
  altes Versions-Label) — können bei Gelegenheit aufgeräumt werden, ist aber
  unkritisch.

## Was in dieser Sitzung umgesetzt wurde

### Native App: Einwilligungswiderruf nachgezogen

Der Widerruf einer DSGVO-Einwilligung (Art. 7 Abs. 3), insbesondere der
Art.-9-Einwilligung zu Geschlecht/gesuchtem Geschlecht, ging bisher nur über
die Web-App. Codex hatte dafür bereits API-Client, DTOs, Repository und
ViewModel-Logik fertig (unversioniert liegen gelassen), aber keine
Compose-Oberfläche — genau da gingen die Tokens aus.

- Neuer Abschnitt „Datenschutz & Sicherheit" im Konto-Bereich
  (`AccountScreen.kt`): aufklappbare Zeile mit Pfeil rechts, optisch identisch
  zu „Hilfe & Rechtliches". Zeigt Liste aller Einwilligungen (Status, Datum,
  Fassung, Rechtsgrundlage) mit Widerruf-Button je widerrufbarer Einwilligung.
- Für den Art.-9-Widerruf (Geschlecht/gesuchtes Geschlecht) erscheint derselbe
  Warnhinweis-Dialog wie im Web vor dem eigentlichen Widerruf.
- `FlexrLinkButton` (gemeinsame Design-System-Komponente) ist jetzt linksbündig
  statt durch die von `TextButton` erzwungene Mindestbreite eingerückt —
  betrifft auch „Jetzt abonnieren" und „Abo verwalten / kündigen".

### Bug gefunden und behoben: Abo-Checkout schlug fehl

Beim Testen fiel auf: Klick auf „Jetzt abonnieren" in der nativen App zeigte
den Fehler **„Field required"**. Ursache: Der native Client rief
`POST /api/billing/checkout` ganz ohne Body auf. Das Backend verlangt aber
zwei getrennte, nicht vorangekreuzte Erklärungen (§ 10 und § 18 Abs. 1 Z 1
FAGG: sofortiger Leistungsbeginn + Kenntnisnahme über den Verlust des
Rücktrittsrechts) — ohne sie lehnt FastAPI mit `422` ab, und die rohe
Pydantic-Meldung landete ungefiltert als Toast beim Nutzer.

- Beide Plattformen (App-Profil-Screen und Paywall nach Ablauf des
  Probemonats — beide nutzen `AccountViewModel`) zeigen jetzt vorher einen
  Dialog mit genau diesen zwei Checkboxen, Wortlaut identisch zur Web-App.
  Erst nach Bestätigung beider Punkte wird der Checkout gestartet.
- **Dieser Bug betraf nur die native App**, nicht die Web-App — dort gab es
  den Dialog schon.

### Web: Checkout-Popup im FLEXR-Stil vereinheitlicht

Beim Vergleich fiel auf, dass `immediateStartOverlay` (das „Vor der
Zahlung"-Popup vor Stripe) eine eigene, vom Rest der Seite abweichende Optik
hatte:

- Der „Abbrechen"-Button nutzte `class="btn"` mit `background:transparent`,
  aber `.btn` setzt `color:#191008` (dunkle Schrift für den orangen
  Verlauf) — auf transparentem Grund praktisch unlesbar.
- Die Checkbox-Labels waren generische `<label>`-Elemente und erbten dadurch
  ungewollt `text-transform:uppercase` von der globalen `label{…}`-Regel
  (gedacht für Formularfeld-Labels wie „POSTLEITZAHL") — der ganze
  Erklärungstext erschien in Großbuchstaben.
- Generische, unthemte Checkboxen statt der im Rest der App verwendeten
  orangen `accent-color`.

Behoben durch Wiederverwendung der bereits etablierten Klassen statt neuer
Optik: `.legal-modal-backdrop`/`.legal-modal`/`.legal-modal-body` (wie beim
„Konto löschen"-Dialog) und `.consent-label` (wie bei der Registrierung).
Visuell auf der Live-Seite geprüft (Screenshot, DOM-Klassen per curl
bestätigt).

### Version

`versionCode` 29 → 30 → 31 → 32, `versionName` 2.4.1 → 2.4.2 → 2.4.3 → 2.4.4.
Ab 2.4.2 nur noch Versions-Label-Änderungen auf Nutzerwunsch, kein neuer Code.

## Android-Build — Hinweis zur RAM-Lage auf diesem Rechner

Dieser Rechner hat nur **3,7 GB RAM**, explizit auf max. 1,5 GB Build-Speicher
begrenzt. `bundleProdRelease` geriet dabei mehrfach in schwere
Swap-Auslastung (einmal musste ein hängender Java-Prozess manuell per `kill`
beendet werden, um einen erneuten Systemstillstand wie bei einem früheren
Versuch zu verhindern — der hatte einen Neustart der Maschine erzwungen).

**Ursache gefunden und behoben:** `kotlin.compiler.execution.strategy=in-process`
zwingt den Kotlin-Compiler in denselben JVM-Prozess wie Gradle selbst. Bei
einer kompletten Neukompilierung (z. B. nach einer Änderung an
`build.gradle.kts`, die den Configuration-Cache invalidiert) reichte der
1,5-GB-Heap für Gradle + Kotlin-Compiler zusammen in einem Prozess nicht.
Der `bundleProdRelease`-Build für 2.4.3 lief deshalb 3× fehl
(`packageProdReleaseBundle FAILED` bzw. `compileProdReleaseKotlin FAILED`
mit `InvocationTargetException`), bis ein separater, ebenfalls begrenzter
Kotlin-Compiler-Daemon eingerichtet wurde. Seitdem (2.4.4) liefen Test- und
Bundle-Build im ersten Versuch durch.

Aktuelle, funktionierende `~/.gradle/gradle.properties` (nutzerweit, **nicht**
im Projekt-Git):

```properties
org.gradle.jvmargs=-Xmx1536m -XX:MaxMetaspaceSize=256m -XX:+UseSerialGC -Dfile.encoding=UTF-8
org.gradle.parallel=false
org.gradle.workers.max=1
org.gradle.caching=true
kotlin.daemon.jvmargs=-Xmx1024m -XX:MaxMetaspaceSize=320m -XX:+UseSerialGC
```

Zwei getrennte, jeweils begrenzte Prozesse (Gradle max. 1,5 GB, Kotlin-Daemon
max. 1 GB) statt ein einzelner, überladener Prozess. Zusätzlich **immer**
`:app:testProdReleaseUnitTest` und `:app:bundleProdRelease` als **getrennte
Gradle-Aufrufe** starten, nicht in einem Befehl kombinieren — das hat in
dieser Sitzung zusätzlich zu Abstürzen geführt (zwei Tasks im selben
Single-Use-Daemon-Prozess addieren sich).

Auf einem neuen/anderen Gerät mit mehr RAM ist das wahrscheinlich kein
Thema — die RAM-Probleme sind rechnerspezifisch, nicht projektspezifisch. Auf
einer schwachen Maschine zusätzlich **andere speicherhungrige Anwendungen
vorher schließen**: ein Teil der Knappheit kam von parallel laufenden
Anwendungen auf demselben Rechner, nicht nur von Gradle/Kotlin selbst.

Falls auf einem neuen Gerät keine JDK/Android-SDK-Toolchain existiert: lässt
sich ohne root/sudo in einen beliebigen Ordner installieren (Eclipse Temurin
17 von `api.adoptium.net`, Android Commandline-Tools von
`dl.google.com/android/repository/`, Platform 36 + Build-Tools 36.0.0 per
`sdkmanager`).

## Testdaten für manuelles Testen (neu in dieser Sitzung)

Auf Wunsch wurden alte synthetische Testkonten entfernt und neue angelegt,
alle über den echten Löschweg (`admin.py:delete_user`-Logik) bzw. die echte
Registrierungs-API — keine rohen SQL-Eingriffe.

**Gelöscht:** 20 synthetische `@flexrtest.at`-Konten (Batch vom 08.08.2026)
sowie 2 E2E-Testkonten (`pachernegg+flexrtest…20260816@gmail.com`, „E2E
Test"/„E2E Test 2" vom 16.08.2026).

**Bewusst nicht angerührt:** `teresa.pachernegg@gmail.com` („Teresa") — nicht
eindeutig als Testkonto erkennbar, auf Nutzerwunsch erhalten geblieben.

**Neu angelegt:** 5 Frauenprofile, alle im 158-km-Suchradius von
`pachernegg@gmail.com` (Julian, McFit Triester Straße, 1100 Wien), über die
echte Registrierungs-API mit je einem genehmigten Foto (bereits öffentliche
Demo-Bilder aus `frontend/brand/demo/`) und `verification_required=False`
(überspringt die volle Selfie/Ausweis-Prüfung bewusst — reine
Deck-Sichtbarkeit fürs manuelle Testen, nicht die Verifizierungs-UX selbst):

| Name | Login-E-Mail | Gym | Entfernung |
|---|---|---|---|
| Katharina | `pachernegg+flexrtest-katharina@gmail.com` | FITINN, 1050 Wien | ~4,5 km |
| Laura | `pachernegg+flexrtest-laura@gmail.com` | Clever fit, Stockerau | ~30,6 km |
| Sofia | `pachernegg+flexrtest-sofia@gmail.com` | Clever fit, Krems an der Donau | ~66,5 km |
| Maya | `pachernegg+flexrtest-maya@gmail.com` | INJOY, Amstetten | ~114,9 km |
| Miriam | `pachernegg+flexrtest-miriam@gmail.com` | MoreFit, Lieboch | ~152,8 km |

Alle E-Mails laufen über Gmail-Plus-Adressierung im selben Postfach wie
`pachernegg@gmail.com`. Über `get_deck()`-Logik geprüft: alle 5 erscheinen im
Deck (Gender/Interest-Match, Gym löst auf, Foto genehmigt, Radius erfüllt).

**Passwörter absichtlich nicht in diesem Dokument** — `flexrsocial/flexr` ist
ein öffentliches GitHub-Repository, Klartext-Zugangsdaten zu echten,
einloggbaren Konten gehören da nicht rein, auch nicht zu Testprofilen. Sie
wurden im Chat dieser Sitzung mitgeteilt; falls nicht mehr griffbereit,
einfach über „Passwort vergessen" mit der jeweiligen E-Mail zurücksetzen.

Zum späteren Aufräumen: gleicher Ablauf wie oben beschrieben (Storage-Objekte
über `cleanup.storage_keys_for_user` + `delete_storage_objects`, danach
`db.delete(user)`), Filter auf `email LIKE 'pachernegg+flexrtest-%'`.

## Noch offen / bewusst nicht produktiv ausgelöst

1. Die native App muss auf einem echten Android-Gerät im internen Play-Testtrack
   geprüft werden, besonders Kamera, Profilfoto, Selfie, Ausweisaufnahme —
   und jetzt zusätzlich der neue Checkout-Dialog und der
   Datenschutz-&-Sicherheit-Widerruf.
2. Ein echter Stripe-Checkout wurde nicht ausgelöst, um keine reale Zahlung oder
   Subscription anzulegen. Der Checkout gehört mit einem kontrollierten
   Testnutzer geprüft — jetzt mit dem neuen Zwei-Checkbox-Dialog auf beiden
   Plattformen. Dafür eignen sich auch die fünf neuen Test-Frauenprofile
   (siehe „Testdaten" oben) als Gegenüber zum Deck-/Match-/Chat-Testen.
3. Das AAB (2.4.4, siehe oben) ist noch in die Play Console hochzuladen. Dabei `PLAY-CONSOLE.md`
   beachten: Data-Safety-Angaben, Kamera/Ausweisfotos und Deep Links prüfen.
4. Die Rechtstexte wurden technisch und inhaltlich bereinigt, ersetzen aber
   keine abschließende Prüfung durch eine österreichische Rechtsberatung.
5. In der Google Search Console prüfen, ob
   `https://flexr.social/sitemap.xml` den Status „Erfolgreich" hat. Für die
   Startseite einmal „Live-URL testen" und „Indexierung beantragen". Falls dort
   noch ein Soft-404-Problem gemeldet wird, nach dem neuen echten 404-Verhalten
   „Fehlerbehebung überprüfen" starten.
6. `backend/tests/test_public_frontend.py` wurde nach der Checkout-Popup-
   Änderung **nicht** erneut laufen gelassen (kein lokaler venv auf diesem
   Rechner vorhanden) — vor dem nächsten Deploy einmal nachholen, auch wenn
   ein `grep` bereits bestätigt hat, dass kein Test die entfernten
   `.istart-*`-Klassen referenziert.

## Auf einem anderen Gerät starten

```bash
git clone git@github.com:flexrsocial/flexr.git
cd flexr
git switch main
git pull --ff-only origin main
git status --short --branch
git log -5 --oneline
```

Falls das Repository schon vorhanden ist, reichen die letzten vier Befehle.
Vor jeder Änderung zuerst prüfen, dass keine fremden lokalen Änderungen
überschrieben werden.

### Nicht im Git enthaltene Zugangsdaten

Diese Dateien oder Zugänge müssen auf einem neuen Gerät separat und sicher
bereitgestellt werden; niemals in Git committen oder in ein Handoff kopieren:

- SSH-Key und SSH-Konfiguration für GitHub sowie den Alias `flexr-vps`
- `backend/.env`, falls das Backend lokal mit externen Diensten laufen soll
- `android/android.keystore`
- `android/KEYSTORE-CREDENTIALS.txt`

Die Produktions-Secrets liegen bereits auf dem VPS in `/flexr/backend/.env`.
Brevo-, Stripe-, JWT-, Datenbank- und Storage-Schlüssel nicht aus alten Chats
übernehmen oder erneut posten. Der Brevo-Schlüssel wurde bereits rotiert.

## Tests auf dem neuen Gerät

Backend:

```bash
cd backend
python3 -m venv venv
venv/bin/pip install -r requirements-dev.txt
venv/bin/python -m pytest
```

Schneller statischer Frontend-/SEO-Test ohne laufende Datenbank:

```bash
cd backend
venv/bin/python -m pytest tests/test_public_frontend.py -q
```

Android benötigt JDK 17, Android SDK Platform 36 und Build Tools 36.0.0:

```bash
cd android-native
./gradlew --no-daemon --max-workers=1 :app:testProdReleaseUnitTest
./gradlew --no-daemon --max-workers=1 :app:bundleProdRelease
unzip -l app/build/outputs/bundle/prodRelease/app-prod-release.aab | grep META-INF/FLEXR
sha256sum app/build/outputs/bundle/prodRelease/app-prod-release.aab
```

Ohne Keystore oder Passwortdatei kann Gradle ein nicht uploadfähiges,
unsigniertes Bundle erzeugen. Deshalb die `FLEXR.RSA`-Prüfung nie auslassen.

## Normaler Commit- und Deploy-Ablauf

```bash
git status --short
git diff --check
git add <nur-die-beabsichtigten-dateien>
git commit -m "Kurze aussagekräftige Beschreibung"
git push origin main

ssh flexr-vps 'cd /flexr && git pull --ff-only origin main'
ssh flexr-vps 'sudo systemctl restart flexr-api && systemctl is-active flexr-api'
curl -fsS https://flexr.social/api/health
```

Wichtig: Auf dem VPS ist `frontend/dl-a616e78274de323b/` absichtlich
unversioniert. Darin liegen die AAB-Downloads. Diesen Ordner bei Deploys oder
Aufräumarbeiten nicht löschen.

Ein neues Bundle wird so bereitgestellt:

```bash
scp android-native/app/build/outputs/bundle/prodRelease/app-prod-release.aab \
  flexr-vps:/flexr/frontend/dl-a616e78274de323b/flexr-X.Y.Z.aab
ssh flexr-vps 'sha256sum /flexr/frontend/dl-a616e78274de323b/flexr-X.Y.Z.aab'
```

Lokale und entfernte SHA-256 müssen identisch sein. Danach den öffentlichen
Download ebenfalls prüfen.

## Empfohlener Einstiegsprompt für Claude Code

> Lies zuerst `HANDOFF.md`, danach die für deine Aufgabe relevanten README- und
> Handoff-Dateien vollständig. Prüfe `git status`, `git log -5` und den aktuellen
> Stand von `origin/main`. Bewahre bestehende lokale Änderungen und den
> unversionierten VPS-Downloadordner. Poste oder committe keine Secrets. Arbeite
> die offenen Punkte aus dem Handoff der Reihe nach ab, teste proportional zum
> Risiko und committe/deploye erst nach erfolgreicher Prüfung.

## Erinnerung für die nächste Sitzung

- Zuerst `git pull --ff-only origin main` und dieses Handoff vollständig lesen.
- Web-App-Profil nicht wieder in Aufklappregister umbauen; offenes Layout und
  Scrollregel sind absichtlich durch einen Regressionstest geschützt.
- Bei Änderungen am Konto die Darstellung zusätzlich bei 390 × 844 Pixeln
  prüfen: orange Aktionen, Abstände, vertikales Scrollen und kein horizontaler
  Overflow.
- `backend/tests/test_public_frontend.py` einmal laufen lassen (siehe „Noch
  offen" Punkt 6).
- Auf einem echten Android-Gerät bzw. im internen Play-Testtrack testen —
  inklusive neuem Checkout-Dialog und Einwilligungswiderruf. Die fünf neuen
  Test-Frauenprofile (siehe „Testdaten" oben) eignen sich als Gegenüber.
- Anschließend kontrollierten Stripe-Testcheckout durchführen.
- Danach AAB 2.4.4 (bereits gebaut, signiert und live hochgeladen — siehe
  Kurzfassung) in die Play Console laden und Data Safety/Deep Links
  kontrollieren.
- Die 5 neuen Test-Frauenprofile (`pachernegg+flexrtest-*@gmail.com`) sind für
  manuelles Deck-/Match-/Chat-Testen gedacht — nach Abschluss des Testens
  wieder löschen (Ablauf siehe „Testdaten"-Abschnitt oben).
- Erst danach neue Produktfunktionen beginnen.
