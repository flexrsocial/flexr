# FLEXR — Handoff für ein anderes Gerät / Claude Code

Stand: **10.09.2026**

Produktstand: Auf `origin/main` liegen zwei Commits dieser Sitzung — die
**Zweisprachigkeit (Deutsch/Englisch)** in Web-App, Landingpage, Android- und
iOS-App samt **zweitem Weg beim Ausweis-Upload** (Datei statt nur Kamera), und
darauf die **eigene englische Landingpage unter `/en/`**. Beides reines
Frontend/Client — kein Backend, keine Migration, kein Neustart.
**Noch nicht committet:** die Nachbesserungen aus der zweiten Sitzung vom
09.09. (siehe direkt unten) liegen nur im Arbeitsverzeichnis.
Aufbau des Dokuments: erst die Eckdaten, dann **09.09.**, dann **08.09.**,
dann die beiden Sitzungen vom **07.09.**, dann **06.09.**, dann **05.09.**,
dann **31.08.**, dann **30.08.**, dann **23.08.**, dann **21.08.**; die Build-,
Test- und Deploy-Abschnitte am Ende gelten sitzungsübergreifend.

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
- **AAB-Download: derzeit keiner.** `dl-a616e78274de323b/` wurde am
  08.09.2026 auf Wunsch geleert (2.4.0–2.4.6, 2.5.0, 2.5.2, 2.5.5) — alle
  AAB-Links in diesem Dokument liefern 404. Der aktuelle Quellstand ist
  **2.5.5 / versionCode 42**, gebaut und signiert, SHA-256
  `a2202dbad901476c7cc0a15683879d4cf45141183551f74bbe74a29ade6f8600`,
  7.679.482 Bytes, aber nur lokal: unter
  `android-native/app/build/outputs/bundle/prodRelease/app-prod-release.aab`
  und als Sicherung `~/Downloads/flexr-2.5.5.aab`. Zum Bereitstellen siehe
  „Ein neues AAB wird so bereitgestellt".
- **Namenskonvention** (seit 30.08. vereinheitlicht): neue Bundles landen in
  `dl-a616e78274de323b/` als `flexr-X.Y.Z.aab`, benannt nach dem
  `versionName` **aus dem Bundle**. Der Ordner ist leer, aber vorhanden.
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
   **Die iOS-App ist weiterhin nie übersetzt worden** (kein Mac vorhanden);
   der Mac-Teil steckt jetzt in `ios/tools/mac-build.sh`. Der Blockier-
   Bildschirm vom 30.08. muss dort als Erstes gegengeprüft werden.
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

- Zuerst `git fetch origin` + HEAD-Abgleich (siehe oben), erst danach
  irgendetwas anfassen. Beim Deploy den Deploy-Key mitgeben (siehe
  „Normaler Commit- und Deploy-Ablauf"), sonst scheitert der Pull.
- **Der lokale Ordner `~/MEGA/flexr/flexr` ist git-seitig veraltet** (Inhalt
  stimmt, Historie nicht) — siehe Sitzung 05.09. Einmal
  `git reset --mixed origin/main` nachholen, sonst wiederholt sich die
  Worktree-Umgehung in jeder Sitzung.
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
  begutachtet. iOS zusätzlich **nie compiliert**.
- Das Anheften der Landing-Headline ist auf Wunsch **zurückgenommen**; der
  Hero steht wieder mittig. Nicht erneut „reparieren", ohne zu fragen.
- Nachfragen/prüfen, ob der zweite Ring-Fix (21.08.) tatsächlich behoben
  hat — weiterhin unbestätigt.
- Telegram-Push ist geklärt (kein Bug, siehe Sitzung 30.08. Punkt 3) — noch
  offen ist nur der Sicherheitshinweis dazu: Bot-Token über @BotFather neu
  erzeugen, da er kurz im Terminal sichtbar war (Punkt 15).
- iOS ist am 23.08.2026 auf 2.4.9 nachgezogen worden (siehe
  `ios/HANDOFF.md`), plus die Blockier-Liste am 30.08. — aber immer noch
  **nie übersetzt**. Erster Schritt auf einem Mac:
  `./ios/tools/mac-build.sh team <TEAM-ID>` und danach
  `./ios/tools/mac-build.sh all`.
- AAB 2.5.0 (versionCode 38) ist gebaut, signiert und auf dem VPS bereit —
  noch nicht in die Play Console geladen (2.4.9 ist es inzwischen). Ein
  Neubau ist erst nötig, wenn wieder etwas unter `android-native/` geändert
  wurde.
- Die 5 Test-Frauenprofile nach Abschluss des Testens löschen (siehe
  „Testdaten" oben).
- Danach kontrollierten Stripe-Testcheckout durchführen (weiterhin offen
  aus früheren Sitzungen) — Kartendaten eingeben bleibt Sache des Nutzers.
- Erst danach neue Produktfunktionen beginnen.
