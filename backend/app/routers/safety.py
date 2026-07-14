from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Block, Report, User
from ..rate_limit import limiter
from ..schemas import BlockRequest, ReportRequest
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["safety"])


@router.post("/reports", status_code=201)
@limiter.limit("20/minute")
def create_report(
    request: Request,
    payload: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.reported_user_id == current_user.id:
        raise HTTPException(400, "Du kannst dich nicht selbst melden.")

    reported_user = db.query(User).filter(User.id == payload.reported_user_id).first()
    if not reported_user:
        raise HTTPException(404, "Nutzer nicht gefunden.")

    db.add(
        Report(
            reporter_id=current_user.id,
            reported_id=payload.reported_user_id,
            reason=payload.reason,
        )
    )
    db.commit()
    return {"reported": True}


@router.post("/blocks", status_code=201)
@limiter.limit("20/minute")
def create_block(
    request: Request,
    payload: BlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.user_id == current_user.id:
        raise HTTPException(400, "Du kannst dich nicht selbst blockieren.")

    blocked_user = db.query(User).filter(User.id == payload.user_id).first()
    if not blocked_user:
        raise HTTPException(404, "Nutzer nicht gefunden.")

    existing = (
        db.query(Block)
        .filter(Block.blocker_id == current_user.id, Block.blocked_id == payload.user_id)
        .first()
    )
    if not existing:
        db.add(Block(blocker_id=current_user.id, blocked_id=payload.user_id))
        db.commit()
    return {"blocked": True}


@router.get("/blocks")
def list_blocks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(Block).filter(Block.blocker_id == current_user.id).all()
    return [row.blocked_id for row in rows]


@router.delete("/blocks/{user_id}")
def remove_block(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    block = (
        db.query(Block)
        .filter(Block.blocker_id == current_user.id, Block.blocked_id == user_id)
        .first()
    )
    if not block:
        raise HTTPException(404, "Blockierung nicht gefunden.")
    db.delete(block)
    db.commit()
    return {"blocked": False}
