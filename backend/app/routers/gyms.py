from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Gym, GymStatus
from ..rate_limit import limiter
from ..schemas import GymOut, GymSuggestRequest

router = APIRouter(prefix="/api/gyms", tags=["gyms"])


def gym_exists_for_profile(db: Session, gym_name: str) -> bool:
    """Gültig als Profil-Gym: freigegebene Einträge sowie noch offene
    Vorschläge (damit der Vorschlagende sein Gym sofort nutzen kann)."""
    return (
        db.query(Gym)
        .filter(
            Gym.name == gym_name,
            Gym.status.in_([GymStatus.approved, GymStatus.pending]),
        )
        .first()
        is not None
    )


@router.get("", response_model=list[GymOut])
def list_gyms(
    q: str = Query("", max_length=100),
    db: Session = Depends(get_db),
):
    """Durchsuchbare Liste aller freigegebenen Gyms (öffentlich, wird schon
    bei der Registrierung gebraucht)."""
    # Nur Einträge mit vollständiger Adresse anzeigen. Die reinen Legacy-Namen
    # (McFit, FitInn, ... ohne Adresse) bleiben in der Tabelle, damit bestehende
    # Profile weiter gültig sind, tauchen aber nicht mehr in der Auswahl auf.
    query = db.query(Gym).filter(
        Gym.status == GymStatus.approved,
        Gym.street != "",
        Gym.plz != "",
    )
    term = q.strip()
    if term:
        like = f"%{term}%"
        query = query.filter(
            or_(Gym.name.ilike(like), Gym.city.ilike(like), Gym.plz.like(f"{term}%"))
        )
    rows = query.order_by(Gym.name.asc(), Gym.plz.asc()).limit(30).all()
    return [
        GymOut(
            id=g.id, name=g.name, street=g.street, house_number=g.house_number,
            plz=g.plz, city=g.city, label=g.label,
        )
        for g in rows
    ]


@router.post("/suggest", response_model=GymOut, status_code=201)
@limiter.limit("5/hour")
def suggest_gym(
    request: Request,
    payload: GymSuggestRequest,
    db: Session = Depends(get_db),
):
    """Nutzer-Vorschlag für ein fehlendes Gym (öffentlich, da bereits bei der
    Registrierung nötig). Erscheint im Admin-Dashboard zur Freigabe; der
    Vorschlagende kann den Namen sofort als sein Gym verwenden."""
    name = payload.name.strip()
    existing = (
        db.query(Gym)
        .filter(Gym.name.ilike(name), Gym.plz == payload.plz)
        .first()
    )
    if existing:
        if existing.status == GymStatus.rejected:
            raise HTTPException(400, "Dieses Gym wurde bereits geprüft und abgelehnt.")
        # Bereits vorhanden (freigegeben oder offen) - einfach zurückgeben
        return GymOut(
            id=existing.id, name=existing.name, street=existing.street,
            house_number=existing.house_number, plz=existing.plz,
            city=existing.city, label=existing.label,
        )

    gym = Gym(
        name=name,
        street=payload.street.strip(),
        house_number=payload.house_number.strip(),
        plz=payload.plz,
        city=(payload.city or "").strip(),
        status=GymStatus.pending,
    )
    db.add(gym)
    db.commit()
    db.refresh(gym)
    return GymOut(
        id=gym.id, name=gym.name, street=gym.street, house_number=gym.house_number,
        plz=gym.plz, city=gym.city, label=gym.label,
    )
