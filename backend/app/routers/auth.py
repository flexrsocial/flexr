import re
from datetime import date, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..age import UNDERAGE_MESSAGE, age_on, is_adult
from ..database import get_db
from ..email_verification import TOKEN_TTL_HOURS, build_link, issue
from ..geo import city_for_plz
from ..mailer import send_verification_email
from ..models import ModerationAction, UnderageSignupAttempt, User, UserDevice
from ..moderation import restriction_detail
from ..rate_limit import limiter
from ..safety_checks import check_public_text, is_disposable_email
from ..schemas import (
    AgeCheckRequest,
    AgeCheckResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

_DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")

# Altersfilter gegen systematisches Durchprobieren.
#
# Ein einzelner Tippfehler soll sofort korrigierbar bleiben - deshalb greift die
# Sperre erst ab dem zweiten abgeschickten Registrierungsversuch mit einem
# Geburtsdatum unter 18 innerhalb des Zeitfensters. Wer die Grenze auslotet,
# braucht dagegen mehrere Anläufe und läuft in die Sperre. Der eigentliche
# Schutz bleibt die manuelle Prüfung des Lichtbildausweises vor der
# Freischaltung: ein nachträglich "korrigiertes" Geburtsdatum fällt dort beim
# Abgleich mit dem Ausweis auf.
#
# Gezählt wird ausschließlich das tatsächliche Abschicken von /register. Die
# Vorabprüfung im Formular zählt bewusst NICHT mit: Ein Datumsfeld liefert schon
# während der Eingabe vollständige Zwischenwerte (etwa nach Tag und Monat, bevor
# das Jahr korrigiert ist), und daraus dürfen keine Versuche werden.
UNDERAGE_ATTEMPT_WINDOW = timedelta(hours=24)
UNDERAGE_ATTEMPT_LIMIT = 2

# Mehrfaches Abschicken derselben Eingabe (Doppelklick, Wiederholung nach einem
# Netzfehler) darf nicht als zwei Versuche zählen.
UNDERAGE_ATTEMPT_DEDUP = timedelta(seconds=60)

UNDERAGE_BLOCKED_MESSAGE = (
    "Die Registrierung ist von diesem Gerät derzeit nicht möglich. "
    "Bitte versuche es später erneut oder wende dich an flexr.social@proton.me."
)


def _underage_attempts(db: Session, device_id: str) -> int:
    since = datetime.utcnow() - UNDERAGE_ATTEMPT_WINDOW
    return (
        db.query(func.count(UnderageSignupAttempt.id))
        .filter(
            UnderageSignupAttempt.device_id == device_id,
            UnderageSignupAttempt.created_at >= since,
        )
        .scalar()
        or 0
    )


def _is_signup_blocked(db: Session, device_id: str | None) -> bool:
    if not device_id:
        return False
    return _underage_attempts(db, device_id) >= UNDERAGE_ATTEMPT_LIMIT


def _record_underage_attempt(db: Session, device_id: str | None) -> None:
    """Hält nur fest, DASS ein Versuch stattfand - ohne Name, E-Mail oder
    Geburtsdatum. Ohne Geräte-ID gibt es nichts zu zählen."""
    if not device_id:
        return
    recent = (
        db.query(UnderageSignupAttempt.id)
        .filter(
            UnderageSignupAttempt.device_id == device_id,
            UnderageSignupAttempt.created_at >= datetime.utcnow() - UNDERAGE_ATTEMPT_DEDUP,
        )
        .first()
    )
    if recent:
        return  # dieselbe Eingabe erneut abgeschickt, kein zweiter Versuch
    db.add(UnderageSignupAttempt(device_id=device_id))
    db.commit()


def _reject_underage(db: Session, device_id: str | None) -> None:
    _record_underage_attempt(db, device_id)
    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        {"code": "underage", "message": UNDERAGE_MESSAGE},
    )


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


