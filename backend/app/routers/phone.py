import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PhoneVerification, User
from ..rate_limit import limiter
from ..schemas import MyProfileOut, PhoneConfirmRequest, PhoneRequestRequest
from ..security import get_current_user
from ..sms import send_sms

router = APIRouter(prefix="/api/phone", tags=["phone"])

CODE_TTL_MINUTES = 10
MAX_ATTEMPTS = 5


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


@router.post("/request")
@limiter.limit("3/hour")
def request_code(
    request: Request,
    payload: PhoneRequestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.phone_verified and current_user.phone == payload.phone:
        raise HTTPException(400, "Diese Nummer ist bereits bestätigt.")

    # Nummer darf nicht bereits von einem anderen Konto bestätigt sein
    taken = (
        db.query(User)
        .filter(
            User.phone == payload.phone,
            User.phone_verified_at.isnot(None),
            User.id != current_user.id,
        )
        .first()
    )
    if taken:
        raise HTTPException(409, "Diese Nummer wird bereits von einem anderen Konto verwendet.")

    # Alte offene Prüfungen ersetzen
    db.query(PhoneVerification).filter(PhoneVerification.user_id == current_user.id).delete()

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(
        PhoneVerification(
            user_id=current_user.id,
            phone=payload.phone,
            code_hash=_hash_code(code),
            expires_at=datetime.utcnow() + timedelta(minutes=CODE_TTL_MINUTES),
        )
    )
    db.commit()

    send_sms(payload.phone, f"Dein FLEXR-Bestätigungscode: {code}")
    return {"sent": True}


@router.post("/confirm", response_model=MyProfileOut)
@limiter.limit("10/hour")
def confirm_code(
    request: Request,
    payload: PhoneConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pending = (
        db.query(PhoneVerification)
        .filter(PhoneVerification.user_id == current_user.id)
        .order_by(PhoneVerification.created_at.desc())
        .first()
    )
    if pending is None:
        raise HTTPException(400, "Keine laufende Telefonprüfung. Bitte zuerst einen Code anfordern.")
    if datetime.utcnow() > pending.expires_at:
        raise HTTPException(400, "Der Code ist abgelaufen. Bitte einen neuen anfordern.")
    if pending.attempts >= MAX_ATTEMPTS:
        raise HTTPException(429, "Zu viele Fehlversuche. Bitte einen neuen Code anfordern.")

    if _hash_code(payload.code) != pending.code_hash:
        pending.attempts += 1
        db.commit()
        raise HTTPException(400, "Falscher Code.")

    # Rennen absichern: Nummer könnte inzwischen anderweitig bestätigt worden sein
    taken = (
        db.query(User)
        .filter(
            User.phone == pending.phone,
            User.phone_verified_at.isnot(None),
            User.id != current_user.id,
        )
        .first()
    )
    if taken:
        raise HTTPException(409, "Diese Nummer wird bereits von einem anderen Konto verwendet.")

    current_user.phone = pending.phone
    current_user.phone_verified_at = datetime.utcnow()
    db.query(PhoneVerification).filter(PhoneVerification.user_id == current_user.id).delete()
    db.commit()
    db.refresh(current_user)
    return current_user
