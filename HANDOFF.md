# FLEXR — Handoff für ein anderes Gerät / Claude Code

Stand: **20.08.2026**

Produktstand vor diesem Dokumentationscommit: **`7b47740` auf `main`**. Das
vorliegende Handoff folgt als reiner Dokumentationscommit. Der jeweils
verbindliche Stand ist immer `git log -1 --oneline` auf `origin/main`.

## Kurzfassung

FLEXR ist auf GitHub und dem Produktions-VPS deployt. Landingpage, Web-App,
Admin-Dashboard und native Android-App wurden UX-seitig vereinfacht und
produktiv getestet. Brevo übernimmt E-Mail-Verifizierung und transaktionale
Nutzermails. Das neue signierte Android App Bundle ist Version **2.4.1** mit
`versionCode 29`.

- Repository: `git@github.com:flexrsocial/flexr.git`
- Produktionsseite: <https://flexr.social>
- API-Healthcheck: <https://flexr.social/api/health>
- VPS-SSH-Alias auf dem bisherigen Rechner: `flexr-vps`
- Repository auf dem VPS: `/flexr`
- API-Dienst: `flexr-api.service`
- E-Mail-Jobtimer: `flexr-email-jobs.timer`
- AAB-Download: <https://flexr.social/dl-a616e78274de323b/flexr-2.4.1.aab>
- AAB SHA-256: `760ded8a14e798c186deda3695734831e66a18cd3b7d08d465fdd51f3606b481`

## Was zuletzt umgesetzt wurde

### Landingpage und Muster-Swipedecks

- Der obere Landingpage-Bereich hat jetzt einen Profilkarten-Fotostapel mit
  X-/Herz-Aktionen und ist auf Desktop und Mobil responsiv.
- Die Musterdecks auf Landingpage und `/app/` verwenden das echte
  Swipe-Erscheinungsbild und eine gemischte Profilreihenfolge.
- Samuel ist nicht mehr eingebunden.
- Fünf zuvor beanstandete Musterprofile wurden durch drei weibliche und zwei
  männliche, klar erwachsene Gym-Profile mit Österreich-Bezug ersetzt:
  Hannah, Theresa, Viktoria, Maximilian und Fabian.
- Die Bildausschnitte wurden so korrigiert, dass Gesichter auf der Landingpage
  nicht abgeschnitten werden.

### Web-App und native Android-App

- Die Web-App-Profilseite verwendet wieder das offene Ursprungsdesign: Profil,
  Fotos und Konto stehen dauerhaft untereinander und der Screen scrollt als
  Ganzes. Keine Aufklappregister wieder einführen; sie blockierten auf manchen
  Geräten das Scrollen.
- Der Mitgliedschaftshinweis ist ein eigener ruhiger Kasten. „Jetzt
  abonnieren“ und „Datenschutz & Sicherheit“ erscheinen in FLEXR-Orange und
  haben eigenen Abstand statt direkt am Fließtext zu kleben.
- Der Widerruf einer DSGVO-Einwilligung bleibt im Konto direkt erreichbar
  (Art. 7 Abs. 3 DSGVO), steht aber als eigene orange Aktion unter einer
  Trennlinie. Nicht entfernen, ohne einen ebenso einfachen Ersatzweg zu bauen.
- Unter „Rechtliches“ stehen kompakt Datenschutz, AGB, Rücktrittsrecht,
  Nutzungsrichtlinien, Impressum und „Inhalt melden“. Nicht jede öffentliche
  Informationsseite muss im Profil dupliziert werden.
- Datenschutz, Meldungen und Rechtliches bleiben als sekundärer Bereich über
  den Link unterhalb der Konto-Aktionen erreichbar.
- Sicherheits- und Rechtshinweise wurden aus den Hauptabläufen herausgenommen,
  soweit sie nicht zwingend direkt sichtbar sein müssen.
- Android bündelt die Rechts-/Sicherheitslinks in einem Dialog; Melden und
  Blockieren im Chat liegen im Overflow-Menü.
- Telefon-/SMS- und Twilio-Hinweise wurden aus den relevanten Rechtstexten
  entfernt. Es wird bei der Registrierung keine Telefonnummer erhoben.
- Brevo ist als E-Mail-Dienstleister dokumentiert und produktiv konfiguriert.

### Admin-Dashboard

- Förmliche Art.-16-DSA-Meldungen sind im Aufgabenbereich sichtbar und
  entscheidbar.
- Offene Notices sind Teil der Admin-Statistik.
- Fotoablehnungen verwenden strukturierte Gründe statt eines generischen
  Fallbacks.
