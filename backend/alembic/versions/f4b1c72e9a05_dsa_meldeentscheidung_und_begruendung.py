"""dsa: entscheidung zur meldung (art. 16) und begruendung der massnahme (art. 17)

Revision ID: f4b1c72e9a05
Revises: e7a2c9d14b83
Create Date: 2026-08-03 08:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4b1c72e9a05'
down_revision: Union[str, None] = 'e7a2c9d14b83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Art. 16 Abs. 5 DSA: Entscheidung ueber eine Meldung, die der Melder sieht.
    op.add_column('reports', sa.Column('outcome', sa.String(length=20), nullable=True))
    op.add_column('reports', sa.Column('decision_note', sa.String(length=500), nullable=True))

    # Bestandsdaten: abgehakte Meldungen gelten als geprueft ohne Verstoss.
    op.execute(
        "UPDATE reports SET outcome = 'no_action' "
        "WHERE dismissed_at IS NOT NULL AND outcome IS NULL"
    )

    # Art. 17 DSA: Begruendung der letzten Massnahme gegen ein Konto.
    op.add_column('users', sa.Column('moderation_action', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('moderation_reason', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('moderation_action_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'moderation_action_at')
    op.drop_column('users', 'moderation_reason')
    op.drop_column('users', 'moderation_action')
    op.drop_column('reports', 'decision_note')
    op.drop_column('reports', 'outcome')