@router.post("/age-check", response_model=AgeCheckResponse)
@limiter.limit("20/minute")
def age_check(request: Request, payload: AgeCheckRequest, db: Session = Depends(get_db)):
    """Altersprüfung für das Registrierungsformular.

    Rechnet serverseitig - der Client kann das Ergebnis nur anzeigen, nicht
    bestimmen. Verbindlich bleibt dieselbe Prüfung in /register; dieser
    Endpunkt existiert, damit unter 18 gar kein Formular weiterläuft und keine
    Kamera geöffnet wird.

    Bewusst ohne Nebenwirkung: Hier wird kein Versuch gezählt (siehe
    UNDERAGE_ATTEMPT_WINDOW). Das Feld meldet schon während der Eingabe
    vollständige Zwischenwerte, die keine Registrierungsversuche sind.
    """
    device_id = _device_id_from(request)
    if _is_signup_blocked(db, device_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {"code": "signup_blocked", "message": UNDERAGE_BLOCKED_MESSAGE},
        )

    if payload.birthdate > date.today():
        raise HTTPException(400, "Bitte ein gültiges Geburtsdatum angeben.")

    age = age_on(payload.birthdate)
    if age < 18:
        return AgeCheckResponse(eligible=False, age=age, message=UNDERAGE_MESSAGE)
    if age > 99:
        return AgeCheckResponse(
            eligible=False, age=age, message="Bitte ein gültiges Geburtsdatum angeben."
        )
    return AgeCheckResponse(eligible=True, age=age)


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(
    request: Request,
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    from .gyms import gym_exists_for_profile

    # Altersgrenze zuerst: Sie entscheidet, ob überhaupt ein Konto entsteht.
    # Maßgeblich ist ausschließlich diese serverseitige Berechnung - ein
    # manipuliertes Frontend ändert daran nichts.
    device_id = _device_id_from(request)
    if _is_signup_blocked(db, device_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {"code": "signup_blocked", "message": UNDERAGE_BLOCKED_MESSAGE},
        )
    if not is_adult(payload.birthdate):
        _reject_underage(db, device_id)

    if not gym_exists_for_profile(db, payload.gym):
        raise HTTPException(400, "Unbekanntes Gym. Bitte aus der Liste wählen oder vorschlagen.")

    # Automatische Sicherheitsprüfung: Wegwerf-Adressen und unzulässige Bios
    if is_disposable_email(payload.email):
        raise HTTPException(400, "Wegwerf-E-Mail-Adressen sind nicht erlaubt.")
    bio_problem = check_public_text(payload.bio)
    if bio_problem:
        raise HTTPException(400, bio_problem)

    # Geräteprüfung (Ban-Evasion): Neuregistrierung von Geräten, die zu einem
    # gesperrten Konto gehören, wird blockiert.
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
        # Der Ort ist aus der PLZ ableitbar - maßgeblich ist der amtliche Name
        # aus dem Backend-Datensatz, nicht der vom Client geschickte Wert.
        city=city_for_plz(payload.plz) or payload.city,
        gender=payload.gender,
        interest=interest,
        gym=payload.gym,
        bio=payload.bio,
        sensitive_data_consent_at=consent_timestamp,
        withdrawal_waiver_consent_at=consent_timestamp,
        # Neue Konten durchlaufen die Alters- und Identitätsprüfung, bevor sie
        # nutzbar werden. trial_ends_at wird bei der Freischaltung neu gesetzt
        # (verification_service.activate_account), damit die Prüfzeit nicht vom
        # Probemonat abgeht.
        verification_required=True,
        verification_required_at=consent_timestamp,
        activated_at=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_device(db, user.id, request)

    # Bestätigungsmail mit dem Aktivierungslink - zugleich die Begrüßung und
    # die Aufforderung zur Verifizierung. Nach der Antwort, nicht davor: Ein
    # hängender oder kaputter Mailserver darf die Registrierung weder verzögern
    # noch scheitern lassen (siehe app/mailer.py).
    # Der Token entsteht synchron: Er ist eine Datenbankänderung und muss
    # feststehen, bevor die Sitzung endet - FastAPI schließt Dependencies mit
    # yield vor den BackgroundTasks. Nur der Versand wandert nach hinten.
    verification_token = issue(db, user)
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.name,
        build_link(verification_token),
        TOKEN_TTL_HOURS,
    )

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    # Opportunistischer Aufräum-Lauf: endgültige Löschung abgelaufener Konten
    # (30-Tage-Karenz). Billige Abfrage, in der Regel null Treffer - erspart
    # einen eigenen Cron-Job.
    from ..cleanup import purge_deleted_users, purge_stale_verification_uploads

    purge_deleted_users(db)
    # Ebenso billig: verwaiste Ausweisaufnahmen und fehlgeschlagene Löschungen
    purge_stale_verification_uploads(db)

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-Mail oder Passwort falsch.")
    if user.deleted_at is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieses Konto wurde gelöscht.")
    if user.is_banned:
        # Art. 17 DSA: Der Gesperrte erfährt den Grund und den Widerspruchsweg.
        # Beim Ban ist der Login der einzige Kanal - ein Token bekommt er nicht.
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            restriction_detail(user, ModerationAction.ban),
        )

    record_device(db, user.id, request)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
