import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import consents, legal, mailer
from ..database import get_db
from ..email_notifications import send_once
from ..models import CheckoutConsent, ConsentType, User
from ..schemas import CheckoutRequest, MembershipStatus
from ..security import get_current_user
from ..stripe_client import construct_webhook_event, create_checkout_session, create_portal_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

# Abostatus, die weiterhin Zugang bedeuten.
#
# "past_due" steht hier bewusst mit drin: Stripe wiederholt eine
# fehlgeschlagene Abbuchung ueber mehrere Tage. Wer waehrend dieser Zeit
# ausgesperrt wird, steht ohne eigenes Zutun vor einer verschlossenen App,
# obwohl die Zahlung noch zustande kommen kann. Bleibt sie endgueltig aus,
# beendet Stripe das Abo und schickt customer.subscription.deleted - erst das
# entzieht den Zugang.
ENTITLING_SUBSCRIPTION_STATUS = {"active", "trialing", "past_due"}


@router.get("/status", response_model=MembershipStatus)
def membership_status(current_user: User = Depends(get_current_user)):
    return MembershipStatus(
        is_subscribed=current_user.is_subscribed,
        trial_ends_at=current_user.trial_ends_at,
        is_active=current_user.is_active_member(),
    )


@router.post("/checkout")
def create_checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Beide Erklaerungen sind per Validator schon auf True geprueft - ohne sie
    # kommt die Anfrage gar nicht bis hierher (422). Zusaetzlich zum
    # bestehenden Consent-Nachweis (Konto-Bereich, widerrufbar) legen wir
    # einen eigenen, nicht widerrufbaren Datensatz mit beiden Erklaerungen an
    # dieselbe Checkout-Anfrage an - er bekommt die Abo-ID nachgetragen,
    # sobald Stripe sie liefert (siehe handle_stripe_event()).
    consents.grant(db, current_user, ConsentType.immediate_start)

    checkout_consent = CheckoutConsent(
        user_id=current_user.id,
        immediate_start_version=legal.WITHDRAWAL_VERSION,
        withdrawal_ack_version=legal.WITHDRAWAL_ACK_VERSION,
    )
    db.add(checkout_consent)
    db.commit()

    # trial_ends_at wird mitgegeben, damit Stripe nur die seit der Registrierung
    # verbliebene Gratiszeit als Trial ansetzt und danach sofort abrechnet.
    url = create_checkout_session(
        current_user.email,
        current_user.id,
        current_user.trial_ends_at,
    )
    return {"checkout_url": url}


@router.post("/portal")
def create_portal(current_user: User = Depends(get_current_user)):
    """Self-Service-Verwaltung/Kündigung des Abos über Stripes Billing Portal."""
    if not current_user.stripe_customer_id:
        raise HTTPException(400, "Noch kein Abo abgeschlossen.")
    url = create_portal_session(current_user.stripe_customer_id)
    return {"portal_url": url}


def _user_for_subscription_event(db: Session, obj: dict):
    """Ordnet ein Abo-Ereignis einem Nutzer zu.

    Abo-Ereignisse tragen kein ``client_reference_id`` - das gibt es nur an der
    Checkout-Session. Zugeordnet wird deshalb ueber die Abo-ID und, solange die
    noch nicht gespeichert ist, ersatzweise ueber die Kunden-ID.
    """
    subscription_id = obj.get("id")
    customer_id = obj.get("customer")

    user = None
    if subscription_id:
        user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
    if user is None and customer_id:
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    return user


def _user_for_invoice_event(db: Session, obj: dict):
    """Ordnet eine Rechnung ueber Abo- oder Kunden-ID einem Nutzer zu."""
    subscription_id = obj.get("subscription")
    customer_id = obj.get("customer")

    user = None
    if subscription_id:
        user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
    if user is None and customer_id:
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    return user


def _deliver_or_retry(
    db: Session,
    notification_key: str,
    kind: str,
    sender,
) -> None:
    sent = send_once(db, notification_key, kind, sender)
    if mailer.email_configured() and not sent:
        # FastAPI antwortet dadurch mit 500; Stripe wiederholt den Webhook.
        raise RuntimeError(f"Transaktionale E-Mail fehlgeschlagen: {kind}")


def _event_object_key(event: dict, obj: dict, kind: str) -> str:
    stable_id = obj.get("id") or event.get("id")
    if not stable_id:
        # Nur Test-/Entwicklungsereignisse haben gelegentlich keine IDs.
        stable_id = f"{obj.get('customer', 'unknown')}:{obj.get('subscription', 'unknown')}"
    return f"stripe:{kind}:{stable_id}"


