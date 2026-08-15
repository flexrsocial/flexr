# Alters- und Identitätsprüfung — Datenschutzrechtliche Bewertung

**Stand:** 15.08.2026
**Verantwortlicher:** Julian Pachernegg, Einzelunternehmer, Betreiber von FLEXR
**Status:** interne Arbeitsgrundlage, **keine abschließende Rechtsberatung**

Dieses Dokument hält fest, was die Prüfung technisch tut, warum sie stattfindet
und wo die rechtliche Bewertung offen ist. Es ist die Vorarbeit für eine
Schwellwertanalyse nach Art. 35 Abs. 1 DSGVO und für die Prüfung durch einen
Rechtsanwalt. Die offenen Punkte stehen zusätzlich in `LEGAL_REVIEW.md`.

---

## 1. Was tatsächlich passiert

Belegt durch `backend/app/verification_service.py`,
`backend/app/routers/verification.py`, `backend/app/routers/admin.py`,
`backend/app/storage.py` und `backend/app/models.py`.

| Schritt | Was geschieht | Wo im Code |
|---|---|---|
| 0 | Geburtsdatum bei der Registrierung, Alter serverseitig berechnet, unter 18 wird abgewiesen | `routers/auth.py`, `age.py` |
| 1 | E-Mail-Bestätigung per Aktivierungslink (Token nur als SHA-256-Hash) | `email_verification.py` |
| 2 | Ein Selfie, live über die Kamera aufgenommen, Presigned PUT direkt in den Objektspeicher | `routers/verification.py`, `storage.create_presigned_verification_upload` |
| 3 | Aufnahme eines amtlichen Lichtbildausweises, eigener privater Prefix `verification-documents/` | `storage.create_presigned_document_upload` |
| 4 | Serverseitige Prüfung von Größe und echten Magic Bytes | `storage.inspect_uploaded_image` |
| 5 | Ein Mensch sieht Profilfoto, Selfie und Ausweis nebeneinander und entscheidet | `routers/admin.py` |
| 6 | Bei Freigabe: `age_verified`, `activated_at`, Trial startet ab hier | `verification_service.activate_account` |
| 7 | Bilder werden gelöscht, Löschung wird verifiziert; scheitert sie, bleibt `cleanup_pending=True` | `verification_service.purge_uploads`, `storage.delete_objects_verified` |

### Was ausdrücklich **nicht** passiert

Geprüft durch Durchsicht von `backend/requirements.txt` und Volltextsuche über
`backend/app/`:

* keine Bibliothek für Gesichtserkennung, Gesichtsvergleich oder Embeddings
  (Abhängigkeiten sind ausschließlich FastAPI, SQLAlchemy, Alembic, Pydantic,
  jose, passlib, stripe, boto3, slowapi)
* keine OCR, keine Texterkennung, kein Auslesen der maschinenlesbaren Zone
* kein Speichern der Ausweisnummer, keine zweite Kopie des Geburtsdatums aus
  dem Dokument
* kein externer Identifizierungs- oder KYC-Dienstleister
* keine Rückseite des Dokuments (`DOCUMENT_TYPES_WITH_BACK` ist seit dem
  09.08.2026 leer — eine Aufnahme anzufordern, die niemand ansieht, wäre
  überschüssige Erhebung)

**Folgerung:** Es entstehen keine biometrischen Daten im Sinne des Art. 4 Z 14
DSGVO. Biometrische Daten setzen eine *technische Verarbeitung* voraus, die die
eindeutige Identifizierung ermöglicht; ein menschlicher Sichtvergleich ist das
nicht. Art. 9 Abs. 1 DSGVO greift für die Aufnahmen daher nicht über den
Umweg „biometrisch".

Ein Gesichtsbild bleibt trotzdem ein sensibler Personenbezug — die Bewertung
unten behandelt es entsprechend vorsichtig.

---

## 2. Zweck und Notwendigkeit

