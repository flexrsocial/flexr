"""gps position und suchradius

Revision ID: b06c1b8f5dff
Revises: 7b0ebbe34048
Create Date: 2026-07-18 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b06c1b8f5dff'
down_revision: Union[str, None] = '7b0ebbe34048'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('gps_lat', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('gps_lon', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('search_radius_km', sa.Integer(), nullable=True))
    op.execute("UPDATE users SET search_radius_km = 20")
    op.alter_column('users', 'search_radius_km', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'search_radius_km')
    op.drop_column('users', 'gps_lon')
    op.drop_column('users', 'gps_lat')
