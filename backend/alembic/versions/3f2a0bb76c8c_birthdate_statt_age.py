"""birthdate statt age

Revision ID: 3f2a0bb76c8c
Revises: 7d5ac671b02b
Create Date: 2026-07-18 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f2a0bb76c8c'
down_revision: Union[str, None] = '7d5ac671b02b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('birthdate', sa.Date(), nullable=True))
    # Backfill: Aus dem gespeicherten Alter lässt sich das exakte Geburtsdatum
    # nicht rekonstruieren - wir setzen es so, dass das heutige Alter dem bisher
    # gespeicherten entspricht (Geburtstag = Migrationsdatum). Bestandsprofile
    # behalten damit ihr angezeigtes Alter.
    op.execute("UPDATE users SET birthdate = (CURRENT_DATE - (age || ' years')::interval)::date")
    op.alter_column('users', 'birthdate', nullable=False)
    op.drop_column('users', 'age')


def downgrade() -> None:
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    op.execute("UPDATE users SET age = date_part('year', age(birthdate))")
    op.alter_column('users', 'age', nullable=False)
    op.drop_column('users', 'birthdate')
