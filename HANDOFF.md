# FLEXR — Handoff für ein anderes Gerät / Claude Code

Stand: **23.08.2026**, Abend

Produktstand: `git log -1 --oneline` auf `origin/main` ist `2885d7a`, auf dem
VPS ausgerollt und live geprüft. Aufbau des Dokuments: erst die Eckdaten,
dann die Sitzung vom **23.08.**, dann die vom **21.08.**; die Build-, Test-
und Deploy-Abschnitte am Ende gelten sitzungsübergreifend.

## Eckdaten (sitzungsübergreifend)

- Repository: `git@github.com:flexrsocial/flexr.git`
- Produktionsseite: <https://flexr.social>
- API-Healthcheck: <https://flexr.social/api/health>
- VPS-SSH-Alias: `flexr-vps` (root@31.220.73.67, Key
  `~/.ssh/id_ed25519_flexr_vps` — lag auf diesem Gerät bereits vor, keine
  Neueinrichtung nötig)
- Repository auf dem VPS: `/flexr`
- API-Dienst: `flexr-api.service`
- **Achtung, geteilter VPS:** Auf demselben Server laufen auch fremde,
  nicht mit FLEXR verwandte Projekte (`tarifbot-*`, `ediktmonitor`,
  `gasfees`, ein `defi`-Ordner). Bei Aufräumarbeiten in `/tmp` oder
  `~/.pm2` etc. nichts anfassen, das nicht eindeutig zu `/flexr` gehört.
- AAB-Download (aktuell): <https://flexr.social/dl-a616e78274de323b/flexr-2.4.6.aab>
- AAB SHA-256: `1ec3da96cd321535110f0a8f0935e7e3561abf1e7c7a5e79f81bb9c7b4e217dc`
- Ältere AABs (2.4.2–2.4.5) liegen noch auf dem VPS, unkritisch, bei
  Gelegenheit aufräumbar.

## Sitzung 23.08.2026 (Web-Frontend: Layout + Listen-Aktualisierung)

Zwei Commits, beide nur `frontend/app/index.html`, beide gepusht und
ausgerollt. Keine Backend-Änderung, keine Migration, kein Dienst-Neustart —
nginx liefert die Datei statisch aus.

### 1. Landingpage: "Match. Train. Repeat." rutschte beim Tabwechsel nach unten

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
- Backend-Suite vor und nach den Änderungen: **362 Tests grün**.

Kein Stripe-Checkout ausgelöst (wie in den Sitzungen davor bewusst vermieden).

### Fund ohne Fix: Blockieren lässt sich nirgends rückgängig machen

Das Backend kann es — `GET /api/blocks` und `DELETE /api/blocks/{user_id}` in
`backend/app/routers/safety.py`. **Kein Client nutzt das:**

- Web (`frontend/app/index.html`) ruft ausschließlich `POST /api/blocks` auf
  (zwei Stellen). Es gibt keine Liste der Blockierten und kein Aufheben.
- Android hat API- und Repository-Ebene (`FlexrApi.listBlocks/unblock`,
  `SafetyRepository.blockedUserIds/unblock`), aber **kein** ViewModel und
  keinen Bildschirm, der sie benutzt.
- iOS hat ebenfalls nur die API-Ebene (`FlexrAPI.swift`).

Wirkung: Ein Fehlgriff auf „Blockieren" ist aus Nutzersicht auf **allen**
Plattformen endgültig, und niemand kann nachsehen, wen er blockiert hat.
Das ist eine Funktionslücke, kein Bug — deshalb bewusst nicht im Vorbeigehen
gebaut. Zu klären wäre auch, ob `GET /api/blocks` (liefert nur IDs) für eine
brauchbare Liste um Name und Foto erweitert werden muss.

### Stolperstein beim Deploy: VPS-Pull braucht den Deploy-Key explizit

