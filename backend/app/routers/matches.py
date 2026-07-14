from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Match, User
from ..schemas import ProfileOut
from ..security import require_active_membership

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[ProfileOut])
def get_matches(
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Match)
        .filter(or_(Match.user_a_id == current_user.id, Match.user_b_id == current_user.id))
        .all()
    )
    other_ids = [
        row.user_b_id if row.user_a_id == current_user.id else row.user_a_id for row in rows
    ]
    if not other_ids:
        return []
    return db.query(User).filter(User.id.in_(other_ids)).all()
