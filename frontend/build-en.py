#!/usr/bin/env python3
"""Erzeugt die englische Landingpage `en/index.html` aus `index.html`.

Warum ein Generator und keine zweite, von Hand gepflegte Datei:

Deutsch und Englisch brauchen **zwei eigene Adressen**, damit Suchmaschinen je
Adresse eindeutig eine Sprache sehen (siehe `lang-switch.js`). Zwei
handgepflegte HTML-Dateien mit 1300 Zeilen laufen aber garantiert auseinander —
eine Aenderung am Aufbau muesste jedes Mal doppelt gemacht werden.

Deshalb bleibt `index.html` die einzige Quelle des Markups. Die
`data-i18n`-Auszeichnungen darin sagen, welcher Text uebersetzbar ist; die
englischen Texte stehen im `en`-Block von `i18n-landing.js` beziehungsweise in
`i18n.js` (gemeinsame Schluessel wie die Rechts-Links). Dieses Skript setzt
beides zusammen und schreibt das Ergebnis nach `en/index.html`.

    python3 frontend/build-en.py

Die Verweise auf die Rechtstexte zeigen in der erzeugten Fassung auf `/en/`
(siehe `rechtslinks_umbiegen`) - jeden Rechtstext gibt es dort in englischer
Uebersetzung, unter demselben Dateinamen.

Nach jeder Aenderung an `index.html` oder an den Woerterbuechern erneut laufen
lassen. Das Skript prueft dabei mit, ob zu jeder Auszeichnung ein englischer
Text existiert, und bricht sonst ab — eine halb uebersetzte Seite soll gar
nicht erst entstehen.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
QUELLE = HIER / "index.html"
ZIEL = HIER / "en" / "index.html"
WOERTERBUECHER = [HIER / "i18n.js", HIER / "i18n-landing.js"]

# data-i18n-Attribut -> HTML-Attribut, das gesetzt wird. `None` heisst: Inhalt.
ATTRIBUTE = {
    "data-i18n": None,           # textContent
    "data-i18n-html": "#html",   # innerHTML
    "data-i18n-ph": "placeholder",
    "data-i18n-aria": "aria-label",
    "data-i18n-title": "title",
    "data-i18n-alt": "alt",
    "data-i18n-content": "content",
}


def lies_woerterbuch(pfade: list[Path], sprache: str) -> dict[str, str]:
    """Den `de:`- oder `en:`-Block aus den i18n-Dateien einsammeln.

    Bewusst mit regulaeren Ausdruecken und nicht mit einem JS-Parser: die
    Bloecke sind schlichte Objektliterale aus einfach gequoteten Zeichenketten,
    und eine Abhaengigkeit auf node waere fuer diesen einen Zweck zu viel.
    """
    eintraege: dict[str, str] = {}
    for pfad in pfade:
        quelle = pfad.read_text(encoding="utf-8")
        block = re.search(
            r"\n(\s+)%s:\s*\{(.*?)\n\1\}" % sprache, quelle, re.S
        )
        if not block:
            sys.exit(f"FEHLER: kein `{sprache}`-Block in {pfad.name}")
        for treffer in re.finditer(
            r"^\s+'([A-Za-z0-9._]+)':\s*'((?:[^'\\]|\\.)*)'", block.group(2), re.M
        ):
            wert = treffer.group(2)
            # In der JS-Quelle maskierte Zeichen zurueckwandeln.
            wert = wert.replace("\\'", "'").replace("\\n", "\n").replace("\\\\", "\\")
            eintraege[treffer.group(1)] = wert
    return eintraege


def ersetze_auszeichnungen(html: str, texte: dict[str, str]) -> tuple[str, list[str]]:
    """Jeden ausgezeichneten Knoten durch seinen englischen Text ersetzen."""
    fehlend: list[str] = []

    def hole(schluessel: str) -> str | None:
        if schluessel not in texte:
            fehlend.append(schluessel)
            return None
        return texte[schluessel]

    # 1. Inhalte (data-i18n / data-i18n-html). Das Markup ist durchgehend
    #    wohlgeformt und die ausgezeichneten Knoten enthalten hoechstens
    #    einfaches Inline-Markup (<b>, <em>, <a>, <s>, <br>) - ein Abgleich
    #    ueber das oeffnende Tag bis zum passenden schliessenden reicht.
    def ersetze_inhalt(treffer: re.Match) -> str:
        tag, attribute, schluessel = treffer.group("tag"), treffer.group("attrs"), treffer.group("key")
        text = hole(schluessel)
        if text is None:
            return treffer.group(0)
        return f"<{tag}{attribute}>{text}</{tag}>"

    muster = re.compile(
        r"<(?P<tag>[a-z0-9]+)(?P<attrs>[^>]*\bdata-i18n(?:-html)?=\"(?P<key>[A-Za-z0-9._]+)\"[^>]*)>"
        r"(?P<body>.*?)</(?P=tag)>",
        re.S,
    )
    html = muster.sub(ersetze_inhalt, html)

    # 2. Attribute (placeholder, aria-label, title, alt, content)
    for daten_attribut, ziel_attribut in ATTRIBUTE.items():
        if ziel_attribut in (None, "#html"):
            continue

        def ersetze_attribut(treffer: re.Match, ziel=ziel_attribut) -> str:
            tag = treffer.group(0)
            schluessel = treffer.group("key")
            text = hole(schluessel)
            if text is None:
                return tag
            if re.search(r'\b%s="[^"]*"' % ziel, tag):
                return re.sub(r'\b%s="[^"]*"' % ziel, f'{ziel}="{text}"', tag, count=1)
            return tag[:-1] + f' {ziel}="{text}">'

        html = re.sub(
            r"<[a-z0-9]+[^>]*\b%s=\"(?P<key>[A-Za-z0-9._]+)\"[^>]*>" % daten_attribut,
            ersetze_attribut,
            html,
        )

    return html, fehlend


#: Rechtstexte, die es unter /en/ ebenfalls gibt. Die Namen bleiben in beiden
#: Sprachen gleich - /agb.html und /en/agb.html.
RECHTSTEXTE = [
    "faq", "impressum", "datenschutz", "agb", "widerruf",
    "nutzungsrichtlinien", "sicherheit", "meldung", "strafverfolgung",
]


def rechtslinks_umbiegen(html: str) -> str:
    """Verweise auf die Rechtstexte auf die englische Fassung umstellen.

    Die Adressen stehen an zwei verschiedenen Stellen: in der Fussleiste als
    Markup in `index.html`, und mitten im Fliesstext einzelner Woerterbuch-
    Eintraege (etwa `faq.more`). Eine Regel ueber das fertige Dokument erwischt
    beide - dann muss weder das Markup doppelt gepflegt noch in jedem
    englischen String die Adresse mitgeaendert werden.

    Sprungmarken bleiben erhalten: /nutzungsrichtlinien.html#kontakt wird zu
    /en/nutzungsrichtlinien.html#kontakt.
    """
    muster = re.compile(
        r'href="/(%s)\.html' % "|".join(RECHTSTEXTE)
    )
    html, anzahl = muster.subn(lambda m: 'href="/en/%s.html' % m.group(1), html)
    if not anzahl:
        sys.exit("FEHLER: keine Verweise auf Rechtstexte gefunden")
    return html


def englische_kopfdaten(html: str, texte: dict[str, str]) -> str:
    """Sprache, kanonische Adresse, Titel, Beschreibung und JSON-LD umstellen."""
    ersetzungen: list[tuple[str, str]] = [
        ('<html lang="de-AT">', '<html lang="en">'),
        (
            '<link rel="canonical" href="https://flexr.social/">',
            '<link rel="canonical" href="https://flexr.social/en/">',
        ),
        (
            '<meta property="og:url" content="https://flexr.social/">',
            '<meta property="og:url" content="https://flexr.social/en/">',
        ),
        ('<meta property="og:locale" content="de_AT">', '<meta property="og:locale" content="en">'),
        # Der Regler zeigt jetzt in die andere Richtung.
        (
            '<a href="/" hreflang="de" class="on" aria-current="true" title="Deutsch">DE</a>\n'
            '        <a href="/en/" hreflang="en" title="English">EN</a>',
            '<a href="/" hreflang="de" title="Deutsch">DE</a>\n'
            '        <a href="/en/" hreflang="en" class="on" aria-current="true" title="English">EN</a>',
        ),
        ('<span class="lang-switch" data-active="de"', '<span class="lang-switch" data-active="en"'),
        # Bilder und Schriften liegen an der Wurzel; relative Pfade gibt es
        # keine, alles ist absolut ab "/". Nur der Selbstverweis der Wortmarke
        # zeigt auf die deutsche Startseite und muss mitwandern.
        (
            '<a href="/" style="text-decoration:none; color:inherit;" data-i18n-aria="nav.home"',
            '<a href="/en/" style="text-decoration:none; color:inherit;" data-i18n-aria="nav.home"',
        ),
    ]
    for alt, neu in ersetzungen:
        if alt not in html:
            sys.exit(f"FEHLER: erwartete Stelle nicht gefunden:\n  {alt[:90]}")
        html = html.replace(alt, neu, 1)

    # Titel und Beschreibungen kommen aus demselben Woerterbuch wie der Rest.
    ersatz_meta = {
        r"<title>[^<]*</title>": f"<title>{texte['meta.title']}</title>",
        r'<meta name="description" content="[^"]*">':
            f'<meta name="description" content="{texte["meta.description"]}">',
        r'<meta property="og:title" content="[^"]*">':
            f'<meta property="og:title" content="{texte["meta.ogTitle"]}">',
        r'<meta property="og:description" content="[^"]*">':
            f'<meta property="og:description" content="{texte["meta.ogDescription"]}">',
        r'<meta name="twitter:title" content="[^"]*">':
            f'<meta name="twitter:title" content="{texte["meta.ogTitle"]}">',
        r'<meta name="twitter:description" content="[^"]*">':
            f'<meta name="twitter:description" content="{texte["meta.ogDescription"]}">',
        r'<meta property="og:image:alt" content="[^"]*">':
            '<meta property="og:image:alt" content="FLEXR — Match. Train. Repeat. '
            'Dating for gym people in Austria.">',
        r'<meta name="twitter:image:alt" content="[^"]*">':
            '<meta name="twitter:image:alt" content="FLEXR — dating for gym people in Austria.">',
    }
    for muster, neu in ersatz_meta.items():
        html, anzahl = re.subn(muster, lambda _m, n=neu: n, html, count=1)
        if anzahl != 1:
            sys.exit(f"FEHLER: Meta-Angabe nicht ersetzt: {muster}")

    # JSON-LD: dieselbe Organisation, aber eine eigene WebPage-Sprache und
    # englische Beschreibungen. Die @id der Organisation bleibt bewusst gleich -
    # es ist dasselbe Unternehmen, nicht ein zweites.
    # `inLanguage` steht zweimal (WebSite und SoftwareApplication) - beide.
    html = html.replace('"inLanguage": "de-AT"', '"inLanguage": "en"')

    json_ld_ersatz = [
        (
            '"@id": "https://flexr.social/#website",\n      "url": "https://flexr.social/",',
            '"@id": "https://flexr.social/en/#website",\n      "url": "https://flexr.social/en/",',
        ),
        (
            '"@id": "https://flexr.social/#app",',
            '"@id": "https://flexr.social/en/#app",',
        ),
        (
            '"operatingSystem": "Web, Android",\n      "url": "https://flexr.social/",',
            '"operatingSystem": "Web, Android",\n      "url": "https://flexr.social/en/",',
        ),
        (
            '"description": "Betreiber der Dating-App FLEXR für Gym-People in Österreich. '
            'Nicht verwandt mit gleichnamigen Fitness- oder Software-Anbietern.",',
            '"description": "Operator of the FLEXR dating app for gym people in Austria. '
            'Not affiliated with similarly named fitness or software providers.",',
        ),
        (
            '"description": "Dating-App für Gym-People in Österreich: '
            'Matches nach Fitnessstudio und Umkreis.",',
            '"description": "Dating app for gym people in Austria: '
            'matches by gym and radius.",',
        ),
        (
            '"description": "Die Nutzung von FLEXR ist dauerhaft kostenlos; es wird kein '
            'Zahlungsmittel hinterlegt. FLEXR Premium kostet 10 € pro Monat, ist freiwillig '
            'und monatlich kündbar."',
            '"description": "Using FLEXR is permanently free; no payment method is stored. '
            'FLEXR Premium costs €10 per month, is optional and can be cancelled monthly."',
        ),
        ('"areaServed": { "@type": "Country", "name": "Österreich" }',
         '"areaServed": { "@type": "Country", "name": "Austria" }'),
    ]
    for alt, neu in json_ld_ersatz:
        if alt not in html:
            sys.exit(f"FEHLER: JSON-LD-Stelle nicht gefunden:\n  {alt[:90]}")
        html = html.replace(alt, neu, 1)

    return html


def hinweis_einfuegen(html: str) -> str:
    """Kopfkommentar: die Datei ist erzeugt, nicht von Hand gepflegt."""
    kopf = (
        "<!--\n"
        "  ERZEUGTE DATEI — nicht von Hand bearbeiten.\n"
        "\n"
        "  Quelle ist frontend/index.html (deutsche Fassung, einzige Quelle des\n"
        "  Markups) plus die englischen Texte aus frontend/i18n-landing.js und\n"
        "  frontend/i18n.js. Neu erzeugen mit:\n"
        "\n"
        "      python3 frontend/build-en.py\n"
        "\n"
        "  Aenderungen hier gehen beim naechsten Lauf verloren.\n"
        "-->\n"
    )
    return html.replace("<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + kopf, 1)


def main() -> None:
    html = QUELLE.read_text(encoding="utf-8")
    texte = lies_woerterbuch(WOERTERBUECHER, "en")

    html, fehlend = ersetze_auszeichnungen(html, texte)
    if fehlend:
        sys.exit(
            "FEHLER: keine englische Fassung fuer "
            + ", ".join(sorted(set(fehlend)))
        )

    html = englische_kopfdaten(html, texte)
    html = rechtslinks_umbiegen(html)
    html = hinweis_einfuegen(html)

    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(html, encoding="utf-8")
    print(f"geschrieben: {ZIEL.relative_to(HIER.parent)} ({len(html):,} Zeichen)")


if __name__ == "__main__":
    main()
