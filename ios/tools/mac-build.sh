#!/usr/bin/env bash
#
# FLEXR iOS — alles, was auf dem Mac zu tun ist, in einem Skript.
#
# Das Projekt ist auf einem Linux-Rechner ohne Xcode entstanden. Dieses Skript
# nimmt die Schritte ab, die sonst von Hand in der Xcode-Oberfläche laufen —
# Team-ID eintragen, übersetzen, testen, archivieren, hochladen.
#
#   ./ios/tools/mac-build.sh team ABCDE12345   # Team-ID einmalig eintragen
#   ./ios/tools/mac-build.sh check             # Toolchain und Projekt prüfen
#   ./ios/tools/mac-build.sh test              # Übersetzen + Unit-Tests
#   ./ios/tools/mac-build.sh archive           # Release-Archiv bauen
#   ./ios/tools/mac-build.sh upload            # Archiv zu App Store Connect
#   ./ios/tools/mac-build.sh all               # check + test + archive
#
# Ohne Argument gibt das Skript diese Hilfe aus und macht sonst nichts.

set -euo pipefail

IOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJEKT="$IOS_DIR/FLEXR.xcodeproj"
PBXPROJ="$PROJEKT/project.pbxproj"
SCHEMA="FLEXR"
BUILD_DIR="$IOS_DIR/build"
ARCHIV="$BUILD_DIR/FLEXR.xcarchive"
EXPORT_DIR="$BUILD_DIR/export"
# Simulator: irgendein iPhone der aktuellen Runtime. Xcode sucht sich selbst
# ein passendes Gerät, wenn nur der Name grob stimmt.
ZIEL="${FLEXR_DESTINATION:-platform=iOS Simulator,name=iPhone 16}"

rot()   { printf '\033[31m%s\033[0m\n' "$*"; }
gruen() { printf '\033[32m%s\033[0m\n' "$*"; }
info()  { printf '\033[1m==> %s\033[0m\n' "$*"; }

team_id_aus_projekt() {
    sed -n 's/.*FLEXR_DEVELOPMENT_TEAM = "\{0,1\}\([A-Z0-9]*\)"\{0,1\};.*/\1/p' "$PBXPROJ" | head -1
}

cmd_team() {
    local id="${1:-}"
    if [[ -z "$id" ]]; then
        rot "Bitte die zehnstellige Team-ID angeben:"
        echo "    ./ios/tools/mac-build.sh team ABCDE12345"
        echo
        echo "Sie steht in App Store Connect unter Account → Membership,"
        echo "oder in Xcode unter Settings → Accounts → Team."
        exit 1
    fi
    if [[ ! "$id" =~ ^[A-Z0-9]{10}$ ]]; then
        rot "„$id\" sieht nicht wie eine Team-ID aus (10 Zeichen, A–Z und 0–9)."
        exit 1
    fi
    cp "$PBXPROJ" "$PBXPROJ.bak"
    # Nur die Projektebene anfassen; die Ziele erben über $(FLEXR_DEVELOPMENT_TEAM).
    sed -i '' "s/FLEXR_DEVELOPMENT_TEAM = \"\";/FLEXR_DEVELOPMENT_TEAM = $id;/g" "$PBXPROJ"
    sed -i '' "s/FLEXR_DEVELOPMENT_TEAM = [A-Z0-9]\{10\};/FLEXR_DEVELOPMENT_TEAM = $id;/g" "$PBXPROJ"
    gruen "Team-ID $id eingetragen (Sicherung: project.pbxproj.bak)."
}

cmd_check() {
    info "Toolchain"
    if ! command -v xcodebuild >/dev/null; then
        rot "xcodebuild fehlt. Xcode aus dem App Store installieren, danach einmal"
        echo "    sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
        echo "    sudo xcodebuild -license accept"
        exit 1
    fi
    xcodebuild -version
    echo "Swift: $(swift --version 2>&1 | head -1)"

    info "Projekt"
    local team
    team="$(team_id_aus_projekt)"
    if [[ -z "$team" ]]; then
        rot "Keine Team-ID eingetragen — Signieren schlägt fehl."
        echo "    ./ios/tools/mac-build.sh team ABCDE12345"
    else
        gruen "Team-ID: $team"
    fi
    grep -m1 "MARKETING_VERSION" "$PBXPROJ" | tr -d '\t'
    grep -m1 "CURRENT_PROJECT_VERSION" "$PBXPROJ" | tr -d '\t'
    grep -m1 "PRODUCT_BUNDLE_IDENTIFIER" "$PBXPROJ" | tr -d '\t'

    info "Simulatoren"
    xcrun simctl list devices available | grep -i iphone | head -5 ||
        rot "Keine iPhone-Simulatoren installiert (Xcode → Settings → Components)."
}

