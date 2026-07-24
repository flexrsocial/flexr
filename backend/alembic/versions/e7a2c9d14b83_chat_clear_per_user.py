"""chatverlauf leeren pro nutzer: user_a/b_cleared_at

Revision ID: e7a2c9d14b83
Revises: d5f1a2b3c4e6
Create Date: 2026-07-24 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a2c9d14b83'
down_revision: Union[str, None] = 'd5f1a2b3c4e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matches', sa.Column('user_a_cleared_at', sa.DateTime(), nullable=True))
    op.add_column('matches', sa.Column('user_b_cleared_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('matches', 'user_b_cleared_at')
    op.drop_column('matches', 'user_a_cleared_at')
