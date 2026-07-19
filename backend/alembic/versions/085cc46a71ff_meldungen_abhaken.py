"""meldungen abhaken (dismissed_at)

Revision ID: 085cc46a71ff
Revises: 89b1eea3aa43
Create Date: 2026-07-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '085cc46a71ff'
down_revision: Union[str, None] = '89b1eea3aa43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('dismissed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'dismissed_at')
