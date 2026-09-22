"""password reset

Revision ID: d5e2f8a1b9c3
Revises: c3d8e1a5f647
Create Date: 2026-09-22 20:00:00.000000

Bis hierher gab es kein "Passwort vergessen": Wer sein Passwort nicht mehr
wusste, kam nur noch ueber den Support in sein Konto. Diese Migration legt die
Tabelle fuer Zuruecksetz-Links an (Token nur als Hash) und den Zeitpunkt des
letzten Passwortwechsels, gegen den aeltere Zugriffstoken verfallen.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e2f8a1b9c3'
down_revision: Union[str, None] = 'c3d8e1a5f647'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(), nullable=True))
    op.create_table(
        "password_resets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_password_resets_user_id", "password_resets", ["user_id"])
    op.create_index("ix_password_resets_token_hash", "password_resets", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_password_resets_token_hash", table_name="password_resets")
    op.drop_index("ix_password_resets_user_id", table_name="password_resets")
    op.drop_table("password_resets")
    op.drop_column("users", "password_changed_at")
