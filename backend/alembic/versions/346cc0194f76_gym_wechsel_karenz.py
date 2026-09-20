"""gym wechsel karenz

Revision ID: 346cc0194f76
Revises: 5f8ae574bc95
Create Date: 2026-09-20 16:14:27.848394

Ohne Karenz liesse sich der von FLEXR Premium bezahlte groessere
Suchumkreis umgehen, indem der Mittelpunkt der Umkreissuche (das
eingetragene Gym) einfach mitgewandert wird. ``gym_changed_at`` haelt fest,
wann zuletzt tatsaechlich gewechselt wurde - NULL fuer Bestandskonten und
fuer die Erstwahl bei der Registrierung, die nicht als Wechsel zaehlt.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '346cc0194f76'
down_revision: Union[str, None] = '5f8ae574bc95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("gym_changed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "gym_changed_at")
