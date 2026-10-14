"""geraetewechsel

Revision ID: c4f8a2d6e1b9
Revises: b8e4f2a6d1c7
Create Date: 2026-10-14 22:00:00.000000

device_handoffs: Einmal-Links "am Handy weitermachen" (QR-Code im
Pruefbildschirm der Web-App), nur als Hash, 10 Minuten gueltig - siehe
app/geraetewechsel.py.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4f8a2d6e1b9'
down_revision: Union[str, None] = 'b8e4f2a6d1c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'device_handoffs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_device_handoffs_user_id', 'device_handoffs', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_device_handoffs_user_id', table_name='device_handoffs')
    op.drop_table('device_handoffs')
