from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser, Block, Match, Photo, PhotoStatus, Report, Swipe, User
from ..rate_limit import limiter
from ..schemas import (
    AdminLoginRequest,
    AdminReportOut,
    AdminStats,
    AdminTokenResponse,
    AdminUserDetailOut,
    AdminUserListItem,
    PhotoModerationOut,
)
from ..security import create_admin_access_token, get_current_admin, verify_password

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
    open_reports = db.query(func.count(Report.id)).scalar()
    return AdminStats(
        total_users=total_users,
        active_subscriptions=active_subscriptions,
        trial_users=trial_users,
        banned_users=banned_users,
        pending_photos=pending_photos,
        open_reports=open_reports,
    )


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
    return AdminUserDetailOut(
        id=user.id,
        email=user.email,
        name=user.name,
        age=user.age,
        plz=user.plz,
        city=user.city,
        street=user.street,
        gender=user.gender.value,
        interest=user.interest.value,
        gym=user.gym,
        bio=user.bio,
        is_subscribed=user.is_subscribed,
        is_banned=user.is_banned,
        is_active=user.is_active_member(),
        created_at=user.created_at,
        trial_ends_at=user.trial_ends_at,
        stripe_customer_id=user.stripe_customer_id,
        photos=user.photos,
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
