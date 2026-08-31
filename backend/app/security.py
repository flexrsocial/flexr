from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import AdminUser, ModerationAction, User
from .moderation import restriction_detail

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


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
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
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            restriction_detail(user, ModerationAction.ban),
        )

    # Online-Anzeige: last_seen_at gedrosselt aktualisieren (max. 1 Schreibzugriff
    # pro Minute), damit nicht jeder Request eine DB-Schreiboperation auslöst.
    now = datetime.utcnow()
    if user.last_seen_at is None or now - user.last_seen_at > timedelta(seconds=60):
        user.last_seen_at = now
        _record_daily_access(db, user)
        db.commit()

    # last_active_at zählt nur echte Vordergrund-Nutzung. Die nativen Apps
    # gleichen im Hintergrund ab (WorkManager/BGTaskScheduler) und schicken
    # dabei X-Flexr-Background: 1 - würden diese Abrufe mitzählen, wäre die
    # Inaktivitäts-Erinnerung nie fällig, weil der Poller den Zeitstempel alle
    # paar Stunden auffrischt, ohne dass jemand die App geöffnet hat.
    if request.headers.get("X-Flexr-Background") != "1":
        if user.last_active_at is None or now - user.last_active_at > timedelta(seconds=60):
            user.last_active_at = now
            db.commit()

    return user


def optional_current_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """Nutzer, falls ein gültiger Token mitkommt - sonst None.

    Gebraucht für Vorgänge, die jedem offenstehen müssen, aber besser werden,
    wenn sie sich einem Konto zuordnen lassen: die Rücktrittsfunktion nach
    § 13a FAGG und das Meldeverfahren nach Art. 16 DSA. Beide dürfen an einer
    fehlenden Anmeldung nicht scheitern - wer sein Konto gelöscht hat oder gar
    keines besitzt, muss trotzdem erklären bzw. melden können.

    Anders als get_current_user wirft diese Funktion nie: Ein kaputter Token
    ist hier gleichbedeutend mit "nicht angemeldet". Gesperrte und gelöschte
    Konten werden ebenfalls als "nicht angemeldet" behandelt - sie sollen die
    Funktion nutzen können, nur eben ohne Zuordnung.
    """
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    if payload.get("scope") != "user":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def _country_for_user(user: User) -> str:
    """Grober Ländercode für die Statistik. Alle Profile sind über die
    Pflicht-PLZ in Österreich verortet, eine Geräteposition wird nicht mehr
    erhoben - daher konstant "AT". Keine IP-Speicherung."""
    return "AT"


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


def require_activated_account(user: User = Depends(get_current_user)) -> User:
    """Sperrt alle Dating-Funktionen, solange die Alters- und Identitätsprüfung
    nicht bestanden ist.

    Betrifft Deck, Swipes, Matches und Chat. Profil, Fotos, Verifizierung und
    Abo-Status bleiben erreichbar - sonst käme der Nutzer nicht durch die
    Prüfung und nicht an seine Kontolöschung.

    Das Fehlerdetail ist ein Objekt mit ``code``, damit die Clients gezielt auf
    den Verifizierungsbildschirm leiten können, statt einen Text zu vergleichen.
    """
    if not user.is_account_activated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "verification_required",
                "message": (
                    "Dein Konto ist noch nicht freigeschaltet. Schließe zuerst die "
                    "Alters- und Identitätsprüfung ab."
                ),
            },
        )
    return user


def require_active_membership(user: User = Depends(require_activated_account)) -> User:
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
