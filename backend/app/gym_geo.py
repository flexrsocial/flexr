"""Mittelpunkt der Umkreissuche: die Adresse des eingetragenen Gyms.

Gesucht wird rund um das Studio, in dem jemand trainiert - nicht um seinen
Wohnort und nicht um die Position, an der das Gerät gerade steht. Das ist der
Sinn der Plattform: man will Leute treffen, die im selben oder einem nahen
Studio trainieren.

Das Profilfeld ``User.gym`` hält den vollen Anzeigenamen inklusive Adresse
("FITINN — Favoritenstraße 100, 1100 Wien"). Bestandsprofile aus der Zeit vor
der Gym-Tabelle tragen dort nur den blanken Namen ("McFit"); ein solcher Name
kann auf mehrere Studios in verschiedenen PLZ zeigen und ergibt deshalb keinen
eindeutigen Punkt - diese Profile nehmen an der Umkreissuche nicht teil, bis
das Gym neu aus der Liste gewählt wurde.
"""

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from .geo import coords_for_plz
from .models import Gym, GymStatus


def gym_name_part(gym_value: Optional[str]) -> str:
    """Der Name-Teil eines Gym-Werts, ohne den Adresszusatz."""
    return (gym_value or "").split(" — ")[0].strip()


def coords_for_gyms(db: Session, gym_values: Iterable[str]) -> dict[str, tuple[float, float]]:
    """Ordnet jedem Gym-Wert seine Koordinate zu (lat, lon).

    Gym-Werte ohne eindeutig auflösbare Adresse fehlen im Ergebnis - die
    Aufrufer behandeln das als "nimmt an der Umkreissuche nicht teil".
    Eine einzige Abfrage für alle Werte, damit das Deck nicht pro Kandidat
    in die Datenbank greift.
    """
    wanted = {value for value in gym_values if value}
    if not wanted:
        return {}

    names = {gym_name_part(value) for value in wanted}
    names.discard("")
    if not names:
        return {}

    rows = (
        db.query(Gym)
        .filter(
            Gym.name.in_(names),
            Gym.status.in_([GymStatus.approved, GymStatus.pending]),
            Gym.plz != "",
        )
        .all()
    )

    by_name: dict[str, list[Gym]] = {}
    for gym in rows:
        by_name.setdefault(gym.name, []).append(gym)

    result: dict[str, tuple[float, float]] = {}
    for value in wanted:
        candidates = by_name.get(gym_name_part(value), [])
        if not candidates:
            continue
        # Volles Label -> genau ein Studio. Blanker Name -> nur dann eindeutig,
        # wenn es unter diesem Namen ohnehin nur ein Studio gibt.
        match = next((g for g in candidates if g.label == value), None)
        if match is None and len(candidates) == 1 and value == candidates[0].name:
            match = candidates[0]
        if match is None:
            continue
        coords = coords_for_plz(match.plz)
        if coords:
            result[value] = coords
    return result


def coords_for_gym(db: Session, gym_value: Optional[str]) -> Optional[tuple[float, float]]:
    """Koordinate eines einzelnen Gym-Werts, sonst None."""
    if not gym_value:
        return None
    return coords_for_gyms(db, [gym_value]).get(gym_value)
