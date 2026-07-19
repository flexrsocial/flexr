"""gewicht entfernen - wird nicht mehr erfasst

Revision ID: dd6aa5619053
Revises: 3d77a884f91d
Create Date: 2026-07-19 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd6aa5619053'
down_revision: Union[str, None] = '3d77a884f91d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('users', 'weight_kg')


def downgrade() -> None:
    op.add_column('users', sa.Column('weight_kg', sa.Integer(), nullable=True))
