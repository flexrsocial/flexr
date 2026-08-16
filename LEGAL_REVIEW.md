# LEGAL_REVIEW — was Julian noch klären muss

**Angelegt:** 15.08.2026, im Zuge des SEO-, Rechts- und DSA-Audits.

Hier stehen **ausschließlich** Punkte, die sich nicht aus dem Code beantworten
lassen: Auskünfte, die nur Julian hat, Verträge, die nur er einsehen kann, und
rechtliche Bewertungen, die ein Anwalt treffen muss.

**Was hier nicht steht:** technische Fehler. Die sind im Audit behoben worden.
Wo eine technische Aufgabe doch auftaucht (T-Nummern), hängt sie an einer
Auskunft oder an einem Zugang, den nur Julian hat.

**Wichtig:** Solange ein Punkt offen ist, behauptet der Rechtstext an dieser
Stelle nichts. Die Aussagen, die nicht belegbar waren, sind entfernt worden —
nicht abgeschwächt. Wer einen Punkt klärt, trägt die Antwort ein **und** zieht
den betreffenden Rechtstext nach.

---

## L — Impressum und Gewerberecht

### L-01 · Gewerbeberechtigung
**Offen.** Wortlaut der Gewerbeberechtigung ist im Repository nirgends belegt.
**Nötig:** Gewerberegisterauszug oder Gewerbeschein ansehen und den genauen
Wortlaut eintragen.
**Wirkt sich aus auf:** `frontend/impressum.html`, Abschnitt „Gewerberechtliche
Angaben" (dort steht derzeit ein `TODO_LEGAL`-Kommentar, sichtbar ist nur der
Verweis auf die GewO).
**Warum es zählt:** § 5 Abs. 1 Z 6 ECG verlangt Angaben zu berufsrechtlichen
Vorschriften; ohne Kenntnis der Berechtigung lässt sich das nicht ausfüllen.

### L-02 · Zuständige Gewerbebehörde
**Offen.** Für 8232 Grafendorf ist die Bezirksverwaltungsbehörde zuständig;
welche genau, wurde bewusst **nicht** geraten.
**Nötig:** Bei der Gemeinde oder der WKO erfragen und eintragen.
**Wirkt sich aus auf:** `frontend/impressum.html`.

### L-03 · WKO-Zugehörigkeit
**Offen.** Fachgruppe bzw. Fachverband unbekannt.
**Nötig:** WKO-Mitgliedsbestätigung ansehen.
**Wirkt sich aus auf:** `frontend/impressum.html`.

### L-04 · § 14 UGB — bestätigen, dass keine Firmenbucheintragung besteht
**Angenommen: keine Eintragung.** Der Verweis auf § 14 UGB stand bisher im
Impressum, ist aber am 15.08.2026 entfernt worden: Die Vorschrift richtet sich
an *eingetragene* Unternehmer.
**Nötig:** Bestätigen, dass tatsächlich keine Eintragung besteht. Falls doch:
Verweis, Firmenbuchnummer und Firmenbuchgericht wieder aufnehmen.
**Wirkt sich aus auf:** `frontend/impressum.html`, `shared/betreiber.json`
(Feld `im_firmenbuch`).

### L-05 · Kleinunternehmerregelung
**Angenommen: trifft zu.** Steht als *umsatzsteuerliche* Angabe im Impressum,
nicht mehr als „Rechtsform".
**Nötig:** Jährlich prüfen, ob die Umsatzgrenze noch eingehalten wird, und ob
tatsächlich keine UID vergeben ist. Bei Überschreitung müssen Preisangaben
(brutto/netto) und Rechnungen angepasst werden.
**Wirkt sich aus auf:** `frontend/impressum.html`, `frontend/agb.html` (Punkt 9),
`shared/betreiber.json`.

### L-06 · Anschrift als Geschäftsanschrift
**Hinweis, keine Frage.** Johann-Schrey-Weg 260 ist eine Privatadresse, steht
aber nach § 5 ECG und § 25 MedienG zwingend im Impressum.
**Zu bedenken:** Falls das stört, hilft nur eine Geschäftsadresse (etwa über
einen Bürodienstleister). Ein Weglassen ist keine Option.

---

## D — Datenschutz

### D-01 · Cloudflare R2: Jurisdiktion statt Standort-Hinweis
**Kritisch. Aussage wurde entfernt.**

