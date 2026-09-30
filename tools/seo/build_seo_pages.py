#!/usr/bin/env python3
"""Erzeugt die Such-Einstiegsseiten von flexr.social.

Warum es diese Seiten gibt: Die Landingpage kann nur fuer eine Handvoll
Suchbegriffe ranken ("FLEXR", "Dating fuer Gym-People"). Wer "Fitness Dating
Wien", "Gym Dating App" oder "Gym-Crush ansprechen" sucht, braucht eine eigene
Seite, die genau diese Frage beantwortet.

Warum sie trotzdem keine duennen "Doorway"-Seiten sind (die straft Google ab):
Jede Stadtseite traegt eigenen Inhalt - die tatsaechlich in FLEXR
auswaehlbaren Studios dieser Stadt (aus der oeffentlichen Gym-API), eigene
Ideen fuers erste Treffen vor Ort und eigene Fragen. Nichts davon ist
erfunden: keine Nutzerzahlen, keine Erfolgsversprechen - dieselbe Linie wie
auf der Landingpage.

    python3 tools/seo/build_seo_pages.py            # Seiten aus gyms.json bauen
    python3 tools/seo/build_seo_pages.py --refresh  # vorher Gyms live abrufen

`gyms.json` ist ein Schnappschuss von GET /api/gyms (nur freigegebene Studios
mit Adresse). Nach dem Bauen die geaenderten Seiten und sitemap.xml
committen; die Sitemap-Eintraege dieser Seiten schreibt das Skript selbst
(zwischen den Markern SEO-SEITEN-ANFANG/-ENDE).
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent
FRONTEND = HIER.parent.parent / "frontend"
GYMS = HIER / "gyms.json"
SITE = "https://flexr.social"
HEUTE = dt.date.today().isoformat()

WIEN_BEZIRKE = {
    "1010": "Innere Stadt", "1020": "Leopoldstadt", "1030": "Landstraße",
    "1040": "Wieden", "1050": "Margareten", "1060": "Mariahilf",
    "1070": "Neubau", "1080": "Josefstadt", "1090": "Alsergrund",
    "1100": "Favoriten", "1110": "Simmering", "1120": "Meidling",
    "1130": "Hietzing", "1140": "Penzing", "1150": "Rudolfsheim-Fünfhaus",
    "1160": "Ottakring", "1170": "Hernals", "1180": "Währing",
    "1190": "Döbling", "1200": "Brigittenau", "1210": "Floridsdorf",
    "1220": "Donaustadt", "1230": "Liesing",
}


# --------------------------------------------------------------------------
# Daten
# --------------------------------------------------------------------------

def gyms_abrufen() -> list[dict]:
    """Alle freigegebenen Gyms ueber die oeffentliche Suche einsammeln.

    Die API liefert hoechstens 30 Treffer je Anfrage - deshalb Postleitzahl
    fuer Postleitzahl. Eine volle Seite (30) waere ein Hinweis auf fehlende
    Treffer; dann bricht das Skript ab, statt still eine Luecke zu bauen.
    """
    gesehen: dict[str, dict] = {}
    # Alle 4-stelligen PLZ waeren ~8000 Anfragen - stattdessen mit der ersten
    # Ziffer anfangen und nur bei voller Seite eine Stelle genauer werden.
    def hole(q: str) -> list[dict]:
        time.sleep(0.1)
        url = f"{SITE}/api/gyms?q=" + urllib.parse.quote(q)
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.load(r)

    def sammle(prefix: str) -> None:
        treffer = hole(prefix)
        if len(treffer) == 30:
            if len(prefix) >= 4:
                sys.exit(f"FEHLER: PLZ {prefix} liefert 30 Treffer - Liste unvollstaendig")
            for ziffer in "0123456789":
                sammle(prefix + ziffer)
            return
        for g in treffer:
            gesehen[g["id"]] = g

    for erste in "123456789":
        sammle(erste)
    return sorted(gesehen.values(), key=lambda g: (g["plz"], g["name"].lower()))


def gyms_laden() -> list[dict]:
    return json.loads(GYMS.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Inhalte
# --------------------------------------------------------------------------

STAEDTE = [
    {
        "slug": "wien",
        "name": "Wien",
        "orte": ["Wien"],
        "umland": ["Purkersdorf", "Wiener Neudorf", "Mödling"],
        "umland_titel": "Rund um Wien",
        "intro": (
            "Wien ist die Stadt mit den meisten Fitnessstudios in Österreich – "
            "vom großen Kettenstudio am Gürtel bis zur kleinen Kraftsport-Box "
            "im Hinterhof. Genau deshalb ist das Gym in Wien ein guter "
            "Ausgangspunkt fürs Dating: Wer in Favoriten trainiert, hat einen "
            "anderen Alltag als jemand, der nach der Arbeit in der Inneren "
            "Stadt ins Studio geht."
        ),
        "radius": (
            "Wien ist kompakt: Schon mit wenigen Kilometern Umkreis erreichst "
            "du von deinem Studio aus mehrere Bezirke. Wer in einem "
            "Außenbezirk wie Floridsdorf, Donaustadt oder Liesing trainiert, "
            "stellt den Radius etwas größer ein – dann ist auch das Umland mit "
            "dabei."
        ),
        "dates": [
            ("Laufrunde in der Prater Hauptallee",
             "Flach, gerade, autofrei und gut besucht – ideal für ein erstes "
             "Treffen in Bewegung, bei dem man trotzdem reden kann."),
            ("Donauinsel",
             "Radfahren, Laufen, im Sommer schwimmen: Auf der Donauinsel gibt "
             "es genug Platz, und der nächste Imbiss ist nie weit."),
            ("Auf den Kahlenberg",
             "Vom Stadtrand zu Fuß hinauf, oben der Blick über die Stadt – ein "
             "Date mit eingebautem Workout."),
            ("Bouldern",
             "Wien hat mehrere Boulderhallen. Zu zweit Routen auszuknobeln "
             "bricht das Eis schneller als jedes Kaffeehaus."),
            ("Stand-up-Paddling an der Alten Donau",
             "Im Sommer ein Klassiker – und wer ins Wasser fällt, hat sofort "
             "eine gemeinsame Geschichte."),
        ],
        "faq": [
            ("Gibt es in Wien eine Dating-App speziell für Leute aus dem Fitnessstudio?",
             "Ja, FLEXR. Du wählst dein Wiener Studio aus einer Liste und "
             "siehst Profile von Leuten, die in Studios in deinem Umkreis "
             "trainieren. Die Nutzung ist dauerhaft kostenlos."),
            ("Muss ich im selben Studio trainieren wie mein Match?",
             "Nein. FLEXR zeigt Profile aus allen Studios innerhalb deines "
             "Suchumkreises – kostenlos bis 50 Kilometer. Du kannst also "
             "Leute aus dem Nachbarbezirk genauso treffen wie aus deinem Gym."),
        ],
    },
    {
        "slug": "graz",
        "name": "Graz",
        "orte": ["Graz"],
        "umland": ["Hart bei Graz", "Feldkirchen bei Graz"],
        "umland_titel": "Rund um Graz",
        "intro": (
            "Graz ist Studierendenstadt und Sportstadt zugleich: Zwischen Uni, "
            "Murufer und Schloßberg wird viel trainiert – im Studio, am "
            "Radweg und auf dem Hausberg. FLEXR bringt Leute zusammen, die "
            "denselben Rhythmus haben: morgens Training, abends Zeit."
        ),
        "radius": (
            "Die meisten Grazer Studios liegen nah beieinander. Mit einem "
            "mittleren Umkreis erreichst du die ganze Stadt, mit einem "
            "größeren auch das Grazer Umland."
        ),
        "dates": [
            ("Die Schloßbergstiege",
             "Die Stufen auf den Schloßberg hinauf sind das inoffizielle "
             "Grazer Stiegen-Workout – oben wartet die Aussicht über die "
             "Dächer der Altstadt."),
            ("Am Murradweg",
             "Laufen oder Radfahren entlang der Mur: flach, grün und mitten in "
             "der Stadt."),
            ("Auf den Schöckl",
             "Der Grazer Hausberg ist ein Halbtagesausflug – zu Fuß hinauf "
             "oder gemütlich mit der Seilbahn, falls das Date doch eher "
             "gemütlich werden soll."),
            ("Plabutsch",
             "Die Wanderwege am Plabutsch beginnen direkt am Stadtrand – "
             "ideal für eine Runde nach Feierabend."),
            ("Frühstück nach dem Training",
             "Graz hat viele Cafés mit gutem Frühstück. Wer schon trainiert "
             "hat, bestellt ohne schlechtes Gewissen doppelt."),
        ],
        "faq": [
            ("Wo lerne ich in Graz sportliche Singles kennen?",
             "Im Studio selbst ist Ansprechen oft schwierig – viele wollen in "
             "Ruhe trainieren. Auf FLEXR siehst du Profile von Leuten aus "
             "Grazer Studios, und ein Chat entsteht nur, wenn beide Interesse "
             "haben."),
            ("Ist FLEXR in Graz kostenlos?",
             "Ja, die Nutzung ist dauerhaft kostenlos und ohne hinterlegtes "
             "Zahlungsmittel. FLEXR Premium (10 € im Monat) ist freiwillig."),
        ],
    },
    {
        "slug": "linz",
        "name": "Linz",
        "orte": ["Linz"],
        "umland": ["Leonding", "Steyregg"],
        "umland_titel": "Rund um Linz",
        "intro": (
            "In Linz trainieren viele vor oder nach der Schicht, zwischen "
            "Industrie, Uni und Innenstadt. Wer so einen Tagesablauf hat, "
            "sucht oft jemanden, der ihn versteht – FLEXR matcht dich mit "
            "Leuten aus Linzer Studios und dem Umland."
        ),
        "radius": (
            "Linz hat weniger Studios als Wien oder Graz. Stell den Umkreis "
            "deshalb eher größer ein – dann sind auch Leonding, Traun und "
            "das Mühlviertel-Umland mit dabei."
        ),
        "dates": [
            ("Laufen an der Donaulände",
             "Die Donaulände zwischen Lentos und Brucknerhaus ist Linz' "
             "Laufstrecke Nummer eins – flach, am Wasser, abends belebt."),
            ("Auf den Pöstlingberg",
             "Zu Fuß hinauf ist es ein ordentliches Training, hinunter geht es "
             "mit der Pöstlingbergbahn."),
            ("Pleschinger See",
             "Im Sommer schwimmen, sonst eine Runde um den See – nur ein paar "
             "Minuten vom Zentrum."),
            ("Am Donauradweg",
             "Eine Radtour Richtung Ottensheim oder Mauthausen – mit Zeit zum "
             "Reden und einer Einkehr am Ende."),
        ],
        "faq": [
            ("Wie funktioniert Fitness-Dating in Linz?",
             "Du wählst dein Linzer Studio und deinen Suchumkreis. FLEXR zeigt "
             "dir Profile aus Studios in diesem Umkreis; liken sich zwei "
             "Personen gegenseitig, könnt ihr chatten."),
            ("Mein Linzer Studio fehlt in der Liste – was tun?",
             "Du kannst es bei der Registrierung mit Adresse vorschlagen und "
             "sofort für dein Profil verwenden. Nach der Prüfung erscheint es "
             "für alle in der Auswahl."),
        ],
    },
    {
        "slug": "salzburg",
        "name": "Salzburg",
        "orte": ["Salzburg"],
        "umland": ["Wals-Himmelreich"],
        "umland_titel": "Rund um Salzburg",
        "intro": (
            "In Salzburg liegen Studio und Berg nah beieinander: Wer unter der "
            "Woche Gewichte hebt, steht am Wochenende oft am Gaisberg oder "
            "Untersberg. FLEXR bringt Leute zusammen, die beides mögen."
        ),
        "radius": (
            "Die Stadt ist überschaubar – ein kleiner Umkreis deckt die "
            "Salzburger Studios ab. Mit größerem Radius kommen Flachgau und "
            "Tennengau dazu."
        ),
        "dates": [
            ("Auf den Kapuzinerberg",
             "Mitten in der Stadt, trotzdem Wald und Stufen – eine kurze, "
             "knackige Runde mit Blick auf die Altstadt."),
            ("Gaisberg",
             "Der Salzburger Hausberg: zu Fuß, mit dem Rad oder als "
             "Trailrunde – je nachdem, wie sportlich das erste Date "
             "werden soll."),
            ("Hellbrunner Allee",
             "Die Allee Richtung Schloss Hellbrunn ist flach und schattig – "
             "gut für einen lockeren Lauf oder einen langen Spaziergang."),
            ("Am Salzachufer",
             "Laufen, Radfahren oder einfach sitzen: Die Salzach verbindet "
             "die halbe Stadt."),
        ],
        "faq": [
            ("Gibt es eine Dating-App für sportliche Singles in Salzburg?",
             "FLEXR ist die Dating-App für Gym-People in Österreich, auch in "
             "Salzburg. Du matchst nach Fitnessstudio und Umkreis; jedes "
             "Konto wird vor der Freischaltung manuell geprüft."),
            ("Muss ich ein Abo abschließen?",
             "Nein. FLEXR ist dauerhaft kostenlos nutzbar, ohne "
             "Zahlungsmittel. Premium ist freiwillig und monatlich kündbar."),
        ],
    },
    {
        "slug": "innsbruck",
        "name": "Innsbruck",
        "orte": ["Innsbruck"],
        "umland": ["Rum", "Hall in Tirol"],
        "umland_titel": "Rund um Innsbruck",
        "intro": (
            "Innsbruck ist die Stadt, in der man nach der Arbeit mit der "
            "Seilbahn ins Hochgebirge fährt. Trainiert wird hier oft für "
            "etwas: die nächste Skitour, die nächste Kletterroute, den "
            "nächsten Berglauf. FLEXR matcht dich mit Leuten, die so ticken."
        ),
        "radius": (
            "Das Inntal ist schmal und lang: Ein mittlerer Umkreis reicht von "
            "Innsbruck bis Hall und Telfs. Wer im Wipptal oder "
            "Stubaital wohnt, stellt ihn etwas größer ein."
        ),
        "dates": [
            ("Kletterzentrum Innsbruck",
             "Eine der größten Kletterhallen Europas – auch für Anfänger, "
             "und zu zweit sichert es sich ohnehin besser."),
            ("Nordkette",
             "Mit der Bahn aus der Innenstadt direkt auf über 2000 Meter – "
             "oder zu Fuß ab der Hungerburg."),
            ("Am Inn-Radweg",
             "Flach, am Fluss, in beide Richtungen endlos – für eine "
             "Laufrunde oder eine lockere Radtour."),
            ("Baggersee Rossau",
             "Im Sommer der Treffpunkt zum Schwimmen – mit Beachvolleyball "
             "und Platz zum Liegen danach."),
        ],
        "faq": [
            ("Gibt es in Innsbruck eine Dating-App für Sportler?",
             "Ja, FLEXR. Du wählst dein Studio in Innsbruck oder Umgebung und "
             "siehst Profile von Leuten, die in deiner Nähe trainieren – "
             "kostenlos bis 50 Kilometer Umkreis."),
            ("Zählt Klettern oder Bergsport auch?",
             "Ja. FLEXR ist nicht nur für Kraftsport. Auf dem Profil gibst du "
             "an, was du trainierst – Klettern, Ausdauer, Functional Fitness "
             "und mehr."),
        ],
    },
    {
        "slug": "klagenfurt",
        "name": "Klagenfurt",
        "orte": ["Klagenfurt am Wörthersee"],
        "umland": [],
        "umland_titel": "",
        "intro": (
            "In Klagenfurt liegt der Wörthersee direkt vor der Tür – im Sommer "
            "wird hier draußen trainiert, im Winter im Studio. FLEXR bringt "
            "Leute aus Klagenfurter Studios zusammen, die Training und "
            "Seeleben verbinden."
        ),
        "radius": (
            "Klagenfurt hat eine überschaubare Zahl an Studios. Mit einem "
            "größeren Umkreis sind auch Villach und das Umland rund um den "
            "Wörthersee mit dabei."
        ),
        "dates": [
            ("Strandbad Klagenfurt",
             "Im Sommer der Klassiker am Wörthersee: schwimmen, "
             "Beachvolleyball, danach ein Eis."),
            ("Kreuzbergl",
             "Das Naherholungsgebiet am Stadtrand hat Laufwege, eine "
             "Sternwarte und einen Aussichtsturm."),
            ("Am Lendkanal",
             "Der Weg entlang des Lendkanals führt aus der Stadt Richtung See "
             "– flach und ideal für eine gemeinsame Laufrunde."),
            ("Pyramidenkogel",
             "Ein kurzer Ausflug südlich des Sees – hinauf auf den "
             "Aussichtsturm, hinunter über die Rutsche im Turm."),
        ],
        "faq": [
            ("Wo finde ich in Klagenfurt Singles, die gern trainieren?",
             "Auf FLEXR siehst du Profile von Leuten aus Klagenfurter Studios "
             "und – mit größerem Umkreis – aus Villach und der Umgebung."),
            ("Ist FLEXR seriös?",
             "Jedes Konto wird vor der Freischaltung manuell alters- und "
             "identitätsgeprüft, jedes Foto von einem Menschen freigegeben. "
             "Eine Garantie, dass jedes Profil echt ist, gibt es trotzdem "
             "nirgends – lies vor einem Treffen die Sicherheitstipps."),
        ],
    },
]


# --------------------------------------------------------------------------
# Bausteine
# --------------------------------------------------------------------------

def e(text: str) -> str:
    return html.escape(text, quote=True)


def jsonld(obj: dict) -> str:
    return (
        '<script type="application/ld+json">\n'
        + json.dumps(obj, ensure_ascii=False, indent=2)
        + "\n</script>"
    )


def breadcrumb(pfad: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + url}
            for i, (name, url) in enumerate(pfad)
        ],
    }


def faq_schema(url: str, fragen: list[tuple[str, str]]) -> dict:
    return {
        "@type": "FAQPage",
        "@id": SITE + url + "#faq",
        "inLanguage": "de-AT",
        "mainEntity": [
            {"@type": "Question", "name": f,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for f, a in fragen
        ],
    }


def faq_html(fragen: list[tuple[str, str]]) -> str:
    teile = []
    for f, a in fragen:
        teile.append(
            '  <details class="faq-item">\n'
            f"    <summary>{e(f)}</summary>\n"
            f'    <div class="faq-a">{e(a)}</div>\n'
            "  </details>"
        )
    return "\n".join(teile)


STIL = """<style>
  /* Nur auf den Such-Einstiegsseiten (erzeugt von tools/seo/build_seo_pages.py). */
  .crumbs{ font-size:13px; color:var(--chalk-dim); margin:0 0 14px; }
  .crumbs a{ color:var(--chalk-dim); }
  .crumbs a:hover{ color:var(--chalk); }
  .cta-box{ margin:28px 0; padding:18px; border:1px solid rgba(255,90,31,.35); border-radius:14px; background:var(--surface); }
  .cta-box p{ margin:0; }
  .cta-box .btn{ margin-top:14px; text-decoration:none; }
  .gym-group{ margin:0 0 14px; }
  .gym-group h3{ margin:16px 0 6px; }
  .gym-group ul{ margin:0; padding-left:18px; color:var(--chalk-dim); font-size:14.5px; }
  .gym-group li b{ color:var(--chalk); font-weight:600; }
  .link-grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:10px; margin:14px 0; padding:0; list-style:none; }
  .link-grid a{ display:block; padding:12px 14px; border:1px solid var(--steel); border-radius:12px; background:var(--surface); text-decoration:none; color:var(--chalk); font-weight:600; }
  .link-grid a:hover{ border-color:var(--plate); color:var(--plate-bright); }
  .link-grid span{ display:block; font-weight:400; font-size:13px; color:var(--chalk-dim); }
  .ideas{ padding-left:18px; }
  .ideas li{ margin-bottom:10px; }
  .ideas b{ color:var(--chalk); }
  .note{ font-size:13px; color:var(--chalk-dim); }
  .faq-item{ border:1px solid var(--hairline); border-radius:14px; background:var(--surface); margin-bottom:12px; overflow:hidden; }
  .faq-item[open]{ border-color:rgba(255,90,31,.35); }
  .faq-item summary{ list-style:none; cursor:pointer; padding:16px 48px 16px 18px; position:relative; font-weight:600; font-size:16px; color:var(--chalk); }
  .faq-item summary::-webkit-details-marker{ display:none; }
  .faq-item summary::after{ content:'+'; position:absolute; right:18px; top:50%; transform:translateY(-50%); font-size:24px; line-height:1; color:var(--plate); }
  .faq-item[open] summary::after{ content:'\\2212'; }
  .faq-a{ padding:0 18px 18px; color:var(--chalk-dim); font-size:14.5px; }
