from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Block, Match, Message, Swipe, User
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

    users_by_id = {
        u.id: u
        for u in db.query(User)
        .filter(User.id.in_(other_ids), User.deleted_at.is_(None))
        .all()
    }

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
                    is_online=users_by_id[other_id].is_online,
                ),
            )
        )

    result.sort(
        key=lambda pair: pair[1].last_message.created_at if pair[1].last_message else pair[0],
        reverse=True,
    )
    return [match_out for _, match_out in result]


@router.delete("/{match_id}")
def unmatch(
    match_id: str,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    """Match auflösen: Match und Chatverlauf werden gelöscht. Der eigene Swipe
    wird ebenfalls entfernt, damit die Person noch einmal ganz normal im Deck
    erscheint und bewusst weggewischt werden kann. Eine Sperre wie beim
    Blockieren ist das ausdrücklich nicht."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or current_user.id not in (match.user_a_id, match.user_b_id):
        raise HTTPException(404, "Match nicht gefunden.")

    other_id = match.user_b_id if match.user_a_id == current_user.id else match.user_a_id

    db.query(Message).filter(Message.match_id == match_id).delete()
    db.query(Swipe).filter(
        Swipe.from_user_id == current_user.id, Swipe.to_user_id == other_id
    ).delete()
    db.delete(match)
    db.commit()
    return {"unmatched": True}
