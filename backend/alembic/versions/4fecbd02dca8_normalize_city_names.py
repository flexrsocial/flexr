"""normalize city names

Revision ID: 4fecbd02dca8
Revises: 3f2a0bb76c8c
Create Date: 2026-07-18 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fecbd02dca8'
down_revision: Union[str, None] = '3f2a0bb76c8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Der PLZ-Lookup speichert ab jetzt den Gemeindenamen ("Wien", "Graz")
    # statt der einzelnen Ortschaft ("Wien, Favoriten"). Bestandsdaten werden
    # angeglichen, damit das Stadt-Matching im Swipe-Deck (exakter Vergleich)
    # nicht an unterschiedlichen Bezirks-Schreibweisen scheitert.
    op.execute("UPDATE users SET city = trim(split_part(city, ',', 1))")


def downgrade() -> None:
    # Nicht umkehrbar - der Bezirksteil ist nach der Normalisierung nicht mehr
    # rekonstruierbar. Bewusst no-op.
    pass
