#!/bin/bash
# Lokales Backend auf Port 8000 (der local-Flavor der App spricht 10.0.2.2:8000).
# Ohne SMTP landen Mails im Log ("[MAIL-DEV]") - dort stehen auch Reset-Links.
HIER="$(cd "$(dirname "$0")" && pwd)"
VENV="${FLEXR_TEST_VENV:-$HOME/.cache/flexr-test/venv}"
source "$HIER/env.sh"
cd "$HIER/../../backend"
exec "$VENV/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000