def handle_stripe_event(event: dict, db: Session) -> None:
    """Traegt ein Stripe-Ereignis in den Abostatus des Nutzers ein.

    Ausgelagert aus dem Endpunkt, damit der Ablauf ohne Signaturpruefung
    testbar ist - dieselbe Trennung wie bei ``trial_end_timestamp``.

    Bekannte Grenze: Stripe stellt Ereignisse nicht garantiert in der
    Reihenfolge ihres Entstehens zu. Trifft ein veraltetes "updated" nach einem
    "deleted" ein, wird der Zugang faelschlich wieder geoeffnet. Sauber
    aufloesen liesse sich das nur, indem der Abostatus bei jedem Ereignis frisch
    von Stripe geholt wird - das kostet einen API-Aufruf pro Ereignis und ist
    hier bewusst nicht getan.
    """
    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user = db.query(User).filter(User.id == obj.get("client_reference_id")).first()
        if user:
            user.is_subscribed = True
            user.stripe_customer_id = obj.get("customer")
            user.stripe_subscription_id = obj.get("subscription")

            # Die juengste noch unverknuepfte Checkout-Erklaerung dieses
            # Nutzers bekommt jetzt die Abo-ID nachgetragen - vorher konnte
            # sie nicht bekannt sein, es gab ja noch kein Abo.
            offene_erklaerung = (
                db.query(CheckoutConsent)
                .filter(
                    CheckoutConsent.user_id == user.id,
                    CheckoutConsent.stripe_subscription_id.is_(None),
                )
                .order_by(CheckoutConsent.created_at.desc())
                .first()
            )
            if offene_erklaerung:
                offene_erklaerung.stripe_subscription_id = obj.get("subscription")
                offene_erklaerung.stripe_customer_id = obj.get("customer")

            db.commit()
            # Vertragsbestätigung auf dauerhaftem Datenträger (Art. 246a § 4
            # Abs. 3 EGBGB-Wertung / vergleichbare österreichische Pflicht).
            # Fehlschlagen darf das nicht den Abo-Status verhindern - deshalb
            # erst nach dem commit() und ohne den Rückgabewert zu prüfen.
            _deliver_or_retry(
                db,
                f"stripe:subscription-confirmation:{user.stripe_subscription_id or obj.get('id')}",
                "subscription_confirmation",
                lambda: mailer.send_subscription_confirmation(user.email, user.name),
            )
        return

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        user = _user_for_subscription_event(db, obj)
        if user:
            # Die Abo-ID nachtragen, falls die Checkout-Session sie nicht
            # geliefert hat - sonst greift die Zuordnung beim naechsten
            # Ereignis nur noch ueber die Kunden-ID.
            user.stripe_subscription_id = obj.get("id") or user.stripe_subscription_id
            user.is_subscribed = obj.get("status") in ENTITLING_SUBSCRIPTION_STATUS
            db.commit()

            previous = event.get("data", {}).get("previous_attributes", {})
            cancellation_newly_scheduled = (
                event_type == "customer.subscription.updated"
                and bool(obj.get("cancel_at_period_end"))
                and not bool(previous.get("cancel_at_period_end"))
            )
            if cancellation_newly_scheduled:
                end_at = obj.get("current_period_end") or obj.get("cancel_at")
                _deliver_or_retry(
                    db,
                    f"stripe:cancellation-scheduled:{obj.get('id')}:{end_at}",
                    "cancellation_scheduled",
                    lambda: mailer.send_cancellation_scheduled(
                        user.email, user.name, end_at
                    ),
                )
        return

    if event_type == "customer.subscription.trial_will_end":
        user = _user_for_subscription_event(db, obj)
        if user:
            _deliver_or_retry(
                db,
                _event_object_key(event, obj, "trial-ending"),
                "trial_ending",
                lambda: mailer.send_trial_ending(
                    user.email, user.name, obj.get("trial_end")
                ),
            )
        return

    if event_type == "customer.subscription.deleted":
        user = _user_for_subscription_event(db, obj)
        if user:
            user.is_subscribed = False
            db.commit()
            _deliver_or_retry(
                db,
                _event_object_key(event, obj, "subscription-ended"),
                "subscription_ended",
                lambda: mailer.send_subscription_ended(user.email, user.name),
            )
        return

    if event_type == "invoice.upcoming":
        user = _user_for_invoice_event(db, obj)
        if user and obj.get("billing_reason") != "subscription_create":
            charge_at = obj.get("next_payment_attempt") or obj.get("period_end")
            _deliver_or_retry(
                db,
                _event_object_key(event, obj, "renewal-reminder"),
                "renewal_reminder",
                lambda: mailer.send_renewal_reminder(
                    user.email,
                    user.name,
                    obj.get("amount_due"),
                    obj.get("currency"),
                    charge_at,
                ),
            )
        return

    if event_type in ("invoice.paid", "invoice.payment_succeeded"):
        user = _user_for_invoice_event(db, obj)
        if user and (obj.get("amount_paid") or 0) > 0:
            _deliver_or_retry(
                db,
                _event_object_key(event, obj, "payment-succeeded"),
                "payment_succeeded",
                lambda: mailer.send_payment_succeeded(
                    user.email,
                    user.name,
                    obj.get("amount_paid"),
                    obj.get("currency"),
                    obj.get("hosted_invoice_url"),
                ),
            )
        return

    if event_type == "invoice.payment_failed":
        # Bewusst kein Entzug, siehe ENTITLING_SUBSCRIPTION_STATUS. Stattdessen
        # erhaelt der Nutzer sofort einen Link zu seinen Zahlungsdaten.
        logger.warning(
            "Stripe: Zahlung fehlgeschlagen (customer=%s, subscription=%s)",
            obj.get("customer"),
            obj.get("subscription"),
        )
        user = _user_for_invoice_event(db, obj)
        if user:
            _deliver_or_retry(
                db,
                _event_object_key(event, obj, "payment-failed"),
                "payment_failed",
                lambda: mailer.send_payment_failed(
                    user.email,
                    user.name,
                    obj.get("amount_due"),
                    obj.get("currency"),
                    obj.get("next_payment_attempt"),
                    obj.get("hosted_invoice_url"),
                ),
            )
        return


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = construct_webhook_event(payload, sig_header)
    except Exception:
        raise HTTPException(400, "Ungültige Webhook-Signatur.")

    handle_stripe_event(event, db)

    return {"received": True}
