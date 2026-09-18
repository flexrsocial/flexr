# Was noch von Hand zu erledigen ist

Stand: 17.09.2026 abends. Vier Blöcke, unabhängig voneinander abzuarbeiten —
**B ist erledigt**, A, C und D stehen noch offen:

| Block | Wirkung | Dauer | Stand |
|---|---|---|---|
| A — Firebase | Push auf Android | ~20 min | **offen** |
| B — APNs | Push auf iOS | ~15 min | ✓ erledigt 17.09.2026 |
| C — Play Console | Kauf-Knopf in der Android-App | ~30 min + Prüfung | **offen** |
| D — App Store Connect | Kauf-Knopf in der iOS-App | ~30 min + Prüfung | **offen** |

**Alles ist so gebaut, dass nichts kaputtgeht, solange du nichts davon machst.**
Ohne Zugangsdaten bleibt Push aus (die Apps holen weiter selbst ab), ohne
Produktkennung bleibt der Kauf-Knopf unsichtbar. Es gibt keine halbe Stufe, in
der etwas ins Leere läuft.

Die Werte, die du brauchst:

* Android-Paket: `flexr.social.app`
* iOS-Bundle: `social.flexr.app`
* Server-`.env`: `/flexr/backend/.env` (eine Sicherung liegt daneben)

---

## A — Firebase für Android-Push

### A1. Projekt anlegen

1. https://console.firebase.google.com → **Projekt hinzufügen**
2. Name z. B. `FLEXR`. Google Analytics kannst du **abwählen** — für Push wird
   es nicht gebraucht.

### A2. Android-App registrieren

1. Im Projekt: **Zahnrad → Projekteinstellungen → Allgemein**
2. Unter *Meine Apps*: **Android-Symbol**
3. Paketname exakt: `flexr.social.app`
4. Spitzname und SHA-1 kannst du leer lassen — beides ist für Push nicht nötig.
5. `google-services.json` wird angeboten: **nicht herunterladen.** Die App
   benutzt sie bewusst nicht (sonst ließe sie sich ohne diese Datei nicht mehr
   bauen). Stattdessen brauchst du vier Werte daraus, die auf derselben Seite
   stehen.

### A3. Die vier Werte abschreiben

**Projekteinstellungen → Allgemein**, unten bei der Android-App:

| Wert in der Konsole | Beispielform |
|---|---|
| Projekt-ID | `flexr-1a2b3` |
| App-ID | `1:123456789012:android:abc123def456` |
| Web-API-Schlüssel | `AIzaSy…` |
| Projektnummer (= Absender-ID) | `123456789012` |

Diese Werte sind **keine Geheimnisse** — sie stecken in jeder ausgelieferten
Android-App.

Trag sie ein in `~/.gradle/gradle.properties` (Datei anlegen, falls nicht da):

```properties
flexr.firebase.projectId=flexr-1a2b3
flexr.firebase.appId=1:123456789012:android:abc123def456
flexr.firebase.apiKey=AIzaSy…
flexr.firebase.senderId=123456789012
```

> **Danach muss das Android-Bundle neu gebaut werden.** Das ausgelieferte
> 2.7.1 kennt diese Werte noch nicht — sie landen zur Bauzeit in der App.

### A4. Dienstkonto für den Server

1. **Projekteinstellungen → Dienstkonten**
2. **Neuen privaten Schlüssel generieren** → JSON wird heruntergeladen
3. Auf den Server legen:

```bash
scp ~/Downloads/flexr-*.json flexr-vps:/flexr/backend/fcm-service-account.json
ssh flexr-vps 'chmod 600 /flexr/backend/fcm-service-account.json'
```

4. In `/flexr/backend/.env` ergänzen:

```
FCM_SERVICE_ACCOUNT_FILE=/flexr/backend/fcm-service-account.json
FCM_PROJECT_ID=flexr-1a2b3
```

5. `sudo systemctl restart flexr-api`

---

## B — APNs für iOS-Push

Kein Firebase. Die iOS-App spricht direkt mit Apple.

### B1. Push für die App-ID einschalten

1. https://developer.apple.com/account → **Certificates, Identifiers & Profiles**
2. **Identifiers** → `social.flexr.app`
3. **Push Notifications** anhaken → **Save**

> Ohne diesen Haken schlägt der nächste Build beim Signieren fehl: Die App
> verlangt jetzt das `aps-environment`-Entitlement, und das Profil muss es
> hergeben.