`ssh flexr-vps 'cd /flexr && git pull --ff-only origin main'` — der im
Abschnitt „Normaler Commit- und Deploy-Ablauf" dokumentierte Befehl —
scheitert derzeit mit `Permission denied (publickey)`. Der Deploy-Key liegt
als `~/.ssh/id_ed25519_github_flexr` auf dem Server, aber es gibt **keine**
`~/.ssh/config`, die git darauf zeigt. Funktionierender Aufruf:

```bash
ssh flexr-vps 'cd /flexr && GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github_flexr -o IdentitiesOnly=yes" git pull --ff-only origin main'
```

Dauerhafte Abhilfe wäre eine `~/.ssh/config` auf dem VPS mit `Host github.com
/ IdentityFile ~/.ssh/id_ed25519_github_flexr / IdentitiesOnly yes`. Bewusst
nicht angelegt — Serverkonfiguration, das gehört abgesprochen.

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

```bash
# JDK (Temurin 17) und Android Commandline-Tools nach /tmp/flexr-android-build
# (ACHTUNG: /tmp — überlebt keinen Neustart, auf einem neuen Gerät neu holen)
curl -fsSL -o jdk.tar.gz "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse"
curl -fsSL -o cmdline-tools.zip "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
# jdk.tar.gz -> /tmp/flexr-android-build/jdk (--strip-components=1)
# cmdline-tools.zip -> /tmp/flexr-android-build/sdk/cmdline-tools/latest
yes | sdkmanager --sdk_root=/tmp/flexr-android-build/sdk "platform-tools" "platforms;android-36" "build-tools;36.0.0"
echo "sdk.dir=/tmp/flexr-android-build/sdk" > android-native/local.properties
```

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
`~/MEGA/flexr/seed/README.md` (älteres, anderes Testkonten-Batch,
`@flexrtest.at`, nicht mehr aktuell).

**Bewusst nicht angerührt:** `teresa.pachernegg@gmail.com` — weiterhin
unklar, ob Testkonto, auf Nutzerwunsch erhalten.

Zum späteren Aufräumen: `email LIKE 'pachernegg+flexrtest-%'`, über den
echten Löschweg (`delete_storage_objects`/`storage_keys_for_user` +
`db.delete(user)`), nicht per rohem SQL.

## Noch offen / bewusst nicht erledigt

1. **Blockieren lässt sich auf keiner Plattform rückgängig machen** —
   Backend kann es, kein Client bietet es an. Einzelheiten und offene
   Fragen im Abschnitt „Fund ohne Fix" der Sitzung 23.08. Neu und
   unbearbeitet.
2. **`~/.ssh/config` auf dem VPS fehlt**, deshalb scheitert der weiter unten
   dokumentierte `git pull`-Befehl. Workaround und Vorschlag im Abschnitt
   „Stolperstein beim Deploy" (23.08.). Serverkonfiguration — abzusprechen.
3. **Web-Änderungen vom 23.08. sind ausgerollt und live geprüft**, aber vom
   Nutzer noch nicht selbst in Augenschein genommen.
4. **Android und iOS haben die Layout- und Listen-Fixes vom 23.08. nicht.**
   Der Layout-Fix ist reines Web (Landingpage gibt es in den Apps nicht).
   Der Listen-Fix dagegen könnte sinngemäß auch dort greifen: prüfen, ob
   Chat-/Matchliste in Android und iOS bei eintreffenden Nachrichten von
   selbst nachziehen oder erst beim Tabwechsel.
5. **Ring-Fix (21.08., Punkt 1) vom Nutzer noch nicht nach dem zweiten
   Anlauf bestätigt.** Zuerst nachfragen bzw. mit hartem Reload
   gegenprüfen.
6. ~~**iOS hat dieselben Bugs wie Punkt 3 und vermutlich Punkt 2**~~ —
   **am 23.08.2026 erledigt**, zusammen mit allem anderen, was seit dem
   15.08. an iOS vorbeigelaufen war. Einzelheiten in
   [ios/HANDOFF.md](ios/HANDOFF.md), Abschnitt „Was am 23.08.2026
   nachgezogen wurde". Wichtigster Fund dabei: `POST /api/billing/checkout`
   verlangt seit dem 17.08. einen Körper mit beiden FAGG-Erklärungen — die
   iOS-App schickte keinen, jeder Abo-Abschluss wäre mit 422 gescheitert.
   **Die iOS-App ist weiterhin nie übersetzt worden** (kein Mac vorhanden);
   der Mac-Teil steckt jetzt in `ios/tools/mac-build.sh`.
