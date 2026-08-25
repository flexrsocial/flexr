from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""
    stripe_trial_days: int = 30

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


settings = Settings()
