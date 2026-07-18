from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..geo import haversine_km
from ..models import Block, Match, Swipe, User
from ..rate_limit import limiter
from ..schemas import ProfileOut, SwipeRequest, SwipeResult
from ..security import require_active_membership
from .profiles import to_public_profile

router = APIRouter(prefix="/api/swipes", tags=["swipes"])


@router.get("/deck", response_model=list[ProfileOut])
def get_deck(
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    already_swiped_ids = [
        row.to_user_id
        for row in db.query(Swipe.to_user_id).filter(Swipe.from_user_id == current_user.id)
    ]
    blocked_ids = {
        row.blocked_id
        for row in db.query(Block.blocked_id).filter(Block.blocker_id == current_user.id)
    }
    blocked_by_ids = {
        row.blocker_id
        for row in db.query(Block.blocker_id).filter(Block.blocked_id == current_user.id)
    }
    excluded_ids = set(already_swiped_ids) | blocked_ids | blocked_by_ids

    candidates = (
        db.query(User)
        .filter(
            User.id != current_user.id,
            User.gender == current_user.interest,
            User.interest == current_user.gender,
            ~User.id.in_(excluded_ids) if excluded_ids else True,
        )
        .limit(500)
        .all()
    )

    # Umkreissuche: GPS-Position (wenn freigegeben) bzw. PLZ-Koordinate,
    # Kandidaten analog. Ohne eigene Koordinaten (unbekannte PLZ) greift
    # als Notlösung der alte Gleiche-Stadt-Filter.
    my_coords = current_user.effective_coords()
    if my_coords is None:
        nearby = [u for u in candidates if u.city == current_user.city][:50]
        return [to_public_profile(u) for u in nearby]

    radius = current_user.search_radius_km or 20
    results = []
    for u in candidates:
        their_coords = u.effective_coords()
        if their_coords is None:
            continue
        dist = haversine_km(my_coords[0], my_coords[1], their_coords[0], their_coords[1])
        if dist <= radius:
            results.append((dist, u))

    results.sort(key=lambda pair: pair[0])
    profiles = []
    for dist, u in results[:50]:
        profile = to_public_profile(u)
        profile.distance_km = round(dist)
        profiles.append(profile)
    return profiles


@router.post("", response_model=SwipeResult)
@limiter.limit("60/minute")
def swipe(
    request: Request,
    payload: SwipeRequest,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    if payload.to_user_id == current_user.id:
        raise HTTPException(400, "Du kannst nicht mit dir selbst swipen.")

    target_user = db.query(User).filter(User.id == payload.to_user_id).first()
    if not target_user:
        raise HTTPException(404, "Nutzer nicht gefunden.")

    existing_swipe = (
        db.query(Swipe)
        .filter(Swipe.from_user_id == current_user.id, Swipe.to_user_id == payload.to_user_id)
        .first()
    )
    if existing_swipe:
        existing_swipe.action = payload.action
    else:
        db.add(Swipe(from_user_id=current_user.id, to_user_id=payload.to_user_id, action=payload.action))
    db.commit()

    matched = False
    if payload.action == "like":
        reverse_like = (
            db.query(Swipe)
            .filter(
                Swipe.from_user_id == payload.to_user_id,
                Swipe.to_user_id == current_user.id,
                Swipe.action == "like",
            )
            .first()
        )
        if reverse_like:
            a, b = sorted([current_user.id, payload.to_user_id])
            existing_match = (
                db.query(Match)
                .filter(Match.user_a_id == a, Match.user_b_id == b)
                .first()
            )
            if not existing_match:
                db.add(Match(user_a_id=a, user_b_id=b))
                db.commit()
            matched = True

    return SwipeResult(matched=matched)
