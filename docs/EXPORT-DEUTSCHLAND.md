# Ablaufplan: FLEXR für Deutschland öffnen

Stand: 03.11.2026. Grundlage ist eine Durchsicht des Codes (Backend, Web,
Android, iOS, SEO-Generator, Rechtstexte). Reihenfolge = Abhängigkeiten:
Was weiter unten steht, setzt das Obere voraus.

## Umsetzungsstand (03.11.2026)

| Phase | Stand |
|---|---|
| 1 Daten/Backend | ✅ 8.211 deutsche PLZ (Großkunden-/Postfach-PLZ ausgefiltert), Migrationen `f4d9b2e6a8c1` (PLZ 5-stellig) und `b8d4f0a2c6e3` (deutsche Gyms aus OSM, nur mit vollständiger Adresse) |
| 2 Web/Admin | ✅ inkl. Schutz gegen veraltete Antworten bei 4 getippten Ziffern |
| 3 Apps | ✅ Code; Android 2.7.42 / 154 gebaut und signiert (`release-2.7.42/`), Store-Texte DE/EN fertig — **Hochladen macht der Nutzer**, iOS 2.4.17 ungebaut (kein Mac) |
| 4 Recht | ✅ Kündigungsbutton (§ 312k BGB), AGB, Widerruf, Impressum, Datenschutz, Nutzungsrichtlinien, Sicherheit — DE/EN und App-Kopien. Offen: Umsatzsteuer (LEGAL_REVIEW DE-01) |
| 5 Website/SEO | ✅ Landingpage, FAQ, Hub, Stadtseiten Berlin, Hamburg, München, Köln, Frankfurt |
| 6 Abschluss | ✅ Tests (812 Backend, 90 Android, Journey-Test `test_journey_deutschland.py`), Deploy `8f2510b` |

**Gym-Daten:** 2.073 Studios aus 69 Großstädten. Der Overpass-Dienst war
überlastet; nicht mehr abgerufen wurden Recklinghausen, Erlangen, Bergisch
Gladbach, Remscheid, Jena, Trier, Salzgitter, Moers, Siegen, Hildesheim,
Gütersloh, Cottbus, Kaiserslautern, Witten, Hanau, Schwerin, Ludwigsburg,
Esslingen, Gera, Iserlohn, Düren, Tübingen, Flensburg, Zwickau, Gießen,
Ratingen, Konstanz, Villingen-Schwenningen und Worms (ab Recklinghausen, die
Liste ist nach Einwohnerzahl sortiert). Nachholen: Abrufskript erneut
laufen lassen, `tools/gyms/build_gyms_de.py`, dann eine **neue** Migration nach
dem Muster von `b8d4f0a2c6e3` (die bestehende überspringt schon vorhandene
Name/PLZ-Paare, ist also auch erneut ausführbar).

**Bewusst nicht gemacht:** OSM-Studios ohne Adresse (rund 40 % der Treffer)
sind nicht per Rückwärts-Geokodierung ergänzt worden — eine geratene
Hausnummer wäre schlechter als ein fehlendes Studio, das Nutzer vorschlagen
können. Store-Einträge (Verfügbarkeit Deutschland, Name „… Österreich“) liegen
beim Nutzer (LEGAL_REVIEW DE-03).

**Leitgedanke:** Deutsche PLZ haben 5 Stellen, österreichische 4. Damit gibt
es keine Überschneidung, und das Land lässt sich eindeutig aus der PLZ
ablesen. Alles, was heute „genau 4 Ziffern“ prüft, muss „4 oder 5“ lernen —
und das Backend muss das **vor** den Apps können, weil alte App-Versionen
noch monatelang im Umlauf sind.

---

## Phase 1 — Daten und Backend (Fundament)

