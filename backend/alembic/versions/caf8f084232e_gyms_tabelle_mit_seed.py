"""gyms-tabelle mit osm-seed und legacy-eintraegen

Revision ID: caf8f084232e
Revises: 990c3b5678b5
Create Date: 2026-07-20 12:00:00.000000

"""
import json
import os
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'caf8f084232e'
down_revision: Union[str, None] = '990c3b5678b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_LEGACY_GYMS = [
    "John Harris Fitness", "Holmes Place", "FitInn", "Clever Fit", "McFit",
    "Fitness First", "Kraftwerk Gym", "Iron Gym Wien", "USI Wien", "Anderes Studio",
]


def upgrade() -> None:
    sa.Enum('approved', 'pending', 'rejected', name='gymstatus').create(
        op.get_bind(), checkfirst=True
    )
    # create_type=False: der Typ existiert bereits, create_table darf ihn
    # nicht erneut anlegen
    gym_status = postgresql.ENUM(
        'approved', 'pending', 'rejected', name='gymstatus', create_type=False
    )

    op.create_table(
        'gyms',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('street', sa.String(), nullable=False),
        sa.Column('house_number', sa.String(), nullable=False),
        sa.Column('plz', sa.String(length=4), nullable=False),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('status', gym_status, nullable=False),
        sa.Column('suggested_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['suggested_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_gyms_name'), 'gyms', ['name'], unique=False)
    op.create_index(op.f('ix_gyms_plz'), 'gyms', ['plz'], unique=False)

    # Seed 1: Legacy-Namen aus dem Prototyp (bestehende Profile referenzieren
    # sie) - ohne Adresse, direkt freigegeben.
    gyms_table = sa.table(
        'gyms',
        sa.column('id', sa.String), sa.column('name', sa.String),
        sa.column('street', sa.String), sa.column('house_number', sa.String),
        sa.column('plz', sa.String), sa.column('city', sa.String),
        sa.column('status', gym_status),
    )
    rows = [
        {'id': str(uuid.uuid4()), 'name': n, 'street': '', 'house_number': '',
         'plz': '', 'city': '', 'status': 'approved'}
        for n in _LEGACY_GYMS
    ]

    # Seed 2: OSM-Import (Name, Straße, Hausnummer, PLZ, Ort) - freigegeben.
    seed_file = os.path.join(
        os.path.dirname(__file__), '..', '..', 'app', 'data', 'gyms_seed.json'
    )
    with open(seed_file, encoding='utf-8') as f:
        for g in json.load(f):
            rows.append({
                'id': str(uuid.uuid4()), 'name': g['name'], 'street': g['street'],
                'house_number': g.get('house_number', ''), 'plz': g['plz'],
                'city': g.get('city', ''), 'status': 'approved',
            })

    op.bulk_insert(gyms_table, rows)


def downgrade() -> None:
    op.drop_index(op.f('ix_gyms_plz'), table_name='gyms')
    op.drop_index(op.f('ix_gyms_name'), table_name='gyms')
    op.drop_table('gyms')
    sa.Enum(name='gymstatus').drop(op.get_bind(), checkfirst=True)