</style>"""


FUSS = """  <nav class="nav-legal" aria-label="Rechtliche Seiten">
    <a href="/impressum.html">Impressum</a>
    <a href="/datenschutz.html">Datenschutz</a>
    <a href="/agb.html">AGB</a>
    <a href="/widerruf.html" data-widerruf-link>Rücktrittsrecht</a>
    <a href="/nutzungsrichtlinien.html">Nutzungsrichtlinien</a>
    <a href="/sicherheit.html">Sicherheit</a>
    <a href="/meldung.html">Inhalt melden</a>
    <a href="/faq.html">FAQ</a>
  </nav>"""


def cta(text: str) -> str:
    return (
        '  <div class="cta-box">\n'
        f"    <p>{text}</p>\n"
        '    <a class="btn" href="/app/#registrieren">Kostenlos registrieren</a>\n'
        "  </div>"
    )


def seite(*, url: str, titel: str, beschreibung: str, og_titel: str,
          krumen: list[tuple[str, str]], schema: list[dict], rumpf: str,
          og_type: str = "website") -> str:
    if len(titel) > 65:
        sys.exit(f"FEHLER: Titel zu lang ({len(titel)}): {titel}")
    if not 70 <= len(beschreibung) <= 160:
        sys.exit(f"FEHLER: Beschreibung {len(beschreibung)} Zeichen: {url}")
    graph = {"@context": "https://schema.org", "@graph": schema + [breadcrumb(krumen)]}
    krumen_html = " › ".join(
        [f'<a href="{u}">{e(n)}</a>' for n, u in krumen[:-1]] + [e(krumen[-1][0])]
    )
    return f"""<!DOCTYPE html>
