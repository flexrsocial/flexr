"""gyms deutschland: osm-seed der grossstaedte

Revision ID: b8d4f0a2c6e3
Revises: a7c3e9d1f5b2
Create Date: 2026-11-03 16:00:00.000000

Fuegt die deutschen Studios aus app/data/gyms_seed_de.json als freigegebene
Gyms hinzu (erzeugt von tools/gyms/build_gyms_de.py, Daten (c)
OpenStreetMap-Mitwirkende, ODbL). Getrennt vom oesterreichischen Seed, weil
caf8f084232e gyms_seed.json bei jedem frischen Aufbau neu einliest - deutsche
Eintraege dort kaemen auf neuen Datenbanken doppelt.

Studios, die es unter demselben Namen und derselben PLZ schon gibt (z. B. von
Nutzern vorgeschlagen), werden uebersprungen.
"""
import json
import os
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8d4f0a2c6e3'
down_revision: Union[str, None] = 'a7c3e9d1f5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEED = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'data', 'gyms_seed_de.json')


def _seed() -> list[dict]:
    with open(_SEED, encoding='utf-8') as f:
        return json.load(f)


def upgrade() -> None:
    bind = op.get_bind()
    vorhanden = {
        (name.lower(), plz)
        for name, plz in bind.execute(sa.text("SELECT name, plz FROM gyms WHERE length(plz) = 5"))
    }
    gyms = sa.table(
        'gyms',
        sa.column('id', sa.String), sa.column('name', sa.String),
        sa.column('street', sa.String), sa.column('house_number', sa.String),
        sa.column('plz', sa.String), sa.column('city', sa.String),
        sa.column('status', sa.String),
    )
    zeilen = []
    for g in _seed():
        schluessel = (g['name'].lower(), g['plz'])
        if schluessel in vorhanden:
            continue
        vorhanden.add(schluessel)
        zeilen.append({
            'id': str(uuid.uuid4()), 'name': g['name'], 'street': g['street'],
            'house_number': g.get('house_number', ''), 'plz': g['plz'],
            'city': g['city'], 'status': 'approved',
        })
    if zeilen:
        if bind.dialect.name == 'postgresql':
            # status ist ein Postgres-Enum; bulk_insert mit String-Spalte
            # braeuchte sonst einen Cast.
            bind.execute(
                sa.text(
                    "INSERT INTO gyms (id, name, street, house_number, plz, city, status, created_at) "
                    "VALUES (:id, :name, :street, :house_number, :plz, :city, 'approved', now())"
                ),
                zeilen,
            )
        else:
            op.bulk_insert(gyms, zeilen)


def downgrade() -> None:
    # Nur Seed-Eintraege ohne Vorschlagenden; Nutzer-Vorschlaege bleiben.
    bind = op.get_bind()
    for g in _seed():
        bind.execute(
            sa.text(
                "DELETE FROM gyms WHERE name = :name AND plz = :plz AND street = :street "
                "AND suggested_by IS NULL"
            ),
            {'name': g['name'], 'plz': g['plz'], 'street': g['street']},
        )
