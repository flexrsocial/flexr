#!/usr/bin/env python3
"""Prueft, ob die Content-Security-Policy zu den echten Storage-Hosts passt.

Am 15.08.2026 lief genau das auseinander und legte den Foto-Upload lahm:

  * Die Policy erlaubte als Bildquelle photos.flexr.social - eine Domain, die
    noch gar nicht existiert (LEGAL_REVIEW.md D-01 haelt sie bewusst zurueck).
    Ausgeliefert wurde aber von pub-<id>.r2.dev.
  * connect-src stand auf 'self'. Der Presigned PUT geht aber an
    <account>.r2.cloudflarestorage.com. Der Browser brach ihn ohne HTTP-Status
    ab - im Frontend sichtbar als "Failed to fetch".

Beides war im Konfigurationstext nicht zu sehen, weil dort nur Hostnamen
stehen und nicht, ob sie stimmen. Deshalb dieses Skript: Es haelt die Policy
gegen die tatsaechlich konfigurierten Endpunkte.

Die Pruefung ist bewusst gerichtet, nicht symmetrisch: Ein *zusaetzlicher*
Host in der Policy ist kein Fehler (photos.flexr.social steht dort auf Vorrat
fuer die EU-Migration). Ein *fehlender* ist einer, denn dann bricht der Upload
oder die Anzeige.

    python3 tools/check_csp_hosts.py                  # nimmt backend/.env
    python3 tools/check_csp_hosts.py /flexr/backend/.env

Auf dem Server nach jeder Aenderung an S3_ENDPOINT_URL, S3_PUBLIC_BASE_URL
oder an der Policy laufen lassen - insbesondere bei Schritt 6 des
Migrationsplans in LEGAL_REVIEW.md. Danach zusaetzlich mit

    curl -sI https://flexr.social/app/ | grep -i content-security-policy

nachmessen: Dieses Skript liest die Vorlage im Repository, nicht das, was
nginx am Ende wirklich sendet. Beides kann auseinanderlaufen, und genau die
Luecke hat den Ausfall so lange verdeckt.

Rueckgabewert 0 = alles sauber, 1 = Befunde (Details auf stdout).
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
SNIPPET = REPO / "deploy" / "nginx-security-snippet.conf"

# Welche .env-Variable in welcher Direktive auftauchen muss, und warum.
ERWARTET = [
    ("S3_ENDPOINT_URL", "connect-src",
     "Presigned PUT des Foto-Uploads (putToPresigned() im Frontend)"),
    ("S3_PUBLIC_BASE_URL", "img-src",
     "Anzeige der Profilfotos"),
]


def lies_env(pfad: Path) -> dict:
    """Minimaler .env-Leser. Kein dotenv-Paket, damit das Skript auch auf einem
    Server laeuft, auf dem nur die venv des Backends existiert."""
    werte = {}
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        schluessel, _, wert = zeile.partition("=")
        werte[schluessel.strip()] = wert.strip().strip('"').strip("'")
    return werte


def policy_aus_snippet(text: str) -> str:
    treffer = re.search(
        r'add_header\s+Content-Security-Policy\s+"([^"]*)"', text)
    if not treffer:
        raise SystemExit(f"Keine Content-Security-Policy in {SNIPPET} gefunden.")
    return treffer.group(1)


def hosts_der_direktive(policy: str, direktive: str) -> list:
    """Alle Quellen einer Direktive. Die Policy ist mit ';' getrennt, die
    Direktive selbst mit Leerzeichen."""
    for teil in policy.split(";"):
        teil = teil.strip()
        if teil.split(" ")[0] == direktive:
            return teil.split(" ")[1:]
    return []


def main() -> int:
    env_pfad = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "backend" / ".env"
    if not env_pfad.exists():
        print(f"Keine .env unter {env_pfad}.")
        print("Pfad als Argument angeben, etwa: "
              "python3 tools/check_csp_hosts.py /flexr/backend/.env")
        return 1

    env = lies_env(env_pfad)
    policy = policy_aus_snippet(SNIPPET.read_text(encoding="utf-8"))

    befunde = []
    for variable, direktive, zweck in ERWARTET:
        url = env.get(variable, "")
        if not url:
            print(f"– {variable} ist in {env_pfad} nicht gesetzt, "
                  f"{direktive} nicht pruefbar.")
            continue

        host = urlparse(url).netloc
        if not host:
            befunde.append(f"{variable}={url!r} ist keine brauchbare URL.")
            continue

        erlaubte = hosts_der_direktive(policy, direktive)
        passt = any(urlparse(q).netloc == host for q in erlaubte if "//" in q)
        if passt:
            print(f"✓ {direktive}: {host} ({zweck})")
        else:
            befunde.append(
                f"{direktive} erlaubt {host} nicht — {zweck} bricht ab.\n"
                f"    {variable} = {url}\n"
                f"    erlaubt sind: {' '.join(erlaubte) or '(nichts)'}")

    if befunde:
        print("\nBefunde:")
        for b in befunde:
            print(f"  ✗ {b}")
        return 1

    print("\nPolicy und Storage-Konfiguration passen zusammen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
