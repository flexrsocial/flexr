"""stripe ereignis reihenfolge

Revision ID: d2a9f4c6b8e1
Revises: c5e1d8a3f7b2
Create Date: 2026-09-30 15:00:00.000000

users.stripe_event_at: Zeitpunkt des zuletzt angewandten Abo-Ereignisses,
damit ein verspaetet zugestelltes "updated" ein beendetes Abo nicht wieder
oeffnet.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2a9f4c6b8e1'
down_revision: Union[str, None] = 'c5e1d8a3f7b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('stripe_event_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'stripe_event_at')
