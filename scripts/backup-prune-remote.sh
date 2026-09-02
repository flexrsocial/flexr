#!/usr/bin/env bash
#
# Aufbewahrungsfristen auf dem externen Backup-Ziel (R2) anwenden.
#
# Getrennt von `backup.sh`, weil der taegliche Lauf nur anhaengen und lesen
# soll: ein kompromittierter Server oder ein Bug im taeglichen Job kann so
# hoechstens neue Snapshots schreiben, aber keine alten vernichten. Dieses
# Skript laeuft deutlich seltener (monatlich) als der taegliche Backup-Lauf.
#
# Erwartet in /etc/flexr/backup.env:
#   RESTIC_REPOSITORY_REMOTE, RESTIC_PASSWORD_FILE_REMOTE, Fristen (dieselben
#   wie fuer das lokale Ziel)
#   AWS_ACCESS_KEY_ID_REMOTE_PRUNE, AWS_SECRET_ACCESS_KEY_REMOTE_PRUNE bevorzugt;
#   fehlen sie, faellt dieses Skript mit einer Warnung auf
#   AWS_ACCESS_KEY_ID_REMOTE / AWS_SECRET_ACCESS_KEY_REMOTE zurueck, damit ein
#   einzelner Zugang zum Start ausreicht.
#
set -euo pipefail

readonly CONFIG_DIR=/etc/flexr

log() { printf '%s  %s\n' "$(date --iso-8601=seconds)" "$*"; }
die() { log "FEHLER: $*" >&2; exit 1; }

[[ -r "$CONFIG_DIR/backup.env" ]] || die "$CONFIG_DIR/backup.env fehlt oder ist nicht lesbar"

set -a
# shellcheck source=/dev/null
. "$CONFIG_DIR/backup.env"
set +a

: "${RESTIC_REPOSITORY_REMOTE:?ist nicht gesetzt - kein externes Ziel konfiguriert}"
: "${RESTIC_PASSWORD_FILE_REMOTE:?ist nicht gesetzt}"

if [[ -n "${AWS_ACCESS_KEY_ID_REMOTE_PRUNE:-}" ]]; then
  PRUNE_KEY_ID="$AWS_ACCESS_KEY_ID_REMOTE_PRUNE"
  PRUNE_KEY_SECRET="${AWS_SECRET_ACCESS_KEY_REMOTE_PRUNE:?ist nicht gesetzt, obwohl AWS_ACCESS_KEY_ID_REMOTE_PRUNE gesetzt ist}"
else
  log "WARNUNG: kein eigener Loesch-Zugang (AWS_ACCESS_KEY_ID_REMOTE_PRUNE) konfiguriert, verwende den taeglichen Zugang"
  PRUNE_KEY_ID="${AWS_ACCESS_KEY_ID_REMOTE:?ist nicht gesetzt}"
  PRUNE_KEY_SECRET="${AWS_SECRET_ACCESS_KEY_REMOTE:?ist nicht gesetzt}"
fi

readonly KEEP_DAILY="${BACKUP_RETENTION_DAILY:-14}"
readonly KEEP_WEEKLY="${BACKUP_RETENTION_WEEKLY:-8}"
readonly KEEP_MONTHLY="${BACKUP_RETENTION_MONTHLY:-12}"

export RESTIC_CACHE_DIR="${RESTIC_CACHE_DIR:-/var/cache/flexr-restic}"
install -d -m 700 "$RESTIC_CACHE_DIR"

log "Aufbewahrungsfristen auf dem externen Ziel anwenden (taeglich ${KEEP_DAILY}, woechentlich ${KEEP_WEEKLY}, monatlich ${KEEP_MONTHLY})"
AWS_ACCESS_KEY_ID="$PRUNE_KEY_ID" \
AWS_SECRET_ACCESS_KEY="$PRUNE_KEY_SECRET" \
RESTIC_PASSWORD_FILE="$RESTIC_PASSWORD_FILE_REMOTE" \
  restic --repo "$RESTIC_REPOSITORY_REMOTE" forget \
    --tag flexr \
    --keep-daily "$KEEP_DAILY" \
    --keep-weekly "$KEEP_WEEKLY" \
    --keep-monthly "$KEEP_MONTHLY" \
    --prune \
  || die "restic forget (extern) fehlgeschlagen"

log "Fertig"
