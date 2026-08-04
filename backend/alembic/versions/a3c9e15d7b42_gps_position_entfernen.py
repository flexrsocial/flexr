"""GPS-Position entfernen - die Umkreissuche geht vom Gym aus

Die Suche zentriert seit der Umstellung auf die Adresse des eingetragenen
Gyms (app/gym_geo.py). Die Geraeteposition wird dafuer nicht mehr gebraucht,
kein Client sendet sie noch, und beide Spalten waren zum Zeitpunkt der
Migration in der Produktionsdatenbank durchgehend NULL.

Revision ID: a3c9e15d7b42
Revises: f4b1c72e9a05
Create Date: 2026-08-04 07:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3c9e15d7b42'
down_revision: Union[str, None] = 'f4b1c72e9a05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('users', 'gps_lat')
    op.drop_column('users', 'gps_lon')


def downgrade() -> None:
    op.add_column('users', sa.Column('gps_lon', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('gps_lat', sa.Float(), nullable=True))
