"""Die Content-Security-Policy muss zur tatsaechlichen Foto-Auslieferung passen.

Zwei getrennte Ausfaelle, beide am Verhaeltnis zwischen CSP und
Storage-Konfiguration:

15.08.2026 - Upload: ``connect-src`` stand auf ``'self'``, der Presigned PUT
geht aber direkt an ``<account>.r2.cloudflarestorage.com``. Der Browser brach
die Anfrage ohne HTTP-Status ab ("Failed to fetch").

16.08.2026 - Anzeige: Fotos liefen zunaechst direkt vom oeffentlichen
R2-Testhost ``pub-<id>.r2.dev``. Der blockte reproduzierbar Einbettungen von
flexr.social selbst mit HTTP 403 (direkte Aufrufe und referrer-lose
Einbettungen liefen klaglos durch) - ein Testhost, den Cloudflare
ausdruecklich nicht fuer Produktionsbetrieb vorsieht. Der Fix: Die Location
``/photos/`` in ``deploy/nginx-flexr.conf`` holt das Objekt server-seitig und
reicht es weiter; fuer den Browser ist es kein Cross-Origin-Bild mehr,
``img-src 'self'`` genuegt. ``S3_PUBLIC_BASE_URL`` muss deshalb auf den
eigenen Ursprung zeigen, nicht mehr auf R2.

Geprueft wird hier die Mechanik von ``tools/check_csp_hosts.py``, nicht die
Produktionskonfiguration - die .env des Servers liegt nicht im Repository.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKRIPT = REPO / "tools" / "check_csp_hosts.py"
SNIPPET = REPO / "deploy" / "nginx-security-snippet.conf"
NGINX_SITE = REPO / "deploy" / "nginx-flexr.conf"


@pytest.fixture(scope="module")
def pruefer():
    spec = importlib.util.spec_from_file_location("check_csp_hosts", SKRIPT)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def policy(pruefer):
    return pruefer.policy_aus_snippet(SNIPPET.read_text(encoding="utf-8"))


def test_snippet_hat_ueberhaupt_eine_policy(policy):
    assert "default-src" in policy


def test_connect_src_erlaubt_einen_externen_host(pruefer, policy):
    """Der Presigned PUT geht direkt an R2 - dafuer braucht connect-src mehr
    als 'self', sonst bricht der Upload ohne HTTP-Status ab."""
    quellen = pruefer.hosts_der_direktive(policy, "connect-src")
    fremde = [q for q in quellen if q.startswith("https://")]
    assert fremde, "connect-src nennt keinen Storage-Host - der Presigned PUT bricht ab."


def test_img_src_erlaubt_den_eigenen_ursprung(pruefer, policy):
    """Profilfotos laufen seit dem Proxy in /photos/ ueber den eigenen
    Ursprung (siehe test_photos_proxy_existiert_und_hat_ein_ziel)."""
    quellen = pruefer.hosts_der_direktive(policy, "img-src")
    assert "'self'" in quellen


def test_img_src_erlaubt_den_storage_endpunkt(pruefer, policy):
    """Gegenstueck zum Ausfall vom 23.08.2026.

    frontend/admin.html bettet Verifizierungs-Selfie und Ausweisaufnahme als
    Presigned GET direkt von S3_ENDPOINT_URL ein - ein Proxy wie /photos/
    scheidet dort aus, weil der offen ist und diese Aufnahmen nur der
    angemeldete Admin sehen darf. Ohne den Host in img-src blockt der Browser
    genau diese beiden Bilder still, waehrend die Profilfotos daneben laden.

    Derselbe Host steht in connect-src (Presigned PUT des Uploads); beide
    Direktiven muessen ihn nennen.
    """
    connect_hosts = [
        q for q in pruefer.hosts_der_direktive(policy, "connect-src")
        if q.startswith("https://")
    ]
    img_hosts = [
        q for q in pruefer.hosts_der_direktive(policy, "img-src")
        if q.startswith("https://")
    ]
    assert img_hosts, (
        "img-src nennt keinen Storage-Host - Selfie und Ausweisaufnahme im "
        "Admin-Tool werden vom Browser blockiert."
    )
    assert set(connect_hosts) <= set(img_hosts), (
        f"Storage-Host in connect-src, aber nicht in img-src: "
        f"{set(connect_hosts) - set(img_hosts)}"
    )


def test_erkennt_fehlenden_img_src_host_fuer_admin_aufnahmen(pruefer, tmp_path):
    """Gegenprobe: Die kaputte Policy von vor dem 23.08.2026 muss auffallen -
    connect-src nennt den Endpunkt, img-src nicht."""
    env = tmp_path / ".env"
    env.write_text(
        "S3_ENDPOINT_URL=https://beispiel.r2.cloudflarestorage.com\n"
        "S3_PUBLIC_BASE_URL=https://flexr.social/photos\n",
        encoding="utf-8")

    import subprocess
    import sys
    kaputt = tmp_path / "snippet.conf"
    kaputt.write_text(
        'add_header Content-Security-Policy "default-src \'self\'; '
        "img-src 'self' data: blob:; "
        'connect-src \'self\' https://beispiel.r2.cloudflarestorage.com" always;',
        encoding="utf-8")

    p = pruefer.policy_aus_snippet(kaputt.read_text(encoding="utf-8"))
    erlaubt = pruefer.hosts_der_direktive(p, "img-src")
    assert not [q for q in erlaubt if q.startswith("https://")], (
        "Die Gegenprobe-Policy soll gerade KEINEN img-src-Host haben."
    )


def test_photos_proxy_existiert_und_hat_ein_ziel(pruefer):
    text = NGINX_SITE.read_text(encoding="utf-8")
    ziel = pruefer.photos_proxy_ziel(text)
    assert ziel, "Location /photos/ mit proxy_pass fehlt in deploy/nginx-flexr.conf"
    assert "r2" in ziel, f"Unerwartetes Proxy-Ziel fuer /photos/: {ziel}"


def test_erkennt_fehlenden_connect_src_host(pruefer, tmp_path):
    """Gegenprobe: Die kaputte Policy von 5b0c4a8 muss auffallen."""
    kaputt = ('add_header Content-Security-Policy "default-src \'self\'; '
              'img-src \'self\' data: blob:; '
              'connect-src \'self\'" always;')
    p = pruefer.policy_aus_snippet(kaputt)
    erlaubte = pruefer.hosts_der_direktive(p, "connect-src")
    assert not [q for q in erlaubte if q.startswith("https://")]


def test_erkennt_fremden_host_ohne_img_src_eintrag(pruefer, tmp_path):
    """Falls S3_PUBLIC_BASE_URL wieder auf einen fremden Host zeigt (z.B.
    waehrend einer Migration, bevor der Proxy umgestellt ist), muss img-src
    ihn explizit nennen - sonst bricht die Anzeige."""
    env = tmp_path / ".env"
    env.write_text(
        "S3_ENDPOINT_URL=https://beispiel.r2.cloudflarestorage.com\n"
        "S3_PUBLIC_BASE_URL=https://pub-fremd.r2.dev\n",
        encoding="utf-8")

    import subprocess
    import sys
    ergebnis = subprocess.run(
        [sys.executable, str(SKRIPT), str(env)],
        capture_output=True, text=True)
    assert ergebnis.returncode == 1
    assert "pub-fremd.r2.dev" in ergebnis.stdout


def test_akzeptiert_gleichen_ursprung_fuer_fotos(pruefer, policy, tmp_path):
    # connect-src-Host muss zum echten Snippet passen, sonst schlaegt die
    # erste Pruefung fehl, bevor die zweite (der eigentliche Testgegenstand)
    # ueberhaupt zum Zug kommt.
    echter_connect_host = [
        q for q in pruefer.hosts_der_direktive(policy, "connect-src")
        if q.startswith("https://")
    ][0]

    env = tmp_path / ".env"
    env.write_text(
        f"S3_ENDPOINT_URL={echter_connect_host}\n"
        "S3_PUBLIC_BASE_URL=https://flexr.social/photos\n",
        encoding="utf-8")

    import subprocess
    import sys
    ergebnis = subprocess.run(
        [sys.executable, str(SKRIPT), str(env)],
        capture_output=True, text=True)
    assert ergebnis.returncode == 0, ergebnis.stdout


def test_env_leser_ignoriert_kommentare_und_anfuehrungszeichen(pruefer, tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        '# Kommentar\n'
        'S3_ENDPOINT_URL="https://beispiel.r2.cloudflarestorage.com"\n'
        '\n'
        "S3_PUBLIC_BASE_URL='https://flexr.social/photos'\n",
        encoding="utf-8")
    werte = pruefer.lies_env(env)
    assert werte["S3_ENDPOINT_URL"] == "https://beispiel.r2.cloudflarestorage.com"
    assert werte["S3_PUBLIC_BASE_URL"] == "https://flexr.social/photos"


def test_direktive_wird_nicht_mit_einer_anderen_verwechselt(pruefer, policy):
    """``img-src`` darf nicht als Treffer fuer ``src`` durchgehen und
    ``connect-src`` nicht die Quellen von ``default-src`` erben."""
    assert pruefer.hosts_der_direktive(policy, "src") == []
    assert pruefer.hosts_der_direktive(policy, "frame-ancestors") == ["'none'"]
