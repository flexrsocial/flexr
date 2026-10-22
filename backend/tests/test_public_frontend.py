"""Regressionstests fuer indexierbare Seiten und statische Auslieferung."""

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree


REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
NGINX = REPO / "deploy" / "nginx-flexr.conf"

#: Rechts- und Infoseiten. Es gibt sie zweimal: deutsch an der Wurzel,
#: englisch unter /en/ mit demselben Dateinamen.
LEGAL_PAGES = [
    "faq.html", "sicherheit.html", "nutzungsrichtlinien.html", "meldung.html",
    "widerruf.html", "agb.html", "datenschutz.html", "impressum.html",
    "strafverfolgung.html",
    # Seit 22.10.2026: Googles "Child Safety Standards" verlangen eigene,
    # oeffentlich erreichbare Standards mit App-Namen und CSAE-Verbot.
    "kinderschutz.html",
]

PUBLIC_PAGES = {
    "index.html": "https://flexr.social/",
    # Eigene englische Landingpage seit dem 09.09.2026 (build-en.py). Sie ist
    # indexierbar, hat ihre eigene kanonische Adresse und gehoert deshalb in
    # die Sitemap - anders als /app/, das noindex traegt.
    "en/index.html": "https://flexr.social/en/",
}
PUBLIC_PAGES.update({name: f"https://flexr.social/{name}" for name in LEGAL_PAGES})
PUBLIC_PAGES.update(
    {f"en/{name}": f"https://flexr.social/en/{name}" for name in LEGAL_PAGES}
)

#: Such-Einstiegsseiten seit dem 30.09.2026, nur deutsch. Erzeugt von
#: tools/seo/build_seo_pages.py, das sie auch in die Sitemap schreibt.
SEO_PAGES = [
    "gym-dating.html", "gym-crush-ansprechen.html", "date-ideen-sportler.html",
    *(f"fitness-dating-{stadt}.html"
      for stadt in ("wien", "graz", "linz", "salzburg", "innsbruck", "klagenfurt")),
]
PUBLIC_PAGES.update({name: f"https://flexr.social/{name}" for name in SEO_PAGES})


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.ids = set()
        self.images = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
        if tag == "img" and attributes.get("src"):
            self.images.append(attributes)


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def meta_content(parser: PageParser, *, name=None, prop=None):
    for tag, attrs in parser.tags:
        if tag != "meta":
            continue
        if name is not None and attrs.get("name") == name:
            return attrs.get("content")
        if prop is not None and attrs.get("property") == prop:
            return attrs.get("content")
    return None


def test_oeffentliche_seiten_haben_vollstaendige_seo_und_semantik():
    for filename, canonical in PUBLIC_PAGES.items():
        parser = parse_page(FRONTEND / filename)
        html = next(attrs for tag, attrs in parser.tags if tag == "html")
        mains = [attrs for tag, attrs in parser.tags if tag == "main"]
        canonicals = [
            attrs.get("href") for tag, attrs in parser.tags
            if tag == "link" and attrs.get("rel") == "canonical"
        ]

        erwartete_sprache = "en" if filename.startswith("en/") else "de-AT"
        assert html.get("lang") == erwartete_sprache, filename
        assert len(mains) == 1 and mains[0].get("id") == "main-content", filename
        assert any(link == "#main-content" for link in parser.links), filename
        assert meta_content(parser, name="description"), filename
        assert "index" in meta_content(parser, name="robots"), filename
        assert canonicals == [canonical], filename
        assert meta_content(parser, prop="og:url") == canonical, filename
        assert meta_content(parser, prop="og:image") == "https://flexr.social/og-image.png", filename


def test_statische_bilder_reservieren_ihren_layoutplatz():
    for filename in ("index.html", "app/index.html"):
        parser = parse_page(FRONTEND / filename)
        for image in parser.images:
            assert image.get("width") and image.get("height"), (filename, image.get("src"))