Die Datenschutzerklärung behauptete: *„Eastern Europe (EEUR) — EU, kein
Drittstaatentransfer."* Aus dem Repository nicht belegbar:
`backend/.env.example` nennt `https://<account-id>.r2.cloudflarestorage.com` —
das ist der **Standard-Endpunkt ohne Jurisdiktion**. Ein Bucket mit echter
EU-Jurisdiktion spricht `https://<account-id>.eu.r2.cloudflarestorage.com` an.

Cloudflare unterscheidet:
* **Location Hint** (`eeur`) — ein *Wunsch*, wo die Daten bevorzugt liegen
  sollen. Keine Zusicherung.
* **Jurisdiction** (`eu`) — eine vertragliche Bindung, dass die Daten die EU
  nicht verlassen.

**Nötig:**
1. In der Cloudflare-Konsole nachsehen, wie der Bucket `flexr-photos`
   tatsächlich angelegt wurde: Jurisdiction oder nur Location Hint?
2. Den produktiven `S3_ENDPOINT_URL` in `/flexr/backend/.env` auf dem VPS
   ansehen — enthält er `.eu.`?

**Falls nur Location Hint:** Migration auf einen EU-Jurisdiction-Bucket. Ein
Bucket lässt sich **nicht** nachträglich umstellen; es braucht einen neuen.
Migrationsplan siehe unten.
**Wirkt sich aus auf:** `frontend/datenschutz.html`, Punkt 6.

#### Migrationsplan (nur ausführen, wenn D-01 ergibt: keine EU-Jurisdiktion)

Keine Daten verschieben oder löschen, ohne die Integrität sicherzustellen.
Reihenfolge:

1. Neuen Bucket mit `jurisdiction=eu` anlegen, etwa `flexr-photos-eu`.
2. Bestand kopieren, nicht verschieben — `rclone copy` oder `aws s3 sync` gegen
   beide Endpunkte. Der alte Bucket bleibt unangetastet.
3. **Abgleich vor dem Umschalten:** Objektzahl und Gesamtgröße beider Buckets
   vergleichen. Zusätzlich stichprobenartig ETags prüfen. Erst bei
   Übereinstimmung weiter.
4. Wartungsfenster: neue Uploads kurz anhalten (der einfachste Weg ist, den
   API-Dienst zu stoppen), damit während des letzten Abgleichs nichts entsteht.
5. Letzten Abgleich fahren (`sync` erneut, sollte nichts mehr finden).
6. `S3_BUCKET_NAME` und `S3_ENDPOINT_URL` in `/flexr/backend/.env` umstellen,
   Dienst neu starten.
7. **Seit dem 16.08.2026 anders als hier ursprünglich beschrieben:** Es gibt
   keine öffentliche R2-Domain mehr umzuhängen. `S3_PUBLIC_BASE_URL` zeigt auf
   den eigenen Ursprung (`https://flexr.social/photos`); ausgeliefert wird
   über die Location `/photos/` in `deploy/nginx-flexr.conf`, die serverseitig
   an den tatsächlichen R2-Host weiterreicht (`proxy_pass`,
   `proxy_set_header Host`). **Diese beiden Zeilen auf den neuen Bucket-Host
   umstellen und `nginx -t` vor dem Reload.** Die Objektschlüssel bleiben
   gleich, deshalb bleiben alle in der Datenbank gespeicherten URLs gültig -
   sie zeigen ja weiterhin auf `/photos/…`, unabhängig davon, welcher Bucket
   dahintersteht. `tools/check_csp_hosts.py` danach laufen lassen.
8. Eine Woche beobachten. Erst dann den alten Bucket löschen, nicht früher.
9. `frontend/datenschutz.html`, Punkt 6 aktualisieren — dann darf die
   EU-Aussage wieder hinein.

**Fallstrick:** Der Prefix `verification-documents/` muss mitwandern. Er liegt
im selben Bucket, ist aber der sensibelste Teil.

### D-02 · Auftragsverarbeitungsverträge
**Aussage wurde entfernt.** Die Erklärung behauptete pauschal: *„Mit allen
Auftragsverarbeitern bestehen Auftragsverarbeitungsverträge (Art. 28 DSGVO)."*
Im Repository ist kein einziger belegt.

**Nötig — je Anbieter prüfen und ablegen:**

| Anbieter | Wofür | Was zu prüfen ist |
|---|---|---|
| Contabo GmbH | VPS, Datenbank | AVV abgeschlossen? Contabo bietet einen zum Download an. |
| Cloudflare | R2, Fotos und Ausweisaufnahmen | Cloudflare DPA gilt idR automatisch über die Self-Serve-Bedingungen — Fassung und Datum festhalten. |
| Stripe | Zahlungen | Siehe D-03 — Stripe ist nicht durchgehend Auftragsverarbeiter. |
| Twilio | SMS | Nur relevant, wenn die Telefonprüfung produktiv genutzt wird. |
| SMTP-Anbieter | E-Mail | Steht noch nicht fest (siehe T-06). |

