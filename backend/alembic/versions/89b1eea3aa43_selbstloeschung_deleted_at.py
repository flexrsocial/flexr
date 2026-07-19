"""selbstloeschung: deleted_at fuer 30-tage-karenz

Revision ID: 89b1eea3aa43
Revises: dd6aa5619053
Create Date: 2026-07-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89b1eea3aa43'
down_revision: Union[str, None] = 'dd6aa5619053'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'deleted_at')
