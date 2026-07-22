"""koerpergroesse entfernen - wird nicht mehr erfasst

Revision ID: 990c3b5678b5
Revises: 085cc46a71ff
Create Date: 2026-07-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '990c3b5678b5'
down_revision: Union[str, None] = '085cc46a71ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('users', 'height_cm')


def downgrade() -> None:
    op.add_column('users', sa.Column('height_cm', sa.Integer(), nullable=True))