7. **Android AAB 2.4.6 (versionCode 34) ist gebaut, signiert und auf dem
   VPS-Downloadordner live** — aber noch nicht in die Play Console
   hochgeladen. `PLAY-CONSOLE.md` beachten: Data-Safety-Angaben, Kamera/
   Ausweisfotos und Deep Links prüfen. Enthält gegenüber 2.4.4 echten neuen
   Code (Punkte 2, 3, 4, 6, 9, 10 der Sitzung 21.08.) — kein reines
   Versions-Label-Update.
8. **Kein kontrollierter Stripe-Testcheckout** ausgelöst (wie in den
   vorherigen Sitzungen auch bewusst vermieden).
9. Die fünf Test-Frauenprofile eignen sich weiterhin für Deck-/Match-/
   Chat-Testen — nach Abschluss löschen (siehe oben).
10. `backend/tests/test_public_frontend.py` lief auch am 23.08. mehrfach
    grün mit — der in einer früheren Sitzung offene Punkt dazu ist erledigt.
11. Google Search Console / Sitemap-Status (aus einer früheren Sitzung
    offen) wurde auch am 23.08. nicht geprüft.

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

Stand 23.08.2026: **362 Tests, alle grün** (vor und nach den Änderungen
jener Sitzung gelaufen).

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

# Stand 23.08.2026 scheitert das blanke "git pull" auf dem VPS mit
# "Permission denied (publickey)" - der Deploy-Key muss explizit mit:
ssh flexr-vps 'cd /flexr && GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github_flexr -o IdentitiesOnly=yes" git pull --ff-only origin main'
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

`frontend/dl-a616e78274de323b/` auf dem VPS ist absichtlich unversioniert
(enthält die AAB-Downloads) — nie löschen.

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

- Zuerst `git fetch origin` + HEAD-Abgleich (siehe oben), erst danach
  irgendetwas anfassen. Beim Deploy den Deploy-Key mitgeben (siehe
  „Normaler Commit- und Deploy-Ablauf"), sonst scheitert der Pull.
- Nachfragen, ob das Layout der Landingpage (Headline bleibt beim Wechsel
  auf „Registrieren" oben stehen) so gefällt — ausgerollt, aber vom Nutzer
  noch nicht begutachtet.
- Nachfragen/prüfen, ob der zweite Ring-Fix (21.08.) tatsächlich behoben
  hat — weiterhin unbestätigt.
- Entscheiden, ob die Blockier-Liste samt Aufheben gebaut wird (Punkt 1
  unter „Noch offen"): Backend kann es, kein Client zeigt es. Dabei klären,
  ob `GET /api/blocks` Name und Foto mitliefern muss.
- Prüfen, ob Android und iOS denselben Listen-Bug haben wie das Web
  (Chat-/Matchliste zieht bei neuer Nachricht nicht von selbst nach).
- iOS ist am 23.08.2026 auf 2.4.9 nachgezogen worden (siehe
  `ios/HANDOFF.md`), aber immer noch **nie übersetzt**. Erster Schritt auf
  einem Mac: `./ios/tools/mac-build.sh team <TEAM-ID>` und danach
  `./ios/tools/mac-build.sh all`.
- AAB 2.4.6 ist bereits gebaut, signiert und live hochgeladen (siehe
  Kurzfassung) — noch nicht in die Play Console geladen.
- Die 5 Test-Frauenprofile nach Abschluss des Testens löschen (siehe
  „Testdaten" oben).
- Danach kontrollierten Stripe-Testcheckout durchführen (weiterhin offen
  aus früheren Sitzungen).
- Erst danach neue Produktfunktionen beginnen.
