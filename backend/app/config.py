from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""

    # ---- FLEXR Premium -----------------------------------------------------
    #
    # Das Geschaeftsmodell ab 10.09.2026: **Die Plattform selbst ist dauerhaft
    # kostenlos** - registrieren, Profile sehen, liken, matchen und schreiben
    # kostet nie etwas, auch nach der Beta nicht. Wer mehr will, kann FLEXR
    # Premium abschliessen (10 EUR pro Monat, jederzeit kuendbar).
    #
    # Damit ist die frueher hier beschriebene Bezahlwand ersatzlos weg: Es gibt
    # keinen Probemonat mehr, der ablaufen koennte, und kein Konto, das mangels
    # Zahlung ausgesperrt wird. ``stripe_trial_days`` ist deshalb entfallen -
    # ein Probemonat auf ein Angebot, dessen Grundnutzung ohnehin gratis ist,
    # waere sinnlos, und der Preis gilt ab dem ersten Tag.
    #
    # Der Schalter unten entscheidet nur, ob Premium **kaufbar** ist und ob die
    # Grenzen fuer Standardnutzer greifen. Solange er aus ist (Beta), ist alles
    # unbegrenzt und niemand kann etwas abschliessen. Die Clients holen den
    # Zustand ueber GET /api/billing/status (Feld ``premium_enabled``) und
    # zeigen Preis, Vorteile und Abo-Knoepfe nur, solange er wahr ist.
    #
    # Das Umlegen ist gefahrlos und braucht keine Datenmigration: Bestandskonten
    # verlieren nichts, sie bekommen lediglich dieselben Grenzen wie alle
    # anderen Standardnutzer. ``User.trial_ends_at`` wird nirgends mehr
    # ausgewertet (die Spalte bleibt nur stehen, um die Tabelle nicht anfassen
    # zu muessen).
    #
    # Seit 17.09.2026 steht der Schalter in der Produktion auf True (in der
    # ``.env`` des Servers, nicht hier - der Standard bleibt aus, damit ein
    # frisch aufgesetzter Entwicklungsserver niemandem Geld abnimmt).
    # **Im Browser** ist Premium damit buchbar; in den beiden Apps nicht, siehe
    # ``clients.py`` - das entscheidet der Server pro Anfrage, nicht dieser
    # Schalter.
    premium_enabled: bool = False

    # ---- Kaeufe in den Apps (App Store / Play Store) -----------------------
    #
    # Premium laesst sich auf drei Wegen kaufen, und welcher es war, aendert
    # an den Vorteilen nichts:
    #
    #   * im Browser ueber Stripe (die Felder ganz oben),
    #   * in der iOS-App ueber StoreKit,
    #   * in der Android-App ueber Play Billing.
    #
    # Die beiden Stores verlangen ihren eigenen Kaufweg fuer alles, was in
    # ihrer App wirkt (App Review Guideline 3.1.1, Play-Payments-Policy) - und
    # behalten dafuer 15 bis 30 Prozent. Der Preis steht deshalb NICHT hier:
    # Apple und Google kennen nur ihre eigenen Preispunkte (9,99 EUR statt
    # 10,00 EUR), rechnen Landeswaehrungen und Steuern selbst und liefern den
    # anzuzeigenden Text mit. Die Clients zeigen ihn, statt ihn zu berechnen -
    # ``premium_price_cents`` gilt nur noch fuer den Stripe-Weg.
    #
    # Ohne Zugangsdaten unten bleiben die App-Kaeufe **aus**: Der Server bietet
    # sie dann nicht an und lehnt eingereichte Belege ab. Er nimmt lieber
    # keinen Kauf an, als einen ungeprueften gutzuschreiben.
    apple_bundle_id: str = "social.flexr.app"
    apple_subscription_product_id: str = ""
    google_package_name: str = "flexr.social.app"
    google_subscription_product_id: str = ""

    # Dienstkonto mit Zugriff auf die Google Play Developer API (JSON-Datei).
    # Bei Apple braucht es dafuer nichts: Ein StoreKit-Beleg traegt seine
    # Zertifikatskette selbst und wird gegen Apples Wurzelzertifikat geprueft.
    google_service_account_file: str = ""

    # Gemeinsames Geheimnis im Pfad der Google-Benachrichtigungen. Apple
    # signiert seine Benachrichtigungen (und wird darueber geprueft), Googles
    # Pub/Sub-Zustellung traegt keine Signatur, die wir ohne weitere
    # Abhaengigkeit pruefen koennten - also ein nicht zu erratender Pfad.
    google_notifications_token: str = ""

    # Sandbox-Belege annehmen. In der Produktion aus: Ein Testkauf aus einem
    # Entwicklergeraet darf dort kein echtes Premium erzeugen.
    store_sandbox_allowed: bool = False

    # ---- Push-Zustellung (Firebase Cloud Messaging) ------------------------
    #
    # Ohne diese beiden Werte bleibt Push **aus**: Der Server stellt dann nicht
    # zu, und die Apps holen ihre Benachrichtigungen weiter per
    # Hintergrundabgleich ab - langsam, aber vollstaendig. Genau dieser
    # Fallback ist der Grund, warum hier nichts erzwungen wird.
    #
    # Das Dienstkonto ist dasselbe Format wie bei der Play-Developer-API
    # (JSON-Datei), braucht aber die Rolle "Firebase Cloud Messaging API
    # Admin" im **Firebase**-Projekt.
    fcm_service_account_file: str = ""
    fcm_project_id: str = ""

    # iOS geht **nicht** ueber Firebase, sondern direkt an Apple.
    #
    # Der Grund ist nicht Geschmack: Fuer FCM muesste die iOS-App das
    # Firebase-SDK einbinden, und ein Swift-Package laesst sich nicht so
    # nebenbei ins Xcode-Projekt haengen wie eine Gradle-Zeile. Direkt an APNs
    # braucht die App kein einziges fremdes Paket - nur die
    # Push-Berechtigung. Weniger Abhaengigkeiten, und es geht nichts an
    # Google, was nicht muss.
    #
    # Die .p8-Datei kommt aus dem Apple-Developer-Konto (Keys -> Apple Push
    # Notification service). Sie wird **einmal** heruntergeladen und ist
    # danach nicht erneut zu bekommen.
    apns_key_file: str = ""
    apns_key_id: str = ""
    apns_team_id: str = ""
    # Der Bundle-Identifier der App - APNs nennt ihn "topic".
    apns_topic: str = "social.flexr.app"
    # Entwicklungs-Builds (direkt aus Xcode) bekommen Tokens, die nur gegen
    # Apples Sandbox funktionieren; TestFlight und App Store gegen die
    # Produktion. Der Server versucht deshalb beides, siehe push.py - dieser
    # Schalter bestimmt nur, womit er anfaengt.
    apns_sandbox: bool = False

    # ---- Beta-Kennzeichnung ------------------------------------------------
    #
    # Getrennt von ``premium_enabled``, seit die beiden auseinanderfallen: Die
    # Oberflaechen haben "Beta" bis 17.09.2026 daraus abgeleitet, dass Premium
    # noch nicht scharf war ("Beta - alles unbegrenzt"). Mit dem Scharfschalten
    # waere das Beta-Abzeichen ueberall von selbst verschwunden, obwohl FLEXR
    # unveraendert im Aufbau ist: duenn besetzte Regionen, Funktionen, die sich
    # noch aendern, Stores, in denen die App gerade erst erscheint.
    #
    # "Beta" sagt seither etwas ueber den Reifegrad des Angebots aus und nichts
    # mehr ueber den Tarif. Die Clients lesen es als ``beta_active`` aus
    # GET /api/billing/status.
    beta_active: bool = True

    # Preis in Cent, damit Anzeige und Rechnung dieselbe Quelle haben.
    premium_price_cents: int = 1000
    premium_currency: str = "EUR"

    # ---- Grenzen fuer Standardnutzer (greifen nur bei premium_enabled) -----
    #
    # Zahlen bewusst hier und nicht im Code verstreut: Sie stehen wortgleich in
    # der Oberflaeche, auf der Landingpage und in den AGB. Wer sie aendert,
    # aendert eine Zusage - der Abgleich mit ``frontend/i18n-*.js``,
    # ``res/values*/strings.xml`` und ``agb.html`` gehoert dazu.
    free_daily_likes: int = 20          # rollierend ueber 24 Stunden
    free_open_chats: int = 3            # gleichzeitig laufende Unterhaltungen
    free_max_radius_km: int = 50        # Premium bis zum vollen Regler (250)

    frontend_url: str = "https://flexr.social"
    env: str = "development"

    # Objekt-Storage (S3-kompatibel, z. B. Cloudflare R2) für Foto-Uploads
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket_name: str = ""
    s3_public_base_url: str = ""
    s3_region: str = "auto"

    # SMS-Versand für die Telefonprüfung (Twilio). Ohne Zugangsdaten wird der
    # Code nur ins Server-Log geschrieben (Entwicklungs-/Testbetrieb).
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # E-Mail-Versand (z. B. Willkommensmail). Ohne SMTP_HOST/SMTP_FROM wird die
    # Nachricht nur ins Server-Log geschrieben (Entwicklungs-/Testbetrieb).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_starttls: bool = True
    smtp_ssl: bool = False
    mail_from_name: str = "FLEXR"
    support_email: str = "flexr.social@proton.me"

    # Telegram-Push ans Admin-Team, sobald im Admin-Dashboard eine neue
    # Aufgabe entsteht (Meldung, Foto-Prüfung, Verifizierung, ...). Ohne
    # Zugangsdaten wird nur geloggt (Entwicklungs-/Testbetrieb).
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    class Config:
        env_file = ".env"

        # Unbekannte Schluessel in der .env werden ueberlesen statt abgelehnt.
        #
        # Der Grund ist ein konkreter Beinahe-Ausfall: Mit dem Wegfall des
        # Probemonats verschwand ``stripe_trial_days`` aus dieser Klasse, in
        # der .env auf dem Server stand STRIPE_TRIAL_DAYS aber weiter. Pydantic
        # lehnt Extras standardmaessig ab - der Dienst waere beim naechsten
        # Neustart nicht mehr hochgekommen, und zwar erst Minuten nach dem
        # Deploy, wenn niemand mehr hinsieht.
        #
        # Eine Einstellung zu entfernen darf keinen Ausfall ausloesen koennen.
        # Der Preis dafuer ist, dass ein Tippfehler in einem Schluesselnamen
        # stillschweigend zum Standardwert fuehrt - vertretbar, weil jede
        # sicherheitsrelevante Einstellung hier ohne Standard deklariert ist
        # (database_url, jwt_secret) und ihr Fehlen weiterhin sofort auffaellt.
        extra = "ignore"


settings = Settings()
