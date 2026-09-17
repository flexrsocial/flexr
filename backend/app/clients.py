"""Welche Art Client fragt gerade an - und was daraus folgt.

FLEXR Premium wird ueber Stripe im Browser verkauft. Genau das verbieten beide
App-Stores innerhalb ihrer Apps:

* **Apple, App Review Guideline 3.1.1** - wer in einer iOS-App Funktionen
  freischaltet, muss dafuer In-App-Kaeufe verwenden. Untersagt sind
  ausdruecklich auch "buttons, external links, or other calls to action that
  direct customers to purchasing mechanisms other than in-app purchase". Ein
  Knopf, der aus der App in einen Stripe-Checkout fuehrt, ist ein
  Ablehnungsgrund - und ebenso der blosse Hinweis, man koenne "auf
  flexr.social" buchen.
* **Google Play, Payments-Policy** - digitale Inhalte, die in der App wirken,
  laufen ueber Play Billing.

Deshalb entscheidet der Server, wem er den Kauf ueberhaupt anbietet, statt das
den Clients zu ueberlassen: Im Browser ist FLEXR Premium buchbar, in den
beiden Apps nicht. Die Apps bekommen dadurch weder Preis noch Abschluss-Knopf
zu sehen - auch die Fassungen, die schon veroeffentlicht oder gerade in
Pruefung sind und von dieser Regel nichts wissen (siehe ``routers/billing.py``,
``membership_status()``).

Die Grenzen des kostenlosen Kontos gelten davon unberuehrt fuer **jeden**:
Sie haengen am Konto, nicht am Geraet. Ein Konto laesst sich sonst dadurch
entgrenzen, dass man dieselbe Anmeldung abwechselnd in App und Browser
benutzt.

Erkennung
---------
Ab den Fassungen dieser Umstellung (Android 2.7.0, iOS ab dem naechsten
Build) schicken beide Apps ``X-Flexr-Client``. Aeltere Fassungen -
darunter der iOS-Build, der bei Apple in Pruefung liegt - kennen den Header
nicht; fuer sie bleibt der User-Agent das Merkmal. Beide sind eindeutig und
stammen nicht aus unserem Code, sondern von der jeweiligen Plattform:

    FLEXR/24 CFNetwork/3896.100.1.2.1 Darwin/27.0.0     (iOS, URLSession)
    okhttp/4.12.0                                       (Android, OkHttp)

Erkannt wird deshalb die **App**, nicht der Browser: Alles andere gilt als
Web. Der umgekehrte Weg - "alles Unbekannte ist eine App" - klaenge
vorsichtiger, traefe aber jedes Skript, jeden Health-Check und jeden Testlauf
und haette nur eine Wirkung: Im Browser waere Premium nicht mehr verkaeuflich,
sobald irgendein Zwischenglied den User-Agent umschreibt. Die beiden Signale
oben kommen von URLSession und OkHttp selbst; sie fallen nicht weg, ohne dass
jemand die Netzwerkschicht der App austauscht - und der schickt dann den
Header.
"""

from enum import Enum

from fastapi import Request

CLIENT_HEADER = "X-Flexr-Client"


class ClientPlatform(str, Enum):
    web = "web"
    ios = "ios"
    android = "android"


def platform(request: Request | None) -> ClientPlatform:
    """Von wo kommt diese Anfrage? Im Zweifel: aus dem Browser."""
    if request is None:
        return ClientPlatform.web

    declared = (request.headers.get(CLIENT_HEADER) or "").strip().lower()
    if declared in ("ios", "android", "web"):
        return ClientPlatform(declared)

    agent = (request.headers.get("user-agent") or "").lower()
    if agent.startswith("flexr/") or ("cfnetwork" in agent and "darwin" in agent):
        return ClientPlatform.ios
    if agent.startswith("okhttp/"):
        return ClientPlatform.android
    return ClientPlatform.web


def is_store_app(request: Request | None) -> bool:
    """Laeuft die Anfrage in einer App aus einem der beiden Stores?

    Der Name sagt bewusst nicht "ist eine App", sondern nennt den Grund:
    Entscheidend ist nicht die Technik, sondern dass fuer diesen Client die
    Regeln eines App-Stores gelten.
    """
    return platform(request) is not ClientPlatform.web
