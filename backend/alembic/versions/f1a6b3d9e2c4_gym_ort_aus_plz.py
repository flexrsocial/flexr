"""gym ort aus plz

Revision ID: f1a6b3d9e2c4
Revises: e8f3a2c7d4b1
Create Date: 2026-09-22 22:30:00.000000

Reine Datenmigration. Gyms aus dem OSM-Import ohne Ort und alle Nutzer-
Vorschlaege (das Formular fragt keinen Ort ab) hatten ein Label wie
"JOHN REED Fitness — Dominikanerbastei 15, 1010". Der Ort wird aus der PLZ
ergaenzt (app/data/plz_cities.json, dieselbe Quelle wie geo.city_for_plz).

Weil User.gym das volle Label haelt und Umkreissuche wie Profilpruefung es
zeichengenau vergleichen, ziehen die Profile mit dem alten Label mit.
"""
import json
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a6b3d9e2c4'
down_revision: Union[str, None] = 'e8f3a2c7d4b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PLZ_DATEI = Path(__file__).resolve().parents[2] / "app" / "data" / "plz_cities.json"


def _label(name, street, house_number, plz, city):
    # Wortgleich mit app.models.gym_label - hier kopiert, damit die Migration
    # nicht an spaetere Aenderungen der App-Funktion gebunden ist.
    addr = f"{street} {house_number}".strip()
    place = f"{plz} {city}".strip()
    parts = [p for p in (addr, place) if p]
    return f"{name} — {', '.join(parts)}" if parts else name


def upgrade() -> None:
    orte = json.loads(_PLZ_DATEI.read_text(encoding="utf-8"))
    bind = op.get_bind()
    zeilen = bind.execute(sa.text(
        "SELECT id, name, street, house_number, plz FROM gyms "
        "WHERE coalesce(trim(city), '') = '' AND plz <> ''"
    )).fetchall()
    for gym_id, name, street, house_number, plz in zeilen:
        ort = orte.get(plz)
        if not ort:
            continue
        alt = _label(name, street or "", house_number or "", plz, "")
        neu = _label(name, street or "", house_number or "", plz, ort)
        bind.execute(sa.text("UPDATE gyms SET city = :ort WHERE id = :id"), {"ort": ort, "id": gym_id})
        bind.execute(sa.text("UPDATE users SET gym = :neu WHERE gym = :alt"), {"neu": neu, "alt": alt})


def downgrade() -> None:
    # Bewusst leer: Welcher Ort vorher fehlte, ist nicht mehr bekannt, und ein
    # leerer Ort war nie ein gewollter Zustand.
    pass