<!-- ERZEUGTE DATEI - nicht von Hand aendern.
     Quelle: tools/seo/build_seo_pages.py (python3 tools/seo/build_seo_pages.py) -->
<html lang="de-AT">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(titel)}</title>
<meta name="description" content="{e(beschreibung)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<link rel="canonical" href="{SITE}{url}">
<meta name="theme-color" content="#121212">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="FLEXR">
<meta property="og:locale" content="de_AT">
<meta property="og:title" content="{e(og_titel)}">
<meta property="og:description" content="{e(beschreibung)}">
<meta property="og:url" content="{SITE}{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="192x192" href="/icons/icon-192.png?v=4">
<link rel="apple-touch-icon" sizes="180x180" href="/icons/apple-touch-icon-180.png?v=1">
<link rel="preload" href="/fonts/oswald.woff2?v=1" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/legal.css?v=2">
{jsonld(graph)}
{STIL}
</head>
<body>
<a class="skip-link" href="#main-content">Zum Inhalt springen</a>
<div class="wrap">
  <div class="legal-head">
    <a class="back" href="/">← zu FLEXR</a>
  </div>

  <main id="main-content">
  <nav class="crumbs" aria-label="Brotkrumen">{krumen_html}</nav>
{rumpf}
  </main>

{FUSS}
</div>
<script src="/legal-status.js?v=2" defer></script>
</body>
</html>
"""


def stadt_gyms(gyms: list[dict], orte: list[str]) -> list[dict]:
    return sorted(
        [g for g in gyms if g["city"] in orte],
        key=lambda g: (g["plz"], g["name"].lower(), g["street"]),
    )


def gym_li(g: dict) -> str:
    adresse = f'{g["street"]} {g["house_number"]}'.strip()
    return f'      <li><b>{e(g["name"])}</b> – {e(adresse)}</li>'


def gym_liste(stadt: dict, gyms: list[dict]) -> tuple[str, int]:
    kern = stadt_gyms(gyms, stadt["orte"])
    umland = stadt_gyms(gyms, stadt["umland"])
    gruppen: dict[str, list[dict]] = {}
    for g in kern:
        if stadt["slug"] == "wien":
            bezirk = WIEN_BEZIRKE.get(g["plz"])
            titel = f'{g["plz"]} Wien, {bezirk}' if bezirk else f'{g["plz"]} Wien'
        else:
            titel = f'{g["plz"]} {stadt["name"]}'
        gruppen.setdefault(titel, []).append(g)
    if umland:
        gruppen[stadt["umland_titel"]] = umland
    teile = []
    for titel, liste in gruppen.items():
        teile.append('  <div class="gym-group">')
        teile.append(f"    <h3>{e(titel)}</h3>")
        teile.append("    <ul>")
        teile.extend(gym_li(g) for g in liste)
        teile.append("    </ul>")
        teile.append("  </div>")
    return "\n".join(teile), len(kern) + len(umland)


def andere_staedte(aktuell: str | None) -> str:
    teile = ['  <ul class="link-grid">']
    for s in STAEDTE:
        if s["slug"] == aktuell:
            continue
        teile.append(
            f'    <li><a href="/fitness-dating-{s["slug"]}.html">{e(s["name"])}'
            f"<span>Fitness-Dating in {e(s['name'])}</span></a></li>"
        )
    teile.append("  </ul>")
    return "\n".join(teile)


def stadtseite(stadt: dict, gyms: list[dict]) -> str:
    name = stadt["name"]
    url = f"/fitness-dating-{stadt['slug']}.html"
    liste, anzahl = gym_liste(stadt, gyms)
    if anzahl < 5:
        sys.exit(f"FEHLER: {name} hat nur {anzahl} Gyms - zu duenn fuer eine eigene Seite")
    ideen = "\n".join(
        f"    <li><b>{e(t)}:</b> {e(b)}</li>" for t, b in stadt["dates"]
    )
    fragen = stadt["faq"] + [
        (f"Wie viele Leute nutzen FLEXR in {name}?",
         "Wir nennen bewusst keine Nutzerzahlen – wer das tut, hat sie meist "
         "geschönt. Wie viele Profile du siehst, hängt davon ab, wie viele "
         "Leute in deinem Umkreis dabei sind. FLEXR ist noch im Aufbau."),
    ]
    rumpf = f"""  <h1>Fitness-Dating in {e(name)}: Singles aus deinem Gym</h1>
  <p class="lead">{e(stadt['intro'])}</p>

  <h2>So funktioniert FLEXR in {e(name)}</h2>
  <p>Du wählst bei der Registrierung dein Fitnessstudio in {e(name)} und
  deinen Suchumkreis. FLEXR zeigt dir dann Profile von Leuten, die in Studios
  in diesem Umkreis trainieren. Liken sich zwei Personen gegenseitig, entsteht
  ein Match – erst dann könnt ihr schreiben. Niemand bekommt ungefragt
  Nachrichten.</p>
  <p>{e(stadt['radius'])}</p>
  <p>FLEXR fragt nie deinen Standort ab: Die Umkreissuche rechnet ausschließlich
  mit der Adresse des Studios, das du selbst auswählst. Jedes Konto wird vor
  der Freischaltung manuell alters- und identitätsgeprüft, jedes Foto von
  einem Menschen freigegeben.</p>

