"""Telegram-Push ans Admin-Team, sobald im Admin-Dashboard eine neue Aufgabe
entsteht (Meldung, Foto-Prüfung, Verifizierung, Gym-Vorschlag, markierte
Nachricht).

Mit konfigurierten Zugangsdaten (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID in der
.env) wird echt versendet - direkt über die Telegram-Bot-API, ohne
zusätzliche Abhängigkeit. Ohne Zugangsdaten landet die Nachricht nur im
Server-Log (Entwicklungs-/Testbetrieb), analog zu app/sms.py und app/mailer.py.

Ein Fehlschlag beim Versand darf nie den auslösenden Vorgang kippen: Wer eine
Meldung abschickt, hat sie abgeschickt - auch wenn Telegram gerade streikt.
Deshalb fängt notify_admin_task() alles ab und meldet nur, ob es geklappt hat.
"""

import json
import logging
import urllib.error
import urllib.request

from .config import settings

logger = logging.getLogger("flexr.telegram")


def telegram_configured() -> bool:
    return bool(settings.telegram_bot_token and settings.telegram_chat_id)


def notify_admin_task(text: str) -> bool:
    if not telegram_configured():
        logger.warning("[TELEGRAM-DEV] Kein Bot konfiguriert - Push unterdrückt: %s", text)
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = json.dumps({"chat_id": settings.telegram_chat_id, "text": text}).encode()

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status >= 300:
                logger.error("Telegram-Push fehlgeschlagen: HTTP %s", resp.status)
                return False
        return True
    except (urllib.error.URLError, OSError):
        logger.exception("Telegram-Push fehlgeschlagen")
        return False
