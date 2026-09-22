"""user login lockout

Revision ID: e8f3a2c7d4b1
Revises: d5e2f8a1b9c3
Create Date: 2026-09-22 21:30:00.000000

Gegenstueck zur Admin-Sperre aus c3d8e1a5f647 fuer normale Konten: Nach
mehreren falschen Passwoertern ist die Anmeldung kurz gesperrt - unabhaengig
davon, von wie vielen IPs die Versuche kommen.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f3a2c7d4b1'
down_revision: Union[str, None] = 'd5e2f8a1b9c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("users", sa.Column("login_locked_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "login_locked_until")
    op.drop_column("users", "failed_login_attempts")