{cta(f"Die Nutzung ist dauerhaft kostenlos – kein Abo, kein Zahlungsmittel. FLEXR&nbsp;Premium (10&nbsp;€ im Monat) ist freiwillig.")}

  <h2>Fitnessstudios in {e(name)} auf FLEXR</h2>
  <p>Diese {anzahl} Studios kannst du derzeit in FLEXR als dein Gym auswählen.
  Dein Studio fehlt? Du kannst es bei der Registrierung mit Adresse vorschlagen
  und sofort verwenden.</p>
{liste}
  <p class="note">FLEXR ist mit den genannten Studios nicht verbunden und wird
  von ihnen nicht empfohlen. Die Liste zeigt nur, welche Studios in der App
  auswählbar sind (Stand: {dt.date.today().strftime('%d.%m.%Y')}).</p>

  <h2>Ideen fürs erste Date in {e(name)}</h2>
  <p>Wer gern trainiert, muss sich nicht im Kaffeehaus gegenübersitzen. Ein
  paar Ideen mit Bewegung – beim ersten Treffen immer an einem belebten Ort,
  siehe unsere <a href="/sicherheit.html">Sicherheitstipps</a>:</p>
  <ul class="ideas">
{ideen}
  </ul>
  <p>Mehr Anregungen: <a href="/date-ideen-sportler.html">Date-Ideen für
  Sportler</a>.</p>

  <h2>Häufige Fragen zu Fitness-Dating in {e(name)}</h2>
{faq_html(fragen)}

  <h2>FLEXR in anderen Städten</h2>
{andere_staedte(stadt['slug'])}
  <p>FLEXR funktioniert mit jeder österreichischen Postleitzahl. Mehr zum
  Konzept: <a href="/gym-dating.html">Gym-Dating in Österreich</a>.</p>
