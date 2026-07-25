# FLEXR Android-App (Trusted Web Activity)

Die Android-App lädt die bestehende Web-App (https://flexr.social) als
**Trusted Web Activity (TWA)** — vollbildig, ohne Browser-Leiste, mit eigenem
Icon im Play Store bzw. am Homescreen. Das PWA-Fundament (manifest.json,
Service Worker, Icons) liegt bereits im Frontend und ist deployt.

Vorteil dieses Wegs: Es gibt genau EINE Codebasis. Jede Änderung an der
Web-App ist sofort auch in der Android-App live, ohne App-Update.

## Fertige Artefakte (bereits gebaut)

Der Build wurde bereits ausgeführt. Im Ordner liegen:

- `app-release-bundle.aab` — **das lädst du in die Play Console hoch**
- `app-release-signed.apk` — zum direkten Testen am Handy (siehe unten)
- `android.keystore` — **Signing-Key, STRENG GEHEIM, nie ins Git!**
- `KEYSTORE-CREDENTIALS.txt` — Passwort + SHA256-Fingerprint, **sichern!**

`android.keystore` und `KEYSTORE-CREDENTIALS.txt` sind per `.gitignore`
ausgeschlossen. Beide Dateien an einem sicheren Ort sichern (Passwortmanager):
Ohne sie kannst du künftige Updates nicht mehr mit demselben Key signieren.

## Neu bauen (z. B. für ein Update)

Alles steckt in einem Skript:

```bash
bash android/build.sh
```

Vor einem Play-Store-Update in `twa-manifest.json` `appVersionCode` um 1 erhöhen
und `appVersion` + `appVersionName` auf die neue Versionsnummer setzen (z. B.
`1.0.1`), dann `build.sh` erneut laufen lassen. Der Keystore wird nur beim
allerersten Lauf erzeugt und danach wiederverwendet.

Die Toolchain (Node, JDK 17, Android-SDK) liegt user-lokal in
`~/.local/opt` bzw. `~/.bubblewrap` und wird von `build.sh` automatisch
in den PATH gebracht.

## Digital Asset Links (Pflicht fürs Vollbild ohne URL-Leiste)

Damit die TWA ohne Browser-Leiste startet, muss der SHA256-Fingerprint des
**tatsächlich signierenden** Keys in `frontend/.well-known/assetlinks.json`
stehen und live sein.

- Für die **direkt installierte APK** (Test) ist das der lokale Upload-Key.
  Dessen Fingerprint ist bereits eingetragen.
- Für die **über den Play Store veröffentlichte App** signiert Google selbst
  neu (**Play App Signing**). Der dafür gültige Fingerprint steht nach dem
  ersten Upload in der Play Console unter
  **Play App Signing → App-Signaturschlüssel-Zertifikat (SHA-256)**.
  Diesen Fingerprint zusätzlich in `assetlinks.json` eintragen (als zweiten
  Eintrag im Array) und deployen — sonst zeigt die Store-App oben eine
  Browser-Leiste.

Prüfen lässt sich das mit:
https://developers.google.com/digital-asset-links/tools/generator

## Direktinstallation ohne Play Store (sofort möglich)

Die signierte APK kann direkt aufs Handy ("Unbekannte Quellen" erlauben)
oder per `adb install android/app-release-signed.apk` installiert werden.

Schon HEUTE ohne App: https://flexr.social am Android-Handy in Chrome öffnen
-> Menü -> "App installieren" — dank PWA-Manifest läuft FLEXR dann bereits als
eigenständige Vollbild-App.

## Hinweise

- `locationDelegation` ist aktiviert, damit die GPS-Umkreissuche auch in der
  TWA die Android-Standortberechtigung nutzen kann.
- Kamera (Foto-Verifizierung) funktioniert in der TWA über die normalen
  Chrome-Berechtigungen.
- Paket-ID: `social.flexr.app` (fix — nach der ersten Veröffentlichung nicht
  mehr änderbar).
