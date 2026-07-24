from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import AdminUser, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire, "scope": "user"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige oder abgelaufene Anmeldung.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None or payload.get("scope") != "user":
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_error
    if user.deleted_at is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieses Konto wurde gelöscht.")
    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account gesperrt.")

    # Online-Anzeige: last_seen_at gedrosselt aktualisieren (max. 1 Schreibzugriff
    # pro Minute), damit nicht jeder Request eine DB-Schreiboperation auslöst.
    now = datetime.utcnow()
    if user.last_seen_at is None or now - user.last_seen_at > timedelta(seconds=60):
        user.last_seen_at = now
        _record_daily_access(db, user)
        db.commit()

    return user


def _country_for_user(user: User) -> str:
    """Grober Ländercode für die Statistik. Aus GPS-Koordinaten per
    Bounding-Box (Österreich + direkte Nachbarn), sonst "AT" (alle Profile sind
    per Pflicht-PLZ in Österreich). Keine IP-Speicherung."""
    if user.gps_lat is None or user.gps_lon is None:
        return "AT"
    lat, lon = user.gps_lat, user.gps_lon
    boxes = [
        ("AT", 46.3, 49.1, 9.4, 17.2),
        ("DE", 47.2, 55.1, 5.8, 15.1),
        ("CH", 45.8, 47.8, 5.9, 10.5),
        ("IT", 36.6, 47.1, 6.6, 18.6),
        ("SI", 45.4, 46.9, 13.3, 16.6),
        ("CZ", 48.5, 51.1, 12.0, 18.9),
        ("SK", 47.7, 49.6, 16.8, 22.6),
        ("HU", 45.7, 48.6, 16.1, 22.9),
    ]
    for code, lat0, lat1, lon0, lon1 in boxes:
        if lat0 <= lat <= lat1 and lon0 <= lon <= lon1:
            return code
    return "XX"  # außerhalb der bekannten Region


def _record_daily_access(db: Session, user: User) -> None:
    from datetime import date

    from .models import DailyAccess

    today = date.today()
    country = _country_for_user(user)
    exists = (
        db.query(DailyAccess.id)
        .filter(
            DailyAccess.user_id == user.id,
            DailyAccess.day == today,
            DailyAccess.country == country,
        )
        .first()
    )
    if not exists:
        db.add(DailyAccess(user_id=user.id, day=today, country=country))


def require_active_membership(user: User = Depends(get_current_user)) -> User:
    if not user.is_active_member():
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Probemonat abgelaufen. Bitte Abo abschließen.",
        )
    return user


def create_admin_access_token(admin_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": admin_id, "exp": expire, "scope": "admin"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_admin(
    token: str = Depends(admin_oauth2_scheme), db: Session = Depends(get_db)
) -> AdminUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige oder abgelaufene Anmeldung.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        admin_id = payload.get("sub")
        if admin_id is None or payload.get("scope") != "admin":
            raise credentials_error
    except JWTError:
        raise credentials_error

    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if admin is None:
        raise credentials_error
    return admin