**Zweck.** Sicherstellen, dass ausschließlich Volljährige die Plattform nutzen,
und dass das Profil zur Person gehört.

**Warum das nicht optional ist.** FLEXR ist eine Dating-Plattform mit
Chatfunktion, Fotos und der Anbahnung persönlicher Treffen. Der Zugang
Minderjähriger ist hier kein Formalproblem, sondern das zentrale Risiko:
Grooming, Sexualisierung Minderjähriger, CSAM. Der Jugendschutz ist damit kein
Nebenzweck, sondern die Existenzbedingung des Dienstes.

**Warum eine reine Selbstauskunft nicht reicht.** Ein Datumsfeld, das ein
Minderjähriger in vier Sekunden umstellt, ist keine Altersprüfung. Der Code
zählt zwar Fehlversuche (`UnderageSignupAttempt`, ab dem zweiten Versuch
binnen 24 Stunden Sperre des Geräts), aber das erschwert das Durchprobieren
nur — es ersetzt keine Prüfung.

---

## 3. Geprüfte Alternativen

| Alternative | Bewertung |
|---|---|
| Nur Selbstauskunft | Verworfen. Kein Schutz, siehe oben. |
| Kreditkarte als Altersnachweis | Verworfen. Schließt Volljährige ohne Karte aus, sagt wenig über das Alter, und die Registrierung ist bewusst zahlungsmittelfrei. |
| Externer eID-/KYC-Dienst | Verworfen für den jetzigen Stand. Verlagert die sensibelsten Daten an einen weiteren Empfänger, erzeugt einen zusätzlichen Drittlandbezug und typischerweise echte biometrische Verarbeitung. Für einen Einzelunternehmer außerdem unverhältnismäßig teuer. **Erneut zu prüfen, sobald die Zahl der Prüfungen manuell nicht mehr zu bewältigen ist.** |
| Automatischer Gesichtsvergleich im eigenen Haus | Verworfen. Würde biometrische Daten nach Art. 9 erzeugen und damit die Eingriffstiefe deutlich erhöhen — ohne dass die Fehlerquote bei dieser Größenordnung besser wäre als ein Mensch. |
| **Manuelle Sichtprüfung, Bilder danach gelöscht** | **Gewählt.** Geringste Datenmenge, kein zusätzlicher Empfänger, keine biometrische Verarbeitung, kürzeste Speicherdauer. |

---

## 4. Datenminimierung

* Nur ein Selfie (bis 09.08.2026 waren es mehrere mit wechselnden Posen — der
  Liveness-Schutz wurde gestrichen, weil ohnehin ein Mensch entscheidet).
* Keine Rückseite des Dokuments.
* Schwärzen nicht benötigter Angaben ist ausdrücklich erlaubt und in der
  Oberfläche erwähnt.
* Der Objektschlüssel enthält weder Name noch Geburtsdatum noch E-Mail — nur
  die UUID des Vorgangs (`storage.document_object_key`).
* Vom Prüfgrund bleibt nur ein Wert aus einer festen Liste
  (`VerificationReviewReason`), kein Freitext. Das verhindert, dass Notizen zu
  Personen entstehen.
* Bei Registrierungsversuchen Minderjähriger wird nur festgehalten, **dass**
  einer stattfand — Geräte-ID und Zeitpunkt, sonst nichts.

---

## 5. Speicherdauer und Löschung

| Datum | Frist | Umsetzung |
|---|---|---|
| Selfie | sofort nach der Entscheidung | `purge_uploads` |
| Ausweisaufnahme | sofort nach der Entscheidung | `purge_uploads` |
| Ersetzte Aufnahme bei Neu-Upload | sofort | `purge_uploads` |
| Nie eingereichter Vorgang | spätestens 14 Tage | `cleanup.purge_stale_verification_uploads` |
| Bei Kontolöschung | sofort, ohne die 30-Tage-Karenz abzuwarten | `cleanup.purge_verification_uploads_for_user` |
| Prüfergebnis (Status, Grund, Zeitpunkte) | mit dem Konto | Cascade |