| # | Aufgabe | Wo | Bemerkung |
|---|---|---|---|
| 1.1 | Deutsche PLZ-Koordinaten und Ortsnamen ergänzen (~8.200 PLZ) | `backend/app/data/plz_coords.json`, `plz_cities.json`, Erzeugerskript | GeoNames DE (CC BY 4.0), Lizenzhinweis im Modulkopf `geo.py` und in der Datenschutz-/Impressumsseite wie bei AT |
| 1.2 | Hilfsfunktion `land_fuer_plz()` (4 → AT, 5 → DE) | `backend/app/geo.py` | eine Stelle, alle anderen fragen hier |
| 1.3 | Schema-Validierung `^\d{4}$` → `^\d{4,5}$` | `schemas.py` (4 Stellen), `routers/geo.py` | Fehlermeldungen „österreichische PLZ“ neutralisieren |
| 1.4 | Alembic-Migration: `users.plz`, `gyms.plz` von `VARCHAR(4)` auf `VARCHAR(5)` | `models.py`, neue Migration | Postgres schneidet nicht ab, sondern lehnt ab — ohne Migration scheitert jede deutsche Registrierung mit 500 |
| 1.5 | Ländercode der Zugriffsstatistik aus der PLZ statt konstant `"AT"` | `security.py:192`, Admin-Dashboard | |
| 1.6 | Gym-Seed Deutschland | `data/gyms_seed.json` + Datenmigration | siehe Entscheidung A |
| 1.7 | Tests: deutsche PLZ, Umkreis über die Grenze (Salzburg ↔ Freilassing), Migration | `backend/tests/` | |

## Phase 2 — Web-App und Admin

| # | Aufgabe | Wo |
|---|---|---|
| 2.1 | PLZ-Felder `maxlength="4"` → 5, Regex `^\d{4}$` → `^\d{4,5}$` (Registrierung, Konto, Gym-Vorschlag, Gym-Suche `near`) | `frontend/app/index.html` (3 Felder, 7 Prüfungen) |
| 2.2 | Platzhalter „1010“ → neutral (z. B. „PLZ“) | dito |
| 2.3 | App-Texte mit „Österreich“ anpassen (10 Stellen DE/EN) | `frontend/app/i18n-app.js`, `index.html` |
| 2.4 | Admin: Gym-Bearbeitung akzeptiert 5-stellige PLZ, Länderspalte in der Statistik | `frontend/admin.js` |

**Hinweis:** Das Konto-PLZ-Feld liegt in `#screen-account` — im August war
dieser Bildschirm eingefroren. Vor dem Anfassen kurz bestätigen, dass das
nicht mehr gilt.

## Phase 3 — Android und iOS (neue App-Versionen)

| # | Aufgabe | Wo |
|---|---|---|
| 3.1 | PLZ-Prüfung 4 → 4/5 | `PlzRepository.kt`, `GymRepository.kt`, `GymPicker.kt` |
| 3.2 | Texte „Österreich“ (je 4 DE/EN) | `res/values*/strings.xml` |
| 3.3 | iOS dito | `PlzRepository.swift`, `PostalCodeField.swift`, `FlexrStrings+*.swift`, `PaywallView.swift`, `LegalContent.swift`, `AccountModel.swift` |
| 3.4 | `versionName`/`versionCode` bzw. iOS-Version hochzählen, bauen | |
| 3.5 | Store-Seiten: Verfügbarkeit Deutschland, Beschreibung, Screenshots | Play Console / App Store Connect — **macht der Nutzer** |

Alte App-Versionen lassen weiterhin nur 4 Stellen zu → Deutsche können sich
erst mit dem Update registrieren (oder im Web). Kein Sackgassen-Risiko, aber
bei der Landingpage-Bewerbung zeitlich beachten.

## Phase 4 — Rechtstexte (deutsches Verbraucherrecht)

Wer seine Tätigkeit auf Deutschland ausrichtet, muss deutschen Verbrauchern
deren zwingenden Schutz gewähren (Art. 6 Rom-I). Die AGB sagen das schon
(Punkt 21 b) — die Texte selbst sind aber durchgehend österreichisch.

