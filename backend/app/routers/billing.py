import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import consents, legal, mailer
from ..database import get_db
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
            mailer.send_subscription_confirmation(user.email, user.name)
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
        return

    if event_type == "customer.subscription.deleted":
        user = _user_for_subscription_event(db, obj)
        if user:
            user.is_subscribed = False
            db.commit()
        return

    if event_type == "invoice.payment_failed":
        # Bewusst kein Entzug, siehe ENTITLING_SUBSCRIPTION_STATUS. Der Eintrag
        # im Log ist der einzige Hinweis darauf, dass bei jemandem die Zahlung
        # klemmt - es gibt keine Benachrichtigung im Betrieb.
        logger.warning(
            "Stripe: Zahlung fehlgeschlagen (customer=%s, subscription=%s)",
            obj.get("customer"),
            obj.get("subscription"),
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
