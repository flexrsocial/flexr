from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Block, Match, Message, User
from ..schemas import MatchOut
from ..security import require_active_membership
from .profiles import to_public_profile

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[MatchOut])
def get_matches(
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Match)
        .filter(or_(Match.user_a_id == current_user.id, Match.user_b_id == current_user.id))
        .all()
    )
    if not rows:
        return []

    other_ids = [
        row.user_b_id if row.user_a_id == current_user.id else row.user_a_id for row in rows
    ]
    # Blockierungen wirken in beide Richtungen: ein Match verschwindet aus der
    # Liste, sobald eine Seite die andere blockiert hat.
    blocked_ids = {
        b.blocked_id for b in db.query(Block).filter(Block.blocker_id == current_user.id)
    } | {
        b.blocker_id for b in db.query(Block).filter(Block.blocked_id == current_user.id)
    }

    users_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(other_ids)).all()}

    result = []
    for row in rows:
        other_id = row.user_b_id if row.user_a_id == current_user.id else row.user_a_id
        if other_id in blocked_ids or other_id not in users_by_id:
            continue

        last_message = (
            db.query(Message)
            .filter(Message.match_id == row.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        unread_count = (
            db.query(Message)
            .filter(
                Message.match_id == row.id,
                Message.sender_id == other_id,
                Message.read_at.is_(None),
            )
            .count()
        )
        result.append(
            (
                row.created_at,
                MatchOut(
                    match_id=row.id,
                    profile=to_public_profile(users_by_id[other_id]),
                    last_message=last_message,
                    unread_count=unread_count,
                    is_online=users_by_id[other_id].is_online(),
                ),
            )
        )

    result.sort(
        key=lambda pair: pair[1].last_message.created_at if pair[1].last_message else pair[0],
        reverse=True,
    )
    return [match_out for _, match_out in result]
