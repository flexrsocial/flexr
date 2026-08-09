from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..gym_geo import coords_for_gym, gym_values_within
from ..models import Block, Match, Swipe, User
from ..rate_limit import limiter
from ..schemas import ProfileOut, SwipeRequest, SwipeResult
from ..security import require_active_membership
from ..verification_service import account_visible_condition
from .profiles import to_public_profile

router = APIRouter(prefix="/api/swipes", tags=["swipes"])

# Wie viele Profile ein Deck höchstens enthält.
DECK_SIZE = 50

# Wie viele Studios pro Abfrage zusammengefasst werden. Klein genug, dass bei
# einem dichten Umkreis nicht das halbe Land geladen wird, groß genug, dass es
# im Normalfall bei einer Abfrage bleibt.
GYM_BATCH_SIZE = 40


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

    # Umkreissuche rund um das eingetragene Gym - nicht um den Wohnort und
    # nicht um die aktuelle Geräteposition. Wer kein Gym mit auflösbarer
    # Adresse hat (Bestandsprofile mit blankem Gym-Namen), nimmt an der Suche
    # nicht teil: weder sieht er ein Deck noch erscheint er in fremden.
    my_coords = coords_for_gym(db, current_user.gym)
    if my_coords is None:
        return []

    radius = current_user.search_radius_km or 20
    # Erst die Studios im Umkreis bestimmen, dann die Nutzer dazu holen. Die
    # Entfernung hängt nur am Gym, und die Gym-Tabelle bleibt klein - so wird
    # nie ein naher Treffer abgeschnitten, weil weiter entfernte Konten die
    # Abfrage gefüllt haben.
    nearby_gyms = gym_values_within(db, my_coords, radius)
    if not nearby_gyms:
        return []

    base_filters = [
        User.id != current_user.id,
        User.deleted_at.is_(None),
        User.is_banned.is_(False),
        # Nicht freigeschaltete Konten (Prüfung offen oder abgelehnt) sind
        # für andere unsichtbar.
        account_visible_condition(),
        User.gender == current_user.interest,
        User.interest == current_user.gender,
    ]
    if excluded_ids:
        base_filters.append(~User.id.in_(excluded_ids))

    # Gyms nach Entfernung abarbeiten und abbrechen, sobald das Deck voll ist:
    # Ein Stapel enthält nur Studios, die näher liegen als alle folgenden, die
    # Reihenfolge bleibt also über alle Stapel hinweg korrekt sortiert.
    gyms_by_distance = sorted(nearby_gyms.items(), key=lambda pair: pair[1])
    profiles = []
    for start in range(0, len(gyms_by_distance), GYM_BATCH_SIZE):
        batch = [value for value, _ in gyms_by_distance[start:start + GYM_BATCH_SIZE]]
        users = db.query(User).filter(*base_filters, User.gym.in_(batch)).all()
        users.sort(key=lambda u: nearby_gyms[u.gym])
        for u in users:
            profile = to_public_profile(u)
            # Nur Profile mit mindestens einem freigegebenen Foto erscheinen in der Suche.
            if not profile.photos:
                continue
            profile.distance_km = round(nearby_gyms[u.gym])
            profiles.append(profile)
        if len(profiles) >= DECK_SIZE:
            break
    return profiles[:DECK_SIZE]


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

    target_user = (
        db.query(User)
        .filter(
            User.id == payload.to_user_id,
            User.deleted_at.is_(None),
            User.is_banned.is_(False),
            account_visible_condition(),
        )
        .first()
    )
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