"""
    beschreibung = (
        f"Fitness-Singles in {name} kennenlernen: FLEXR matcht dich nach "
        f"Fitnessstudio und Umkreis – {anzahl} Studios in {name} auswählbar, "
        "geprüfte Profile, kostenlos."
    )
    return seite(
        url=url,
        titel=f"Fitness-Dating {name} – Singles aus deinem Gym | FLEXR",
        og_titel=f"Fitness-Dating in {name} – FLEXR",
        beschreibung=beschreibung,
        krumen=[("FLEXR", "/"), ("Gym-Dating", "/gym-dating.html"), (name, url)],
        schema=[
            {"@type": "WebPage", "@id": SITE + url, "url": SITE + url,
             "name": f"Fitness-Dating in {name}", "inLanguage": "de-AT",
             "isPartOf": {"@id": SITE + "/#website"},
             "about": {"@id": SITE + "/#app"},
             "dateModified": HEUTE},
            faq_schema(url, fragen),
        ],
        rumpf=rumpf,
    )


def hub(gyms: list[dict]) -> str:
    url = "/gym-dating.html"
    gesamt = len(gyms)
    fragen = [
        ("Was ist Gym-Dating?",
         "Gym-Dating heißt, Partnerinnen oder Partner über das gemeinsame "
         "Training kennenzulernen. Statt nach Fotos allein zu swipen, siehst "
         "du Menschen, die einen ähnlichen Alltag haben: feste Trainingszeiten, "
         "Ernährung, frühes Aufstehen."),
        ("Welche Dating-App ist für Sportler in Österreich?",
         "FLEXR ist eine Dating-App speziell für Gym-People in Österreich. Sie "
         "matcht nach Fitnessstudio und Umkreis und ist dauerhaft kostenlos "
         "nutzbar."),
        ("Ist FLEXR nur für Bodybuilder?",
         "Nein. FLEXR ist für alle, die Training ernst nehmen – Kraftsport, "
         "Functional Fitness, Ausdauer, Kampfsport, Klettern. Es geht um den "
         "gemeinsamen Lifestyle, nicht um einen bestimmten Körper."),
        ("Was unterscheidet FLEXR von Tinder oder Bumble?",
         "Allgemeine Dating-Apps zeigen dir alle in deiner Nähe. FLEXR zeigt "
         "dir Menschen, die in Fitnessstudios in deinem Umkreis trainieren, "
         "prüft jedes Konto vor der Freischaltung manuell und kostet in der "
         "Grundversion dauerhaft nichts."),
        ("Kann ich über FLEXR einen Trainingspartner finden?",
         "FLEXR ist eine Dating-App. Viele Matches trainieren später gemeinsam "
         "– wer aber ausschließlich einen Trainingspartner ohne romantisches "
         "Interesse sucht, sollte das im Profil offen schreiben."),
    ]
    rumpf = f"""  <h1>Gym-Dating in Österreich: Die Dating-App für Fitness-Singles</h1>
  <p class="lead">Du trainierst vier Mal die Woche, planst deine Mahlzeiten und
  gehst früh schlafen, weil morgen Beintag ist? Dann weißt du, wie schwer es
  ist, jemanden zu finden, der das nicht seltsam findet. FLEXR ist die
  Dating-App für genau diese Leute – in ganz Österreich.</p>

  <h2>Warum Dating über das Fitnessstudio funktioniert</h2>
  <p>Wer regelmäßig trainiert, hat einen Alltag mit festen Zeiten: Training
  vor der Arbeit oder danach, Meal-Prep am Sonntag, Wettkampf oder
  Bergtour am Wochenende. In allgemeinen Dating-Apps ist das oft ein
  Reibungspunkt. Auf FLEXR ist es der gemeinsame Nenner.</p>
  <p>Im Studio selbst jemanden anzusprechen ist dagegen heikel: Viele wollen
  mit Kopfhörern in Ruhe trainieren, und niemand möchte der Grund sein, warum
  jemand das Gym wechselt. Auf FLEXR entsteht ein Chat nur, wenn beide
  Interesse haben. (Wenn du es trotzdem im Studio versuchen willst: unser
  Ratgeber <a href="/gym-crush-ansprechen.html">Gym-Crush ansprechen</a>.)</p>

  <h2>So funktioniert FLEXR</h2>
  <ol class="ideas">
    <li><b>Profil erstellen:</b> Fotos, ein paar Sätze über dich und was du
    trainierst. Jedes Konto wird vor der Freischaltung manuell alters- und
    identitätsgeprüft.</li>
    <li><b>Gym und Umkreis wählen:</b> Du suchst dein Studio aus {gesamt}
    Fitnessstudios in ganz Österreich aus – oder schlägst es vor, falls es
    fehlt. Der Suchumkreis ist kostenlos bis 50&nbsp;km.</li>
    <li><b>Liken, matchen, schreiben:</b> Liken sich zwei Personen
    gegenseitig, entsteht ein Match, und ihr könnt chatten.</li>
  </ol>

