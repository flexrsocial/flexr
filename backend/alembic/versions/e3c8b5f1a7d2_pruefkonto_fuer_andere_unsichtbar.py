"""pruefkonto fuer andere unsichtbar

Revision ID: e3c8b5f1a7d2
Revises: d2e7a9c4b1f6
Create Date: 2026-10-17 12:00:00.000000

users.hidden_from_others: Das Prüfkonto für Google und Apple
(appreview@flexr.social) erscheint bei niemandem sonst - weder im Deck noch
unter "Wer dich geliket hat" noch in der Like-Erinnerung. Gesetzt wird es nicht
hier, sondern mit scripts/activate_review_account.py (siehe models.User).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3c8b5f1a7d2'
down_revision: Union[str, None] = 'd2e7a9c4b1f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('hidden_from_others', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('users', 'hidden_from_others')
