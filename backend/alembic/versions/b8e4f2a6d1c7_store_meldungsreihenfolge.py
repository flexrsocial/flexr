"""store meldungsreihenfolge

Revision ID: b8e4f2a6d1c7
Revises: a3d7e1f5c9b2
Create Date: 2026-10-14 19:00:00.000000

store_subscriptions.store_signed_at: Signaturzeitpunkt der zuletzt
angewandten Store-Transaktion (Apple ``signedDate``), damit eine verspaetet
zugestellte alte Meldung das Ablaufdatum nicht zuruecksetzt (wie
users.stripe_event_at fuer Stripe).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8e4f2a6d1c7'
down_revision: Union[str, None] = 'a3d7e1f5c9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('store_subscriptions', sa.Column('store_signed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('store_subscriptions', 'store_signed_at')
