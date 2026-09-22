import logging
import re
from datetime import date, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import consents
from ..age import UNDERAGE_MESSAGE, age_on, is_adult
from ..database import get_db
from ..email_verification import TOKEN_TTL_HOURS, build_link, issue
from ..geo import city_for_plz
from .. import password_reset
from ..mailer import send_password_reset, send_verification_email
from ..models import ConsentType, ModerationAction, UnderageSignupAttempt, User, UserDevice
from ..moderation import restriction_detail
from ..rate_limit import limiter
from ..retention import ACCOUNT_GRACE_PERIOD_DAYS
from ..safety_checks import check_public_text, is_disposable_email
from ..schemas import (
    OkResponse,
    PasswordForgotRequest,
    PasswordResetRequest,
    AgeCheckRequest,
    AgeCheckResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from ..security import create_access_token, hash_password, verify_password
from ..timeutil import utcnow

router = APIRouter(prefix="/api/auth", tags=["auth"])

logger = logging.getLogger(__name__)

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
    since = utcnow() - UNDERAGE_ATTEMPT_WINDOW
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
            UnderageSignupAttempt.created_at >= utcnow() - UNDERAGE_ATTEMPT_DEDUP,
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
        entry.last_seen = utcnow()
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

    existing = db.query(User).filter(func.lower(User.email) == payload.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-Mail bereits registriert.")

    # Kein eigenes "Interessiert an"-Feld mehr - die Plattform matcht aktuell
    # ausschließlich gegengeschlechtlich (Produktentscheidung).
    interest = "frau" if payload.gender == "mann" else "mann"

    consent_timestamp = utcnow()
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
        # withdrawal_waiver_consent_at wird bewusst NICHT mehr gesetzt: Bei der
        # Registrierung entsteht kein entgeltlicher Vertrag (kein Zahlungsmittel,
        # keine automatische Umwandlung des Probemonats), also gibt es auch kein
        # Rücktrittsrecht, auf das verzichtet werden könnte. Siehe models.User.
        # Neue Konten durchlaufen die Alters- und Identitätsprüfung, bevor sie
        # nutzbar werden. trial_ends_at wird bei der Freischaltung neu gesetzt
        # (verification_service.activate_account), damit die Prüfzeit nicht vom
        # Probemonat abgeht.
        verification_required=True,
        verification_required_at=consent_timestamp,
        activated_at=None,
        # Sprache des Clients. Aeltere App-Fassungen schicken das Feld nicht -
        # dann bleibt es bei der Ausgangssprache (models.User.language).
        language=payload.language or "de",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Versionierter Nachweis: welche Fassung der Nutzer akzeptiert bzw. worin er
    # eingewilligt hat. Der Zeitstempel am Nutzer bleibt zusätzlich bestehen.
    # Die AGB-Annahme steht bewusst als eigener Eintrag daneben - sie ist
    # Vertragsschluss, keine datenschutzrechtliche Einwilligung.
    consents.grant(db, user, ConsentType.sensitive_data, at=consent_timestamp, commit=False)
    consents.grant(db, user, ConsentType.terms, at=consent_timestamp, commit=False)
    db.commit()

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
        user.language,
    )

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


# ---------- Bremse gegen Passwort-Raten ----------
#
# Die IP-Grenze (10/Minute) haelt einen Angreifer mit vielen Adressen nicht
# auf. Deshalb zaehlt jedes Konto seine Fehlversuche selbst. Bewusst maessig
# streng: Eine harte Sperre waere ihrerseits ein Werkzeug, um fremde Konten
# auszusperren. 15 Minuten nach dem zehnten Fehlversuch, und "Passwort
# vergessen" hebt die Sperre sofort auf (password_reset.set_new_password).
LOGIN_LOCKOUT_THRESHOLD = 10
LOGIN_LOCKOUT_DURATION = timedelta(minutes=15)

# Vergleichshash fuer unbekannte Adressen: Ohne ihn antwortete der Login bei
# einer unbekannten Adresse messbar schneller (kein bcrypt) - daran liesse
# sich ablesen, wer ein Konto hat.
_DUMMY_HASH = hash_password("flexr-kein-konto-vorhanden")


def _check_credentials(db: Session, payload: LoginRequest) -> User:
    """Gemeinsame Pruefung fuer Login und Reaktivierung."""
    user = db.query(User).filter(func.lower(User.email) == payload.email).first()
    if user is None:
        verify_password(payload.password, _DUMMY_HASH)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-Mail oder Passwort falsch.")

    jetzt = utcnow()
    if user.login_locked_until and user.login_locked_until > jetzt:
        minuten = max(1, int((user.login_locked_until - jetzt).total_seconds() // 60) + 1)
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Zu viele Fehlversuche. Bitte versuche es in {minuten} Minuten erneut.",
        )

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= LOGIN_LOCKOUT_THRESHOLD:
            user.login_locked_until = jetzt + LOGIN_LOCKOUT_DURATION
            user.failed_login_attempts = 0
            logger.warning("Login fuer Konto %s nach Fehlversuchen gesperrt", user.id)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-Mail oder Passwort falsch.")

    if user.failed_login_attempts or user.login_locked_until:
        user.failed_login_attempts = 0
        user.login_locked_until = None
        db.commit()
    return user


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

    user = _check_credentials(db, payload)
    if user.deleted_at is not None:
        # purge_deleted_users() ist oben bereits gelaufen - wenn deleted_at
        # noch gesetzt ist, läuft die 30-Tage-Karenzzeit also noch. Strukturiertes
        # Detail mit code, damit der Client statt eines Sackgassen-Logins die
        # Reaktivierung anbieten kann (POST /api/auth/reactivate).
        deadline = user.deleted_at + timedelta(days=ACCOUNT_GRACE_PERIOD_DAYS)
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {
                "code": "account_deleted",
                "message": (
                    "Dieses Konto wurde gelöscht. Bis zum "
                    f"{deadline.strftime('%d.%m.%Y')} kannst du es noch reaktivieren."
                ),
                "reactivate_until": deadline.isoformat(),
            },
        )
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


@router.post("/reactivate", response_model=TokenResponse)
@limiter.limit("10/minute")
def reactivate(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """Macht eine Selbstlöschung innerhalb der 30-Tage-Karenzzeit rückgängig.

    Nimmt bewusst dieselben Zugangsdaten wie /login entgegen: Wer E-Mail und
    aktuelles Passwort kennt, darf die eigene Löschung widerrufen - dieselbe
    Vertrauensbasis wie ein normaler Login. Nach Ablauf der Karenzzeit gibt es
    das Konto nicht mehr (purge_deleted_users hat es bereits entfernt), dann
    verhält sich dieser Endpunkt wie ein Login mit falschen Daten.
    """
    from ..cleanup import purge_deleted_users, purge_stale_verification_uploads

    purge_deleted_users(db)
    purge_stale_verification_uploads(db)

    user = _check_credentials(db, payload)
    if user.deleted_at is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dieses Konto ist nicht gelöscht.")

    user.deleted_at = None
    db.commit()

    record_device(db, user.id, request)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


# ---------- Passwort vergessen ----------


@router.post("/password/forgot", response_model=OkResponse)
@limiter.limit("5/hour")
def forgot_password(
    request: Request,
    payload: PasswordForgotRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Zuruecksetz-Link anfordern.

    Antwortet immer gleich - ob es zu der Adresse ein Konto gibt, verraet
    dieser Endpunkt nicht, sonst liesse sich damit pruefen, wer bei einer
    Dating-App angemeldet ist.
    """
    user = db.query(User).filter(func.lower(User.email) == payload.email).first()
    if (
        user is not None
        and user.deleted_at is None
        and not user.is_banned
        # Kurz nach der letzten Mail keine weitere - die Antwort bleibt gleich,
        # der offene Link aus der ersten Mail gilt ja noch.
        and not password_reset.recently_issued(db, user)
    ):
        token = password_reset.issue(db, user)
        background_tasks.add_task(
            send_password_reset,
            user.email,
            user.name,
            password_reset.build_link(token),
            password_reset.TOKEN_TTL_MINUTES,
            payload.language or user.language,
        )
    return OkResponse()


@router.post("/password/reset", response_model=TokenResponse)
@limiter.limit("10/hour")
def reset_password(
    request: Request,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Token aus dem Link einloesen und direkt anmelden."""
    try:
        user = password_reset.redeem(db, payload.token, payload.new_password)
    except password_reset.ResetError as err:
        raise HTTPException(400, str(err))
    record_device(db, user.id, request)
    return TokenResponse(access_token=create_access_token(user.id))
