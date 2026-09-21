"""admin login lockout

Revision ID: c3d8e1a5f647
Revises: a1c9f3e0d7b2
Create Date: 2026-09-21 17:30:00.000000

Bisher gab es nur IP-basierten Schutz gegen Bruteforce am Admin-Login
(slowapi-Limiter, Fail2ban-Jail). Ein Angreifer mit vielen IPs war davon
unberuehrt. Diese Migration ergaenzt einen kontobezogenen Zaehler: nach
mehreren Fehlversuchen (falsches Passwort oder falscher TOTP-Code) wird
das Konto fuer eine begrenzte Zeit gesperrt, unabhaengig davon, von wie
vielen verschiedenen IPs die Versuche kommen.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d8e1a5f647'
down_revision: Union[str, None] = 'a1c9f3e0d7b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "admin_users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("admin_users", sa.Column("locked_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("admin_users", "locked_until")
    op.drop_column("admin_users", "failed_login_attempts")
