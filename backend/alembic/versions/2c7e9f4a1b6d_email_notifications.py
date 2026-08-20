"""Transaktionale E-Mails idempotent nachhalten.

Revision ID: 2c7e9f4a1b6d
Revises: 897067fff8a7
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2c7e9f4a1b6d"
down_revision: Union[str, None] = "897067fff8a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_notifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("notification_key", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_notifications_notification_key",
        "email_notifications",
        ["notification_key"],
        unique=True,
    )
    op.create_index(
        "ix_email_notifications_kind",
        "email_notifications",
        ["kind"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_email_notifications_kind", table_name="email_notifications")
    op.drop_index(
        "ix_email_notifications_notification_key", table_name="email_notifications"
    )
    op.drop_table("email_notifications")
