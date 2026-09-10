#!/usr/bin/env python3
"""Prueft, ob die Content-Security-Policy zu den echten Storage-Hosts passt.

Am 15.08.2026 lief genau das auseinander und legte den Foto-Upload lahm:
``connect-src`` stand auf ``'self'``, der Presigned PUT geht aber an
``<account>.r2.cloudflarestorage.com``. Der Browser brach ihn ohne HTTP-Status
ab - im Frontend sichtbar als "Failed to fetch".

Am 16.08.2026 kam eine zweite Lektion dazu: Die *Anzeige* der Fotos lief
ueber den oeffentlichen R2-Testhost ``pub-<id>.r2.dev`` direkt im Browser.
Der blockte reproduzierbar ausgerechnet Einbettungen von flexr.social selbst
mit HTTP 403 (direkte Aufrufe und Einbettungen ohne Referer gingen klaglos
durch) - Cloudflare fuehrt diesen Testhost ausdruecklich als nicht fuer
Produktionsbetrieb geeignet. Der Fix: ``deploy/nginx-flexr.conf`` holt das
Objekt jetzt server-seitig ueber die Location ``/photos/`` und reicht es
weiter. Fuer den Browser ist das kein Cross-Origin-Bild mehr, ``img-src``
braucht nur noch ``'self'`` - ``S3_PUBLIC_BASE_URL`` muss deshalb auf den
eigenen Ursprung zeigen (``https://flexr.social/photos``), nicht mehr auf R2.

Geprueft wird hier die Mechanik, nicht die Produktionskonfiguration - die
.env des Servers liegt nicht im Repository. Das Skript selbst wird auf dem
Server gegen die echte .env gefahren:

    python3 tools/check_csp_hosts.py                  # nimmt backend/.env
    python3 tools/check_csp_hosts.py /flexr/backend/.env

Rueckgabewert 0 = alles sauber, 1 = Befunde (Details auf stdout).
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
SNIPPET = REPO / "deploy" / "nginx-security-snippet.conf"
NGINX_SITE = REPO / "deploy" / "nginx-flexr.conf"

EIGENER_URSPRUNG = "flexr.social"


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


def proxy_ziel_fuer(text: str, pfad: str) -> str | None:
    """Host, an den die ``location <pfad>/`` in nginx-flexr.conf weiterreicht.

    Der Pfad kommt aus ``S3_PUBLIC_BASE_URL`` und wird NICHT fest verdrahtet:
    Zeigt die Basis-URL auf ``/bilder``, nginx hat aber nur ``location
    /photos/``, dann liefert niemand die Fotos aus. Genau das uebersah die
    fruehere Fassung, weil sie immer nach ``/photos/`` suchte.

    Seit dem 10.09.2026 steht im ``proxy_pass`` keine Zeichenkette mehr,
    sondern eine Variable (``proxy_pass https://$r2_host``) - nur so loest
    nginx den Namen zur Laufzeit auf und stirbt nicht beim Start, wenn DNS
    gerade ausfaellt. Ohne die Aufloesung unten haette dieses Werkzeug fortan
    bloss "$r2_host" gemeldet und damit gar nichts mehr geprueft.
    """
    pfad = "/" + pfad.strip("/") + "/"
    block = re.search(
        r"location\s+" + re.escape(pfad) + r"\s*\{([^}]*)\}", text)
    if not block:
        return None
    treffer = re.search(r"proxy_pass\s+https?://([^/;\s]+)", block.group(1))
    if not treffer:
        return None
    ziel = treffer.group(1)
    if ziel.startswith("$"):
        gesetzt = re.search(
            r"set\s+" + re.escape(ziel) + r"\s+([^;\s]+)\s*;", block.group(1))
        return gesetzt.group(1) if gesetzt else None
    return ziel


# Oeffentliche R2-Hosts heissen "pub-<32 Hex>.r2.dev"; der S3-API-Endpunkt
# dagegen "<account>.r2.cloudflarestorage.com". Die beiden zu verwechseln ist
# der naheliegendste Fehler - siehe pruefe_proxy_ziel().
R2_PUBLIC = re.compile(r"^pub-[0-9a-f]{32}\.r2\.dev$")


def pruefe_proxy_ziel(ziel: str, endpunkt: str) -> list:
    """Plausibilitaet des Hosts, an den /photos/ weiterreicht.

    Statisch laesst sich **nicht** feststellen, ob es derselbe Bucket ist wie
    in S3_ENDPOINT_URL: Der oeffentliche Host traegt eine eigene, undurchsichtige
    ID (``pub-<32 Hex>``), der Endpunkt die Account-ID. Aus der einen folgt die
    andere nicht. Was sich pruefen laesst, sind die beiden Verwechslungen, die
    tatsaechlich passieren:
    """
    befunde = []
    endpunkt_host = urlparse(endpunkt).netloc if endpunkt else ""

    # 1. Der S3-API-Endpunkt als Proxy-Ziel. Sieht plausibel aus, liefert aber
    #    nichts: Dieser Host verlangt SigV4-signierte Anfragen und beantwortet
    #    einen nackten GET mit 401/403. Jedes Foto waere dann kaputt, ohne dass
    #    an der Konfiguration etwas falsch AUSSAEHE.
    if endpunkt_host and ziel == endpunkt_host:
        befunde.append(
            f"Die Location reicht an den S3-API-Endpunkt weiter ({ziel}). "
            f"Der verlangt signierte Anfragen und beantwortet einen einfachen "
            f"GET mit 401/403 - kein Profilfoto wuerde laden. Ziel muss der "
            f"oeffentliche Bucket-Host sein (pub-<id>.r2.dev).")
        return befunde

    # 2. Irgendein anderer Host. Kann ein Tippfehler sein oder ein Bucket, der
    #    nicht zu diesem Konto gehoert - beides faellt sonst erst auf, wenn
    #    Nutzer leere Bilder melden.
    if not R2_PUBLIC.match(ziel):
        befunde.append(
            f"Die Location reicht an {ziel} weiter - das sieht nicht nach einem "
            f"oeffentlichen R2-Bucket aus (erwartet: pub-<32 Hex>.r2.dev). "
            f"Tippfehler oder falsches Konto fallen sonst erst auf, wenn "
            f"Nutzer leere Bilder melden.")
    return befunde


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

    # ---- connect-src: Presigned PUT geht direkt an S3_ENDPOINT_URL --------
    endpunkt = env.get("S3_ENDPOINT_URL", "")
    if not endpunkt:
        print("– S3_ENDPOINT_URL ist nicht gesetzt, connect-src nicht pruefbar.")
    else:
        host = urlparse(endpunkt).netloc
        erlaubt = hosts_der_direktive(policy, "connect-src")
        if any(urlparse(q).netloc == host for q in erlaubt if "//" in q):
            print(f"✓ connect-src: {host} (Presigned PUT des Foto-Uploads)")
        else:
            befunde.append(
                f"connect-src erlaubt {host} nicht — der Presigned PUT "
                f"(S3_ENDPOINT_URL={endpunkt}) bricht dann ohne HTTP-Status ab.\n"
                f"    erlaubt sind: {' '.join(erlaubt) or '(nichts)'}")

    # ---- img-src: Presigned GET des Admin-Tools --------------------------
    #
    # Diese Pruefung fehlte bis zum 23.08.2026 und liess genau deshalb einen
    # Ausfall durch: frontend/admin.html bettet Verifizierungs-Selfie und
    # Ausweisaufnahme als Presigned GET direkt von S3_ENDPOINT_URL ein
    # (storage.create_presigned_view_url). Die Pruefung unten sah nur die
    # Profilfotos, meldete "img-src 'self' genuegt" - und der Browser blockte
    # die beiden Admin-Bilder still, waehrend die Profilfotos daneben luden.
    if endpunkt:
        host = urlparse(endpunkt).netloc
        erlaubt = hosts_der_direktive(policy, "img-src")
        if any(urlparse(q).netloc == host for q in erlaubt if "//" in q):
            print(f"✓ img-src: {host} (Presigned GET der Verifizierungsaufnahmen im Admin-Tool)")
        else:
            befunde.append(
                f"img-src erlaubt {host} nicht — Selfie und Ausweisaufnahme in "
                f"frontend/admin.html werden dann vom Browser blockiert "
                f"(Profilfotos laufen ueber /photos/ und laden weiterhin).\n"
                f"    erlaubt sind: {' '.join(erlaubt) or '(nichts)'}")

    # ---- img-src: Fotos muessen ueber den eigenen Ursprung laufen ---------
    basis = env.get("S3_PUBLIC_BASE_URL", "")
    if not basis:
        print("– S3_PUBLIC_BASE_URL ist nicht gesetzt, img-src nicht pruefbar.")
    else:
        basis_host = urlparse(basis).netloc
        basis_pfad = urlparse(basis).path.strip("/") or ""
        if EIGENER_URSPRUNG in basis_host:
            print(f"✓ S3_PUBLIC_BASE_URL zeigt auf den eigenen Ursprung ({basis_host}) "
                  f"- fuer die Profilfotos genuegt 'self'.")
            if not basis_pfad:
                befunde.append(
                    f"S3_PUBLIC_BASE_URL ({basis}) hat keinen Pfad. Erwartet "
                    f"wird der Pfad der proxy-Location, etwa "
                    f"https://{EIGENER_URSPRUNG}/photos.")
            else:
                ziel = proxy_ziel_fuer(
                    NGINX_SITE.read_text(encoding="utf-8"), basis_pfad)
                if not ziel:
                    befunde.append(
                        f"S3_PUBLIC_BASE_URL zeigt auf /{basis_pfad}, aber "
                        f"{NGINX_SITE} hat keine Location /{basis_pfad}/ mit "
                        f"proxy_pass. Fotos haetten dann eine URL, die niemand "
                        f"ausliefert.")
                else:
                    ziel_befunde = pruefe_proxy_ziel(ziel, endpunkt)
                    if ziel_befunde:
                        befunde.extend(ziel_befunde)
                    else:
                        print(f"✓ Location /{basis_pfad}/ reicht weiter an {ziel} "
                              f"(oeffentlicher Bucket, nicht der signierte "
                              f"S3-Endpunkt)")
        else:
            # Direkter externer Host (z.B. waehrend einer Migration, bevor der
            # Proxy umgestellt ist) - dann muss img-src ihn explizit nennen.
            erlaubt = hosts_der_direktive(policy, "img-src")
            if any(urlparse(q).netloc == basis_host for q in erlaubt if "//" in q):
                print(f"✓ img-src erlaubt {basis_host} explizit")
            else:
                befunde.append(
                    f"S3_PUBLIC_BASE_URL zeigt auf einen fremden Host ({basis_host}), "
                    f"den img-src nicht erlaubt — die Anzeige der Profilfotos bricht ab.\n"
                    f"    erlaubt sind: {' '.join(erlaubt) or '(nichts)'}")

    if befunde:
        print("\nBefunde:")
        for b in befunde:
            print(f"  ✗ {b}")
        return 1

    print("\nPolicy und Storage-Konfiguration passen zusammen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
