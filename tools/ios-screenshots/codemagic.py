"""iOS-Bildschirmfotos ueber die Codemagic-API starten und abholen.

    python3 tools/ios-screenshots/codemagic.py start [WORKFLOW]  # Lauf starten (ios-screenshots)
    python3 tools/ios-screenshots/codemagic.py hol [BUILD_ID]    # warten, Artefakte laden
    python3 tools/ios-screenshots/codemagic.py status [WORKFLOW] # letzte Laeufe (ios-tests)

Automatisch startet Codemagic nichts: Es gibt keinen Webhook von GitHub
(Stand 15.10.2026 waren alle 49 Laeufe von Hand gestartete ios-flexr). Nach
einem Push auf ios/ deshalb "start ios-tests" und danach "hol".

Der API-Token kommt aus CODEMAGIC_TOKEN oder der Datei
~/.config/flexr/codemagic-token (Codemagic: Teams/Benutzer-Einstellungen ->
Integrations -> Codemagic API -> Token). Er gehoert nicht ins Repository.
Bilder landen in ios-screenshots/<build-id>/ (in .gitignore).
"""

import json
import os
import pathlib
import sys
import time
import urllib.request

API = "https://api.codemagic.io"
REPO = pathlib.Path(__file__).resolve().parents[2]
ZIEL = REPO / "ios-screenshots"
LETZTER = ZIEL / "letzter-build.txt"


def token() -> str:
    wert = os.environ.get("CODEMAGIC_TOKEN")
    if not wert:
        datei = pathlib.Path.home() / ".config" / "flexr" / "codemagic-token"
        if datei.exists():
            wert = datei.read_text().strip()
    if not wert:
        sys.exit("Kein Codemagic-Token (CODEMAGIC_TOKEN oder ~/.config/flexr/codemagic-token).")
    return wert


def anfrage(pfad: str, daten: dict | None = None, roh: bool = False):
    req = urllib.request.Request(
        pfad if pfad.startswith("http") else API + pfad,
        data=json.dumps(daten).encode() if daten is not None else None,
        headers={"x-auth-token": token(), "Content-Type": "application/json"},
        method="POST" if daten is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=60) as antwort:
        inhalt = antwort.read()
    return inhalt if roh else json.loads(inhalt or b"{}")


def app_id() -> str:
    apps = anfrage("/apps").get("applications", [])
    for app in apps:
        url = (app.get("repository") or {}).get("htmlUrl", "") + app.get("appName", "")
        if "flexr" in url.lower():
            return app["_id"]
    sys.exit(f"Keine FLEXR-App unter {len(apps)} Codemagic-Apps gefunden.")


def start(workflow: str = "ios-screenshots") -> str:
    build = anfrage("/builds", {"appId": app_id(), "workflowId": workflow, "branch": "main"})
    build_id = build["buildId"]
    ZIEL.mkdir(exist_ok=True)
    LETZTER.write_text(build_id)
    print("Gestartet:", build_id)
    return build_id


def hol(build_id: str | None) -> None:
    build_id = build_id or LETZTER.read_text().strip()
    while True:
        build = anfrage(f"/builds/{build_id}")["build"]
        status = build.get("status")
        print(time.strftime("%H:%M:%S"), status)
        if status in ("finished", "failed", "canceled", "timeout", "skipped"):
            break
        time.sleep(30)
    ordner = ZIEL / build_id
    ordner.mkdir(parents=True, exist_ok=True)
    for artefakt in build.get("artefacts", []) + build.get("artifacts", []):
        name = artefakt.get("name", "")
        if not name:
            continue
        (ordner / name).write_bytes(anfrage(artefakt["url"], roh=True))
        print("geladen:", ordner / name)
    print("Status:", status)


def letzter_status(workflow: str) -> None:
    # Workflows aus codemagic.yaml stehen in fileWorkflowId, nicht workflowId.
    builds = [b for b in anfrage(f"/builds?appId={app_id()}").get("builds", [])
              if workflow in (b.get("fileWorkflowId"), b.get("workflowId"))]
    for build in builds[:5]:
        print(build.get("_id"), build.get("status"), build.get("startedAt"),
              (build.get("commit") or {}).get("hash", "")[:8])
    if not builds:
        print("Keine Laeufe von", workflow)


if __name__ == "__main__":
    befehl = sys.argv[1] if len(sys.argv) > 1 else "start"
    if befehl == "start":
        start(sys.argv[2] if len(sys.argv) > 2 else "ios-screenshots")
    elif befehl == "hol":
        hol(sys.argv[2] if len(sys.argv) > 2 else None)
    elif befehl == "status":
        letzter_status(sys.argv[2] if len(sys.argv) > 2 else "ios-tests")
    else:
        sys.exit(__doc__)
