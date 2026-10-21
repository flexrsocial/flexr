#!/bin/bash
# S3-Attrappe (Moto) auf Port 5055. Haelt alles im Speicher: nach einem
# Neustart seed_store.py neu laufen lassen.
VENV="${FLEXR_TEST_VENV:-$HOME/.cache/flexr-test/venv}"
exec "$VENV/bin/moto_server" -H 127.0.0.1 -p 5055
