import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GYM_CHOICES, User, UserDevice
from ..rate_limit import limiter
from ..safety_checks import check_public_text, is_disposable_email
from ..schemas import LoginRequest, RegisterRequest, TokenResponse
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

_DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def _device_id_from(request: Request) -> str | None:
    device_id = request.headers.get("X-Device-Id", "").strip()
    return device_id if _DEVICE_ID_RE.match(device_id) else None


def record_device(db: Session, user_id: str, request: Request) -> None:
    """Geräteprüfung: Gerät bei Registrierung/Login erfassen bzw. aktualisieren."""
    device_id = _device_id_from(request)
    if not device_id:
        return
    entry = (
        db.query(UserDevice)
        .filter(UserDevice.user_id == user_id, UserDevice.device_id == device_id)
        .first()
    )
    if entry:
        entry.last_seen = datetime.utcnow()
        entry.user_agent = request.headers.get("User-Agent", "")[:300]
    else:
        db.add(
            UserDevice(
                user_id=user_id,
                device_id=device_id,
                user_agent=request.headers.get("User-Agent", "")[:300],
            )
        )
    db.commit()


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.gym not in GYM_CHOICES:
        raise HTTPException(400, "Unbekanntes Gym.")

    # Automatische Sicherheitsprüfung: Wegwerf-Adressen und unzulässige Bios
    if is_disposable_email(payload.email):
        raise HTTPException(400, "Wegwerf-E-Mail-Adressen sind nicht erlaubt.")
    bio_problem = check_public_text(payload.bio)
    if bio_problem:
        raise HTTPException(400, bio_problem)

    # Geräteprüfung (Ban-Evasion): Neuregistrierung von Geräten, die zu einem
    # gesperrten Konto gehören, wird blockiert.
    device_id = _device_id_from(request)
    if device_id:
        banned_on_device = (
            db.query(UserDevice)
            .join(User, UserDevice.user_id == User.id)
            .filter(UserDevice.device_id == device_id, User.is_banned.is_(True))
            .first()
        )
        if banned_on_device:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Registrierung von diesem Gerät nicht möglich.",
            )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-Mail bereits registriert.")

    # Kein eigenes "Interessiert an"-Feld mehr - die Plattform matcht aktuell
    # ausschließlich gegengeschlechtlich (Produktentscheidung).
    interest = "frau" if payload.gender == "mann" else "mann"

    consent_timestamp = datetime.utcnow()
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        birthdate=payload.birthdate,
        plz=payload.plz,
        city=payload.city,
        gender=payload.gender,
        interest=interest,
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

    record_device(db, user.id, request)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-Mail oder Passwort falsch.")
    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account gesperrt.")

    record_device(db, user.id, request)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
