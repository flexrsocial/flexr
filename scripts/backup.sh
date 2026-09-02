#!/usr/bin/env bash
#
# Verschluesseltes Backup der FLEXR-Datenbank und der Server-Konfiguration.
#
# Wird vom systemd-Timer `flexr-backup.timer` aufgerufen, laeuft aber auch
# von Hand. Legt einen restic-Snapshot lokal UND auf dem externen R2-Ziel an
# und wendet die Aufbewahrungsfristen nur lokal an - das Aufraeumen auf dem
# externen Ziel uebernimmt `backup-prune-remote.sh` (siehe dort, warum
# getrennt).
#
# Erwartet:
#   /etc/flexr/backup.env    RESTIC_REPOSITORY(_REMOTE), RESTIC_PASSWORD_FILE(_REMOTE),
#                             AWS_ACCESS_KEY_ID_REMOTE, AWS_SECRET_ACCESS_KEY_REMOTE, Fristen
#   /flexr/backend/.env       DATABASE_URL (nur ausgelesen, nie ausgefuehrt)
#
set -euo pipefail

readonly CONFIG_DIR=/etc/flexr
readonly APP_ENV=/flexr/backend/.env
readonly STATUS_FILE=/var/lib/flexr/backup-status.json

log() { printf '%s  %s\n' "$(date --iso-8601=seconds)" "$*"; }
die() { log "FEHLER: $*" >&2; write_status "failed" "$*"; exit 1; }

write_status() {
  install -d -m 750 "$(dirname "$STATUS_FILE")"
  printf '{"state":"%s","detail":"%s","finishedAt":"%s","snapshotId":"%s"}\n' \
    "$1" "${2//\"/}" "$(date --iso-8601=seconds)" "${SNAPSHOT_ID:-}" > "$STATUS_FILE"
  chmod 640 "$STATUS_FILE"
}

[[ -r "$CONFIG_DIR/backup.env" ]] || die "$CONFIG_DIR/backup.env fehlt oder ist nicht lesbar"
[[ -r "$APP_ENV" ]] || die "$APP_ENV fehlt oder ist nicht lesbar"

set -a
# shellcheck source=/dev/null
. "$CONFIG_DIR/backup.env"
set +a

: "${RESTIC_REPOSITORY:?ist nicht gesetzt}"
: "${RESTIC_PASSWORD_FILE:?ist nicht gesetzt}"

# Nur den einen Wert auslesen statt die App-.env zu sourcen - die soll nie
# als Shell-Code ausgefuehrt werden, auch nicht versehentlich.
DATABASE_URL="$(grep -m1 '^DATABASE_URL=' "$APP_ENV" | cut -d= -f2-)"
[[ -n "$DATABASE_URL" ]] || die "DATABASE_URL nicht in $APP_ENV gefunden"

readonly KEEP_DAILY="${BACKUP_RETENTION_DAILY:-14}"
readonly KEEP_WEEKLY="${BACKUP_RETENTION_WEEKLY:-8}"
readonly KEEP_MONTHLY="${BACKUP_RETENTION_MONTHLY:-12}"

SNAPSHOT_ID=""

# Der Cache beschleunigt jeden Folgelauf erheblich. Ohne ihn liest restic bei
# jedem Durchgang das gesamte Repository neu. `ProtectHome=true` im
# systemd-Dienst sperrt /root aus, deshalb ein eigener Pfad.
export RESTIC_CACHE_DIR="${RESTIC_CACHE_DIR:-/var/cache/flexr-restic}"
install -d -m 700 "$RESTIC_CACHE_DIR"

# Arbeitsverzeichnis nur fuer root lesbar: der Dump enthaelt Klartextdaten,
# bevor restic ihn verschluesselt.
#
# Der Pfad ist bewusst FEST und nicht `mktemp`. restic erkennt einen
# Vorgaengersnapshot ueber den Pfad; bei wechselnden Zufallsnamen findet es nie
# einen und speichert jedes Mal eine Vollkopie statt nur der Aenderungen.
readonly WORK_DIR=/var/lib/flexr/backup-work
scrub_work_dir() {
  # Ueberschreiben statt nur loeschen, damit der Dump nicht im freien
  # Speicher liegen bleibt.
  [[ -d "$WORK_DIR" ]] || return 0
  find "$WORK_DIR" -type f -exec shred -u {} + 2>/dev/null || true
  rm -rf "$WORK_DIR"
}
# Reste eines abgebrochenen Vorlaufs entfernen, bevor neu gesichert wird.
scrub_work_dir
install -d -m 700 "$WORK_DIR"
trap scrub_work_dir EXIT

