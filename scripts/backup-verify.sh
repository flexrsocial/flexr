#!/usr/bin/env bash
#
# Restore-Test.
#
# Ein Backup, das nie zurueckgespielt wurde, ist kein Backup. Dieses Skript
# spielt den letzten Snapshot in eine Wegwerf-Datenbank ein, vergleicht ihn mit
# dem Original und raeumt wieder auf. Laeuft woechentlich per Timer.
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

log "Letzten Snapshot in '$SCRATCH_DB' wiederherstellen"
drop_scratch
"$(dirname "$0")/restore.sh" --target "$SCRATCH_DB" >/dev/null \
  || die "Wiederherstellung fehlgeschlagen"

# --- Vergleich Original gegen Wiederherstellung -----------------------------

query_live()    { psql "$LIVE_URL" -tAc "$1"; }
query_scratch() { as_postgres psql -d "$SCRATCH_DB" -tAc "$1"; }

compare() {
  local label="$1" sql="$2" live scratch
  live="$(query_live "$sql")"
  scratch="$(query_scratch "$sql")"
  if [[ "$live" != "$scratch" ]]; then
    die "$label weicht ab: Original '$live', Wiederherstellung '$scratch'"
  fi
  log "  $label: $live"
}

log "Vergleichen"
compare "Tabellen" \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
compare "Aufzaehlungen" \
  "SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE t.typtype='e' AND n.nspname='public';"
compare "Fremdschluessel" \
  "SELECT count(*) FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY' AND table_schema='public';"
compare "Migrationsstand" \
  "SELECT version_num FROM alembic_version;"

# Zeilenzahlen aller Tabellen auf einmal. Faengt den Fall, dass das Schema
# vollstaendig ist, die Daten aber fehlen.
#
# Exakte Zaehlung ueber query_to_xml statt der Schaetzwerte aus
# `pg_class.reltuples`: Schaetzwerte verlangen ein vorheriges ANALYZE, das als
# nicht privilegierte Rolle ueber die Systemkataloge stolpert, und koennten
# eine Abweichung verdecken. Fuer einen woechentlichen Lauf ist die exakte
# Zaehlung schnell genug.
readonly ROW_COUNT_SQL="
SELECT string_agg(t || ':' || n, ',' ORDER BY t) FROM (
  SELECT c.relname AS t,
         (xpath(
            '/row/cnt/text()',
            query_to_xml(format('SELECT count(*) AS cnt FROM %I.%I', ns.nspname, c.relname),
                         false, true, '')
          ))[1]::text::bigint AS n
  FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
  WHERE ns.nspname = 'public' AND c.relkind = 'r'
) s;"
log "Zeilenzahlen abgleichen"
compare "Zeilen je Tabelle" "$ROW_COUNT_SQL"

drop_scratch
write_status "ok" "Restore-Test erfolgreich"
log "Restore-Test erfolgreich"