def test_kontoprofil_bleibt_offen_und_scrollbar():
    app = (FRONTEND / "app" / "index.html").read_text(encoding="utf-8")
    account = app.split('<section class="screen" id="screen-account">', 1)[1]
    account = account.split('</section>', 1)[0]

    assert '<details class="account-disclosure"' not in account
    # ".lg" seit c6a49c7 (groessere, weisse Fettschrift fuer die drei
    # Untermenueueberschriften) - dieselbe Klasse an gleicher Stelle im
    # Verifizierungs-Gate (#screen-verify-gate) bleibt bewusst ohne ".lg".
    for schluessel in ("acct.sectionProfile", "acct.sectionPhotos", "common.account"):
        assert f'<div class="account-section-title lg" data-i18n="{schluessel}">' in account
    assert '.screen.active{ display:flex; flex-direction:column; flex:1; min-height:0; overflow-y:auto;' in app
    # Die Statuskarte "Dein Konto ist kostenlos ..." (.account-membership-note)
    # ist seit Sitzung 19.09.2026 (7) komplett entfernt - fuer alle Kontostufen,
    # nicht nur fuer Premium.
    assert 'account-membership-note' not in app
    # Seit 15.10.2026: Einwilligung widerrufen/erteilen als Kompaktknopf
    # (.pill-action) statt unterstrichenem Text (.membership-link).
    assert '.pill-action{' in app
    assert '<div class="consent-setting-action"><button type="button" class="pill-action danger" data-revoke=' in app
    assert 'membership-link' not in app
    # Benachrichtigungen, Abo und Datenschutz als Einstellungs-Liste in einer
    # eigenen Sektion statt unterstrichener Links unter "Konto loeschen".
    assert '<div class="account-section-title lg" data-i18n="acct.sectionSettings">' in account
    for knopf in ("btnOpenNotifications", "btnManageSubscription", "btnOpenPrivacy"):
        assert f'class="settings-row" id="{knopf}"' in account
    assert 'account-footer-link' not in app

    privacy = app.split('<section class="screen" id="screen-privacy">', 1)[1]
    privacy = privacy.split('</section>', 1)[0]
    assert '<nav class="legal-link-list settings-list"' in privacy
    # aria-label steht seit dem 09.09.2026 als data-i18n-aria im Markup und
    # wird zur Laufzeit gesetzt - der Schluessel ist die pruefbare Zusicherung.
    assert 'data-i18n-aria="legal.docs.aria"' in privacy
    for page in (
        "datenschutz.html", "agb.html", "widerruf.html",
        "nutzungsrichtlinien.html", "kinderschutz.html", "impressum.html", "meldung.html",
    ):
        assert f'href="/{page}"' in privacy


def test_kinderschutz_ist_von_ueberall_erreichbar():
    """Googles Child Safety Standards verlangen veroeffentlichte Standards - am
    22.10.2026 verwies nur Abschnitt 7 der Nutzungsrichtlinien darauf, weder die
    Fussleiste der Landingpage noch die Web-App noch die anderen Rechtsseiten."""
    for name, ziel in (("index.html", "/kinderschutz.html"),
                       ("en/index.html", "/en/kinderschutz.html")):
        fuss = (FRONTEND / name).read_text(encoding="utf-8").split('<footer', 1)[1]
        assert f'href="{ziel}"' in fuss, name

    app = (FRONTEND / "app" / "index.html").read_text(encoding="utf-8")
    assert 'data-legal-page="kinderschutz.html"' in app.split('<footer class="legal-footer">', 1)[1]

    for name in [*LEGAL_PAGES, *(f"en/{n}" for n in LEGAL_PAGES), *SEO_PAGES]:
        if name.endswith("kinderschutz.html"):
            continue
        quelle = (FRONTEND / name).read_text(encoding="utf-8")
        nav = re.search(r'<nav class="nav-legal".*?</nav>', quelle, re.S)
        assert nav, name
        ziel = "/en/kinderschutz.html" if name.startswith("en/") else "/kinderschutz.html"
        assert f'href="{ziel}"' in nav.group(0), name


