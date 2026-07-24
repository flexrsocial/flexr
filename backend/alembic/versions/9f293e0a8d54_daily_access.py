"""daily_access fuer zugriffsstatistik

Revision ID: 9f293e0a8d54
Revises: caf8f084232e
Create Date: 2026-07-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f293e0a8d54'
down_revision: Union[str, None] = 'caf8f084232e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'daily_access',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'day', 'country', name='uq_daily_access'),
    )
    op.create_index(op.f('ix_daily_access_day'), 'daily_access', ['day'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_daily_access_day'), table_name='daily_access')
    op.drop_table('daily_access')