Erst wenn alle vorliegen, darf die Aussage zurück in
`frontend/datenschutz.html`.

### D-03 · Stripe — Rollen und Vertragspartner
**Aussage abgeschwächt.** Bisher stand dort schlicht „USA/EU,
Standardvertragsklauseln (SCC)". Das ist zu grob.

**Nötig:**
1. Welche Stripe-Gesellschaft ist Vertragspartner? Bei Nutzern in Österreich
   üblicherweise **Stripe Payments Europe, Ltd.** (Irland) — im Stripe-Dashboard
   unter den Vertragsbedingungen nachsehen.
2. Stripe ist für Teile der Verarbeitung **eigener Verantwortlicher**, nicht
   Auftragsverarbeiter (Betrugsprävention, gesetzliche Pflichten). Die
   Erklärung sollte das benennen, statt Stripe pauschal als
   Auftragsverarbeiter zu führen.
3. Ist Stripe unter dem EU-US Data Privacy Framework zertifiziert? Falls ja,
   ist das der Übermittlungsmechanismus, nicht SCC.
4. Festhalten, welche Daten tatsächlich fließen. Aus dem Code:
   FLEXR **sendet** die E-Mail-Adresse (`customer_email`) und die Nutzer-ID
   (`client_reference_id`); FLEXR **erhält** zurück Kunden-ID, Abo-ID und
   Abostatus. Kartendaten berührt FLEXR nie.

**Wirkt sich aus auf:** `frontend/datenschutz.html`, Punkt 6.

### D-04 · Übermittlungsmechanismen belegen
**Nötig:** Für jeden Anbieter mit Drittlandbezug festhalten, worauf sich die
Übermittlung stützt (Angemessenheitsbeschluss / SCC / Ausnahme). Die Erklärung
verspricht derzeit, den Mechanismus auf Anfrage zu nennen — dafür muss er
bekannt sein.

### D-05 · Art.-9-Einwilligung: ist der Aufbau tragfähig?
**Rechtliche Bewertung nötig.** Ohne Geschlecht und gesuchtes Geschlecht
funktioniert das Matching nicht. Die Einwilligung ist damit faktisch
Voraussetzung der Nutzung — die klassische Konstellation, in der die
Freiwilligkeit angezweifelt wird (Art. 4 Z 11, ErwG 43).