cmd_test() {
    info "Übersetzen und Unit-Tests ($ZIEL)"
    # Der allererste Übersetzungsvorgang dieses Projekts überhaupt — mit
    # Kleinigkeiten ist zu rechnen, siehe ios/HANDOFF.md.
    xcodebuild test \
        -project "$PROJEKT" \
        -scheme "$SCHEMA" \
        -destination "$ZIEL" \
        -derivedDataPath "$BUILD_DIR/DerivedData" \
        CODE_SIGNING_ALLOWED=NO \
        | tee "$BUILD_DIR/test.log" \
        | grep -E "error:|warning:|Test Suite|Test Case .*(passed|failed)|\*\* (TEST|BUILD)" || true
    gruen "Vollständige Ausgabe: $BUILD_DIR/test.log"
}

cmd_archive() {
    local team
    team="$(team_id_aus_projekt)"
    [[ -n "$team" ]] || { rot "Erst die Team-ID eintragen (siehe 'team')."; exit 1; }

    info "Release-Archiv"
    rm -rf "$ARCHIV"
    xcodebuild archive \
        -project "$PROJEKT" \
        -scheme "$SCHEMA" \
        -configuration Release \
        -destination "generic/platform=iOS" \
        -archivePath "$ARCHIV" \
        -allowProvisioningUpdates \
        | tee "$BUILD_DIR/archive.log" \
        | grep -E "error:|\*\* ARCHIVE" || true

    [[ -d "$ARCHIV" ]] || { rot "Kein Archiv entstanden — siehe $BUILD_DIR/archive.log"; exit 1; }
    gruen "Archiv: $ARCHIV"

    cat > "$BUILD_DIR/ExportOptions.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key><string>app-store-connect</string>
    <key>teamID</key><string>$team</string>
    <key>uploadSymbols</key><true/>
    <key>destination</key><string>export</string>
    <key>signingStyle</key><string>automatic</string>
</dict>
</plist>
PLIST
    gruen "Exportvorgaben: $BUILD_DIR/ExportOptions.plist"
}

cmd_upload() {
    [[ -d "$ARCHIV" ]] || { rot "Kein Archiv vorhanden — erst 'archive' laufen lassen."; exit 1; }
    info "Export und Upload zu App Store Connect"
    rm -rf "$EXPORT_DIR"
    xcodebuild -exportArchive \
        -archivePath "$ARCHIV" \
        -exportOptionsPlist "$BUILD_DIR/ExportOptions.plist" \
        -exportPath "$EXPORT_DIR" \
        -allowProvisioningUpdates

    local ipa
    ipa="$(find "$EXPORT_DIR" -name '*.ipa' | head -1)"
    [[ -n "$ipa" ]] || { rot "Keine .ipa im Export gefunden."; exit 1; }
    gruen "IPA: $ipa"

    echo
    echo "Hochladen (App-spezifisches Passwort aus appleid.apple.com nötig):"
    echo "    xcrun altool --upload-app -f \"$ipa\" -t ios \\"
    echo "        -u DEINE-APPLE-ID -p DEIN-APP-SPEZIFISCHES-PASSWORT"
    echo
    echo "Alternativ ohne Passwort auf der Kommandozeile: Xcode öffnen,"
    echo "Window → Organizer → Archives → Distribute App."
}

mkdir -p "$BUILD_DIR"

case "${1:-hilfe}" in
    team)    shift; cmd_team "${1:-}" ;;
    check)   cmd_check ;;
    test)    cmd_check; cmd_test ;;
    archive) cmd_archive ;;
    upload)  cmd_upload ;;
    all)     cmd_check; cmd_test; cmd_archive ;;
    *)       awk 'NR>1 && /^#/ { sub(/^# ?/, ""); print; next } NR>1 { exit }' \
                 "${BASH_SOURCE[0]}" ;;
esac
