#!/usr/bin/env bash
#
# Meldet einen fehlgeschlagenen systemd-Dienst per Telegram ans Admin-Team.
#
#   notify-failure.sh <unit>
#
# Wird von `flexr-notify-failure@.service` aufgerufen, das die Backup-Dienste
# per `OnFailure=` ausloesen. Ohne diese Meldung fiel das taegliche Backup vom
# 22.09. bis 02.10.2026 unbemerkt aus.
#
# Liegt im Betrieb als Kopie unter /usr/local/sbin/flexr-notify-failure und
# NICHT unter /flexr/scripts: fehlt der Checkout-Ordner, muss die Warnung
# trotzdem rausgehen - genau das war damals die Ursache.
#
# Zugangsdaten: TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID aus der App-.env
# (dieselben wie fuer die Admin-Pushes, siehe backend/app/telegram.py).
#
set -euo pipefail

readonly APP_ENV=/flexr/backend/.env
readonly UNIT="${1:?Aufruf: notify-failure.sh <unit>}"

env_value() { grep -m1 "^$1=" "$APP_ENV" 2>/dev/null | cut -d= -f2- | tr -d '"'"'" || true; }

TOKEN="$(env_value TELEGRAM_BOT_TOKEN)"
CHAT_ID="$(env_value TELEGRAM_CHAT_ID)"
if [[ -z "$TOKEN" || -z "$CHAT_ID" ]]; then
  echo "Kein Telegram-Bot in $APP_ENV konfiguriert - Meldung fuer $UNIT nicht versendet" >&2
  exit 1
fi

# Nur die Zeilen des letzten Laufs, nicht die Historie.
INVOCATION="$(systemctl show -p InvocationID --value "$UNIT" 2>/dev/null || true)"
if [[ -n "$INVOCATION" ]]; then
  LOG="$(journalctl --no-pager -o cat -n 12 _SYSTEMD_INVOCATION_ID="$INVOCATION" 2>/dev/null || true)"
else
  LOG="$(journalctl --no-pager -o cat -n 12 -u "$UNIT" 2>/dev/null || true)"
fi

TEXT="$(printf '⚠️ FLEXR: %s fehlgeschlagen (%s, %s)\n\n%s' \
  "$UNIT" "$(hostname)" "$(date '+%d.%m.%Y %H:%M')" "${LOG:0:3500}")"

# Token ueber --config statt in der Befehlszeile, damit er nicht in `ps` steht.
curl -sS --fail --max-time 15 \
  --config - \
  --data-urlencode "chat_id=$CHAT_ID" \
  --data-urlencode "text=$TEXT" \
  -o /dev/null <<<"url = \"https://api.telegram.org/bot${TOKEN}/sendMessage\""
