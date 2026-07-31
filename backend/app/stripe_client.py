from datetime import datetime, timedelta, timezone
from typing import Optional

import stripe

from .config import settings

stripe.api_key = settings.stripe_secret_key

# Stripe verlangt, dass ein gesetztes trial_end mindestens 48 Stunden in der
# Zukunft liegt. Bleibt weniger übrig, wird ohne Trial abgeschlossen.
MIN_TRIAL_REMAINDER = timedelta(hours=48)


def trial_end_timestamp(trial_ends_at: Optional[datetime], now: Optional[datetime] = None):
    """Verbleibende Gratiszeit als Unix-Zeitstempel für Stripe.

    Der Probemonat läuft ab der REGISTRIERUNG, nicht ab der Zahlung. Beim
    Checkout wird deshalb das bereits feststehende Ende des Probemonats
    übergeben - Stripe rechnet nur den Rest als Trial und beginnt danach direkt
    mit dem Abo. Ohne das würde Stripe im Checkout einen neuen 30-Tage-Zeitraum
    ankündigen und die Gratiszeit faktisch verdoppeln.

    Liefert None, wenn der Probemonat abgelaufen ist oder weniger als 48 Stunden
    übrig sind - dann beginnt das Abo sofort.
    """
    if trial_ends_at is None:
        return None
    current = now or datetime.utcnow()
    if trial_ends_at - current < MIN_TRIAL_REMAINDER:
        return None
    # trial_ends_at ist ein naiver UTC-Wert (datetime.utcnow() beim Anlegen).
    # .timestamp() würde einen naiven Wert als LOKALZEIT deuten - auf einem
    # Server mit anderer Zeitzone wäre der Trial dadurch verschoben.
    return int(trial_ends_at.replace(microsecond=0, tzinfo=timezone.utc).timestamp())


def create_checkout_session(
    user_email: str,
    user_id: str,
    trial_ends_at: Optional[datetime] = None,
) -> str:
    """Erstellt eine Stripe-Checkout-Session und gibt die URL zurück."""
    subscription_data = {}
    trial_end = trial_end_timestamp(trial_ends_at)
    if trial_end is not None:
        subscription_data["trial_end"] = trial_end

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user_email,
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        subscription_data=subscription_data or None,
        success_url=f"{settings.frontend_url}/account?checkout=success",
        cancel_url=f"{settings.frontend_url}/account?checkout=cancelled",
        client_reference_id=user_id,
    )
    return session.url


def create_portal_session(stripe_customer_id: str) -> str:
    """Erstellt eine Stripe-Billing-Portal-Session, in der Nutzer:innen ihr Abo
    selbst verwalten/kündigen können, und gibt die URL zurück."""
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{settings.frontend_url}/account",
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str):
    return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