Was am 15.08.2026 verbessert wurde: getrennte Abfrage, Versionierung, Widerruf
mit einem Klick im Konto, und eine ehrliche Beschreibung dessen, was der
Widerruf bewirkt (leeres Deck statt „kein Problem").

**Offen:** Ob das genügt, oder ob es eine Nutzungsvariante ohne
orientierungsbezogenes Matching geben müsste.
**Zuständig:** Rechtsanwalt.

### D-06 · Datenschutz-Folgenabschätzung
**Wahrscheinlich erforderlich.** Vorarbeit liegt vollständig vor in
`docs/privacy/age-verification-assessment.md`, Abschnitt 9.
**Zuständig:** Rechtsanwalt, dann Julian für die Durchführung.

### D-07 · Rechtsgrundlage der Altersprüfung
Am 15.08.2026 von „lit. b + lit. f + zusätzliche Einwilligung" auf
**Art. 6 Abs. 1 lit. c und lit. f** umgestellt. Grund: Eine Einwilligung, ohne
die der Dienst nicht nutzbar ist, ist keine.
**Zu bestätigen:** Trägt lit. c (Jugendschutz, Art. 28 DSA) hier, oder ist lit. f
allein die sauberere Konstruktion?
**Zuständig:** Rechtsanwalt.

---

## V — Verbraucherrecht

### V-01 · Trial-Modell — Feststellung, keine Frage
**Geklärt, hier nur zur Bestätigung.** Der Code wurde geprüft:

* `RegisterRequest` kennt **kein** Zahlungsmittelfeld.
* `User.trial_ends_at` ist ein reines Datenbankfeld.
* Ein Stripe-Vorgang entsteht ausschließlich über
  `POST /api/billing/checkout`, ausgelöst durch „Jetzt abonnieren".
* Nach Ablauf liefert der Server 402 und die App zeigt die Bezahlseite.

→ **Der Probemonat wandelt sich nicht automatisch in ein Abo um.** Sämtliche
Texte sind darauf umgestellt (FALL A).

**Zu bestätigen:** Dass das die gewollte Produktentscheidung ist und so bleiben
soll. Falls doch eine automatische Umwandlung geplant ist, müssen Checkout,
Bestellknopf und sämtliche Texte nach § 8 FAGG neu gebaut werden — dann bitte
vorher melden.

### V-02 · Rücktrittsbelehrung prüfen lassen
`frontend/widerruf.html` enthält Belehrung, Folgen und Muster-Formular,
angelehnt an die Anlage zum FAGG.
**Nötig:** Anwaltliche Durchsicht, insbesondere der Formulierung zum anteiligen
Wertersatz.

### V-03 · Online-Rücktrittsfunktion (§ 13a FAGG)
Umgesetzt und getestet (`backend/tests/test_widerruf.py`): öffentlich
erreichbar, getrennter Bestätigungsschritt, unverzügliche Bestätigung per
E-Mail mit Inhalt, Datum, Uhrzeit und Aktenzeichen.
**Nötig:**
1. Anwaltliche Prüfung, ob Ablauf und Bestätigungstext genügen.
2. **Der Bestätigungsversand hängt an SMTP** — solange kein Mailserver
   eingerichtet ist, landet die Bestätigung nur im Server-Log. Siehe T-06.
   Das ist der einzige Punkt, an dem die Funktion derzeit unvollständig ist.
3. Die Pflicht gilt ab 01.10.2026; die Funktion ist bereits jetzt scharf.

### V-04 · Alter Rücktrittsverzicht — Bestandskunden
Bis 15.08.2026 musste bei jeder Registrierung erklärt werden, das
Rücktrittsrecht gehe verloren. Diese Erklärung wurde entfernt, und die AGB
(Punkt 13 d) sagen ausdrücklich, dass daraus kein Verzicht abgeleitet wird.
**Zu bedenken:** Ob Bestandskunden darüber aktiv informiert werden sollten.
**Zuständig:** Rechtsanwalt.

### V-05 · AGB insgesamt prüfen lassen
`frontend/agb.html` wurde vollständig neu gefasst (21 Abschnitte). Besonders
anzusehen:
* Punkt 18 (Änderungsklausel) — bewusst konservativ, wesentliche nachteilige
  Änderungen nur mit ausdrücklicher Zustimmung.
* Punkt 20 (Haftung) — Beschränkung auf den vertragstypisch vorhersehbaren
  Schaden.
* Punkt 14 e (Rechteeinräumung an Fotos).

---

## S — DSA

### S-01 · Einstufung als Kleinstunternehmen
Die Nutzungsrichtlinien führen FLEXR als Kleinstunternehmen im Sinne der
Empfehlung 2003/361/EG.
**Zu bestätigen:** Trifft zu (unter 10 Beschäftigte, Jahresumsatz und
Bilanzsumme je unter 2 Mio. €)?
**Wichtig:** Die Ausnahme des Art. 19 DSA befreit **nicht** von den Pflichten
für Hostingdiensteanbieter. Art. 11, 12, 14, 16, 17 und 18 gelten weiter und
sind umgesetzt — das steht so auch in den Nutzungsrichtlinien.

### S-02 · Provider-Klassifizierung
**Zu bestätigen:** FLEXR ist Hostingdiensteanbieter und Online-Plattform im
Sinne des Art. 3 lit. i DSA (Speicherung *und* öffentliche Verbreitung
nutzergenerierter Inhalte). Davon geht die Umsetzung aus.
**Zuständig:** Rechtsanwalt.

### S-03 · Meldung an den Koordinator für digitale Dienste
**Zu prüfen:** Ob und wie sich FLEXR bei der österreichischen
Koordinierungsstelle (KommAustria) registrieren bzw. melden muss.

---

## T — Technisch, aber nur von Julian lösbar

### T-01 · Zwei-Faktor-Authentifizierung für den Admin-Zugang
**Empfindlichste Stelle der Anwendung.** Wer das Admin-Passwort hat, sieht
während offener Prüfungen Ausweisaufnahmen. Derzeit nur Passwort.
**Nicht im Audit umgesetzt**, weil es eine Produktentscheidung ist (welcher
zweite Faktor? TOTP, WebAuthn?) und den Admin bei Fehlkonfiguration aussperrt.

### T-02 · Zugriffsprotokoll für Ausweisansichten
Derzeit wird nicht festgehalten, welcher Admin wann welches Dokument geöffnet
hat. Bei einem Admin verzichtbar, bei zweien nicht mehr.

### T-03 · Aufbewahrungsdauer der Sicherungskopien
**Ungeklärt.** Wie lange bestehen Datenbank-Backups und interne Kopien im
Objektspeicher? Solange das offen ist, darf die Datenschutzerklärung nicht von
„vollständiger und unwiderruflicher Löschung" sprechen — sie tut es seit dem
15.08.2026 auch nicht mehr, sondern beschreibt die Einschränkung offen.
**Nötig:** Feststellen und in `frontend/datenschutz.html`, Punkt 7 konkret
eintragen.

### T-04 · Aufbewahrungsdauer der Server-Logs
**Ungeklärt.** nginx und journald auf dem VPS protokollieren IP-Adressen. Wie
lange, ist nicht dokumentiert.
**Nötig:** logrotate-Einstellung ansehen, Frist festlegen (üblich sind 7 bis 14
Tage) und in der Datenschutzerklärung nennen.

### T-05 · Content-Security-Policy ohne `unsafe-inline`
`deploy/nginx-flexr.conf` setzt eine CSP, die für Skripte `'unsafe-inline'`
erlauben muss: Die App trägt rund 2500 Zeilen JavaScript inline in ihrer
`index.html`. Das sauber aufzulösen heißt, das Skript in eine eigene Datei zu
ziehen — eine eigene Aufgabe mit eigenem Testbedarf, nicht Teil dieses Audits.

### T-06 · SMTP einrichten
**Blockiert drei Dinge gleichzeitig:**
1. die E-Mail-Bestätigung (bekannt aus dem Übergabeprotokoll),
2. die Bestätigung der Rücktrittserklärung nach § 13a Abs. 4 FAGG,
3. die Empfangsbestätigung und die Entscheidung im DSA-Meldeverfahren.

Punkt 2 und 3 sind neu und rechtlich verbindlich. Ohne Mailversand erfüllt
FLEXR die Bestätigungspflichten nicht.
**Achtung:** Gmail kann nicht als `noreply@flexr.social` senden — die Domain
hat keinen MX-Eintrag.
**Zugangsdaten trägt nur Julian ein.**

### T-07 · nginx-Konfiguration auf dem VPS angleichen
`deploy/nginx-flexr.conf` wurde erweitert (Schutz-Header, kanonische Domain,
`/app/`-Route). Die auf dem VPS aktive Fassung ist eine andere und enthält die
von certbot eingefügten TLS-Direktiven.
**Nötig:** Vor dem Übernehmen vergleichen, nicht kopieren. Insbesondere:
* Die neue Route `location /app/ { try_files $uri $uri/ /app/index.html; }`
  wird gebraucht, damit Deep-Links in der App funktionieren.
* HSTS erst einschalten, wenn TLS sicher läuft.

---

## Erledigt im Audit — nur zur Kenntnis

Diese Punkte brauchen **keine** Rückmeldung, sie stehen hier, damit klar ist,
was schon behandelt ist:

* Rechtsträger überall auf Julian Pachernegg, Einzelunternehmer, umgestellt
  (7 HTML-Seiten, Android, iOS, Store-Texte). Gegen Rückfall gesichert durch
  `tools/check_betreiber.py` und `backend/tests/test_betreiber.py`.
* „Kleinunternehmerregelung" steht nicht mehr als Rechtsform, sondern unter
  Umsatzsteuer.
* § 14 UGB aus dem Impressum entfernt.
* Rücktrittsverzicht bei der Registrierung ersatzlos gestrichen (Formular,
  Schema, Datenbankspalte nullable, Migration).
* Sämtliche Trial-Texte auf „wird nicht automatisch kostenpflichtig" umgestellt.
* Google Fonts entfernt, Schriften liegen selbst gehostet unter `/fonts/`.
  Das war eine Drittlandübermittlung ohne Rechtsgrundlage und ohne Nennung.
* „Meine Meldungen" gibt es jetzt wirklich — `sicherheit.html` hatte die
  Ansicht versprochen, ohne dass sie existierte.
* Fotoablehnungen bekommen eine Begründung (vorher kommentarlos).
* Strafverfolgungsrichtlinien: „nicht ausweisgeprüft" korrigiert, ohne ins
  andere Extrem zu fallen; Notfallauskunft konservativer gefasst.
* Landingpage und App getrennt (`/` und `/app/`), Sitemap und robots.txt
  entsprechend.
