"""admin totp 2fa

Revision ID: a1c9f3e0d7b2
Revises: 346cc0194f76
Create Date: 2026-09-21 15:40:00.000000

Root-SSH bekam TOTP-2FA am selben Tag - dasselbe Prinzip jetzt auch fuer
den admin_users-Login. totp_secret bleibt NULL bis zum abgeschlossenen
Setup (siehe /api/admin/auth/totp/setup + /confirm); totp_enabled schaltet
die Pflichtabfrage beim Login erst nach bestaetigtem Code scharf, damit ein
Tippfehler beim Scannen niemanden aussperrt.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c9f3e0d7b2'
down_revision: Union[str, None] = '346cc0194f76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("admin_users", sa.Column("totp_secret", sa.String(), nullable=True))
    op.add_column(
        "admin_users",
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("admin_users", "totp_enabled")
    op.drop_column("admin_users", "totp_secret")
