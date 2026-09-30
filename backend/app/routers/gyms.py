from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from .. import telegram
from ..database import get_db
from ..geo import city_for_plz
from ..models import Gym, GymStatus
from ..rate_limit import limiter
from ..schemas import GymOut, GymSuggestRequest

router = APIRouter(prefix="/api/gyms", tags=["gyms"])


def _like_escape(word: str) -> str:
    """% und _ aus der Eingabe woertlich nehmen statt als LIKE-Platzhalter."""
    return word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def gym_exists_for_profile(db: Session, gym_value: str) -> bool:
    """Gültig als Profil-Gym: der volle Anzeigename mit Adresse (label) eines
    freigegebenen bzw. noch offenen Gyms – oder, für Bestandsprofile, der
    bloße Gym-Name ohne Adresse."""
    value = (gym_value or "").strip()
    if not value:
        return False
    # label sieht so aus: "Name — Straße 1, 1100 Wien" -> Name-Teil abspalten
    name_part = value.split(" — ")[0].strip()
    candidates = (
        db.query(Gym)
        .filter(
            Gym.name == name_part,
            Gym.status.in_([GymStatus.approved, GymStatus.pending]),
        )
        .all()
    )
    return any(value in (g.name, g.label) for g in candidates)


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
    # Wortweise suchen: Jedes Wort muss in Name, Ort, Straße oder am Anfang
    # der PLZ vorkommen. Vorher lief die ganze Eingabe als ein Muster gegen
    # jeweils ein Feld - "fitinn wien", "mcfit graz" oder "john harris 1010"
    # fanden nichts, obwohl das Feld "Name, Ort oder PLZ" verspricht.
    # Leerzeichen im Namen zaehlen nicht ("fit inn" findet "FitInn").
    words = [_like_escape(w) for w in q.split()][:6]
    for word in words:
        like = f"%{word}%"
        query = query.filter(
            or_(
                Gym.name.ilike(like, escape="\\"),
                func.replace(Gym.name, " ", "").ilike(like, escape="\\"),
                Gym.city.ilike(like, escape="\\"),
                Gym.street.ilike(like, escape="\\"),
                Gym.plz.like(f"{word}%", escape="\\"),
            )
        )
    # Treffer, deren Name mit dem ersten Wort beginnt, zuerst ("fit inn"
    # soll FitInn vor CrossFit Innsbruck zeigen), danach alphabetisch.
    order = [Gym.name.asc(), Gym.plz.asc()]
    if words:
        starts = func.replace(Gym.name, " ", "").ilike(f"{words[0]}%", escape="\\")
        order.insert(0, case((starts, 0), else_=1))
    rows = query.order_by(*order).limit(30).all()
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
        # Das Vorschlagsformular fragt keinen Ort ab - ohne diese Ableitung
        # stand im Label "Name — Straße 1, 1010" statt "..., 1010 Wien".
        city=(payload.city or "").strip() or city_for_plz(payload.plz) or "",
        status=GymStatus.pending,
    )
    db.add(gym)
    db.commit()
    db.refresh(gym)
    telegram.notify_admin_task(f"🆕 Neuer Gym-Vorschlag im FLEXR-Admin-Dashboard: {gym.name}")
    return GymOut(
        id=gym.id, name=gym.name, street=gym.street, house_number=gym.house_number,
        plz=gym.plz, city=gym.city, label=gym.label,
    )
