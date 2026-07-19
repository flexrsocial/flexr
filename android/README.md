# FLEXR Android-App (Trusted Web Activity)

Die Android-App lädt die bestehende Web-App (https://flexr.social) als
**Trusted Web Activity (TWA)** — vollbildig, ohne Browser-Leiste, mit eigenem
Icon im Play Store bzw. am Homescreen. Das PWA-Fundament (manifest.json,
Service Worker, Icons) liegt bereits im Frontend und ist deployt.

Vorteil dieses Wegs: Es gibt genau EINE Codebasis. Jede Änderung an der
Web-App ist sofort auch in der Android-App live, ohne App-Update.

## Voraussetzungen (einmalig, am eigenen Rechner)

1. Node.js ≥ 18 installieren
2. Java JDK 17 installieren (bringt `keytool` mit)
3. Bubblewrap CLI: `npm i -g @bubblewrap/cli`
   (lädt beim ersten Build automatisch Android-SDK-Teile herunter)

## APK/AAB bauen

```bash
cd android

# 1. Projekt aus der Konfiguration initialisieren (nur beim ersten Mal)
bubblewrap init --manifest https://flexr.social/manifest.json
#   -> Fragen mit den Werten aus twa-manifest.json beantworten
#   (Package: social.flexr.app, Host: flexr.social, Farben #121212)
#   Beim Signing Key "neu erstellen" wählen -> android.keystore
#   WICHTIG: Keystore-Datei + Passwort sicher aufbewahren (nie ins Git!)

# 2. Bauen
bubblewrap build
#   -> erzeugt app-release-signed.apk (zum direkten Installieren/Testen)
#      und app-release-bundle.aab (für den Play-Store-Upload)
```

## Digital Asset Links (Pflicht für Vollbild ohne URL-Leiste)

Nach dem Erzeugen des Signing Keys den SHA256-Fingerprint auslesen:

```bash
keytool -list -v -keystore android.keystore -alias flexr | grep SHA256
```

Diesen Fingerprint in `frontend/.well-known/assetlinks.json` eintragen
(ersetzt den Platzhalter) und deployen. Prüfen mit:
https://developers.google.com/digital-asset-links/tools/generator

Ohne gültige assetlinks.json zeigt die App oben eine Browser-Leiste an —
funktioniert, sieht aber nicht nativ aus.

## Play-Store-Veröffentlichung (später)

1. Google-Play-Console-Konto (einmalig 25 USD)
2. `app-release-bundle.aab` hochladen
3. Store-Eintrag: Screenshots, Beschreibung, Datenschutz-URL
   (https://flexr.social/datenschutz.html), Altersfreigabe 18+
4. Bei Dating-Apps verlangt Google zusätzlich das Formular
   "App-Inhalte > Dating-Apps" in der Console

## Direktinstallation ohne Play Store (sofort möglich)

Die signierte APK kann direkt aufs Handy ("Unbekannte Quellen" erlauben)
oder per `adb install app-release-signed.apk` installiert werden.

Schon HEUTE ohne App: https://flexr.social am Android-Handy in Chrome öffnen
-> Menü -> "App installieren" (bzw. "Zum Startbildschirm hinzufügen") — dank
PWA-Manifest läuft FLEXR dann bereits als eigenständige Vollbild-App.

## Hinweise

- `locationDelegation` ist aktiviert, damit die GPS-Umkreissuche auch in der
  TWA die Android-Standortberechtigung nutzen kann.
- Kamera (Foto-Verifizierung) funktioniert in der TWA über die normalen
  Chrome-Berechtigungen.
- Versionspflege: `appVersionCode` in twa-manifest.json vor jedem
  Play-Store-Update um 1 erhöhen, dann `bubblewrap update && bubblewrap build`.
