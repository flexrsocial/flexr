#!/usr/bin/env bash
#
# Wiederherstellung aus einem restic-Snapshot.
#
#   restore.sh --target <datenbank> [--snapshot <id>] [--force] [--repository local|remote]
#
# Beispiele:
#   restore.sh --target flexr_wiederherstellung          # neue Datenbank
#   restore.sh --target flexr --force                    # Produktion ersetzen
#   restore.sh --target flexr_probe --repository remote  # Notfallprobe
#
# Ohne --force wird eine bestehende Zieldatenbank NICHT ueberschrieben.
# Das Ziel `flexr` verlangt zusaetzlich eine Eingabe von Hand.
#
# --repository waehlt, aus welchem restic-Repository wiederhergestellt wird.
# Vorgabe `local`. `remote` liest aus dem externen Ziel (RESTIC_REPOSITORY_REMOTE)
# und ist der einzige Weg, den vollstaendigen Verlust des Servers wirklich
# durchzuspielen: das lokale Repository waere in diesem Fall mit dem Server
# selbst weg.
#
set -euo pipefail

readonly CONFIG_DIR=/etc/flexr
readonly APP_ENV=/flexr/backend/.env
readonly PRODUCTION_DB=flexr

TARGET=""
SNAPSHOT="latest"
FORCE=0
REPOSITORY="local"

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

die() { log "FEHLER: $*" >&2; exit 1; }

usage() {
  sed -n '2,17p' "$0" | sed 's/^# \?//'
  exit "${1:-0}"
}

while (( $# )); do
  case "$1" in
    --target)     TARGET="${2:-}"; shift 2 ;;
    --snapshot)   SNAPSHOT="${2:-}"; shift 2 ;;
    --force)      FORCE=1; shift ;;
    --repository) REPOSITORY="${2:-}"; shift 2 ;;
    -h|--help)    usage 0 ;;
    *)            die "Unbekannte Option: $1" ;;
  esac
done

[[ -n "$TARGET" ]] || { log "FEHLER: --target fehlt"; usage 1; }
case "$REPOSITORY" in
  local|remote) ;;
  *) die "--repository muss 'local' oder 'remote' sein, nicht '$REPOSITORY'" ;;
esac

[[ -r "$CONFIG_DIR/backup.env" ]] || die "$CONFIG_DIR/backup.env fehlt oder ist nicht lesbar"
[[ -r "$APP_ENV" ]] || die "$APP_ENV fehlt oder ist nicht lesbar"

set -a
# shellcheck source=/dev/null
. "$CONFIG_DIR/backup.env"
set +a
export RESTIC_CACHE_DIR="${RESTIC_CACHE_DIR:-/var/cache/flexr-restic}"

DATABASE_URL="$(grep -m1 '^DATABASE_URL=' "$APP_ENV" | cut -d= -f2-)"
[[ -n "$DATABASE_URL" ]] || die "DATABASE_URL nicht in $APP_ENV gefunden"

if [[ "$REPOSITORY" == "remote" ]]; then
  # Notfallprobe aus dem externen Ziel: eigene Variablennamen, damit ein Server
  # ohne konfiguriertes externes Ziel weiterhin nur `--repository local` kennt.
  : "${RESTIC_REPOSITORY_REMOTE:?ist nicht gesetzt - kein externes Ziel konfiguriert}"
  : "${RESTIC_PASSWORD_FILE_REMOTE:?ist nicht gesetzt}"
  export RESTIC_REPOSITORY="$RESTIC_REPOSITORY_REMOTE"
  export RESTIC_PASSWORD_FILE="$RESTIC_PASSWORD_FILE_REMOTE"
  export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID_REMOTE:?ist nicht gesetzt}"
  export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY_REMOTE:?ist nicht gesetzt}"
  log "Wiederherstellung aus dem EXTERNEN Ziel"
else
  : "${RESTIC_REPOSITORY:?ist nicht gesetzt}"
  : "${RESTIC_PASSWORD_FILE:?ist nicht gesetzt}"
fi

# Verbindung auf die Zieldatenbank, abgeleitet aus DATABASE_URL.
readonly BASE_URL="${DATABASE_URL%%\?*}"
readonly TARGET_URL="${BASE_URL%/*}/$TARGET"

exists() { as_postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$1'" | grep -q 1; }

if exists "$TARGET"; then
  (( FORCE )) || die "Datenbank '$TARGET' existiert bereits. Mit --force ueberschreiben."
  if [[ "$TARGET" == "$PRODUCTION_DB" ]]; then
    # Bewusst kein Schalter, der das umgeht: der Verlust waere nicht umkehrbar.
    log "WARNUNG: '$TARGET' ist die Produktionsdatenbank und wird VOLLSTAENDIG ersetzt."
    read -r -p "Zum Bestaetigen den Datenbanknamen eingeben: " confirmation
    [[ "$confirmation" == "$TARGET" ]] || die "Abgebrochen"
  fi
fi

# Unter /var/lib/flexr statt /var/tmp, weil der Dienst
# `flexr-backup-verify.service` mit ProtectSystem=strict laeuft und nur
# dort schreiben darf.
install -d -m 700 /var/lib/flexr
WORK_DIR="$(mktemp -d /var/lib/flexr/restore.XXXXXXXX)"
chmod 700 "$WORK_DIR"
cleanup() {
  find "$WORK_DIR" -type f -exec shred -u {} + 2>/dev/null || true
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

log "Snapshot '$SNAPSHOT' entpacken"
restic restore "$SNAPSHOT" --tag flexr --target "$WORK_DIR" \
  || die "restic restore fehlgeschlagen"

DUMP="$(find "$WORK_DIR" -name 'flexr.dump' -type f | head -1)"
[[ -n "$DUMP" ]] || die "Im Snapshot ist kein flexr.dump enthalten"
log "Dump gefunden: $DUMP ($(stat -c '%s' "$DUMP") Bytes)"

if exists "$TARGET"; then
  log "Bestehende Datenbank '$TARGET' verwerfen"
  # Offene Verbindungen trennen, sonst schlaegt DROP fehl.
  as_postgres psql -q -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$TARGET' AND pid <> pg_backend_pid();" >/dev/null
  as_postgres psql -q -c "DROP DATABASE \"$TARGET\";"
fi

log "Datenbank '$TARGET' anlegen"
as_postgres createdb -O postgres "$TARGET"

log "Dump einspielen"
# --no-owner, weil der Dump ohne Eigentuemer erzeugt wurde und die Rolle im
# Zielsystem anders heissen kann.
pg_restore --no-owner --dbname="$TARGET_URL" "$DUMP" \
  || die "pg_restore fehlgeschlagen"

TABLES="$(psql "$TARGET_URL" -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")"
log "Wiederhergestellt: $TABLES Tabellen in '$TARGET'"

log "Fertig. Migrationsstand pruefen mit:"
log "  sudo -u postgres psql -d $TARGET -c 'SELECT version_num FROM alembic_version;'"
