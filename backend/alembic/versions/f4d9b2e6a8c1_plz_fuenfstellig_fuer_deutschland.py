"""plz fuenfstellig fuer deutschland

Revision ID: f4d9b2e6a8c1
Revises: e3c8b5f1a7d2
Create Date: 2026-11-03 12:00:00.000000

users.plz und gyms.plz von VARCHAR(4) auf VARCHAR(5): Deutsche PLZ haben fünf
Stellen. Postgres schneidet zu lange Werte nicht ab, sondern lehnt den INSERT
ab - ohne diese Migration endet jede deutsche Registrierung mit HTTP 500.
Bestehende Werte bleiben unverändert (Verbreitern ist verlustfrei).

Das Zurückrollen geht nur, solange noch keine fünfstellige PLZ gespeichert
ist; sonst bricht Postgres das ALTER selbst ab, statt Daten abzuschneiden.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f4d9b2e6a8c1'
down_revision: Union[str, None] = 'e3c8b5f1a7d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ('users', 'gyms'):
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                'plz', type_=sa.String(length=5), existing_type=sa.String(length=4),
                existing_nullable=False,
            )


def downgrade() -> None:
    for table in ('users', 'gyms'):
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                'plz', type_=sa.String(length=4), existing_type=sa.String(length=5),
                existing_nullable=False,
            )
