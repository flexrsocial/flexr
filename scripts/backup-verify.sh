#!/usr/bin/env bash
#
# Restore-Test.
#
# Ein Backup, das nie zurueckgespielt wurde, ist kein Backup. Dieses Skript
# spielt den letzten Snapshot in eine Wegwerf-Datenbank ein, vergleicht sie mit
# den Pruefwerten, die backup.sh beim Sichern mitgeschrieben hat, und raeumt
# wieder auf. Laeuft woechentlich per Timer.
#
# Zusaetzlich liest `restic check --read-data-subset` einen Teil der Daten
# wirklich aus, statt nur die Struktur zu pruefen — das faengt stille
# Bitfehler im Repository.
#
set -euo pipefail

readonly CONFIG_DIR=/etc/flexr
readonly APP_ENV=/flexr/backend/.env
readonly SCRATCH_DB=flexr_restoretest
readonly STATUS_FILE=/var/lib/flexr/backup-verify-status.json
readonly READ_DATA_SUBSET="${BACKUP_VERIFY_SUBSET:-10%}"

log() { printf '%s  %s\n' "$(date --iso-8601=seconds)" "$*"; }

# Fuehrt einen Befehl als Datenbankbenutzer aus.
#
# `runuser` statt `sudo`, wenn wir bereits root sind: `sudo` ist setuid und
# wird von `NoNewPrivileges=true` im systemd-Dienst blockiert. `runuser`
# braucht kein setuid und funktioniert dort. Fuer den Aufruf von Hand durch
# einen Nicht-root-Benutzer bleibt `sudo` der Weg.
as_postgres() {
  if [[ $EUID -eq 0 ]]; then
    runuser -u postgres -- "$@"
  else
    sudo -u postgres -- "$@"
  fi
}

write_status() {
  install -d -m 750 "$(dirname "$STATUS_FILE")"
  printf '{"state":"%s","detail":"%s","finishedAt":"%s"}\n' \
    "$1" "${2//\"/}" "$(date --iso-8601=seconds)" > "$STATUS_FILE"
  chmod 640 "$STATUS_FILE"
}

die() { log "FEHLER: $*" >&2; write_status "failed" "$*"; drop_scratch; exit 1; }

drop_scratch() {
  as_postgres psql -q -c "DROP DATABASE IF EXISTS $SCRATCH_DB;" >/dev/null 2>&1 || true
}

[[ -r "$CONFIG_DIR/backup.env" ]] || die "$CONFIG_DIR/backup.env fehlt oder ist nicht lesbar"
[[ -r "$APP_ENV" ]] || die "$APP_ENV fehlt oder ist nicht lesbar"

set -a
# shellcheck source=/dev/null
. "$CONFIG_DIR/backup.env"
set +a
: "${RESTIC_REPOSITORY:?ist nicht gesetzt}"
: "${RESTIC_PASSWORD_FILE:?ist nicht gesetzt}"
export RESTIC_CACHE_DIR="${RESTIC_CACHE_DIR:-/var/cache/flexr-restic}"

DATABASE_URL="$(grep -m1 '^DATABASE_URL=' "$APP_ENV" | cut -d= -f2-)"
[[ -n "$DATABASE_URL" ]] || die "DATABASE_URL nicht in $APP_ENV gefunden"
readonly LIVE_URL="${DATABASE_URL%%\?*}"

trap drop_scratch EXIT

log "Repository stichprobenartig lesen (${READ_DATA_SUBSET})"
restic check --read-data-subset="$READ_DATA_SUBSET" \
  || die "restic check hat Datenfehler gefunden"

# Ein Restore-Test auf einem wochenalten Snapshot waere gruen, obwohl das
# taegliche Backup laengst nicht mehr laeuft (so geschehen 22.09.-02.10.2026).
readonly MAX_AGE_HOURS="${BACKUP_VERIFY_MAX_AGE_HOURS:-36}"
LATEST_JSON="$(restic snapshots --tag flexr --latest 1 --json)" \
  || die "restic snapshots fehlgeschlagen"