log "Datenbank sichern"
# -Fc ist das komprimierte Eigenformat und laesst selektives Restore zu.
pg_dump --format=custom --no-owner --no-privileges \
  --file="$WORK_DIR/flexr.dump" "${DATABASE_URL%%\?*}" \
  || die "pg_dump fehlgeschlagen"

# Schemastand im Klartext dazu: erlaubt Diff und Sichtpruefung ohne Restore.
pg_dump --schema-only --no-owner --no-privileges \
  --file="$WORK_DIR/schema.sql" "${DATABASE_URL%%\?*}" \
  || die "pg_dump (Schema) fehlgeschlagen"

DUMP_SIZE="$(stat -c '%s' "$WORK_DIR/flexr.dump")"
(( DUMP_SIZE > 0 )) || die "Der Dump ist leer"
log "Dump erzeugt, ${DUMP_SIZE} Bytes"

log "Lokalen Snapshot schreiben"
# Die App-.env wird mitgesichert - sie enthaelt Zugangsdaten (DB, S3, Stripe,
# SMTP, Telegram), liegt im restic-Repository aber verschluesselt. Das
# restic-Passwort selbst gehoert NICHT hierher, sondern in einen
# Passwortspeicher ausserhalb des Servers.
restic backup \
  --tag flexr --tag automatisch \
  --host flexr \
  "$WORK_DIR" "$APP_ENV" \
  || die "restic backup (lokal) fehlgeschlagen"

SNAPSHOT_ID="$(restic snapshots --tag flexr --latest 1 --json | sed -n 's/.*"short_id":"\([^"]*\)".*/\1/p' | tail -1)"
log "Snapshot ${SNAPSHOT_ID:-unbekannt}"

log "Aufbewahrungsfristen anwenden (taeglich ${KEEP_DAILY}, woechentlich ${KEEP_WEEKLY}, monatlich ${KEEP_MONTHLY})"
restic forget \
  --tag flexr \
  --keep-daily "$KEEP_DAILY" \
  --keep-weekly "$KEEP_WEEKLY" \
  --keep-monthly "$KEEP_MONTHLY" \
  --prune \
  || die "restic forget fehlgeschlagen"

log "Struktur pruefen"
restic check || die "restic check fehlgeschlagen"

if [[ -n "${RESTIC_REPOSITORY_REMOTE:-}" ]]; then
  # Zweites, externes Ziel. Ohne dieses Ziel ueberlebt kein Backup den
  # Verlust des Servers, da lokales Repository und Datenbank auf derselben
  # Platte liegen. Bewusst OHNE `restic forget --prune`: das Aufraeumen
  # uebernimmt der seltener laufende `backup-prune-remote.sh`, damit ein
  # taeglich automatisiert laufender Job nicht routinemaessig Loeschrechte
  # auf dem externen Ziel ausuebt.
  : "${RESTIC_PASSWORD_FILE_REMOTE:?ist nicht gesetzt, obwohl RESTIC_REPOSITORY_REMOTE gesetzt ist}"
  : "${AWS_ACCESS_KEY_ID_REMOTE:?ist nicht gesetzt, obwohl RESTIC_REPOSITORY_REMOTE gesetzt ist}"
  : "${AWS_SECRET_ACCESS_KEY_REMOTE:?ist nicht gesetzt, obwohl RESTIC_REPOSITORY_REMOTE gesetzt ist}"

  log "Externes Ziel sichern"
  AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID_REMOTE" \
  AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY_REMOTE" \
  RESTIC_PASSWORD_FILE="$RESTIC_PASSWORD_FILE_REMOTE" \
    restic --repo "$RESTIC_REPOSITORY_REMOTE" backup \
      --tag flexr --tag automatisch \
      --host flexr \
      "$WORK_DIR" "$APP_ENV" \
    || die "restic backup (extern) fehlgeschlagen"

  log "Externes Ziel: Struktur pruefen"
  AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID_REMOTE" \
  AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY_REMOTE" \
  RESTIC_PASSWORD_FILE="$RESTIC_PASSWORD_FILE_REMOTE" \
    restic --repo "$RESTIC_REPOSITORY_REMOTE" check \
    || die "restic check (extern) fehlgeschlagen"
else
  log "WARNUNG: kein externes Ziel konfiguriert (RESTIC_REPOSITORY_REMOTE)"
fi

write_status "ok" "Snapshot ${SNAPSHOT_ID:-unbekannt}"
log "Fertig"