**Erledigt am 17.09.2026** — und es war genau diese fehlende Freigabe. Der
Codemagic-Lauf davor brach im Archiv-Schritt mit Status 65 ab: Der Workflow
holt sein Profil mit `app-store-connect fetch-signing-files --create`, und ein
so erzeugtes Profil enthält nur die Berechtigungen, die im Portal für die
App-ID freigeschaltet sind. Der Haken war nicht gesetzt, das Profil kannte
`aps-environment` nicht, `codesign` verweigerte. Nach dem Setzen lief derselbe
Build unverändert durch.

Merksatz für das nächste Entitlement: **Erst im Portal freischalten, dann
bauen.** Xcode-Projekt und Profil müssen dasselbe wissen.

### B2. APNs-Schlüssel erzeugen

1. **Keys → +**
2. Name z. B. `FLEXR Push`
3. **Apple Push Notifications service (APNs)** anhaken → **Continue → Register**
4. **Download** → Datei `AuthKey_XXXXXXXXXX.p8`

> **Diese Datei gibt es nur einmal.** Apple bietet sie nie wieder zum Download
> an. Leg eine Kopie in deinen Passwortspeicher.

Notiere dazu:

* **Key ID** — die zehn Zeichen im Dateinamen, z. B. `ABC123DEFG`
* **Team ID** — steht rechts oben im Developer-Portal unter deinem Namen,
  ebenfalls zehn Zeichen

Beim Anlegen fragt Apple zwei Dinge, die sich **nach dem Speichern nicht mehr
ändern lassen**:

* **Environment** → *Sandbox & Production*. Nicht optional, sondern von
  `push.py` vorausgesetzt: Der Server probiert bei `BadDeviceToken` die jeweils
  andere Umgebung, und Entwicklungs-Builds (Sandbox-Tokens) und
  TestFlight/App Store (Produktions-Tokens) sind gleichzeitig im Umlauf. Ein
  Schlüssel für nur eine Umgebung würde die andere Hälfte mit
  `InvalidProviderToken` abweisen.
* **Key Restriction** → *Team Scoped (All Topics)* oder *Topic Scoped*. Beides
  funktioniert, weil der Server `apns-topic` ohnehin mitschickt. Topic Scoped
  ist das engere: Bei einem Leck ließen sich nur FLEXR-Nutzer beschicken, nicht
  jede App des Kontos. Bei genau einer App ist der Unterschied heute null.

**Erledigt am 17.09.2026**, mit *Sandbox & Production* und *Team Scoped*.

### B3. Auf den Server

```bash
scp ~/Downloads/AuthKey_ABC123DEFG.p8 flexr-vps:/flexr/backend/apns-key.p8
ssh flexr-vps 'chmod 600 /flexr/backend/apns-key.p8'
```

In `/flexr/backend/.env`:

```
APNS_KEY_FILE=/flexr/backend/apns-key.p8
APNS_KEY_ID=ABC123DEFG
APNS_TEAM_ID=DEINTEAMID
APNS_TOPIC=social.flexr.app
```

Dann `sudo systemctl restart flexr-api`.

`APNS_SANDBOX` brauchst du **nicht** zu setzen: Der Server probiert bei
`BadDeviceToken` automatisch die andere Umgebung. Entwicklungs-Builds bekommen
Sandbox-Tokens, TestFlight und App Store Produktions-Tokens — beide können
gleichzeitig im Umlauf sein.

**Erledigt am 17.09.2026.** Der Schlüssel liegt als
`/flexr/backend/apns-key.p8` (Eigentümer `deploy`, Rechte 600), die vier Werte
stehen in der `.env`: Key ID `93U96DXUDW`, Team ID `UJ46YJU58D`. Der Schlüssel
wurde mit Environment *Sandbox & Production* und *Team Scoped (All Topics)*
angelegt — beides passt zur Umgebungs-Rückfallebene in `push.py`.

Ob Apple den Schlüssel annimmt, lässt sich **ohne Gerät** prüfen: ein Versand an
ein absichtlich unbrauchbares Geräte-Token. Kommt `400 BadDeviceToken`, dann hat
Apple das JWT akzeptiert und nur das Token verworfen — Schlüssel, Team und Topic
stimmen also. Ein `403 InvalidProviderToken` wäre das Gegenteil, ein
`403 BadTopic` ein falscher Bundle-Identifier.

