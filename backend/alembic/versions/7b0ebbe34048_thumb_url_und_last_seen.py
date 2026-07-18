"""thumb_url und last_seen

Revision ID: 7b0ebbe34048
Revises: 4fecbd02dca8
Create Date: 2026-07-18 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b0ebbe34048'
down_revision: Union[str, None] = '4fecbd02dca8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Beide Spalten bewusst nullable: Bestandsfotos haben kein Thumbnail
    # (Frontend fällt auf url zurück), Bestandsnutzer waren noch nie "online".
    op.add_column('photos', sa.Column('thumb_url', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('last_seen_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_seen_at')
    op.drop_column('photos', 'thumb_url')