def test_rechtstexte_gibt_es_zweisprachig_und_wechselseitig_verlinkt():
    """Jeder Rechtstext existiert deutsch und englisch und verweist aufeinander.

    Die beiden Fassungen sind zwei eigene Adressen (kein Umschalter zur
    Laufzeit, siehe lang-switch.js). Damit Google sie als Uebersetzungen und
    nicht als doppelten Inhalt liest, muessen BEIDE Seiten denselben Satz
    hreflang-Verweise tragen - eine einseitige Angabe wertet Google nicht.
    """
    for name in LEGAL_PAGES:
        deutsch = (FRONTEND / name).read_text(encoding="utf-8")
        englisch = (FRONTEND / "en" / name).read_text(encoding="utf-8")

        erwartet = {
            "de-AT": f"https://flexr.social/{name}",
            "de": f"https://flexr.social/{name}",
            "en": f"https://flexr.social/en/{name}",
            # Verbindlich ist die deutsche Fassung - sie ist der Standard.
            "x-default": f"https://flexr.social/{name}",
        }
        for seite, quelle in ((name, deutsch), (f"en/{name}", englisch)):
            gefunden = dict(
                re.findall(
                    r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', quelle
                )
            )
            assert gefunden == erwartet, seite

        # Der Regler fuehrt jeweils auf die andere Fassung derselben Seite.
        assert f'<a href="/en/{name}" hreflang="en"' in deutsch, name
        assert f'<a href="/{name}" hreflang="de"' in englisch, name

        # Die englische Fassung sagt, dass die deutsche verbindlich ist.
        assert "German version" in englisch, name


def test_interne_links_zeigen_auf_vorhandene_dateien():
    for filename in PUBLIC_PAGES:
        source = FRONTEND / filename
        parser = parse_page(source)
        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme or href.startswith(("mailto:", "tel:", "#")):
                continue
            if parsed.path in ("", "/"):
                target = FRONTEND / "index.html"
            elif parsed.path.endswith("/"):
                target = FRONTEND / parsed.path.lstrip("/") / "index.html"
            else:
                target = FRONTEND / parsed.path.lstrip("/")
            assert target.exists(), (filename, href)


def test_nginx_liefert_echte_404_und_cachet_nur_versionierte_demo_assets():
    nginx = NGINX.read_text(encoding="utf-8")
    assert "error_page 404 /404.html;" in nginx
    assert "location = /mail-bestaetigen" in nginx
    assert "try_files $uri $uri/ =404;" in nginx
    assert "try_files $uri $uri/ /index.html;" not in nginx
    assert "location /brand/demo/" in nginx
    assert 'max-age=31536000, immutable' in nginx


def test_service_worker_cachet_weder_nutzerfotos_noch_downloads():
    worker = (FRONTEND / "sw.js").read_text(encoding="utf-8")
    # Bewusst nur das Muster, nicht die Nummer: Der Shell-Cache wird bei jeder
    # Aenderung am Shell hochgezaehlt (zuletzt v10). Eine fest verdrahtete
    # Nummer machte diesen Test bei jedem Hochzaehlen rot, ohne dass an der
    # geprueften Eigenschaft - was NICHT gecacht wird - etwas dran waere.
    assert re.search(r"const CACHE = 'flexr-shell-v\d+';", worker)
    assert "url.pathname.startsWith('/photos/')" in worker
    assert "url.pathname.startsWith('/dl-')" in worker
    assert "STATIC_PREFIXES" in worker


def test_service_worker_laedt_dieselben_versionen_vor_wie_die_app():
    """Die Shell muss genau die Adressen vorladen, die die App anfordert.

    Am 25.09.2026 stand die Shell auf /app/i18n-app.js?v=11 und /i18n.js?v=4,
    die App lud laengst ?v=15 bzw. ?v=5: Vorgeladen wurde, was niemand mehr
    abruft, und offline fehlten die aktuellen Texte.
    """
    worker = (FRONTEND / "sw.js").read_text(encoding="utf-8")
    shell = set(re.findall(r"'(/[^']+\?v=\d+)'", worker))
    app = (FRONTEND / "app" / "index.html").read_text(encoding="utf-8")
    angefordert = set(re.findall(r'(?:src|href)="(/[^"]+\?v=\d+)"', app))
    for adresse in sorted(shell):
        pfad = adresse.split("?")[0]
        gleicher_pfad = {a for a in angefordert if a.split("?")[0] == pfad}
        if gleicher_pfad:
            assert adresse in gleicher_pfad, f"{adresse} in sw.js, App laedt {gleicher_pfad}"