{cta("Die Nutzung ist dauerhaft kostenlos – 20 Likes am Tag, 3 Unterhaltungen gleichzeitig, 50&nbsp;km Umkreis. FLEXR&nbsp;Premium (10&nbsp;€ im Monat) ist freiwillig.")}

  <h2>Fitness-Dating in deiner Stadt</h2>
  <p>FLEXR funktioniert mit jeder österreichischen Postleitzahl. Für die
  größten Städte gibt es eigene Seiten mit den auswählbaren Studios und Ideen
  fürs erste Date vor Ort:</p>
{andere_staedte(None)}

  <h2>Für wen FLEXR gedacht ist</h2>
  <p>Für alle, denen Training wichtig ist: Kraftsport und Bodybuilding,
  CrossFit und Functional Fitness, Laufen und Radfahren, Kampfsport, Klettern,
  Yoga – und genauso für alle, die gerade erst wieder angefangen haben. FLEXR
  ist kein Wettbewerb um Körperfettanteile. Nutzung ab 18 Jahren.</p>

  <h2>Ratgeber</h2>
  <ul class="link-grid">
    <li><a href="/gym-crush-ansprechen.html">Gym-Crush ansprechen<span>Respektvoll, ohne peinlich zu werden</span></a></li>
    <li><a href="/date-ideen-sportler.html">Date-Ideen für Sportler<span>Erste Treffen mit Bewegung</span></a></li>
    <li><a href="/sicherheit.html">Sicherheitstipps<span>Vor dem ersten Treffen lesen</span></a></li>
  </ul>

  <h2>Häufige Fragen zu Gym-Dating</h2>
{faq_html(fragen)}
  <p>Mehr Antworten in den <a href="/faq.html">FAQ</a>.</p>
