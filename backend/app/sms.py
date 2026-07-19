"""SMS-Versand für die Telefonprüfung.

Mit konfigurierten Twilio-Zugangsdaten (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
TWILIO_FROM_NUMBER in der .env) wird echt versendet - direkt über die
Twilio-REST-API, ohne zusätzliche Abhängigkeit. Ohne Zugangsdaten wird der
Code nur ins Server-Log geschrieben (Entwicklungs-/Testbetrieb).
"""

import base64
import logging
import urllib.parse
import urllib.request

from .config import settings

logger = logging.getLogger("flexr.sms")


def sms_configured() -> bool:
    return bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_from_number
    )


def send_sms(to_number: str, body: str) -> None:
    if not sms_configured():
        logger.warning("[SMS-DEV] Kein Twilio konfiguriert - SMS an %s: %s", to_number, body)
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    data = urllib.parse.urlencode(
        {"To": to_number, "From": settings.twilio_from_number, "Body": body}
    ).encode()
    auth = base64.b64encode(
        f"{settings.twilio_account_sid}:{settings.twilio_auth_token}".encode()
    ).decode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Basic {auth}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"Twilio-Fehler: HTTP {resp.status}")
