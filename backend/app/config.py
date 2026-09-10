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
    premium_enabled: bool = False

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