- Nutzer-, Foto-, Verifizierungs-, Melde-, Sperr- und Gym-Abläufe wurden mit
  ausschließlich synthetischen QA-Konten produktiv geprüft.

### SEO, Auslieferung und Barrierefreiheit

- Alle zehn indexierbaren Seiten verwenden `lang="de-AT"`, Canonicals,
  Beschreibungen, Open-Graph-Metadaten, genau einen Hauptinhalt und einen
  Tastatur-Sprunglink.
- Die Sitemap enthält nur die öffentlichen kanonischen Seiten und wurde mit
  `lastmod` 20.08.2026 aktualisiert.
- Unbekannte URLs liefern jetzt einen echten HTTP-404-Status mit gebrandeter
  Fehlerseite statt der Landingpage als Soft-404.
- `/mail-bestaetigen` bleibt als expliziter App-Deep-Link erreichbar und trägt
  `X-Robots-Tag: noindex, nofollow`.
- Demo-Profilbilder werden langfristig und unveränderlich gecacht. Der Service
  Worker cached weder Nutzerfotos unter `/photos/` noch AAB-Downloads unter
  `/dl-*`.
- Breite Tabellen in den Rechtsseiten scrollen mobil in ihrem eigenen Bereich;
  die Seite selbst hat bei 390 Pixeln keinen horizontalen Overflow.
- Die aktive Nginx-Datei wurde gezielt angepasst, nicht mit der Repository-
  Vorlage überschrieben. Backup auf dem VPS:
  `/etc/nginx/sites-available/flexr.social.bak-a9a3faf`.

## Test- und Produktionsstatus

- Backend: effektiv **337 Tests grün**; zusätzlich liefen die 30 direkt
  betroffenen Admin-/DSA-Tests nochmals erfolgreich.
- Die aktuelle Frontend-Auslieferung ist zusätzlich durch **7 statische
  Regressionstests** in `backend/tests/test_public_frontend.py` abgesichert.
- Android: **45 Release-Unit-Tests grün**.
- Android: `bundleProdRelease` erfolgreich, Bundle mit dem bestehenden
  FLEXR-Upload-Key signiert; Zertifikat-Fingerprint stimmt mit dem Keystore
  überein.
- Produktives Web-/Mobile-E2E: Registrierung, Aktivierungs-Gates, Profil,
  Deck, Swipe, Match, Chat, Unread/Read, Linkzensur, Report, Moderation,
  Mute/Unmute, Block/Unblock und Rematch erfolgreich.
- Alle synthetischen QA-Nutzer und abhängigen Daten wurden danach gelöscht;
  reale Profile wurden nicht verändert.
- VPS-API ist aktiv und `/api/health` antwortet mit `{"status":"ok"}`.
- Landingpage, App-Seite, alle fünf neuen Bilder und der öffentliche
  AAB-Download wurden nach dem Deploy mit HTTP 200 geprüft.
- Nach dem letzten Profil-Deploy wurden bei 390 Pixeln Markenfarben,
  Abstände, sechs Rechtstextlinks, fehlender horizontaler Overflow und das
  offene Profil ohne Aufklappregister live geprüft. Nginx und API waren aktiv.

## Noch offen / bewusst nicht produktiv ausgelöst

1. Die native App muss auf einem echten Android-Gerät im internen Play-Testtrack
   geprüft werden, besonders Kamera, Profilfoto, Selfie und Ausweisaufnahme.
2. Ein echter Stripe-Checkout wurde nicht ausgelöst, um keine reale Zahlung oder
   Subscription anzulegen. Der Checkout gehört mit einem kontrollierten
   Testnutzer geprüft.
3. Das AAB ist noch in die Play Console hochzuladen. Dabei `PLAY-CONSOLE.md`
   beachten: Data-Safety-Angaben, Kamera/Ausweisfotos und Deep Links prüfen.
4. Die Rechtstexte wurden technisch und inhaltlich bereinigt, ersetzen aber
   keine abschließende Prüfung durch eine österreichische Rechtsberatung.
5. In der Google Search Console prüfen, ob
   `https://flexr.social/sitemap.xml` den Status „Erfolgreich“ hat. Für die
   Startseite einmal „Live-URL testen“ und „Indexierung beantragen“. Falls dort
   noch ein Soft-404-Problem gemeldet wird, nach dem neuen echten 404-Verhalten
   „Fehlerbehebung überprüfen“ starten.

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
- Zuerst auf einem echten Android-Gerät bzw. im internen Play-Testtrack testen.
- Danach kontrollierten Stripe-Testcheckout durchführen.
- Anschließend AAB 2.4.1 in die Play Console laden und Data Safety/Deep Links
  kontrollieren.
- Erst danach neue Produktfunktionen beginnen.
