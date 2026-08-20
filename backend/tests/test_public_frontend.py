"""Regressionstests fuer indexierbare Seiten und statische Auslieferung."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree


REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
NGINX = REPO / "deploy" / "nginx-flexr.conf"

PUBLIC_PAGES = {
    "index.html": "https://flexr.social/",
    "faq.html": "https://flexr.social/faq.html",
    "sicherheit.html": "https://flexr.social/sicherheit.html",
    "nutzungsrichtlinien.html": "https://flexr.social/nutzungsrichtlinien.html",
    "meldung.html": "https://flexr.social/meldung.html",
    "widerruf.html": "https://flexr.social/widerruf.html",
    "agb.html": "https://flexr.social/agb.html",
    "datenschutz.html": "https://flexr.social/datenschutz.html",
    "impressum.html": "https://flexr.social/impressum.html",
    "strafverfolgung.html": "https://flexr.social/strafverfolgung.html",
}


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

        assert html.get("lang") == "de-AT", filename
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
    assert '<div class="account-section-title">Profil</div>' in account
    assert '<div class="account-section-title">Fotos</div>' in account
    assert '<div class="account-section-title">Konto</div>' in account
    assert '.screen.active{ display:flex; flex-direction:column; flex:1; min-height:0; overflow-y:auto;' in app


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
    assert "flexr-shell-v8" in worker
    assert "url.pathname.startsWith('/photos/')" in worker
    assert "url.pathname.startsWith('/dl-')" in worker
    assert "STATIC_PREFIXES" in worker


def test_sitemap_enthaelt_nur_oeffentliche_kanonische_seiten():
    root = ElementTree.parse(FRONTEND / "sitemap.xml").getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {node.text for node in root.findall("s:url/s:loc", ns)}
    assert urls == set(PUBLIC_PAGES.values())
    assert all(node.text == "2026-08-20" for node in root.findall("s:url/s:lastmod", ns))
