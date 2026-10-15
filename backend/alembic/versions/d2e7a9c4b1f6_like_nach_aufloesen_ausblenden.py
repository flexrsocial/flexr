"""like nach aufloesen ausblenden

Revision ID: d2e7a9c4b1f6
Revises: c4f8a2d6e1b9
Create Date: 2026-10-15 15:00:00.000000

swipes.hidden_in_incoming: Wer ein Match aufloest, bekommt den Like der
anderen Person nicht mehr als offenen Like ("Jemand hat dich geliked",
Like-Erinnerung) angezeigt. Der Like selbst bleibt bestehen - die Person
erscheint wieder im Deck, und ein erneuter Like ergibt sofort wieder ein
Match (siehe routers/matches.py:unmatch).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2e7a9c4b1f6'
down_revision: Union[str, None] = 'c4f8a2d6e1b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'swipes',
        sa.Column('hidden_in_incoming', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('swipes', 'hidden_in_incoming')
