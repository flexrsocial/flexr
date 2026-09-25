"""web push

Revision ID: b7c2e4f9a1d3
Revises: f1a6b3d9e2c4
Create Date: 2026-09-25 18:30:00.000000

Web-Push-Abos (vor allem die Web-App auf dem iPhone-Home-Bildschirm, solange
es keine App-Store-App gibt) liegen in derselben Tabelle wie die Geraetetokens
der Apps, mit platform = "web":

* ``token`` haelt dann den Endpunkt des Push-Dienstes - eine URL, die laenger
  werden kann als ein FCM- oder APNs-Token. Deshalb 512 -> 1024.
* ``web_p256dh`` und ``web_auth`` sind die beiden Schluessel aus dem
  Browser-Abo, ohne die sich keine Nachricht verschluesseln laesst (RFC 8291).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c2e4f9a1d3'
down_revision: Union[str, None] = 'f1a6b3d9e2c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'push_tokens', 'token',
        existing_type=sa.String(length=512), type_=sa.String(length=1024),
        existing_nullable=False,
    )
    op.add_column('push_tokens', sa.Column('web_p256dh', sa.String(length=128), nullable=True))
    op.add_column('push_tokens', sa.Column('web_auth', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.execute("DELETE FROM push_tokens WHERE platform = 'web'")
    op.drop_column('push_tokens', 'web_auth')
    op.drop_column('push_tokens', 'web_p256dh')
    op.alter_column(
        'push_tokens', 'token',
        existing_type=sa.String(length=1024), type_=sa.String(length=512),
        existing_nullable=False,
    )
