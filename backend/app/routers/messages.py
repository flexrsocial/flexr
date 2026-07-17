from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Block, Match, Message, User
from ..rate_limit import limiter
from ..schemas import MessageOut, SendMessageRequest
from ..security import require_active_membership

router = APIRouter(prefix="/api/matches", tags=["messages"])


def _get_match_and_other_id(match_id: str, current_user: User, db: Session) -> tuple[Match, str]:
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or current_user.id not in (match.user_a_id, match.user_b_id):
        raise HTTPException(404, "Match nicht gefunden.")

    other_id = match.user_b_id if match.user_a_id == current_user.id else match.user_a_id

    blocked = (
        db.query(Block)
        .filter(
            or_(
                and_(Block.blocker_id == current_user.id, Block.blocked_id == other_id),
                and_(Block.blocker_id == other_id, Block.blocked_id == current_user.id),
            )
        )
        .first()
    )
    if blocked:
        raise HTTPException(403, "Chat nicht verfügbar.")

    return match, other_id


@router.get("/{match_id}/messages", response_model=list[MessageOut])
def list_messages(
    match_id: str,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    _, other_id = _get_match_and_other_id(match_id, current_user, db)

    messages = (
        db.query(Message)
        .filter(Message.match_id == match_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    unread = [m for m in messages if m.sender_id == other_id and m.read_at is None]
    if unread:
        now = datetime.utcnow()
        for m in unread:
            m.read_at = now
        db.commit()

    return messages


@router.post("/{match_id}/messages", response_model=MessageOut, status_code=201)
@limiter.limit("30/minute")
def send_message(
    request: Request,
    match_id: str,
    payload: SendMessageRequest,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    _get_match_and_other_id(match_id, current_user, db)

    message = Message(match_id=match_id, sender_id=current_user.id, content=payload.content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
