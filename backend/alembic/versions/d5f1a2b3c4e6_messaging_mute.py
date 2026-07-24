"""befristete chat-sperre: messaging_muted_until

Revision ID: d5f1a2b3c4e6
Revises: c610705a09a8
Create Date: 2026-07-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5f1a2b3c4e6'
down_revision: Union[str, None] = 'c610705a09a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('messaging_muted_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'messaging_muted_until')