"""
    return seite(
        url=url,
        titel="Gym-Dating in Österreich – Dating-App für Fitness-Singles | FLEXR",
        og_titel="Gym-Dating in Österreich – FLEXR",
        beschreibung=(
            "Gym-Dating in Österreich: FLEXR ist die Dating-App für Sportler "
            "und Fitness-Singles. Matches nach Fitnessstudio und Umkreis, "
            "dauerhaft kostenlos."
        ),
        krumen=[("FLEXR", "/"), ("Gym-Dating", url)],
        schema=[
            {"@type": "WebPage", "@id": SITE + url, "url": SITE + url,
             "name": "Gym-Dating in Österreich", "inLanguage": "de-AT",
             "isPartOf": {"@id": SITE + "/#website"},
             "about": {"@id": SITE + "/#app"}, "dateModified": HEUTE},
            faq_schema(url, fragen),
        ],
        rumpf=rumpf,
    )


def artikel(*, url: str, titel: str, h1: str, beschreibung: str, rumpf: str,
            fragen: list[tuple[str, str]], veroeffentlicht: str) -> str:
    schema = [{
        "@type": "Article",
        "@id": SITE + url + "#artikel",
        "headline": h1,
        "description": beschreibung,
        "inLanguage": "de-AT",
        "mainEntityOfPage": SITE + url,
        "image": SITE + "/og-image.png",
        "datePublished": veroeffentlicht,
        "dateModified": HEUTE,
        "author": {"@id": SITE + "/#organization"},
        "publisher": {"@id": SITE + "/#organization"},
    }]
    if fragen:
        schema.append(faq_schema(url, fragen))
        rumpf += "\n  <h2>Häufige Fragen</h2>\n" + faq_html(fragen) + "\n"
    return seite(
        url=url, titel=titel, og_titel=h1, beschreibung=beschreibung,
        krumen=[("FLEXR", "/"), ("Gym-Dating", "/gym-dating.html"), (h1, url)],
        schema=schema, rumpf=rumpf, og_type="article",
    )


def gym_crush() -> str:
    url = "/gym-crush-ansprechen.html"
    h1 = "Gym-Crush ansprechen: So geht es respektvoll"
    rumpf = f"""  <h1>{e(h1)}</h1>
  <p class="lead">Seit Wochen trainiert dieselbe Person zur selben Zeit wie du,
  und du überlegst, ob du sie ansprechen sollst. Das Fitnessstudio ist dafür
  kein einfacher Ort: Die meisten sind zum Trainieren da, nicht zum Flirten.
  Mit ein paar Regeln wird es trotzdem kein Moment, den einer von euch
  bereut.</p>

  <h2>1. Nie mitten im Satz</h2>
  <p>Wer gerade unter der Hantel liegt, zählt Wiederholungen und will nicht
  reden. Warte die Satzpause ab – oder besser das Ende des Trainings, etwa
  beim Rausgehen.</p>

  <h2>2. Kopfhörer heißen: bitte nicht stören</h2>
  <p>Große Kopfhörer, Blick auf den Boden, konzentriertes Gesicht: Das ist ein
  klares Signal. Wenn jemand nie aufschaut, ist heute nicht der Tag.</p>

  <h2>3. Kurz, konkret, ohne Körper-Kommentar</h2>
  <p>„Du trainierst auch immer montags – wie lange bist du schon hier?“
  funktioniert. Kommentare über Figur, Po oder Muskeln funktionieren nicht –
  auch wenn sie als Kompliment gemeint sind. Viele wollen im Gym genau das
  nicht hören.</p>

  <h2>4. Keine ungefragten Trainingstipps</h2>
  <p>Die Übungsausführung zu korrigieren ist der häufigste Fehlstart. Es wirkt
  belehrend, auch wenn du recht hast. Frag lieber nach etwas, zum Beispiel
  nach einem Gerät oder einem Trainingsplan.</p>

  <h2>5. Ein Nein ist ein Nein – und danach ist Schluss</h2>
  <p>Das Gym ist ein Ort, an den ihr beide noch lange gehen wollt. Wenn die
  Antwort kurz ausfällt oder freundlich ablehnend ist: bedanken, weitertrainieren,
  nicht nochmal versuchen. Niemand soll wegen dir das Studio oder die
  Trainingszeit wechseln.</p>

  <h2>6. Nicht folgen, nicht warten</h2>
  <p>Vor der Garderobe zu warten oder zum Auto zu begleiten, wirkt bedrohlich –
  egal, wie es gemeint ist. Sprich jemanden nur an, wo ihr euch ohnehin
  begegnet.</p>

  <h2>7. Einen Ausweg anbieten</h2>
  <p>Statt direkt nach der Nummer zu fragen: „Falls du mal Lust auf einen
  Kaffee nach dem Training hast – ich bin meistens montags hier.“ So kann die
  andere Person ohne Druck selbst entscheiden.</p>

  <h2>Die Alternative: erst matchen, dann reden</h2>
  <p>Genau für diese Situation gibt es FLEXR. Du wählst dein Fitnessstudio,
  und siehst Profile von Leuten, die in Studios in deinem Umkreis trainieren.
  Ein Chat entsteht nur, wenn beide Interesse haben – keine Unsicherheit, kein
  unangenehmer Moment am Rack.</p>

{cta("FLEXR ist die Dating-App für Gym-People in Österreich – dauerhaft kostenlos nutzbar.")}
"""
    fragen = [
        ("Ist es okay, jemanden im Fitnessstudio anzusprechen?",
         "Ja, wenn du den richtigen Moment wählst: nicht mitten in der Übung, "
         "nicht bei Kopfhörern und konzentriertem Blick, kurz und ohne "
         "Kommentare über den Körper. Ein Nein akzeptierst du sofort."),
        ("Wie merke ich, ob mein Gym-Crush Interesse hat?",
         "Blickkontakt, ein Lächeln, von sich aus ein kurzes Gespräch "
         "anfangen, die Kopfhörer abnehmen, wenn du grüßt. Sicher weißt du es "
         "erst, wenn du fragst – oder wenn ihr auf einer App wie FLEXR "
         "gegenseitig liked."),
    ]
    return artikel(
        url=url,
        titel="Gym-Crush ansprechen: 7 Regeln fürs Fitnessstudio | FLEXR",
        h1=h1,
        beschreibung=(
            "Gym-Crush ansprechen, ohne dass es peinlich wird: 7 Regeln für "
            "den richtigen Moment im Fitnessstudio – und warum ein Match oft "
            "der entspanntere Weg ist."
        ),
        rumpf=rumpf, fragen=fragen, veroeffentlicht="2026-09-30",
    )


def date_ideen() -> str:
    url = "/date-ideen-sportler.html"
    h1 = "Date-Ideen für Sportler: 12 Ideen fürs erste Treffen"
    ideen = [
        ("Gemeinsam laufen gehen", "Eine lockere Runde in einem Tempo, bei dem ihr noch reden könnt. Danach ein Kaffee – der Gesprächsstoff ist schon da."),
        ("Bouldern", "Zu zweit Routen auszuknobeln bricht das Eis. Leihschuhe gibt es in jeder Halle, Vorerfahrung braucht es nicht."),
        ("Wanderung auf einen Hausberg", "Zwei, drei Stunden mit Aussicht und einer Hütte am Ziel. Wählt eine bekannte, belebte Route."),
        ("Probetraining in einem neuen Studio", "Viele Studios bieten Probetrainings an. Neues Terrain für beide – keiner hat Heimvorteil."),
        ("Frühstück nach dem Training", "Jeder trainiert in seinem eigenen Gym, danach trefft ihr euch zum Frühstück. Entspannt, tagsüber, mit Hunger."),
        ("Radtour mit Einkehr", "Eine flache Strecke am Fluss, Ziel ist ein Gasthaus oder Café. Tempo nach dem Langsameren."),
        ("Tischtennis, Minigolf oder Bowling", "Ein bisschen Wettkampf, aber ohne Schweiß. Gut für alle, die nicht gleich in Sportkleidung erscheinen wollen."),
        ("Stand-up-Paddling", "Im Sommer auf einem See oder ruhigen Fluss. Wer ins Wasser fällt, lacht zuerst."),
        ("Eislaufen", "Im Winter ein Klassiker – Händchenhalten ergibt sich im Zweifel von selbst."),
        ("Gemeinsam kochen", "Eiweißreich, bunt, mit Meal-Prep-Tipps. Eher fürs zweite oder dritte Treffen, weil es bei jemandem zu Hause stattfindet."),
        ("Yoga- oder Mobility-Stunde", "Eine offene Stunde im Studio oder im Park – ruhiger als das Gym, und danach Zeit zum Reden."),
        ("Einen Wettkampf anschauen", "Ein Lauf, ein Kampfsportabend oder ein Kletterwettbewerb: zuschauen, anfeuern, danach diskutieren."),
    ]
    liste = "\n".join(f"    <li><b>{e(t)}:</b> {e(b)}</li>" for t, b in ideen)
    rumpf = f"""  <h1>{e(h1)}</h1>
  <p class="lead">Wer gern trainiert, muss sich beim ersten Date nicht eine
  Stunde lang im Café gegenübersitzen. Ein Treffen mit Bewegung nimmt Druck
  raus: Ihr habt etwas zu tun, das Gespräch ergibt sich nebenbei, und ihr seht
  sofort, ob ihr euch gegenseitig ausreden lasst – auch außer Atem.</p>

  <h2>12 Ideen für ein sportliches erstes Date</h2>
  <ol class="ideas">
{liste}
  </ol>

  <h2>Worauf du beim ersten Treffen achten solltest</h2>
  <ul class="ideas">
    <li><b>Öffentlicher Ort:</b> Das erste Treffen immer dort, wo andere
    Menschen sind – eine belebte Laufstrecke, eine Halle, ein Café. Keine
    einsame Tour zu zweit beim ersten Mal.</li>
    <li><b>Selbst hin und zurück:</b> Komm mit eigenem Fahrrad, Auto oder
    Öffis, damit du jederzeit gehen kannst.</li>
    <li><b>Kein Leistungstest:</b> Das Tempo richtet sich nach der Person, die
    langsamer ist. Wer beim ersten Date seine Bestzeit laufen will, hat das
    Date nicht verstanden.</li>
    <li><b>Jemandem Bescheid sagen:</b> Eine Freundin oder ein Freund weiß,
    wo du bist und mit wem.</li>
  </ul>
  <p>Mehr dazu in unseren <a href="/sicherheit.html">Sicherheitstipps</a>.</p>

  <h2>Ideen für deine Stadt</h2>
  <p>Konkrete Orte für ein sportliches erstes Date findest du auf unseren
  Stadtseiten:</p>
{andere_staedte(None)}

