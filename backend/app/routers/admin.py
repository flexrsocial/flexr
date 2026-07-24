from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    AdminUser,
    Block,
    DailyAccess,
    Gym,
    GymStatus,
    Match,
    Message,
    Photo,
    PhotoStatus,
    Report,
    Swipe,
    User,
    UserDevice,
    VerificationRequest,
    VerificationStatus,
)
from ..rate_limit import limiter
from ..schemas import (
    AdminAccessPoint,
    AdminAccessStats,
    AdminCountryStat,
    AdminFlaggedMessageOut,
    AdminGymOut,
    AdminGymUpdate,
    AdminLoginRequest,
    AdminReportOut,
    AdminStats,
    AdminTokenResponse,
    AdminUserDetailOut,
    AdminUserListItem,
    AdminVerificationOut,
    PhotoModerationOut,
)
from ..security import create_admin_access_token, get_current_admin, verify_password
from .. import storage

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/auth/login", response_model=AdminTokenResponse)
@limiter.limit("10/minute")
def admin_login(request: Request, payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(401, "E-Mail oder Passwort falsch.")
    token = create_admin_access_token(admin.id)
    return AdminTokenResponse(access_token=token)


@router.get("/stats", response_model=AdminStats)
def get_stats(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar()
    active_subscriptions = db.query(func.count(User.id)).filter(User.is_subscribed.is_(True)).scalar()
    trial_users = (
        db.query(func.count(User.id))
        .filter(User.is_subscribed.is_(False), User.trial_ends_at > datetime.utcnow())
        .scalar()
    )
    banned_users = db.query(func.count(User.id)).filter(User.is_banned.is_(True)).scalar()
    pending_photos = db.query(func.count(Photo.id)).filter(Photo.status == PhotoStatus.pending).scalar()
    open_reports = db.query(func.count(Report.id)).filter(Report.dismissed_at.is_(None)).scalar()
    pending_verifications = (
        db.query(func.count(VerificationRequest.id))
        .filter(VerificationRequest.status == VerificationStatus.submitted)
        .scalar()
    )
    flagged_messages = db.query(func.count(Message.id)).filter(Message.is_flagged.is_(True)).scalar()
    pending_gyms = db.query(func.count(Gym.id)).filter(Gym.status == GymStatus.pending).scalar()

    today = date.today()
    active_today = (
        db.query(func.count(func.distinct(DailyAccess.user_id)))
        .filter(DailyAccess.day == today)
        .scalar()
    )
    new_today = (
        db.query(func.count(User.id))
        .filter(func.date(User.created_at) == today, User.deleted_at.is_(None))
        .scalar()
    )
    return AdminStats(
        total_users=total_users,
        active_subscriptions=active_subscriptions,
        trial_users=trial_users,
        banned_users=banned_users,
        pending_photos=pending_photos,
        open_reports=open_reports,
        pending_verifications=pending_verifications,
        flagged_messages=flagged_messages,
        pending_gyms=pending_gyms,
        active_today=active_today,
        new_today=new_today,
    )


@router.get("/access-stats", response_model=AdminAccessStats)
def get_access_stats(
    days: int = Query(14, ge=1, le=90),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Zugriffsstatistik: tagesaktive Nutzer je Tag (letzte `days` Tage) und
    Länderverteilung der heute aktiven Nutzer."""
    today = date.today()
    start = today - timedelta(days=days - 1)

    rows = (
        db.query(DailyAccess.day, func.count(func.distinct(DailyAccess.user_id)))
        .filter(DailyAccess.day >= start)
        .group_by(DailyAccess.day)
        .all()
    )
    counts = {d: c for d, c in rows}
    daily = [
        AdminAccessPoint(
            day=(start + timedelta(days=i)).isoformat(),
            count=counts.get(start + timedelta(days=i), 0),
        )
        for i in range(days)
    ]

    country_rows = (
        db.query(DailyAccess.country, func.count(func.distinct(DailyAccess.user_id)))
        .filter(DailyAccess.day == today)
        .group_by(DailyAccess.country)
        .order_by(func.count(func.distinct(DailyAccess.user_id)).desc())
        .all()
    )
    countries = [AdminCountryStat(country=c or "??", count=n) for c, n in country_rows]

    return AdminAccessStats(daily=daily, countries=countries)


@router.get("/users", response_model=list[AdminUserListItem])
def list_users(
    q: Optional[str] = None,
    banned: Optional[bool] = None,
    subscribed: Optional[bool] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.email.ilike(like), User.name.ilike(like)))
    if banned is not None:
        query = query.filter(User.is_banned.is_(banned))
    if subscribed is not None:
        query = query.filter(User.is_subscribed.is_(subscribed))

    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    user_ids = [u.id for u in users]
    photo_counts = dict(
        db.query(Photo.user_id, func.count(Photo.id))
        .filter(Photo.user_id.in_(user_ids))
        .group_by(Photo.user_id)
        .all()
    ) if user_ids else {}

    return [
        AdminUserListItem(
            id=u.id,
            email=u.email,
            name=u.name,
            age=u.age,
            city=u.city,
            is_subscribed=u.is_subscribed,
            is_banned=u.is_banned,
            is_active=u.is_active_member(),
            created_at=u.created_at,
            photo_count=photo_counts.get(u.id, 0),
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=AdminUserDetailOut)
def get_user_detail(
    user_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Nutzer nicht gefunden.")

    # Geräteprüfung: Geräte des Nutzers inkl. weiterer Konten auf demselben Gerät
    devices = db.query(UserDevice).filter(UserDevice.user_id == user.id).all()
    device_infos = []
    for d in devices:
        shared = (
            db.query(User.name)
            .join(UserDevice, UserDevice.user_id == User.id)
            .filter(UserDevice.device_id == d.device_id, User.id != user.id)
            .all()
        )
        device_infos.append(
            {
                "device_id": d.device_id,
                "user_agent": d.user_agent,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                "shared_with": [name for (name,) in shared],
            }
        )

    return AdminUserDetailOut(
        id=user.id,
        email=user.email,
        name=user.name,
        age=user.age,
        plz=user.plz,
        city=user.city,
        gender=user.gender.value,
        interest=user.interest.value,
        gym=user.gym,
        bio=user.bio,
        is_subscribed=user.is_subscribed,
        is_banned=user.is_banned,
        is_verified=user.is_verified,
        is_active=user.is_active_member(),
        created_at=user.created_at,
        trial_ends_at=user.trial_ends_at,
        stripe_customer_id=user.stripe_customer_id,
        phone=user.phone,
        phone_verified=user.phone_verified,
        photos=user.photos,
        devices=device_infos,
    )


@router.post("/users/{user_id}/ban")
def ban_user(
    user_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Nutzer nicht gefunden.")
    user.is_banned = True
    db.commit()
    return {"is_banned": True}


@router.post("/users/{user_id}/unban")
def unban_user(
    user_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Nutzer nicht gefunden.")
    user.is_banned = False
    db.commit()
    return {"is_banned": False}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Nutzer nicht gefunden.")
    db.delete(user)
    db.commit()
    return {"deleted": True}


@router.get("/photos", response_model=list[PhotoModerationOut])
def list_photos(
    status_filter: Optional[str] = Query("pending", alias="status"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Photo, User).join(User, Photo.user_id == User.id)
    if status_filter and status_filter != "all":
        try:
            query = query.filter(Photo.status == PhotoStatus(status_filter))
        except ValueError:
            raise HTTPException(400, "Ungültiger Status-Filter.")
    rows = query.order_by(Photo.id.desc()).offset(offset).limit(limit).all()
    return [
        PhotoModerationOut(
            id=photo.id,
            url=photo.url,
            status=photo.status.value,
            position=photo.position,
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
        )
        for photo, user in rows
    ]


@router.post("/photos/{photo_id}/approve")
def approve_photo(
    photo_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(404, "Foto nicht gefunden.")
    photo.status = PhotoStatus.approved
    db.commit()
    return {"status": photo.status.value}


@router.post("/photos/{photo_id}/reject")
def reject_photo(
    photo_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(404, "Foto nicht gefunden.")
    photo.status = PhotoStatus.rejected
    db.commit()
    return {"status": photo.status.value}


@router.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(404, "Foto nicht gefunden.")
    db.delete(photo)
    db.commit()
    return {"deleted": True}


import json
from datetime import datetime as _dt


def _delete_selfies_quietly(req: VerificationRequest) -> None:
    """Selfies nach Abschluss der Prüfung aus dem Storage löschen (best effort,
    ein Storage-Fehler soll die Entscheidung nicht blockieren)."""
    if not req.selfies:
        return
    for entry in json.loads(req.selfies):
        try:
            storage.delete_object(entry["object_key"])
        except Exception:
            pass


@router.get("/verifications", response_model=list[AdminVerificationOut])
def list_verifications(
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(VerificationRequest, User)
        .join(User, VerificationRequest.user_id == User.id)
        .filter(VerificationRequest.status == VerificationStatus.submitted)
        .order_by(VerificationRequest.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = []
    for req, user in rows:
        selfies = json.loads(req.selfies) if req.selfies else []
        result.append(
            AdminVerificationOut(
                id=req.id,
                user_id=user.id,
                user_name=user.name,
                user_email=user.email,
                prompts=json.loads(req.prompts),
                selfie_urls=[
                    {"prompt": s["prompt"], "url": storage.public_url_for(s["object_key"])}
                    for s in selfies
                ],
                profile_photo_urls=[p.url for p in user.photos],
                created_at=req.created_at,
            )
        )
    return result


@router.post("/verifications/{request_id}/approve")
def approve_verification(
    request_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    req = db.query(VerificationRequest).filter(VerificationRequest.id == request_id).first()
    if not req or req.status != VerificationStatus.submitted:
        raise HTTPException(404, "Verifizierungsanfrage nicht gefunden.")
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(404, "Nutzer nicht gefunden.")

    _delete_selfies_quietly(req)
    req.selfies = None  # Selfies sind gelöscht (siehe Datenschutzerklärung)
    req.status = VerificationStatus.approved
    req.decided_at = _dt.utcnow()
    user.is_verified = True
    db.commit()
    return {"is_verified": True}


@router.post("/verifications/{request_id}/reject")
def reject_verification(
    request_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    req = db.query(VerificationRequest).filter(VerificationRequest.id == request_id).first()
    if not req or req.status != VerificationStatus.submitted:
        raise HTTPException(404, "Verifizierungsanfrage nicht gefunden.")

    _delete_selfies_quietly(req)
    req.selfies = None
    req.status = VerificationStatus.rejected
    req.decided_at = _dt.utcnow()
    db.commit()
    return {"is_verified": False}


@router.get("/gyms", response_model=list[AdminGymOut])
def list_admin_gyms(
    status_filter: str = Query("pending", alias="status"),
    limit: int = Query(100, le=500),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Gym)
    if status_filter != "all":
        try:
            query = query.filter(Gym.status == GymStatus(status_filter))
        except ValueError:
            raise HTTPException(400, "Ungültiger Status-Filter.")
    rows = query.order_by(Gym.created_at.desc()).limit(limit).all()
    return [
        AdminGymOut(
            id=g.id, name=g.name, street=g.street, house_number=g.house_number,
            plz=g.plz, city=g.city, status=g.status.value, created_at=g.created_at,
        )
        for g in rows
    ]


@router.post("/gyms/{gym_id}/approve")
def approve_gym(
    gym_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise HTTPException(404, "Gym nicht gefunden.")
    gym.status = GymStatus.approved
    db.commit()
    return {"status": gym.status.value}


@router.patch("/gyms/{gym_id}", response_model=AdminGymOut)
def update_gym(
    gym_id: str,
    payload: AdminGymUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Korrigiert einzelne Felder eines Gym-Eintrags (z. B. Rechtschreibung),
    bevor er freigegeben wird. Wird der Name geändert, ziehen bestehende
    Profile mit dem alten Namen mit, damit der Vorschlagende sein Gym behält."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise HTTPException(404, "Gym nicht gefunden.")

    data = payload.model_dump(exclude_unset=True)
    old_name = gym.name

    if "name" in data:
        new_name = data["name"].strip()
        if not new_name:
            raise HTTPException(400, "Name darf nicht leer sein.")
        if new_name != old_name:
            # Kollision mit einem anderen bereits vorhandenen Eintrag vermeiden
            clash = (
                db.query(Gym)
                .filter(Gym.id != gym.id, Gym.name.ilike(new_name), Gym.plz == gym.plz)
                .first()
            )
            if clash:
                raise HTTPException(
                    400, "Ein Gym mit diesem Namen und dieser PLZ existiert bereits."
                )
            # Profile, die den alten Namen referenzieren, mitziehen
            db.query(User).filter(User.gym == old_name).update(
                {User.gym: new_name}, synchronize_session=False
            )
        gym.name = new_name

    for field in ("street", "house_number", "city"):
        if field in data:
            setattr(gym, field, (data[field] or "").strip())
    if "plz" in data:
        gym.plz = data["plz"]

    db.commit()
    db.refresh(gym)
    return AdminGymOut(
        id=gym.id, name=gym.name, street=gym.street, house_number=gym.house_number,
        plz=gym.plz, city=gym.city, status=gym.status.value, created_at=gym.created_at,
    )


@router.post("/gyms/{gym_id}/reject")
def reject_gym(
    gym_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise HTTPException(404, "Gym nicht gefunden.")
    gym.status = GymStatus.rejected
    db.commit()
    return {"status": gym.status.value}


@router.get("/flagged-messages", response_model=list[AdminFlaggedMessageOut])
def list_flagged_messages(
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Message, User.name)
        .join(User, Message.sender_id == User.id)
        .filter(Message.is_flagged.is_(True))
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        AdminFlaggedMessageOut(
            id=msg.id,
            sender_id=msg.sender_id,
            sender_name=sender_name,
            content=msg.content,
            display_content=(msg.display_content if msg.display_content is not None
                             else msg.content),
            was_censored=bool(msg.was_censored),
            delivered=True,
            read_at=msg.read_at,
            flag_reason=msg.flag_reason,
            created_at=msg.created_at,
        )
        for msg, sender_name in rows
    ]


@router.post("/flagged-messages/{message_id}/clear")
def clear_flagged_message(
    message_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    msg = db.query(Message).filter(Message.id == message_id, Message.is_flagged.is_(True)).first()
    if not msg:
        raise HTTPException(404, "Nachricht nicht gefunden.")
    msg.is_flagged = False
    msg.flag_reason = None
    db.commit()
    return {"cleared": True}


@router.get("/reports", response_model=list[AdminReportOut])
def list_reports(
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    reporter = User.__table__.alias("reporter")
    reported = User.__table__.alias("reported")
    rows = (
        db.query(Report, reporter.c.name, reported.c.name)
        .join(reporter, Report.reporter_id == reporter.c.id)
        .join(reported, Report.reported_id == reported.c.id)
        .filter(Report.dismissed_at.is_(None))  # abgehakte Meldungen ausblenden
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        AdminReportOut(
            id=report.id,
            reporter_id=report.reporter_id,
            reporter_name=reporter_name,
            reported_id=report.reported_id,
            reported_name=reported_name,
            reason=report.reason,
            created_at=report.created_at,
        )
        for report, reporter_name, reported_name in rows
    ]


@router.post("/reports/{report_id}/dismiss")
def dismiss_report(
    report_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Meldung als unbedenklich abhaken: verschwindet aus der offenen Liste,
    bleibt aber als Nachweis in der Datenbank."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Meldung nicht gefunden.")
    if report.dismissed_at is None:
        report.dismissed_at = datetime.utcnow()
        db.commit()
    return {"dismissed": True}
