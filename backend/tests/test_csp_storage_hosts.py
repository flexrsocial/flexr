"""Die Content-Security-Policy muss die Storage-Hosts kennen.

Am 15.08.2026 hat genau das den Foto-Upload lahmgelegt. Die Policy erlaubte
``connect-src 'self'``, der Upload geht aber als Presigned PUT direkt an
``<account>.r2.cloudflarestorage.com``. Der Browser brach ihn ohne HTTP-Status
ab; im Frontend stand "Failed to fetch". Dasselbe bei ``img-src``: erlaubt war
``photos.flexr.social`` - eine Domain, die es noch gar nicht gibt
(LEGAL_REVIEW.md D-01) - ausgeliefert wird aber von ``pub-<id>.r2.dev``.

Gefunden wurde es erst, als es ausfiel: Im Konfigurationstext sehen ein
richtiger und ein falscher Hostname gleich aus.

Geprueft wird hier die Mechanik von ``tools/check_csp_hosts.py``, nicht die
Produktionskonfiguration - die .env des Servers liegt nicht im Repository.
Das Skript selbst wird auf dem Server gegen die echte .env gefahren (siehe
sein Modul-Docstring). Diese Tests halten es davon ab, unbemerkt zu verrotten:
Ein Pruefskript, das nichts mehr prueft, ist schlimmer als keines.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKRIPT = REPO / "tools" / "check_csp_hosts.py"
SNIPPET = REPO / "deploy" / "nginx-security-snippet.conf"


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


def test_upload_und_anzeige_haben_je_einen_eigenen_host(pruefer, policy):
    """Der Kern des Ausfalls: Beide Direktiven brauchen mehr als 'self'.

    Welcher Host richtig ist, weiss nur die .env des jeweiligen Servers. Dass
    ueberhaupt einer dasteht, laesst sich hier pruefen - und genau das war am
    15.08.2026 nicht der Fall.
    """
    for direktive in ("connect-src", "img-src"):
        quellen = pruefer.hosts_der_direktive(policy, direktive)
        fremde = [q for q in quellen if q.startswith("https://")]
        assert fremde, (
            f"{direktive} nennt keinen Storage-Host. Presigned PUT bzw. die "
            f"Anzeige der Profilfotos laufen dann in eine CSP-Blockade.")


def test_erkennt_einen_fehlenden_host(pruefer, tmp_path):
    """Gegenprobe: Die kaputte Policy von 5b0c4a8 muss auffallen."""
    kaputt = ("add_header Content-Security-Policy \"default-src 'self'; "
              "img-src 'self' data: blob: https://photos.flexr.social; "
              "connect-src 'self'\" always;")
    p = pruefer.policy_aus_snippet(kaputt)

    erlaubte = pruefer.hosts_der_direktive(p, "connect-src")
    assert not [q for q in erlaubte if q.startswith("https://")]

    bilder = pruefer.hosts_der_direktive(p, "img-src")
    assert "https://pub-0fa239128c094c37bb3bf410428cf0ba.r2.dev" not in bilder


def test_env_leser_ignoriert_kommentare_und_anfuehrungszeichen(pruefer, tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        '# Kommentar\n'
        'S3_ENDPOINT_URL="https://beispiel.r2.cloudflarestorage.com"\n'
        '\n'
        "S3_PUBLIC_BASE_URL='https://pub-beispiel.r2.dev'\n",
        encoding="utf-8")
    werte = pruefer.lies_env(env)
    assert werte["S3_ENDPOINT_URL"] == "https://beispiel.r2.cloudflarestorage.com"
    assert werte["S3_PUBLIC_BASE_URL"] == "https://pub-beispiel.r2.dev"


def test_direktive_wird_nicht_mit_einer_anderen_verwechselt(pruefer, policy):
    """``img-src`` darf nicht als Treffer fuer ``src`` durchgehen und
    ``connect-src`` nicht die Quellen von ``default-src`` erben."""
    assert pruefer.hosts_der_direktive(policy, "src") == []
    assert pruefer.hosts_der_direktive(policy, "frame-ancestors") == ["'none'"]
