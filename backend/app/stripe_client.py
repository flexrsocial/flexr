import stripe

from .config import settings

stripe.api_key = settings.stripe_secret_key


def create_checkout_session(user_email: str, user_id: str) -> str:
    """Erstellt eine Stripe-Checkout-Session mit Trial-Periode und gibt die URL zurück."""
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user_email,
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        subscription_data={"trial_period_days": settings.stripe_trial_days},
        success_url=f"{settings.frontend_url}/account?checkout=success",
        cancel_url=f"{settings.frontend_url}/account?checkout=cancelled",
        client_reference_id=user_id,
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str):
    return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
