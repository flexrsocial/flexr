"""Offene Likes ohne Match: neuer Benachrichtigungs-Anlass.

Revision ID: b1f994fbd4d0
Revises: a4e17c9b2d58
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1f994fbd4d0"
down_revision: Union[str, None] = "a4e17c9b2d58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Zwei weitere Schalter unter "Benachrichtigungen" - derselbe Aufbau wie die
# sechs bestehenden aus a4e17c9b2d58.
_FLAGS = (
    "notify_pending_likes_email",
    "notify_pending_likes_push",
)


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Bestehende Werte des Enums bleiben unverändert, damit ausgelieferte
    # App-Versionen die Antworten weiterhin verstehen (dasselbe Muster wie
    # b7c4e02a91d5 für "verificationstatus").
    if is_postgres:
        with op.get_context().autocommit_block():
            op.execute(
                "ALTER TYPE notificationtopic ADD VALUE IF NOT EXISTS 'pending_likes'"
            )

    for flag in _FLAGS:
        # server_default: Bestandszeilen bekommen die Voreinstellung "an",
        # sonst stuenden sie nach der Migration auf NULL und waeren damit
        # faktisch abgeschaltet, ohne dass es jemand eingestellt haette.
        op.add_column(
            "users",
            sa.Column(flag, sa.Boolean(), nullable=False, server_default=sa.true()),
        )


def downgrade() -> None:
    for flag in _FLAGS:
        op.drop_column("users", flag)

    # Der zusaetzliche Enum-Wert bleibt bestehen: PostgreSQL kann einzelne
    # Werte nicht entfernen, und ein Neuaufbau des Typs wuerde die Spalte
    # anfassen. Er stoert nicht - es gibt danach keine Zeilen mehr, die ihn
    # verwenden.