```bash
ssh flexr-vps 'cd /flexr/backend && sudo -u deploy env $(grep -E "^(APNS_|DATABASE_URL|JWT_SECRET)" .env | xargs) ./venv/bin/python - <<"PY"
import httpx
from app import push
from app.config import settings

jwt = push._apns_jwt_token()
falsch = "0" * 64  # absichtlich unbrauchbares Geraete-Token
for name, host in (("Produktion", push._APNS_PROD), ("Sandbox", push._APNS_SANDBOX)):
    with httpx.Client(http2=True, timeout=10) as c:
        r = c.post(
            f"{host}/3/device/{falsch}",
            headers={
                "authorization": f"bearer {jwt}",
                "apns-topic": settings.apns_topic,
                "apns-push-type": "alert",
                "apns-priority": "10",
            },
            json={"aps": {"alert": {"title": "x", "body": "y"}}},
        )
    print(name, r.status_code, r.text.strip())
PY'
```

Beide Umgebungen antworteten `400 BadDeviceToken` — das ist genau der Beleg
dafür, dass *Sandbox & Production* auch wirklich beides abdeckt.

Was jetzt noch fehlt, damit auf einem iPhone etwas ankommt: die
Push-Berechtigung auf der App-ID (Schritt **B1**) und ein Build, der die
`aps-environment`-Berechtigung trägt.

---

## C — Play Console: Abo anlegen und aktivieren

### C1. Voraussetzung

**Monetarisierung → Zahlungsprofil** muss eingerichtet sein (Händlerkonto).
Ohne das lässt sich kein Abo aktivieren.

### C2. Abo anlegen

1. Play Console → deine App → **Monetarisieren → Produkte → Abos**
2. **Abo erstellen**
3. **Produkt-ID: `premium_monthly`** — exakt so, und **unveränderlich**.
4. Name: `FLEXR Premium`
5. **Speichern**

### C3. Basis-Tarif

1. Im Abo: **Basis-Tarif hinzufügen**
2. Tarif-ID z. B. `monthly`
3. Typ: **Automatisch verlängernd**
4. Abrechnungszeitraum: **1 Monat**
5. Preis für Österreich setzen (Google rechnet die übrigen Länder um)
6. **Aktivieren** — ohne diesen Schritt findet die App das Angebot nicht.

### C4. Serverseitig freischalten

In `/flexr/backend/.env`:

```
GOOGLE_SUBSCRIPTION_PRODUCT_ID=premium_monthly
```

`sudo systemctl restart flexr-api` — **ab hier erscheint der Kauf-Knopf in der
Android-App**, ohne neuen Build.

### C5. Dienstkonto für die Kaufprüfung

Der Server muss jeden Kauf bei Google nachfragen dürfen.

1. Play Console → **Einstellungen → API-Zugriff**
2. Google-Cloud-Projekt verknüpfen (das Firebase-Projekt aus Block A geht)
3. **Dienstkonto erstellen** → führt in die Google Cloud Console
4. Dort: Dienstkonto anlegen, **JSON-Schlüssel** erzeugen und herunterladen
5. Zurück in der Play Console: dem Dienstkonto Zugriff geben — mindestens
   **„Finanzdaten ansehen"** und **„Bestellungen und Abos verwalten"**

```bash
scp ~/Downloads/play-*.json flexr-vps:/flexr/backend/play-service-account.json
ssh flexr-vps 'chmod 600 /flexr/backend/play-service-account.json'
```

```
GOOGLE_SERVICE_ACCOUNT_FILE=/flexr/backend/play-service-account.json
```

> **Ohne diesen Schritt lehnt der Server jeden Play-Kauf ab.** Der Knopf wäre
> da, der Kauf ginge durch, und die Freischaltung käme nicht — der
> unangenehmste aller Zwischenzustände. Also C5 **vor** C4 erledigen oder
> beides zusammen.

### C6. Optional: Benachrichtigungen über Kündigungen (RTDN)

Ohne diesen Block erfährt der Server von Kündigungen und Verlängerungen erst,
wenn die App das nächste Mal startet und ihre Käufe meldet. Das reicht im
Alltag, ist aber träge.

1. Google Cloud Console → **Pub/Sub → Thema erstellen**, z. B. `flexr-play-rtdn`
2. Dem Thema die Veröffentlichungsrechte für
   `google-play-developer-notifications@system.gserviceaccount.com` geben
   (Rolle *Pub/Sub Publisher*)
3. **Push-Abo** auf das Thema mit dieser URL:

```
https://flexr.social/api/billing/google/notifications/<GEHEIMNIS>
```

`<GEHEIMNIS>` erzeugst du selbst, z. B. `openssl rand -hex 24`, und trägst es
ein:

```
GOOGLE_NOTIFICATIONS_TOKEN=<GEHEIMNIS>
```

4. Play Console → **Monetarisieren → Monetarisierungseinstellungen** → Thema
   eintragen

---

## D — App Store Connect: Abo anlegen und aktivieren

