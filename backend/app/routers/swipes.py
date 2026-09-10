import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import consents, notifications, premium
from ..database import get_db
from ..gym_geo import coords_for_gym, gym_values_within
from ..models import Block, Match, Swipe, User
from ..rate_limit import limiter
from ..schemas import IncomingLikesOut, ProfileOut, RewindResult, SwipeRequest, SwipeResult
from ..security import require_active_membership
from ..verification_service import account_visible_condition
from .profiles import to_public_profile

logger = logging.getLogger(__name__)

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
    return deck_profiles(db, current_user)


def deck_profiles(db: Session, current_user: User, limit: int = DECK_SIZE) -> list[ProfileOut]:
    """Die Profile, die dieser Nutzer als nächstes zu sehen bekäme.

    Als eigene Funktion, weil der Benachrichtigungsjob dieselbe Frage stellt
    ("wie viele warten gerade?"). Eine zweite, vereinfachte Zählung dort würde
    zwangsläufig von dieser hier abweichen, sobald jemand die Filter anfasst -
    und dann Mails über Profile verschicken, die im Deck gar nicht auftauchen.
    """
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
        # Widerrufene Art.-9-Einwilligung: gender/interest dürfen dann nicht
        # mehr fürs Matching verwendet werden (siehe consents.py) - das
        # Konto darf also in keinem fremden Deck mehr erscheinen.
        consents.sensitive_data_consent_condition(),
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
        if len(profiles) >= limit:
            break
    return profiles[:limit]


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

    # Das Like-Kontingent des Standardkontos. Ein Pass kostet bewusst nichts:
    # Wer weiterblaettern muss, um an Likes zu sparen, bekommt ein schlechtes
    # Deck vorgesetzt und wir schlechtere Daten. Auch ein bereits gesetztes
    # Like erneut zu senden (siehe existing_swipe weiter unten) zaehlt nicht
    # doppelt - gezaehlt werden Swipe-Zeilen, nicht Aufrufe.
    if payload.action == "like":
        premium.ensure_like_allowed(db, current_user)

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
                new_match = Match(user_a_id=a, user_b_id=b)
                db.add(new_match)
                db.commit()
                # Beide Seiten benachrichtigen, nicht nur die wartende: für den
                # Swipenden ist das Match genauso neu, er sieht es nur zufällig
                # gerade im Vordergrund. Der Versand darf den Swipe nicht
                # scheitern lassen - ein toter SMTP-Server würde sonst das
                # Match-Ergebnis verschlucken, obwohl es längst gespeichert ist.
                for recipient, other in (
                    (current_user, target_user),
                    (target_user, current_user),
                ):
                    try:
                        notifications.notify_new_match(
                            db, recipient, other.name, new_match.id
                        )
                    except Exception:
                        logger.exception(
                            "Match-Benachrichtigung fehlgeschlagen (match=%s)",
                            new_match.id,
                        )
            matched = True

    return SwipeResult(
        matched=matched,
        likes_remaining=premium.likes_remaining(db, current_user),
    )


@router.get("/incoming", response_model=IncomingLikesOut)
def incoming_likes(
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    """Wer dich geliket hat - eine Premium-Funktion.

    Ohne Premium kommt bewusst **keine** 403, sondern nur die Anzahl ohne die
    Profile: "3 Leute warten auf dich" ist die ehrliche Antwort und zugleich
    der beste Grund, Premium anzusehen. Eine Fehlermeldung waere beides nicht.

    Gezaehlt und geliefert werden nur Likes, auf die noch nicht zurueckgeswipet
    wurde - was schon ein Match ist, steht in der Match-Liste, und ein Pass
    soll nicht als offener Like wieder auftauchen.
    """
    eigene_swipes = {
        row.to_user_id
        for row in db.query(Swipe.to_user_id).filter(Swipe.from_user_id == current_user.id)
    }
    blockiert = {
        row.blocked_id
        for row in db.query(Block.blocked_id).filter(Block.blocker_id == current_user.id)
    } | {
        row.blocker_id
        for row in db.query(Block.blocker_id).filter(Block.blocked_id == current_user.id)
    }

    likers = (
        db.query(User)
        .join(Swipe, Swipe.from_user_id == User.id)
        .filter(
            Swipe.to_user_id == current_user.id,
            Swipe.action == "like",
            User.deleted_at.is_(None),
            User.is_banned.is_(False),
            account_visible_condition(),
        )
        .order_by(Swipe.created_at.desc())
        .all()
    )
    offen = [
        u for u in likers if u.id not in eigene_swipes and u.id not in blockiert
    ]

    if not current_user.is_premium:
        return IncomingLikesOut(count=len(offen), profiles=[], premium_required=True)
    return IncomingLikesOut(
        count=len(offen),
        profiles=[to_public_profile(u) for u in offen],
        premium_required=False,
    )


@router.post("/rewind", response_model=RewindResult)
def rewind_last_swipe(
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    """Den letzten Swipe zuruecknehmen - eine Premium-Funktion.

    Der zurueckgenommene Swipe wird geloescht, das Profil taucht dadurch beim
    naechsten Laden wieder im Deck auf (``deck_profiles`` schliesst genau die
    bereits beswipeten aus).

    **Ein Like, aus dem bereits ein Match entstanden ist, laesst sich nicht
    zuruecknehmen.** Sonst verschwaende auf der Gegenseite ein Match wieder,
    das ihr schon angezeigt und womoeglich per Mail gemeldet wurde - das
    Zuruecknehmen ist als Notausgang fuer den eigenen Daumen gedacht, nicht als
    Eingriff in fremde Chatlisten. Wer das Match wirklich los sein will, loest
    es auf; das ist der dafuer vorgesehene Weg.
    """
    if not current_user.is_premium:
        raise HTTPException(
            403,
            {
                "code": "premium_required",
                "message": (
                    "Den letzten Swipe zurücknehmen gibt es mit FLEXR Premium."
                ),
            },
        )

    letzter = (
        db.query(Swipe)
        .filter(Swipe.from_user_id == current_user.id)
        .order_by(Swipe.created_at.desc())
        .first()
    )
    if not letzter:
        raise HTTPException(404, "Es gibt keinen Swipe zum Zurücknehmen.")

    a, b = sorted([current_user.id, letzter.to_user_id])
    if db.query(Match).filter(Match.user_a_id == a, Match.user_b_id == b).first():
        raise HTTPException(
            409,
            "Daraus ist schon ein Match geworden - das lässt sich nur auflösen, "
            "nicht zurücknehmen.",
        )

    zurueckgenommen = letzter.to_user_id
    db.delete(letzter)
    db.commit()
    return RewindResult(
        to_user_id=zurueckgenommen,
        likes_remaining=premium.likes_remaining(db, current_user),
    )
