from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GYM_CHOICES, CITY_CHOICES, User
from ..rate_limit import limiter
from ..schemas import LoginRequest, RegisterRequest, TokenResponse
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.city not in CITY_CHOICES:
        raise HTTPException(400, "Standort wird aktuell nicht unterstützt (nur Österreich).")
    if payload.gym not in GYM_CHOICES:
        raise HTTPException(400, "Unbekanntes Gym.")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-Mail bereits registriert.")

    consent_timestamp = datetime.utcnow()
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        age=payload.age,
        city=payload.city,
        gender=payload.gender,
        interest=payload.interest,
        gym=payload.gym,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        bio=payload.bio,
        sensitive_data_consent_at=consent_timestamp,
        withdrawal_waiver_consent_at=consent_timestamp,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-Mail oder Passwort falsch.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
