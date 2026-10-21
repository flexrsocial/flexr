# Android-App im Emulator gegen ein lokales Backend testen

Eingerichtet am 21.10.2026 auf dem ThinkPad (Linux Mint, 8 GB RAM). Damit
liefen die Tests von 2.7.37 (Foto-Wischen) und 2.7.38 (Mail-Links, Passwort
in der App). Produktion wird dabei nicht berührt.

## Einmalig

* **Emulator und Image** (schon installiert): `~/.bubblewrap/android_sdk/emulator`,
  `system-images;android-35;google_apis;x86_64`, AVD `flexr_test` (Pixel 5,
  2 GB RAM, `~/.android/avd/flexr_test.avd`). KVM läuft ohne Gruppe über ACL.
* **Python-Umgebung** unter `~/.cache/flexr-test/venv` (System-Python hat kein
  pip/ensurepip):

  ```bash
  H=~/.cache/flexr-test; mkdir -p $H/dl-getpip
  curl -fsSL -o $H/dl-getpip/get-pip.py https://bootstrap.pypa.io/get-pip.py
  python3 -m venv --without-pip $H/venv && $H/venv/bin/python -I $H/dl-getpip/get-pip.py
  $H/venv/bin/python -m pip install -r backend/requirements-dev.txt 'moto[server]'
  ```

  Dieselbe Umgebung führt auch die Backend-Tests aus
  (`cd backend && ~/.cache/flexr-test/venv/bin/python -m pytest -q -n 2`).

## Ablauf

1. **S3-Attrappe starten:** `run-s3.sh` (Port 5055). In Claude Code über
   `preview_start` mit `flexr-test-s3` (`~/MEGA/flexr/.claude/launch.json`).
2. **Demo-Daten:** `~/.cache/flexr-test/venv/bin/python -I seed_store.py neu`
   (15 Konten, Fotos in Moto; Passwort `store-demo-1234`, z. B. Lukas mit
   Match Laura, Likes von Hannah und Miriam). Moto hält alles im Speicher -
   nach jedem Neustart von `run-s3.sh` erneut.
3. **Backend starten:** `run-backend.sh` (Port 8000, `flexr-test-backend`).
   **Nach `seed_store.py neu` neu starten**, sonst hält es die gelöschte
   SQLite-Datei offen. Mails gehen ohne SMTP ins Log (`[MAIL-DEV]`), dort
   stehen Reset- und Bestätigungslinks.
4. **App bauen** (`android-native`, nie gleichzeitig mit dem Emulator):

   ```bash
   ./gradlew --no-daemon --max-workers=1 -Dorg.gradle.jvmargs="-Xmx2560m -Dfile.encoding=UTF-8" \
     -Pkotlin.compiler.execution.strategy=in-process :app:assembleLocalDebug
   ```

5. **Emulator:** `~/.bubblewrap/android_sdk/emulator/emulator -avd flexr_test -port 5580
   -no-snapshot -no-audio -no-boot-anim -gpu host -memory 2048`, dann
   `adb -s emulator-5580 install -r app/build/outputs/apk/local/debug/app-local-debug.apk`
   und `adb -s emulator-5580 reverse tcp:5055 tcp:5055` (Fotos).
6. **Bedienen:** `source h.sh`, dann `anmelden lukas DE`, `nodes` (sichtbare
   Elemente), `tapx "<Text>"`, `shot <name>`, `felder`/`feld 2` (Eingabefelder,
   immer frisch abfragen - mit offener Tastatur verschieben sie sich).
   `bars.py <png> 345 395 55 1025 3` liest aus einem Bild, welcher Foto-Strich
   aktiv ist (Match-Profil; im Deck y 610-650).
7. **Mail-Links nachstellen:**
   `adb shell am start -W -a android.intent.action.VIEW -d "https://flexr.social/app/open/matches" flexr.social.app.local.debug`
   bzw. `.../app/open/?reset=<token>`. Mit `-p`/Paketname, weil die
   Testvariante die Domain-Prüfung nicht besteht (Debug-Signatur).

## Stolpersteine

* **RAM:** R8-Release-Build + Browser + Desktop-App = OOM-Kill (auch der
  Claude-App). Emulator (~2,8 GB) und Gradle nie zusammen; Browser-Tabs zu.
* `input text` verliert bei Last Zeichen (Passwortfeld mit 7 statt 15
  Punkten) - in Stücken mit Pausen tippen (`tippe store - demo - 1234`).
* `ESC` (keyevent 111) schließt auch Dialoge; Tastatur im Dialog mit Enter
  im letzten Feld abschicken.
* Kein Play Store im Image: Play Billing nur im internen Test-Track prüfen.