{cta("Noch kein Match für das erste Date? Auf FLEXR triffst du Menschen, die in Fitnessstudios in deiner Nähe trainieren.")}
"""
    fragen = [
        ("Was ist ein gutes erstes Date für Sportler?",
         "Etwas mit leichter Bewegung, bei dem man reden kann: eine lockere "
         "Laufrunde, Bouldern, eine kurze Wanderung oder ein Frühstück nach "
         "dem Training. Immer an einem belebten Ort."),
        ("Soll ich beim ersten Date gemeinsam trainieren?",
         "Ein hartes Training eher nicht – man ist zu beschäftigt, um zu "
         "reden. Besser ist etwas Spielerisches wie Bouldern oder eine lockere "
         "Runde, bei der das Tempo keine Rolle spielt."),
    ]
    return artikel(
        url=url,
        titel="Date-Ideen für Sportler: 12 Ideen fürs erste Treffen | FLEXR",
        h1=h1,
        beschreibung=(
            "Sportliche Date-Ideen fürs erste Treffen: Bouldern, Laufen, "
            "Wandern, Frühstück nach dem Training und mehr – plus Tipps, "
            "worauf du achten solltest."
        ),
        rumpf=rumpf, fragen=fragen, veroeffentlicht="2026-09-30",
    )


# --------------------------------------------------------------------------
# Sitemap
# --------------------------------------------------------------------------

def sitemap_aktualisieren(urls: list[tuple[str, str]]) -> None:
    pfad = FRONTEND / "sitemap.xml"
    xml = pfad.read_text(encoding="utf-8")
    eintraege = ["  <!-- SEO-SEITEN-ANFANG (erzeugt von tools/seo/build_seo_pages.py) -->"]
    for url, prio in urls:
        eintraege.append(
            "  <url>\n"
            f"    <loc>{SITE}{url}</loc>\n"
            f"    <lastmod>{HEUTE}</lastmod>\n"
            "    <changefreq>monthly</changefreq>\n"
            f"    <priority>{prio}</priority>\n"
            "  </url>"
        )
    eintraege.append("  <!-- SEO-SEITEN-ENDE -->")
    block = "\n".join(eintraege)
    muster = re.compile(r"  <!-- SEO-SEITEN-ANFANG.*?SEO-SEITEN-ENDE -->", re.S)
    if muster.search(xml):
        xml = muster.sub(lambda _m: block, xml)
    else:
        xml = xml.replace("</urlset>", block + "\n</urlset>")
    pfad.write_text(xml, encoding="utf-8")


def main() -> None:
    if "--refresh" in sys.argv:
        gyms = gyms_abrufen()
        GYMS.write_text(json.dumps(gyms, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{len(gyms)} Gyms abgerufen")
    gyms = gyms_laden()

    seiten: dict[str, str] = {"/gym-dating.html": hub(gyms)}
    for s in STAEDTE:
        seiten[f"/fitness-dating-{s['slug']}.html"] = stadtseite(s, gyms)
    seiten["/gym-crush-ansprechen.html"] = gym_crush()
    seiten["/date-ideen-sportler.html"] = date_ideen()

    for url, inhalt in seiten.items():
        (FRONTEND / url.lstrip("/")).write_text(inhalt, encoding="utf-8")
        print("geschrieben:", url)

    sitemap_aktualisieren(
        [("/gym-dating.html", "0.8")]
        + [(f"/fitness-dating-{s['slug']}.html", "0.7") for s in STAEDTE]
        + [("/gym-crush-ansprechen.html", "0.6"), ("/date-ideen-sportler.html", "0.6")]
    )
    print("sitemap.xml aktualisiert")


if __name__ == "__main__":
    main()