### D1. Voraussetzung

**Vereinbarungen, Steuern und Bankverbindung** → der *Paid Applications*-Vertrag
muss auf **Aktiv** stehen. Ohne ihn lässt sich kein Abo einreichen.

### D2. Abo-Gruppe und Produkt

1. App Store Connect → **Meine Apps → FLEXR → Abos**
2. **Abo-Gruppe erstellen**, z. B. `FLEXR Premium`
3. In der Gruppe: **Abo erstellen**
4. Referenzname: `FLEXR Premium Monatlich`
5. **Produkt-ID: `social.flexr.premium.monthly`** — exakt so, **unveränderlich**
6. Dauer: **1 Monat**
7. Preis: Apple rechnet in eigenen Preisstufen — **9,99 € statt 10,00 €** ist
   die übliche Stufe. Das ist in Ordnung und rechtlich abgedeckt: AGB Punkt 9 f
   sagt, dass bei einem In-App-Kauf der im Store angezeigte Preis gilt.
8. **Lokalisierung** (Deutsch, Englisch): Anzeigename und Beschreibung
9. **Überprüfungsinformationen**: Screenshot des Kauf-Bildschirms und ein
   kurzer Hinweis für den Prüfer

### D3. Serverseitig freischalten

```
APPLE_SUBSCRIPTION_PRODUCT_ID=social.flexr.premium.monthly
```

`sudo systemctl restart flexr-api` — **ab hier erscheint der Kauf-Knopf in der
iOS-App**, ohne neuen Build.

Bei Apple braucht es **kein Dienstkonto**: Ein StoreKit-Beleg trägt seine
Zertifikatskette selbst und wird gegen Apples Wurzelzertifikat geprüft, das im
Repository liegt.

### D4. Mit der App einreichen

**Wichtig für die Reihenfolge:** Ein neues Abo wird beim **ersten Mal**
zusammen mit einer App-Version geprüft. Lege es also an, **bevor** du die
nächste Version einreichst, und wähle es beim Einreichen unter *In-App-Käufe*
mit aus. Sonst prüft Apple eine App ohne sichtbaren Kauf, und du brauchst eine
zweite Einreichung.

### D5. Optional: Server-Benachrichtigungen

App Store Connect → **App-Informationen → App Store Server Notifications**,
Produktions-URL:

```
https://flexr.social/api/billing/apple/notifications
```

Apple signiert diese Nachrichten; der Server prüft die Signatur. Deshalb ist
hier kein Geheimnis im Pfad nötig.

---

## Reihenfolge

~~1. **B** (APNs)~~ — erledigt am 17.09.2026.

Was noch offen ist, in dieser Reihenfolge:

1. **A** (Firebase) — danach Android neu bauen lassen, sonst wirken die vier
   Werte nicht
2. **C5 + C4** (Play: erst Dienstkonto, dann Produkt-ID)
3. **D2 + D3** (App Store: Produkt anlegen, dann freischalten)
4. Erst dann die nächste iOS-Version einreichen — mit dem Abo zusammen

A und C hängen beide am Android-Build: Es lohnt sich, sie zusammen zu erledigen
und **einmal** neu zu bauen statt zweimal.

## Was danach noch zu tun ist

* **Android neu bauen** mit den Firebase-Werten (Block A3). Der letzte Stand
  ist 2.7.1 (versionCode 112) und enthält den Push-Empfang schon — ohne die
  Firebase-Werte bleibt er aber wirkungslos.
* ~~**iOS neu bauen**~~ — am 17.09.2026 erledigt, der Build mit der
  Push-Berechtigung lief nach Block B1 durch.
* **Testen**: Zwei Geräte, eine Nachricht. Kommt sie sofort an, läuft Push.
  Zum Testen des Kaufs braucht es bei Apple ein Sandbox-Konto, bei Google einen
  Lizenztester (Play Console → Einstellungen → Lizenztests).

## Falls etwas nicht geht

Der Server protokolliert jeden Fehlversuch mit Grund:

```bash
ssh flexr-vps 'journalctl -u flexr-api -n 100 --no-pager | grep -iE "push|apns|fcm|store"'
```

Prüfen, was der Server für eingerichtet hält:

```bash
ssh flexr-vps 'cd /flexr/backend && venv/bin/python -c "
from app import push
from app.config import settings
print(\"FCM:\", push.configured(), \"| APNs:\", push.apns_configured())
print(\"Apple-Produkt:\", settings.apple_subscription_product_id or \"(leer)\")
print(\"Google-Produkt:\", settings.google_subscription_product_id or \"(leer)\")
"'
```
