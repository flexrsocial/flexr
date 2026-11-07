"""radius_1100_for_all

Revision ID: f1a7c3e9b5d2
Revises: e5b9c2d7f4a1
Create Date: 2026-11-07 21:00:00.000000

Einmalige Datenkorrektur (Wunsch des Betreibers, 07.11.2026): Alle
bestehenden Konten bekommen den neuen vollen Suchumkreis von 1100 km
(schemas.MAX_SEARCH_RADIUS_KM, ganz Oesterreich und Deutschland). Neue Konten
starten ohnehin dort (auth.register). Der Umkreis ist derzeit fuer alle frei
(config.radius_free_for_all); wird er wieder Premium, kappt die Suche bei
jedem Aufruf (premium.clamp_radius) - der gespeicherte Wert schadet nicht.

Kein Downgrade: Die vorherigen, individuellen Werte sind nicht gesichert.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f1a7c3e9b5d2'
down_revision: Union[str, None] = 'e5b9c2d7f4a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEUER_UMKREIS_KM = 1100


def upgrade() -> None:
    op.execute(
        f"UPDATE users SET search_radius_km = {NEUER_UMKREIS_KM} "
        f"WHERE search_radius_km IS DISTINCT FROM {NEUER_UMKREIS_KM}"
    )


def downgrade() -> None:
    pass
