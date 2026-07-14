from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import MembershipStatus
from ..security import get_current_user
from ..stripe_client import construct_webhook_event, create_checkout_session

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/status", response_model=MembershipStatus)
def membership_status(current_user: User = Depends(get_current_user)):
    return MembershipStatus(
        is_subscribed=current_user.is_subscribed,
        trial_ends_at=current_user.trial_ends_at,
        is_active=current_user.is_active_member(),
    )


@router.post("/checkout")
def create_checkout(current_user: User = Depends(get_current_user)):
    url = create_checkout_session(current_user.email, current_user.id)
    return {"checkout_url": url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = construct_webhook_event(payload, sig_header)
    except Exception:
        raise HTTPException(400, "Ungültige Webhook-Signatur.")

    # TODO: weitere Events behandeln (invoice.payment_failed, customer.subscription.deleted, ...)
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("client_reference_id")
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_subscribed = True
            user.stripe_customer_id = session.get("customer")
            user.stripe_subscription_id = session.get("subscription")
            db.commit()

    return {"received": True}
