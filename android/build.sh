#!/usr/bin/env bash
# FLEXR Android-Build (Trusted Web Activity) — ein Kommando, reproduzierbar.
#
#   bash android/build.sh
#
# Baut aus der live deployten PWA (https://flexr.social) eine signierte
# Android-App:
#   android/app-release-bundle.aab   -> Upload in die Play Console
#   android/app-release-signed.apk   -> zum direkten Testen am Handy
#
# Signing-Key: android/android.keystore wird beim ersten Lauf automatisch mit
# einem zufälligen, starken Passwort erzeugt. Passwort + Fingerprint landen in
# android/KEYSTORE-CREDENTIALS.txt. BEIDE Dateien sichern und NIE ins Git!
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

# --- Toolchain (user-lokal, kein root nötig) -------------------------------
[ -f "$HERE/.buildenv.sh" ] && source "$HERE/.buildenv.sh"
command -v bubblewrap >/dev/null || { echo "FEHLER: bubblewrap nicht im PATH. Erst 'npm i -g @bubblewrap/cli'."; exit 1; }

JDK_BIN="$HOME/.bubblewrap/jdk/jdk-17.0.11+9/bin"   # von Bubblewrap heruntergeladen
[ -d "$JDK_BIN" ] && export PATH="$JDK_BIN:$PATH"
command -v keytool >/dev/null || { echo "FEHLER: keytool (JDK 17) nicht gefunden."; exit 1; }

KEYSTORE="$HERE/android.keystore"
ALIAS="flexr"
CREDS="$HERE/KEYSTORE-CREDENTIALS.txt"

# --- Signing-Key einmalig erzeugen -----------------------------------------
if [ ! -f "$KEYSTORE" ]; then
  echo ">> Erzeuge neuen Signing-Key (einmalig) ..."
  PW="$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24)"
  keytool -genkeypair -v \
    -keystore "$KEYSTORE" -alias "$ALIAS" \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass "$PW" -keypass "$PW" \
    -dname "CN=FLEXR, OU=FLEXR, O=FLEXR, L=Wien, ST=Wien, C=AT"
  {
    echo "FLEXR Android Signing-Key — STRENG GEHEIM, niemals ins Git!"
    echo "Erzeugt: $(date -Iseconds)"
    echo "Keystore: android/android.keystore"
    echo "Alias:    $ALIAS"
    echo "Passwort (Store + Key): $PW"
    echo
    echo "SHA256-Fingerprint (für .well-known/assetlinks.json):"
    keytool -list -v -keystore "$KEYSTORE" -alias "$ALIAS" -storepass "$PW" | grep -i 'SHA256:' || true
  } > "$CREDS"
  chmod 600 "$CREDS" "$KEYSTORE"
  echo ">> Passwort + Fingerprint in $CREDS gespeichert. SICHERN!"
fi

# Passwort für Bubblewrap bereitstellen (liest diese Env-Variablen)
PW="$(grep -m1 'Passwort (Store + Key):' "$CREDS" | sed 's/.*: //')"
export BUBBLEWRAP_KEYSTORE_PASSWORD="$PW"
export BUBBLEWRAP_KEY_PASSWORD="$PW"

# --- Build -----------------------------------------------------------------
# Zweistufig und komplett nicht-interaktiv:
#   1) update regeneriert das Android-Projekt exakt aus twa-manifest.json
#      (--skipVersionUpgrade verhindert die interaktive Versions-Abfrage).
#   2) build sieht dann keine Änderungen mehr und läuft ohne Prompts durch.
# stdin ist geschlossen (< /dev/null): sollte doch ein Prompt kommen, bricht es
# sofort ab statt endlos zu hängen. Version wird in twa-manifest.json gepflegt
# (appVersion + appVersionName + appVersionCode).
echo ">> Regeneriere Android-Projekt aus twa-manifest.json ..."
rm -rf "$HERE/app" "$HERE/manifest-checksum.txt" "$HERE"/*.aab "$HERE"/*.apk "$HERE"/*.idsig 2>/dev/null || true
bubblewrap update --skipVersionUpgrade < /dev/null

echo ">> Baue App-Bundle + APK ..."
bubblewrap build --skipPwaValidation < /dev/null

echo
echo "FERTIG. Artefakte:"
ls -la "$HERE"/*.aab "$HERE"/*.apk 2>/dev/null || true
echo
echo "SHA256-Fingerprint (muss in frontend/.well-known/assetlinks.json):"
grep -i 'SHA256:' "$CREDS" || true
