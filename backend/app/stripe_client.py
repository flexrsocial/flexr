import stripe

from .config import settings

stripe.api_key = settings.stripe_secret_key


def create_checkout_session(user_email: str, user_id: str) -> str:
    """Erstellt eine Stripe-Checkout-Session für FLEXR Premium.

    **Ohne Probezeit.** Bis zum 10.09.2026 wurde hier der Rest eines
    Probemonats als ``trial_end`` mitgegeben - die Grundnutzung war damals
    kostenpflichtig und der Probemonat lief ab der Registrierung. Heute ist die
    Plattform dauerhaft gratis; ein Gratiszeitraum auf ein Zusatzpaket waere
    nur eine zweite, verwirrende Gratisstufe. Premium kostet ab dem ersten Tag,
    und wer nicht mehr will, kuendigt.
    """
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user_email,
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        # FLEXR-Nutzer sind Verbraucher in Österreich; explizit statt "auto",
        # damit Stripes eigene (bereits EU-konforme) Preis- und Abo-Hinweise
        # auf der gehosteten Checkout-Seite zuverlässig auf Deutsch stehen.
        locale="de",
        # Seit dem 15.08.2026 liegt die Web-App unter /app/; an der Wurzel
        # steht die oeffentliche Landingpage. Wer aus dem Checkout
        # zurueckkommt, soll in der App landen, nicht im Marketing.
        success_url=f"{settings.frontend_url}/app/?checkout=success",
        cancel_url=f"{settings.frontend_url}/app/?checkout=cancelled",
        client_reference_id=user_id,
    )
    return session.url


def create_portal_session(stripe_customer_id: str) -> str:
    """Erstellt eine Stripe-Billing-Portal-Session, in der Nutzer:innen ihr Abo
    selbst verwalten/kündigen können, und gibt die URL zurück."""
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{settings.frontend_url}/app/",
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str):
    return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)


def cancel_subscription_immediately(subscription_id: str) -> None:
    """Beendet ein Abo sofort statt zum Periodenende.

    Fuer einen wirksamen Ruecktritt (§ 13a FAGG): Der Vertrag ist rueckwirkend
    aufgeloest, eine weitere Abbuchung darf nicht mehr stattfinden. Das ist
    die andere Kuendigung (routers/billing.py, Stripe Billing Portal), die
    laesst den Zugang bis zum Periodenende bewusst bestehen.
    """
    stripe.Subscription.delete(subscription_id)
