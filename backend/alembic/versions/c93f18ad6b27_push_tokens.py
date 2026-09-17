"""Push-Tokens fuer echte Zustellung (FCM)

FLEXR hatte bis hierher keinen Push-Kanal: Die Apps holten ihre
Benachrichtigungen per Hintergrundabgleich ab. Das hat eine harte Grenze -
WorkManager laesst fruehestens 15 Minuten zu, und Android schiebt den Lauf im
Doze-Modus weiter nach hinten. Eine Chatnachricht kam dadurch verspaetet an
oder erst beim naechsten Oeffnen der App.

Revision ID: c93f18ad6b27
Revises: b2e75c41a908
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c93f18ad6b27"
down_revision: Union[str, None] = "b2e75c41a908"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "push_tokens",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("platform", sa.String(length=10), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Ein Geraet gehoert zu genau einem Konto. Meldet dasselbe Geraet nach
        # einem Kontowechsel denselben Token, wandert er - sonst bekaeme der
        # Vorbesitzer die Benachrichtigungen des neuen Nutzers.
        sa.UniqueConstraint("token", name="uq_push_token"),
    )
    op.create_index("ix_push_tokens_user_id", "push_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_push_tokens_user_id", table_name="push_tokens")
    op.drop_table("push_tokens")