**Bemerkenswert und gut gelöst:** Die Löschung wird verifiziert
(`delete_objects_verified` prüft per `head_object` nach). Scheitert sie, gilt
der Vorgang nicht als abgeschlossen und wird erneut versucht. Das Admin-Dashboard
zeigt die Zahl offener Aufräumvorgänge (`pending_verification_cleanups`) — solange
sie über null liegt, liegen noch Ausweisbilder im Speicher.

**Offen:** Wie lange Sicherungskopien des Objektspeichers und der Datenbank
bestehen, ist nicht dokumentiert. Solange das nicht geklärt ist, darf die
Datenschutzerklärung nicht von „vollständiger und unwiderruflicher Löschung"
sprechen — sie tut es seit dem 15.08.2026 auch nicht mehr.
→ `LEGAL_REVIEW.md`, T-03.

---

## 6. Zugriff und Schutzmaßnahmen

* Ausweisaufnahmen liegen unter einem eigenen Prefix, **nicht** unter `users/`,
  das über die öffentliche Basis-URL erreichbar ist.
* Sie erhalten nie eine öffentliche URL. Zugriff nur über Signed URLs mit
  **60 Sekunden** Gültigkeit, ausgegeben ausschließlich an angemeldete Admins.
* Ein eigener Test stellt sicher, dass Dokumente keine öffentliche URL bekommen
  (`test_documents_never_get_a_public_url`).
* Das Admin-Login ist vom Nutzer-Login getrennt (eigene Tabelle, eigener
  Token-Scope).
* Größe und echtes Format werden serverseitig geprüft, nicht die Behauptung des
  Clients.

**Schwachstelle:** Für den Admin-Zugang gibt es **keine Zwei-Faktor-Authentifizierung**.
Wer das Admin-Passwort hat, sieht während offener Prüfungen Ausweisaufnahmen.
Bei derzeit einem Admin ist das Risiko überschaubar, aber es ist die
empfindlichste Stelle der ganzen Anwendung.
→ `LEGAL_REVIEW.md`, T-01.

---

## 7. Rechtsgrundlage — die eigentliche Änderung vom 15.08.2026

### Vorher

Die Datenschutzerklärung stützte die Prüfung auf **Art. 6 Abs. 1 lit. b und
lit. f** und holte „für die Aufnahmen von Gesicht und Ausweis zusätzlich eine
ausdrückliche Einwilligung" ein — mit dem Zusatz: „ohne sie kann der Account
nicht freigeschaltet werden."

### Warum das nicht tragfähig war

Eine Einwilligung, ohne die der Dienst überhaupt nicht nutzbar ist, ist nicht
freiwillig im Sinne des Art. 4 Z 11 DSGVO. Erwägungsgrund 43 sagt das
ausdrücklich. Eine so eingeholte „Einwilligung" ist unwirksam — und wer sich
auf sie stützt, steht ohne Rechtsgrundlage da. Der Zusatz machte die Sache
nicht besser, sondern dokumentierte den Mangel.

### Jetzt

Die Prüfung stützt sich auf:

* **Art. 6 Abs. 1 lit. c** — Erfüllung rechtlicher Verpflichtungen des
  Jugendschutzes und der Pflichten aus dem DSA (insbesondere Art. 28 DSA,
  Schutz Minderjähriger).
* **Art. 6 Abs. 1 lit. f** — berechtigtes Interesse an der Sicherheit der
  Plattform und dem Schutz der Nutzer.

Eine Einwilligung wird für die Prüfung **nicht mehr abgefragt**. Das ist
ehrlicher: Der Nutzer hat hier keine echte Wahl, also wird ihm auch keine
vorgespielt.

### Was als Einwilligung bleibt

Nur die Verarbeitung von Geschlecht und gesuchtem Geschlecht (Art. 9 Abs. 2
lit. a DSGVO) — dort ist die Einwilligung die einzig mögliche Grundlage, und
sie wird getrennt, versioniert und widerrufbar erfasst (`models.Consent`).