def test_noindex_seiten_sind_nicht_zusaetzlich_per_robots_gesperrt():
    """robots.txt-Sperre und noindex heben sich gegenseitig auf.

    Eine per robots.txt gesperrte Seite darf Google nicht laden, sieht das
    noindex also nie und kann die URL trotzdem ohne Inhalt indexieren. Genau
    das meldete die Search Console am 07.09.2026 fuer /admin.html. Seither
    traegt /admin.html den X-Robots-Tag aus nginx statt eines Disallow.
    """
    robots = (FRONTEND / "robots.txt").read_text(encoding="utf-8")
    directives = [
        line.split(":", 1)[1].strip()
        for line in robots.splitlines()
        if line.lower().startswith("disallow:")
    ]
    assert directives == ["/api/", "/dl-"]

    for page, marker in (("admin.html", "noindex"), ("app/index.html", "noindex")):
        parser = parse_page(FRONTEND / page)
        assert marker in meta_content(parser, name="robots"), page

    nginx = NGINX.read_text(encoding="utf-8")
    admin = nginx.split("location = /admin.html {", 1)[1].split("}", 1)[0]
    assert 'add_header X-Robots-Tag "noindex, nofollow" always;' in admin
    assert "include /etc/nginx/snippets/flexr-security.conf;" in admin


def test_sitemap_enthaelt_nur_oeffentliche_kanonische_seiten():
    root = ElementTree.parse(FRONTEND / "sitemap.xml").getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {node.text for node in root.findall("s:url/s:loc", ns)}
    assert urls == set(PUBLIC_PAGES.values())
    # lastmod wechselt mit jeder inhaltlichen Aenderung - hier zaehlt nur, dass
    # ueberall ein plausibles Datum steht und keines vergessen wurde.
    lastmods = [node.text for node in root.findall("s:url/s:lastmod", ns)]
    assert len(lastmods) == len(urls)
    assert all(re.fullmatch(r"20\d\d-\d\d-\d\d", d) for d in lastmods)


def _woerterbuch(quelltext: str, sprache: str, ende: str) -> set[str]:
    """Schluessel des Blocks `<sprache>: {` bis zum Beginn von `ende`."""
    start = re.search(rf"^\s+{sprache}: \{{", quelltext, re.M).end()
    stop = re.search(rf"^\s+{ende}: \{{", quelltext[start:], re.M) if ende else None
    block = quelltext[start:start + stop.start()] if stop else quelltext[start:]
    return set(re.findall(r"^\s+'([\w.]+)':", block, re.M))


def test_app_texte_gibt_es_in_beiden_sprachen():
    """Jeder feste Schluessel, den die Web-App per t('...') abfragt, steht im
    deutschen und im englischen Woerterbuch.

    Fehlt einer, zeigt FlexrI18n den nackten Schluessel ("chat.yesterday") bzw.
    auf Englisch den deutschen Text. Zusammengesetzte Schluessel
    (t('reg.step' + n)) erfasst der Ausdruck bewusst nicht.
    """
    app = (FRONTEND / "app" / "index.html").read_text(encoding="utf-8")
    texte = (FRONTEND / "app" / "i18n-app.js").read_text(encoding="utf-8")
    gemeinsam = (FRONTEND / "i18n.js").read_text(encoding="utf-8")
    deutsch = _woerterbuch(texte, "de", "en") | _woerterbuch(gemeinsam, "de", "en")
    englisch = _woerterbuch(texte, "en", "") | _woerterbuch(gemeinsam, "en", "")
    verwendet = set(re.findall(r"\bt\('([\w.]+)'\s*[,)]", app))
    assert {"chat.today", "chat.yesterday"} <= verwendet
    assert verwendet - deutsch == set()
    assert verwendet - englisch == set()
