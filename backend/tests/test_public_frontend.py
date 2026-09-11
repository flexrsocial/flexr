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
    for schluessel in ("acct.sectionProfile", "acct.sectionPhotos", "common.account"):
        assert f'<div class="account-section-title" data-i18n="{schluessel}">' in account
    assert '.screen.active{ display:flex; flex-direction:column; flex:1; min-height:0; overflow-y:auto;' in app
    assert '.account-membership-note .membership-link{ margin-top:10px; }' in app
    assert 'color:var(--plate); font-size:12.5px; font-weight:600;' in app
    assert '<div class="consent-setting-action"><button class="membership-link"' in app

    privacy = app.split('<section class="screen" id="screen-privacy">', 1)[1]
    privacy = privacy.split('</section>', 1)[0]
    assert '<nav class="legal-link-list"' in privacy
    # aria-label steht seit dem 09.09.2026 als data-i18n-aria im Markup und
    # wird zur Laufzeit gesetzt - der Schluessel ist die pruefbare Zusicherung.
    assert 'data-i18n-aria="legal.docs.aria"' in privacy
    for page in (
        "datenschutz.html", "agb.html", "widerruf.html",
        "nutzungsrichtlinien.html", "impressum.html", "meldung.html",
    ):
        assert f'href="/{page}"' in privacy


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