Auch hier bleibt eine Spannung: Ohne diese Angaben funktioniert das Matching
nicht. Die Datenschutzerklärung sagt das jetzt offen, statt den Widerruf als
folgenlos darzustellen.
→ `LEGAL_REVIEW.md`, D-05.

---

## 8. Risiken

| Risiko | Eintritt | Schaden | Maßnahme |
|---|---|---|---|
| Unbefugter Zugriff auf offene Ausweisaufnahmen | gering | **sehr hoch** | privater Prefix, 60-Sekunden-Links, getrenntes Admin-Login. **Offen: MFA** |
| Ausweisbild wird nicht gelöscht | gering | hoch | verifizierte Löschung, `cleanup_pending`, Anzeige im Dashboard, erneuter Versuch beim Login |
| Fehlurteil des Prüfers (Minderjähriger durchgelassen) | mittel | sehr hoch | Sichtprüfung des Dokuments plus Sperre nach wiederholten Versuchen; keine weitere Absicherung |
| Prüfer sieht mehr, als er braucht | sicher | mittel | Schwärzen erlaubt, kein Auslesen, feste Prüfgründe statt Notizen |
| Sicherungskopien überdauern die Löschung | unbekannt | mittel | **ungeklärt**, siehe T-03 |

---

## 9. Braucht es eine DSFA nach Art. 35 DSGVO?

**Einschätzung: wahrscheinlich ja. Extern zu bestätigen.**

Argumente dafür:

* Es werden Daten verarbeitet, aus denen sich die **sexuelle Orientierung**
  ergibt (Art. 9), zusammen mit Gesichtsbildern und einem amtlichen Dokument.
* Die Verarbeitung erfolgt **systematisch und umfassend** für alle Nutzer.
* Betroffen sind Daten, deren Offenlegung erheblichen Schaden anrichten kann —
  eine Dating-Plattform mit Orientierungsbezug ist ein klassisches
  Hochrisikofeld.
* Die Liste der DSB zu Art. 35 Abs. 4 DSGVO nennt Verarbeitungen besonderer
  Kategorien in großem Umfang.

Argumente dagegen:

* Die Datenmenge ist gering, die Speicherdauer der sensibelsten Daten sehr kurz.
* Kein Profiling, keine automatisierte Entscheidung, keine Zusammenführung mit
  externen Quellen.
* Der Nutzerbestand ist derzeit klein — „in großem Umfang" ist fraglich.

**Empfehlung:** Vor einem nennenswerten Wachstum eine DSFA durchführen. Dieses
Dokument liefert die Bausteine dafür (Beschreibung, Notwendigkeit, Alternativen,
Risiken, Maßnahmen). Was fehlt, ist die formale Bewertung und die Konsultation
nach Art. 36, falls das Restrisiko hoch bleibt.
→ `LEGAL_REVIEW.md`, D-06.

---

## 10. Offene Punkte

| Nr. | Punkt | Wer |
|---|---|---|
| D-05 | Ist der Aufbau der Art.-9-Einwilligung tragfähig, obwohl das Matching ohne sie nicht funktioniert? | Rechtsanwalt |
| D-06 | DSFA erforderlich? Wenn ja, formal durchführen | Rechtsanwalt / Julian |
| D-07 | Trägt Art. 6 Abs. 1 lit. c die Prüfung, oder ist lit. f allein sauberer? | Rechtsanwalt |
| T-01 | MFA für den Admin-Zugang | Julian / Technik |
| T-03 | Aufbewahrungsdauer der Sicherungskopien feststellen und dokumentieren | Julian |
| T-02 | Zugriffsprotokoll für Ausweisansichten (wer hat wann welches Dokument geöffnet) | Technik |

---

*Dieses Dokument beschreibt den Stand vom 15.08.2026 und ist bei jeder Änderung
am Prüfverfahren mitzuziehen.*