| # | Aufgabe | Wo | Gewicht |
|---|---|---|---|
| 4.1 | **Kündigungsbutton nach § 312k BGB**: gut sichtbarer Link „Verträge hier kündigen“ → Bestätigungsseite „Jetzt kündigen“, ohne Login erreichbar, mit Eingangsbestätigung per Mail | neue Seite + Backend-Endpunkt, Footer aller Seiten | **Pflicht**, abmahnfähig. Für Store-Abos genügt der Verweis auf den Store |
| 4.2 | Widerrufsbelehrung: Begriffe „Rücktritt/FAGG“ um deutsche Fassung („Widerruf“, §§ 312g, 355, 356 Abs. 4/5 BGB) ergänzen, Muster-Widerrufsformular passt | `widerruf.html`, `agb.html` 13, Consent-Text § 10 FAGG ↔ § 356 Abs. 4 BGB | Pflicht |
| 4.3 | AGB: Geltungsbereich „in Österreich“ → „Österreich und Deutschland“, Gerichtsstand (§ 14 KSchG + deutsches Pendant), Vertragsverlängerung nach § 309 Nr. 9 BGB prüfen (monatlich kündbar → passt) | `agb.html` 1, 21 | Pflicht |
| 4.4 | Impressum: Hinweis „§ 5 DDG“ ergänzen (neben § 5 ECG / § 25 MedienG); bei redaktionellen Artikeln (Date-Ideen, Gym-Crush) Verantwortlicher nach § 18 Abs. 2 MStV | `impressum.html` | Pflicht |
| 4.5 | Datenschutz: Beschwerderecht auch bei der deutschen Aufsichtsbehörde des Wohnorts erwähnen | `datenschutz.html` 10 | empfohlen |
| 4.6 | DSA/Nutzungsrichtlinien: Koordinator (bleibt KommAustria — Sitzland), Hilfsangebote DE ergänzen (z. B. Hilfetelefon), Anzeige bei „zuständigen Behörden“ statt nur österreichischen | `nutzungsrichtlinien.html`, `sicherheit.html` | empfohlen |
| 4.7 | `LEGAL_REVIEW.md` um DE-Punkte ergänzen | | |
| 4.8 | **Umsatzsteuer** — siehe Entscheidung D | kein Code | Steuerberatung |

Leitsatz aus dem Audit gilt weiter: Der Text beschreibt nur, was der Code
wirklich tut.

## Phase 5 — Website-Texte, SEO, Marketing

| # | Aufgabe | Wo |
|---|---|---|
| 5.1 | Landingpage: Hero „in Österreich“, Meta/OG/Twitter/JSON-LD, USP „am anderen Ende Österreichs“, FAQ „jede österreichische PLZ“ | `index.html`, `i18n-landing.js` (33 Stellen), `faq.html` |
| 5.2 | Musterprofile: einige mit deutschen Städten/Studios (Berlin, München, Hamburg) | `index.html` Deck |
| 5.3 | SEO-Stadtseiten Deutschland (Berlin, Hamburg, München, Köln, Frankfurt, …) | `tools/seo/build_seo_pages.py` `STAEDTE`; `gyms_abrufen()` startet bei Ziffer 1 und bricht bei 4 Stellen ab → für DE mit 0 beginnen, 5 Stellen |
| 5.4 | Hub-Seite „Gym-Dating in Österreich“ → DACH bzw. eigene DE-Hubseite | `gym-dating.html` via Generator |
| 5.5 | `sitemap.xml`, Footer-Links, englische Fassung neu bauen | `build-en.py`, Generator |
| 5.6 | Kinderschutz-/App-Titel „FLEXR – Gym Dating Österreich“ | `kinderschutz.html`, Stores |
| 5.7 | Optional: `hreflang="de-AT"`/`de-DE` | nur falls getrennte Seiten |

## Phase 6 — Abschluss

1. Alle Backend-Tests (`AWS_MAX_ATTEMPTS=1 … pytest`), `tools/check_betreiber.py`, Generator-Tests.
2. Dev-Server: Registrierung mit 10115 Berlin, Gym-Suche mit `near`, Umkreis Salzburg ↔ Bayern.
3. Deploy (Migration auf dem VPS!) — nur nach Freigabe.
4. Live-Prüfung mit `curl` und Browser.

---

## Entscheidungen vor dem Start

**A — Gym-Daten Deutschland.** Deutschland hat rund 10.000 Studios.
Empfehlung: OpenStreetMap (`leisure=fitness_centre`, ODbL, Quellenhinweis
nötig) für alle Großstädte importieren und bereinigen, Rest über die
bestehende „Gym vorschlagen“-Funktion. Alternative: nur große Ketten.

**B — Positionierung.** „Dating für Gym-People in Österreich und
Deutschland“ vs. „im DACH-Raum“ (Schweiz würde 4-stellige PLZ bringen, die
mit Österreich kollidieren — dann bräuchte es eine Länderspalte statt
Ableitung aus der Stellenzahl).

**C — Startgebiet.** Ganz Deutschland auf einmal oder zuerst grenznahe
Regionen/Großstädte (München, Berlin)?

**D — Umsatzsteuer.** Österreichische Kleinunternehmerregelung gilt für
Inlandsumsätze. Für digitale Leistungen an deutsche Verbraucher gilt bis
10.000 € EU-Auslandsumsatz pro Jahr das österreichische System, darüber
deutsche USt 19 % über OSS. Vor dem Start mit Steuerberatung klären — betrifft
Preisangaben (Bruttopreis) und Impressum.