LATEST_TIME="$(jq -r 'max_by(.time) | .time' <<<"$LATEST_JSON")"
LATEST_ID="$(jq -r 'max_by(.time) | .short_id' <<<"$LATEST_JSON")"
[[ -n "$LATEST_TIME" && "$LATEST_TIME" != null ]] || die "Kein Snapshot gefunden"
AGE_HOURS=$(( ($(date +%s) - $(date -d "$LATEST_TIME" +%s)) / 3600 ))
(( AGE_HOURS <= MAX_AGE_HOURS )) \
  || die "Letzter Snapshot ${LATEST_ID} ist ${AGE_HOURS} h alt (Grenze ${MAX_AGE_HOURS} h) - laeuft das taegliche Backup?"
log "Letzter Snapshot ${LATEST_ID}, ${AGE_HOURS} h alt"

# Sind Fotos in der Datenbank, muessen auch welche im Snapshot liegen.
PHOTO_ROWS="$(psql "$LIVE_URL" -tAc "SELECT count(*) FROM photos;")"
PHOTO_FILES="$(restic ls --recursive --json "$LATEST_ID" /var/lib/flexr/backup-work/photos \
  | jq -r 'select(.struct_type == "node" and .type == "file") | .path' | wc -l)"
if (( PHOTO_ROWS > 0 && PHOTO_FILES == 0 )); then
  die "Snapshot ${LATEST_ID} enthaelt keine Fotos, die Datenbank kennt ${PHOTO_ROWS}"
fi
log "Fotos im Snapshot: ${PHOTO_FILES} Dateien (Datenbank: ${PHOTO_ROWS} Eintraege)"

# Pruefwerte, die backup.sh aus demselben Datenbankstand wie den Dump
# mitgeschrieben hat (siehe restore-check.sql). Nicht gegen die Live-Datenbank:
# die hat sich seit dem Backup weiterbewegt, jeder Push dazwischen waere eine
# Abweichung.
readonly RESTORE_CHECK_SQL="$(dirname "$0")/restore-check.sql"
EXPECTED="$(restic dump "$LATEST_ID" /var/lib/flexr/backup-work/restore-check.txt)" \
  || die "Snapshot ${LATEST_ID} enthaelt keine Pruefwerte (restore-check.txt) - von einem backup.sh vor dem 18.10.2026?"
[[ -n "$EXPECTED" ]] || die "Pruefwerte in Snapshot ${LATEST_ID} sind leer"

log "Snapshot ${LATEST_ID} in '$SCRATCH_DB' wiederherstellen"
drop_scratch
"$(dirname "$0")/restore.sh" --target "$SCRATCH_DB" --snapshot "$LATEST_ID" >/dev/null \
  || die "Wiederherstellung fehlgeschlagen"

log "Pruefwerte vergleichen"
# Per Umleitung statt `psql -f`: die Datei oeffnet so root, nicht postgres.
ACTUAL="$(as_postgres psql -d "$SCRATCH_DB" -XqAt -v ON_ERROR_STOP=1 < "$RESTORE_CHECK_SQL")" \
  || die "Pruefwerte der Wiederherstellung nicht ermittelt"

MISMATCHES="$(awk -F'|' '
  NR == FNR { backup[$1] = $2; next }
  { restored[$1] = $2 }
  END {
    for (k in backup)
      if (!(k in restored) || restored[k] != backup[k])
        printf "%s: Backup %s, Wiederherstellung %s; ", k, backup[k], (k in restored ? restored[k] : "fehlt")
    for (k in restored)
      if (!(k in backup))
        printf "%s: nur in der Wiederherstellung (%s); ", k, restored[k]
  }' <(printf '%s\n' "$EXPECTED") <(printf '%s\n' "$ACTUAL"))"
[[ -z "$MISMATCHES" ]] || die "Wiederherstellung weicht vom Backup ab: ${MISMATCHES%; }"
log "  $(wc -l <<<"$EXPECTED") Pruefwerte gleich ($(grep -m1 '^Migrationsstand|' <<<"$EXPECTED" | tr '|' ' '), $(grep -c '^Zeilen ' <<<"$EXPECTED") Tabellen mit Zeilenzahl)"

drop_scratch
write_status "ok" "Restore-Test erfolgreich"
log "Restore-Test erfolgreich"
